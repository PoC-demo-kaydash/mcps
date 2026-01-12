"""
Document Server

문서 CRUD 관리 Tool 제공
"""

import sys
import os
import json
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
from shared.mcp_protocol import MCPProtocol
from shared.logging_config import setup_logging, get_logger
from mcp_tools.core.document_tools import (
    GetDocumentTool,
    CreateDocumentTool,
    UpdateDocumentTool,
    DeleteDocumentTool,
    ListDocumentsTool
)

# 로거 설정
setup_logging()
logger = get_logger("document_server")


class DocumentServer:
    """
    Document Server
    
    제공하는 Tool:
    - get_document: 문서 조회
    - create_document: 문서 생성
    - update_document: 문서 수정
    - delete_document: 문서 삭제
    - list_documents: 문서 목록
    """
    
    def __init__(self):
        """초기화"""
        self.protocol = MCPProtocol()
        self.db = None
        self.es = None
        self.tools = {}
    
    async def initialize(self):
        """리소스 초기화"""
        logger.info("=" * 60)
        logger.info("Document Server Initializing...")
        logger.info("=" * 60)
        
        # Database 연결
        self.db = DatabaseManager(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            database=os.getenv("DB_NAME", "mcps_db"),
            user=os.getenv("DB_USER", "mcps_user"),
            password=os.getenv("DB_PASSWORD", "your_password"),
            charset="utf8mb4"
        )
        
        await self.db.initialize()
        logger.info("✓ Database connected")
        
        # Elasticsearch 연결
        es_hosts = os.getenv("ES_HOSTS", "localhost:9200").split(",")
        self.es = ElasticsearchManager(
            hosts=es_hosts,
            timeout=int(os.getenv("ES_TIMEOUT", "30"))
        )
        
        await self.es.initialize()
        logger.info("✓ Elasticsearch connected")
        
        # Tool 초기화
        self.tools = {
            "get_document": GetDocumentTool(self.db),
            "create_document": CreateDocumentTool(self.db, self.es),
            "update_document": UpdateDocumentTool(self.db, self.es),
            "delete_document": DeleteDocumentTool(self.db, self.es),
            "list_documents": ListDocumentsTool(self.db)
        }
        
        logger.info(f"✓ Initialized {len(self.tools)} tools")
        logger.info("=" * 60)
        logger.info("Document Server Ready")
        logger.info("=" * 60)
    
    async def handle_tools_list(self, params: dict) -> dict:
        """
        Tool 목록 요청 처리
        
        Args:
            params: 요청 파라미터
        
        Returns:
            dict: Tool 목록
        """
        tools_list = []
        
        for name, tool in self.tools.items():
            tool_info = {
                "name": name,
                "description": tool.metadata.description,
                "inputSchema": tool.metadata.input_schema,
                "category": tool.metadata.category,
                "requiredPermissions": tool.metadata.required_permissions
            }
            tools_list.append(tool_info)
        
        return {"tools": tools_list}
    
    async def handle_tools_call(self, params: dict) -> dict:
        """
        Tool 실행 요청 처리
        
        Args:
            params: {
                "name": "tool_name",
                "arguments": {...},
                "_context": {
                    "user_id": "U001",
                    "user_role": "engineer",
                    "user_team": "dev_team"
                }
            }
        
        Returns:
            dict: 실행 결과
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        context = params.get("_context", {})
        
        # Tool 존재 확인
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = self.tools[tool_name]
        
        # Tool 실행
        try:
            result = await tool.execute(arguments, context)
            return result
        
        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}")
            raise
    
    async def run(self):
        """메인 루프 (STDIO 통신)"""
        logger.info("Starting STDIO communication loop...")
        
        try:
            while True:
                # STDIN에서 요청 읽기
                line = sys.stdin.readline()
                
                if not line:
                    # EOF
                    logger.info("Received EOF, shutting down...")
                    break
                
                try:
                    # JSON-RPC 요청 파싱
                    request = json.loads(line.strip())
                    
                    # 요청 처리
                    method = request.get("method")
                    params = request.get("params", {})
                    request_id = request.get("id")
                    
                    logger.debug(f"Received request: {method} (id: {request_id})")
                    
                    # Handler 실행
                    if method == "tools/list":
                        result = await self.handle_tools_list(params)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": result
                        }
                    
                    elif method == "tools/call":
                        result = await self.handle_tools_call(params)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": result
                        }
                    
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": "METHOD_NOT_FOUND",
                                "message": f"Unknown method: {method}"
                            }
                        }
                
                except Exception as e:
                    logger.error(f"Request handling error: {e}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id") if 'request' in locals() else None,
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": str(e)
                        }
                    }
                
                # STDOUT으로 응답 전송
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """리소스 정리"""
        logger.info("Cleaning up resources...")
        
        if self.es:
            await self.es.close()
            logger.info("✓ Elasticsearch connection closed")
        
        if self.db:
            await self.db.close()
            logger.info("✓ Database connection closed")
        
        logger.info("Document Server stopped")


async def main():
    """메인 함수"""
    server = DocumentServer()
    
    try:
        await server.initialize()
        await server.run()
    
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

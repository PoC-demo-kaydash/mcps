"""
Version Server

문서 버전 관리 Tool 제공
"""

import sys
import os
import json
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.database import DatabaseManager
from shared.mcp_protocol import MCPProtocol
from shared.logging_config import setup_logging, get_logger
from mcp_tools.core.version_tools import (
    GetDocumentVersionsTool,
    GetDocumentVersionTool,
    CompareVersionsTool
)

# 로거 설정
setup_logging()
logger = get_logger("version_server")


class VersionServer:
    """
    Version Server
    
    제공하는 Tool:
    - get_document_versions: 문서 버전 목록
    - get_document_version: 특정 버전 조회
    - compare_versions: 버전 비교
    """
    
    def __init__(self):
        """초기화"""
        self.protocol = MCPProtocol()
        self.db = None
        self.tools = {}
    
    async def initialize(self):
        """리소스 초기화"""
        logger.info("=" * 60)
        logger.info("Version Server Initializing...")
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
        
        # Tool 초기화
        self.tools = {
            "get_document_versions": GetDocumentVersionsTool(self.db),
            "get_document_version": GetDocumentVersionTool(self.db),
            "compare_versions": CompareVersionsTool(self.db)
        }
        
        logger.info(f"✓ Initialized {len(self.tools)} tools")
        logger.info("=" * 60)
        logger.info("Version Server Ready")
        logger.info("=" * 60)
    
    async def handle_tools_list(self, params: dict) -> dict:
        """Tool 목록 요청 처리"""
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
        """Tool 실행 요청 처리"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        context = params.get("_context", {})
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = self.tools[tool_name]
        
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
                line = sys.stdin.readline()
                
                if not line:
                    logger.info("Received EOF, shutting down...")
                    break
                
                try:
                    request = json.loads(line.strip())
                    method = request.get("method")
                    params = request.get("params", {})
                    request_id = request.get("id")
                    
                    logger.debug(f"Received request: {method} (id: {request_id})")
                    
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
                
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """리소스 정리"""
        logger.info("Cleaning up resources...")
        
        if self.db:
            await self.db.close()
            logger.info("✓ Database connection closed")
        
        logger.info("Version Server stopped")


async def main():
    """메인 함수"""
    server = VersionServer()
    
    try:
        await server.initialize()
        await server.run()
    
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

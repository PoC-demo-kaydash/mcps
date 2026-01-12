"""
문서 검색 Tool

Elasticsearch 기반 전문 검색 및 자동완성 기능 제공
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_tools.base import BaseTool, ToolMetadata
from shared.elasticsearch import ElasticsearchManager
from shared.permissions import PermissionEngine
from shared.logging_config import get_logger

logger = get_logger(__name__)


class SearchDocumentsTool(BaseTool):
    """
    문서 전문 검색 Tool
    
    Elasticsearch 기반 검색
    """
    
    def __init__(self, es: ElasticsearchManager):
        self.es = es
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="search_documents",
            description="문서 전문 검색 (Elasticsearch 기반)",
            category="search",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색어"
                    },
                    "classification": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "문서 등급 필터"
                    },
                    "category": {
                        "type": "string",
                        "description": "카테고리 필터"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "offset": {
                        "type": "integer",
                        "default": 0
                    }
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "total": {"type": "integer"},
                    "results": {"type": "array"},
                    "execution_time_ms": {"type": "number"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """검색 실행"""
        import time
        start_time = time.time()
        
        try:
            # 1. 입력 검증
            valid, error = self.validate_arguments(arguments)
            if not valid:
                return self.create_error_response(error, "INVALID_INPUT")
            
            # 2. 검색 파라미터 추출
            query_text = arguments["query"]
            limit = arguments.get("limit", 10)
            offset = arguments.get("offset", 0)
            
            # 3. 접근 가능한 문서 등급 필터
            if context:
                user_role = context.get("user_role", "")
                accessible_classifications = self.perm_engine.get_accessible_classifications(user_role)
                classifications = arguments.get("classification", accessible_classifications)
                # 권한 있는 등급만 필터링
                classifications = [c for c in classifications if c in accessible_classifications]
            else:
                classifications = arguments.get("classification", ["public"])
            
            # 4. 검색 실행
            result = self.es.search_documents(
                query_text=query_text,
                classifications=classifications,
                category=arguments.get("category"),
                team=context.get("user_team") if context else None,
                size=limit,
                from_=offset
            )
            
            # 5. 결과 반환
            execution_time = (time.time() - start_time) * 1000
            
            return self.create_success_response({
                "total": result.get("total", 0),
                "results": result.get("hits", []),
                "query": query_text,
                "execution_time_ms": round(execution_time, 2)
            })
        
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return self.create_error_response(
                str(e),
                "SEARCH_ERROR",
                {"query": arguments.get("query")}
            )


class SuggestDocumentsTool(BaseTool):
    """
    문서 자동완성 Tool
    """
    
    def __init__(self, es: ElasticsearchManager):
        self.es = es
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="suggest_documents",
            description="문서 제목 자동완성",
            category="search",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "prefix": {
                        "type": "string",
                        "minLength": 1,
                        "description": "검색 prefix"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "maximum": 20
                    }
                },
                "required": ["prefix"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "suggestions": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """자동완성 실행"""
        try:
            prefix = arguments["prefix"]
            limit = arguments.get("limit", 5)
            
            # Elasticsearch completion suggester 또는 prefix 쿼리
            result = self.es.suggest_documents(prefix, limit)
            
            return self.create_success_response({
                "suggestions": result.get("suggestions", [])
            })
        
        except Exception as e:
            logger.error(f"Suggest failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "SUGGEST_ERROR")

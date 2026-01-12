"""
문서 버전 관리 Tool

문서 버전 히스토리 조회, 특정 버전 조회, 버전 비교 기능 제공
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_tools.base import BaseTool, ToolMetadata
from shared.database import DatabaseManager
from shared.permissions import PermissionEngine, User, Document
from shared.logging_config import get_logger
from shared.queries import DocumentQueries

logger = get_logger(__name__)


class GetDocumentVersionsTool(BaseTool):
    """문서 버전 히스토리 조회 Tool"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_document_versions",
            description="문서 버전 히스토리 조회",
            category="version",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"}
                },
                "required": ["doc_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "current_version": {"type": "integer"},
                    "versions": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """버전 히스토리 조회"""
        try:
            doc_id = arguments["doc_id"]
            
            # 1. 문서 권한 확인
            query, params = DocumentQueries.get_by_id(doc_id)
            docs = self.db.fetch_all(query, params)
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            if context:
                user = User(
                    context["user_id"],
                    context.get("user_name", ""),
                    context["user_role"],
                    self.perm_engine.get_role_level(context["user_role"]),
                    context.get("user_team")
                )
                doc_obj = Document(
                    doc["id"],
                    doc["title"],
                    doc["author_id"],
                    doc["classification"],
                    doc.get("team")
                )
                
                if not self.perm_engine.can_view_document(user, doc_obj):
                    return self.create_error_response(
                        "Permission denied",
                        "PERMISSION_DENIED"
                    )
            
            # 2. 버전 히스토리 조회
            version_query = """
            SELECT * FROM document_versions
            WHERE document_id = %s
            ORDER BY version DESC
            """
            versions = self.db.fetch_all(version_query, (doc_id,))
            
            return self.create_success_response({
                "doc_id": doc_id,
                "current_version": doc.get("version", 1),
                "versions": [
                    {
                        "version": v["version"],
                        "title": v["title"],
                        "created_at": v["created_at"].isoformat() if v.get("created_at") else None
                    }
                    for v in versions
                ]
            })
        
        except Exception as e:
            logger.error(f"Get versions failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "VERSION_ERROR")


class GetDocumentVersionTool(BaseTool):
    """특정 버전 문서 조회 Tool"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_document_version",
            description="특정 버전 문서 내용 조회",
            category="version",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "version": {"type": "integer", "minimum": 1}
                },
                "required": ["doc_id", "version"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "version": {"type": "integer"},
                    "title": {"type": "string"},
                    "content": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """특정 버전 조회"""
        try:
            doc_id = arguments["doc_id"]
            version = arguments["version"]
            
            # 1. 권한 확인
            query, params = DocumentQueries.get_by_id(doc_id)
            docs = self.db.fetch_all(query, params)
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            if context:
                user = User(
                    context["user_id"],
                    context.get("user_name", ""),
                    context["user_role"],
                    self.perm_engine.get_role_level(context["user_role"]),
                    context.get("user_team")
                )
                doc_obj = Document(
                    doc["id"],
                    doc["title"],
                    doc["author_id"],
                    doc["classification"],
                    doc.get("team")
                )
                
                if not self.perm_engine.can_view_document(user, doc_obj):
                    return self.create_error_response(
                        "Permission denied",
                        "PERMISSION_DENIED"
                    )
            
            # 2. 버전 조회
            version_query = """
            SELECT * FROM document_versions
            WHERE document_id = %s AND version = %s
            """
            versions = self.db.fetch_all(version_query, (doc_id, version))
            
            if not versions:
                return self.create_error_response(
                    f"Version {version} not found",
                    "NOT_FOUND"
                )
            
            version_data = versions[0]
            
            return self.create_success_response({
                "doc_id": doc_id,
                "version": version,
                "title": version_data["title"],
                "content": version_data["content"],
                "created_at": version_data["created_at"].isoformat() if version_data.get("created_at") else None
            })
        
        except Exception as e:
            logger.error(f"Get version failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "VERSION_ERROR")


class CompareVersionsTool(BaseTool):
    """문서 버전 비교 Tool"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="compare_versions",
            description="두 버전 비교 (diff)",
            category="version",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "version1": {"type": "integer"},
                    "version2": {"type": "integer"}
                },
                "required": ["doc_id", "version1", "version2"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "version1": {"type": "integer"},
                    "version2": {"type": "integer"},
                    "diff": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """버전 비교"""
        try:
            doc_id = arguments["doc_id"]
            version1 = arguments["version1"]
            version2 = arguments["version2"]
            
            # 1. 권한 확인
            query, params = DocumentQueries.get_by_id(doc_id)
            docs = self.db.fetch_all(query, params)
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            if context:
                user = User(
                    context["user_id"],
                    context.get("user_name", ""),
                    context["user_role"],
                    self.perm_engine.get_role_level(context["user_role"]),
                    context.get("user_team")
                )
                doc_obj = Document(
                    doc["id"],
                    doc["title"],
                    doc["author_id"],
                    doc["classification"],
                    doc.get("team")
                )
                
                if not self.perm_engine.can_view_document(user, doc_obj):
                    return self.create_error_response(
                        "Permission denied",
                        "PERMISSION_DENIED"
                    )
            
            # 2. 두 버전 조회
            version_query = """
            SELECT * FROM document_versions
            WHERE document_id = %s AND version = %s
            """
            v1_data = self.db.fetch_all(version_query, (doc_id, version1))
            v2_data = self.db.fetch_all(version_query, (doc_id, version2))
            
            if not v1_data or not v2_data:
                return self.create_error_response(
                    "One or both versions not found",
                    "NOT_FOUND"
                )
            
            # 3. Diff 생성
            import difflib
            
            content1 = v1_data[0]["content"].splitlines()
            content2 = v2_data[0]["content"].splitlines()
            
            diff = difflib.unified_diff(
                content1,
                content2,
                fromfile=f"Version {version1}",
                tofile=f"Version {version2}",
                lineterm=""
            )
            
            diff_text = "\n".join(diff)
            
            return self.create_success_response({
                "doc_id": doc_id,
                "version1": version1,
                "version2": version2,
                "diff": diff_text
            })
        
        except Exception as e:
            logger.error(f"Compare versions failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "COMPARE_ERROR")

"""
문서 CRUD Tool

문서 생성, 조회, 수정, 삭제, 목록 조회 기능 제공
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_tools.base import BaseTool, ToolMetadata
from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
from shared.permissions import PermissionEngine, User, Document
from shared.logging_config import get_logger
from shared.utils import generate_id, now_iso
from shared.queries import DocumentQueries

logger = get_logger(__name__)


class GetDocumentTool(BaseTool):
    """문서 상세 조회 Tool"""
    
    def __init__(self, db: DatabaseManager, es: ElasticsearchManager):
        self.db = db
        self.es = es
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_document",
            description="문서 상세 정보 조회",
            category="document",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string", "description": "문서 ID"}
                },
                "required": ["doc_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "classification": {"type": "string"},
                    "author": {"type": "object"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """문서 조회"""
        try:
            doc_id = arguments["doc_id"]
            
            # 1. 문서 조회
            query, params = DocumentQueries.get_by_id(doc_id)
            docs = self.db.fetch_all(query, params)
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            # 2. 권한 확인
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
                        "Permission denied to view this document",
                        "PERMISSION_DENIED"
                    )
            
            # 3. 응답 생성
            return self.create_success_response({
                "doc_id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "classification": doc["classification"],
                "category": doc.get("category"),
                "team": doc.get("team"),
                "version": doc.get("version", 1),
                "author": {
                    "user_id": doc["author_id"],
                    "name": doc.get("author_name", "Unknown")
                },
                "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
                "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None
            })
        
        except Exception as e:
            logger.error(f"Get document failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "DATABASE_ERROR")


class CreateDocumentTool(BaseTool):
    """문서 생성 Tool"""
    
    def __init__(self, db: DatabaseManager, es: ElasticsearchManager):
        self.db = db
        self.es = es
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="create_document",
            description="새 문서 생성",
            category="document",
            department="core",
            version="1.0.0",
            required_permissions=["document:create"],
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "minLength": 1, "maxLength": 255},
                    "content": {"type": "string"},
                    "classification": {"type": "string", "enum": ["public", "team", "confidential"]},
                    "category": {"type": "string"}
                },
                "required": ["title", "content", "classification"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "message": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """문서 생성"""
        try:
            # 1. 권한 확인
            if context:
                classification = arguments["classification"]
                user_role = context.get("user_role", "")
                
                # confidential은 executive 이상만 생성 가능
                if classification == "confidential":
                    if self.perm_engine.get_role_level(user_role) < 4:
                        return self.create_error_response(
                            "Permission denied to create confidential documents",
                            "PERMISSION_DENIED"
                        )
            
            # 2. 문서 ID 생성
            doc_id = generate_id("DOC", 8)
            
            # 3. team 설정
            team = None
            if arguments["classification"] == "team":
                if context and context.get("user_team"):
                    team = context["user_team"]
            
            # 4. DB 저장
            query, params = DocumentQueries.create(
                doc_id=doc_id,
                title=arguments["title"],
                content=arguments["content"],
                classification=arguments["classification"],
                category=arguments.get("category", "general"),
                author_id=context.get("user_id", "system") if context else "system",
                team=team
            )
            self.db.execute(query, params)
            
            # 5. Elasticsearch 색인
            self.es.index_document(
                "documents",
                doc_id,
                {
                    "doc_id": doc_id,
                    "title": arguments["title"],
                    "content": arguments["content"],
                    "classification": arguments["classification"],
                    "category": arguments.get("category", "general"),
                    "team": team,
                    "created_at": now_iso()
                }
            )
            
            logger.info(f"Document created: {doc_id} by {context.get('user_id') if context else 'system'}")
            
            return self.create_success_response({
                "doc_id": doc_id,
                "message": f"Document created successfully: {doc_id}"
            })
        
        except Exception as e:
            logger.error(f"Create document failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "CREATE_ERROR")


class UpdateDocumentTool(BaseTool):
    """문서 수정 Tool"""
    
    def __init__(self, db: DatabaseManager, es: ElasticsearchManager):
        self.db = db
        self.es = es
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="update_document",
            description="문서 수정",
            category="document",
            department="core",
            version="1.0.0",
            required_permissions=["document:update"],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "classification": {"type": "string"}
                },
                "required": ["doc_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "version": {"type": "integer"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """문서 수정"""
        try:
            doc_id = arguments["doc_id"]
            
            # 1. 기존 문서 조회
            query, params = DocumentQueries.get_by_id(doc_id)
            docs = self.db.fetch_all(query, params)
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            # 2. 권한 확인
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
                
                if not self.perm_engine.can_edit_document(user, doc_obj):
                    return self.create_error_response(
                        "Permission denied to edit this document",
                        "PERMISSION_DENIED"
                    )
            
            # 3. 업데이트 필드 준비
            updates = {}
            if "title" in arguments:
                updates["title"] = arguments["title"]
            if "content" in arguments:
                updates["content"] = arguments["content"]
            if "classification" in arguments:
                updates["classification"] = arguments["classification"]
            
            if not updates:
                return self.create_error_response(
                    "No fields to update",
                    "INVALID_INPUT"
                )
            
            # 4. 버전 증가
            new_version = doc.get("version", 1) + 1
            
            # 5. DB 업데이트
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            update_query = f"""
            UPDATE documents 
            SET {set_clause}, version = %s, updated_at = NOW() 
            WHERE id = %s
            """
            params = list(updates.values()) + [new_version, doc_id]
            self.db.execute(update_query, tuple(params))
            
            # 6. Elasticsearch 업데이트
            es_update = updates.copy()
            es_update["updated_at"] = now_iso()
            es_update["version"] = new_version
            self.es.update_document("documents", doc_id, es_update)
            
            logger.info(f"Document updated: {doc_id} to v{new_version}")
            
            return self.create_success_response({
                "message": f"Document updated to version {new_version}",
                "version": new_version
            })
        
        except Exception as e:
            logger.error(f"Update document failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "UPDATE_ERROR")


class DeleteDocumentTool(BaseTool):
    """문서 삭제 Tool"""
    
    def __init__(self, db: DatabaseManager, es: ElasticsearchManager):
        self.db = db
        self.es = es
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="delete_document",
            description="문서 삭제",
            category="document",
            department="core",
            version="1.0.0",
            required_permissions=["document:delete"],
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
                    "message": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """문서 삭제"""
        try:
            doc_id = arguments["doc_id"]
            
            # 1. 문서 조회
            query, params = DocumentQueries.get_by_id(doc_id)
            docs = self.db.fetch_all(query, params)
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            # 2. 권한 확인
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
                
                if not self.perm_engine.can_delete_document(user, doc_obj):
                    return self.create_error_response(
                        "Permission denied to delete this document",
                        "PERMISSION_DENIED"
                    )
            
            # 3. DB 삭제
            delete_query, delete_params = DocumentQueries.delete(doc_id)
            self.db.execute(delete_query, delete_params)
            
            # 4. Elasticsearch 삭제
            self.es.delete_document("documents", doc_id)
            
            logger.info(f"Document deleted: {doc_id} by {context.get('user_id') if context else 'system'}")
            
            return self.create_success_response({
                "message": f"Document deleted: {doc_id}"
            })
        
        except Exception as e:
            logger.error(f"Delete document failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "DELETE_ERROR")


class ListDocumentsTool(BaseTool):
    """문서 목록 조회 Tool"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="list_documents",
            description="문서 목록 조회 (페이지네이션)",
            category="document",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "classification": {"type": "array", "items": {"type": "string"}},
                    "category": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "total": {"type": "integer"},
                    "documents": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """문서 목록 조회"""
        try:
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            
            # 1. 접근 가능한 등급
            if context:
                user_role = context.get("user_role", "")
                accessible = self.perm_engine.get_accessible_classifications(user_role)
            else:
                accessible = ["public"]
            
            # 2. 쿼리 구성
            placeholders = ", ".join(["%s"] * len(accessible))
            query = f"""
            SELECT d.*, u.name as author_name
            FROM documents d
            LEFT JOIN users u ON d.author_id = u.id
            WHERE d.classification IN ({placeholders})
            """
            
            params = list(accessible)
            
            # 카테고리 필터
            if arguments.get("category"):
                query += " AND d.category = %s"
                params.append(arguments["category"])
            
            # team 필터
            if "team" in accessible and context and context.get("user_team"):
                query += " AND (d.classification != 'team' OR d.team = %s)"
                params.append(context["user_team"])
            
            query += " ORDER BY d.updated_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # 3. 실행
            documents = self.db.fetch_all(query, tuple(params))
            
            # 4. 총 개수
            count_query = f"SELECT COUNT(*) AS total FROM documents d WHERE d.classification IN ({placeholders})"
            count_params = list(accessible)
            
            if arguments.get("category"):
                count_query += " AND d.category = %s"
                count_params.append(arguments["category"])
            
            result = self.db.fetch_one(count_query, tuple(count_params))
            total = result["total"] if result else 0
            
            # 5. 응답
            return self.create_success_response({
                "total": total,
                "limit": limit,
                "offset": offset,
                "documents": [
                    {
                        "doc_id": d["id"],
                        "title": d["title"],
                        "classification": d["classification"],
                        "category": d.get("category"),
                        "author": {
                            "user_id": d["author_id"],
                            "name": d.get("author_name", "Unknown")
                        },
                        "version": d.get("version", 1),
                        "created_at": d["created_at"].isoformat() if d.get("created_at") else None,
                        "updated_at": d["updated_at"].isoformat() if d.get("updated_at") else None
                    }
                    for d in documents
                ]
            })
        
        except Exception as e:
            logger.error(f"List documents failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "LIST_ERROR")

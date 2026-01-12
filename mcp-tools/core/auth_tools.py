"""
인증 및 권한 관리 Tool

사용자 인증, 접근 권한 요청/승인, 권한 조회 기능 제공
"""

import sys
from pathlib import Path

# shared 모듈 import를 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_tools.base import BaseTool, ToolMetadata
from shared.database import DatabaseManager
from shared.permissions import PermissionEngine
from shared.logging_config import get_logger
from shared.utils import generate_id

logger = get_logger(__name__)


class AuthenticateTool(BaseTool):
    """
    사용자 인증 Tool
    
    PoC에서는 user_id만으로 인증 (실제 운영에서는 토큰 기반)
    """
    
    def __init__(self, db: DatabaseManager):
        """
        초기화
        
        Args:
            db: DatabaseManager 인스턴스
        """
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        """메타데이터 정의"""
        return ToolMetadata(
            name="authenticate",
            description="사용자 인증 (PoC: 사용자 선택)",
            category="auth",
            department="core",
            version="1.0.0",
            required_permissions=[],  # 인증 전이므로 권한 불필요
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "사용자 ID (예: U001)"
                    }
                },
                "required": ["user_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "user": {"type": "object"},
                    "token": {"type": "string"},
                    "message": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """
        사용자 인증
        
        Args:
            arguments: {"user_id": "U001"}
        
        Returns:
            인증 결과 및 사용자 정보
        """
        try:
            # 1. 입력 검증
            valid, error = self.validate_arguments(arguments)
            if not valid:
                return self.create_error_response(error, "INVALID_INPUT")
            
            user_id = arguments["user_id"]
            
            # 2. 사용자 조회
            from shared.queries import UserQueries
            query, params = UserQueries.get_by_id(user_id)
            users = self.db.fetch_all(query, params)
            
            if not users:
                return self.create_error_response(
                    f"User not found: {user_id}",
                    "NOT_FOUND"
                )
            
            user = users[0]
            
            # 3. 활성 상태 확인
            if not user.get("active", True):
                return self.create_error_response(
                    f"User account is inactive: {user_id}",
                    "AUTH_ERROR"
                )
            
            # 4. 토큰 생성 (PoC: 간단한 토큰)
            import hashlib
            import time
            token = hashlib.sha256(
                f"{user_id}:{time.time()}".encode()
            ).hexdigest()[:32]
            
            # 5. 감사 로그
            from shared.queries import AuditLogQueries
            log_query, log_params = AuditLogQueries.create(
                user_id=user_id,
                action="login",
                resource_type="user",
                resource_id=user_id,
                result="success"
            )
            self.db.execute(log_query, log_params)
            
            logger.info(f"User authenticated: {user_id} ({user['name']})")
            
            return self.create_success_response({
                "user": {
                    "user_id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                    "team": user["team"],
                    "active": user["active"]
                },
                "token": token,
                "message": f"Welcome, {user['name']}!"
            })
        
        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "AUTH_ERROR")


class RequestAccessTool(BaseTool):
    """
    문서 접근 권한 요청 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="request_access",
            description="문서 접근 권한 요청",
            category="auth",
            department="core",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "description": "문서 ID"
                    },
                    "reason": {
                        "type": "string",
                        "description": "요청 사유"
                    }
                },
                "required": ["doc_id", "reason"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "request_id": {"type": "integer"},
                    "message": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """접근 권한 요청"""
        try:
            if not context or "user_id" not in context:
                return self.create_error_response(
                    "Authentication required",
                    "AUTH_ERROR"
                )
            
            doc_id = arguments["doc_id"]
            reason = arguments["reason"]
            user_id = context["user_id"]
            
            # 1. 문서 존재 확인
            from shared.queries import DocumentQueries
            query, params = DocumentQueries.get_by_id(doc_id)
            docs = self.db.fetch_all(query, params)
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            # 2. 이미 요청했는지 확인
            check_query = """
            SELECT * FROM access_requests
            WHERE user_id = %s AND resource_id = %s AND status = 'pending'
            """
            existing = self.db.fetch_all(check_query, (user_id, doc_id))
            
            if existing:
                return self.create_error_response(
                    "Access request already pending",
                    "ALREADY_EXISTS"
                )
            
            # 3. 요청 생성
            insert_query = """
            INSERT INTO access_requests (user_id, resource_type, resource_id, reason, status)
            VALUES (%s, %s, %s, %s, %s)
            """
            self.db.execute(insert_query, (user_id, "document", doc_id, reason, "pending"))
            
            # 마지막 삽입 ID 가져오기
            request_id = self.db.connection.insert_id()
            
            logger.info(f"Access request created: {request_id} by {user_id} for {doc_id}")
            
            return self.create_success_response({
                "request_id": request_id,
                "message": "Access request submitted successfully. Waiting for approval."
            })
        
        except Exception as e:
            logger.error(f"Request access failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "REQUEST_ERROR")


class ApproveAccessTool(BaseTool):
    """
    접근 권한 승인 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="approve_access",
            description="접근 권한 요청 승인/거부",
            category="auth",
            department="core",
            version="1.0.0",
            required_permissions=["admin:approve"],
            input_schema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "integer",
                        "description": "요청 ID"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["approve", "reject"],
                        "description": "승인 또는 거부"
                    },
                    "comment": {
                        "type": "string",
                        "description": "승인/거부 사유"
                    }
                },
                "required": ["request_id", "action"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """권한 승인/거부"""
        try:
            if not context:
                return self.create_error_response(
                    "Authentication required",
                    "AUTH_ERROR"
                )
            
            # 1. 승인 권한 확인
            user_role = context.get("user_role", "")
            authorized, error = self.check_permission(user_role, ["admin:approve"])
            
            if not authorized:
                return self.create_error_response(error, "PERMISSION_DENIED")
            
            # 2. 요청 조회
            request_id = arguments["request_id"]
            query = "SELECT * FROM access_requests WHERE id = %s"
            requests = self.db.fetch_all(query, (request_id,))
            
            if not requests:
                return self.create_error_response(
                    f"Request not found: {request_id}",
                    "NOT_FOUND"
                )
            
            request = requests[0]
            
            if request["status"] != "pending":
                return self.create_error_response(
                    f"Request already processed: {request['status']}",
                    "ALREADY_EXISTS"
                )
            
            # 3. 승인/거부 처리
            action = arguments["action"]
            status = "approved" if action == "approve" else "rejected"
            
            update_query = """
            UPDATE access_requests
            SET status = %s, approved_by = %s, approved_at = NOW(), approver_comment = %s
            WHERE id = %s
            """
            self.db.execute(
                update_query,
                (status, context["user_id"], arguments.get("comment"), request_id)
            )
            
            # 4. 승인된 경우 권한 부여
            if status == "approved":
                perm_query = """
                INSERT INTO permissions (user_id, resource_type, resource_id, actions, granted_by)
                VALUES (%s, %s, %s, %s, %s)
                """
                self.db.execute(
                    perm_query,
                    (
                        request["user_id"],
                        request["resource_type"],
                        request["resource_id"],
                        "read",
                        context["user_id"]
                    )
                )
            
            logger.info(f"Request {request_id} {status} by {context['user_id']}")
            
            return self.create_success_response({
                "message": f"Request {status} successfully"
            })
        
        except Exception as e:
            logger.error(f"Approve access failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "APPROVE_ERROR")


class GetMyPermissionsTool(BaseTool):
    """
    내 권한 조회 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_my_permissions",
            description="내 권한 목록 조회",
            category="auth",
            department="core",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {}
            },
            output_schema={
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "role_permissions": {"type": "object"},
                    "special_permissions": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """내 권한 조회"""
        try:
            if not context:
                return self.create_error_response(
                    "Authentication required",
                    "AUTH_ERROR"
                )
            
            user_role = context.get("user_role", "")
            user_id = context.get("user_id", "")
            
            # 1. 역할 기반 권한
            role_permissions = self.perm_engine.get_permission_summary(user_role)
            
            # 2. 특별 권한 (DB)
            query = """
            SELECT p.*, u.name as granted_by_name
            FROM permissions p
            LEFT JOIN users u ON p.granted_by = u.id
            WHERE p.user_id = %s
            ORDER BY p.created_at DESC
            """
            special_permissions = self.db.fetch_all(query, (user_id,))
            
            return self.create_success_response({
                "role": user_role,
                "role_permissions": role_permissions,
                "special_permissions": [
                    {
                        "resource_type": p["resource_type"],
                        "resource_id": p["resource_id"],
                        "actions": p["actions"],
                        "granted_by": p.get("granted_by_name", "system"),
                        "created_at": p["created_at"].isoformat() if p.get("created_at") else None
                    }
                    for p in special_permissions
                ]
            })
        
        except Exception as e:
            logger.error(f"Get permissions failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "PERMISSION_ERROR")

"""
SQL 쿼리 저장소
===============

모든 SQL 쿼리를 한 곳에서 관리합니다.
파라미터화된 쿼리만 사용하여 SQL Injection을 방지합니다.

테이블:
- users: 사용자 정보
- documents: 문서 메타데이터
- permissions: 권한 설정
- tools: MCP Tool 등록
- servers: MCP Server 등록
- audit_logs: 감사 로그
- document_versions: 문서 버전 이력
- access_requests: 접근 요청

사용 예:
    from shared.queries import UserQueries, DocumentQueries
    
    # 사용자 조회
    query, params = UserQueries.get_by_id("U001")
    user = db.fetch_one(query, params)
    
    # 문서 검색
    query, params = DocumentQueries.search(title="보고서", status="published")
    docs = db.fetch_all(query, params)
"""

from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime


# 타입 별칭
QueryResult = Tuple[str, List[Any]]


# ===========================================
# 사용자 쿼리
# ===========================================

class UserQueries:
    """사용자 관련 쿼리"""
    
    # 테이블 정의
    TABLE = "users"
    
    @staticmethod
    def get_by_id(user_id: str) -> QueryResult:
        """ID로 사용자 조회"""
        query = """
            SELECT user_id, username, email, role, department, 
                   classification_level, status, created_at, updated_at
            FROM users
            WHERE user_id = %s
        """
        return query, [user_id]
    
    @staticmethod
    def get_by_username(username: str) -> QueryResult:
        """사용자명으로 조회"""
        query = """
            SELECT user_id, username, email, password_hash, role, department,
                   classification_level, status, created_at, updated_at
            FROM users
            WHERE username = %s AND status = 'active'
        """
        return query, [username]
    
    @staticmethod
    def get_by_email(email: str) -> QueryResult:
        """이메일로 조회"""
        query = """
            SELECT user_id, username, email, role, department,
                   classification_level, status
            FROM users
            WHERE email = %s
        """
        return query, [email]
    
    @staticmethod
    def list_all(
        status: Optional[str] = None,
        role: Optional[str] = None,
        department: Optional[str] = None,
        order_by: str = "created_at DESC"
    ) -> QueryResult:
        """사용자 목록"""
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if role:
            conditions.append("role = %s")
            params.append(role)
        
        if department:
            conditions.append("department = %s")
            params.append(department)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT user_id, username, email, role, department,
                   classification_level, status, created_at
            FROM users
            WHERE {where_clause}
            ORDER BY {order_by}
        """
        return query, params
    
    @staticmethod
    def create(
        user_id: str,
        username: str,
        email: str,
        password_hash: str,
        role: str = "junior",
        department: str = "",
        classification_level: int = 1
    ) -> QueryResult:
        """사용자 생성"""
        query = """
            INSERT INTO users (
                user_id, username, email, password_hash, role,
                department, classification_level, status, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', NOW(), NOW())
        """
        params = [user_id, username, email, password_hash, role,
                  department, classification_level]
        return query, params
    
    @staticmethod
    def update(
        user_id: str,
        **fields
    ) -> QueryResult:
        """사용자 정보 업데이트"""
        allowed_fields = ["username", "email", "role", "department",
                         "classification_level", "status"]
        
        set_parts = []
        params = []
        
        for field, value in fields.items():
            if field in allowed_fields:
                set_parts.append(f"{field} = %s")
                params.append(value)
        
        set_parts.append("updated_at = NOW()")
        params.append(user_id)
        
        query = f"""
            UPDATE users
            SET {", ".join(set_parts)}
            WHERE user_id = %s
        """
        return query, params
    
    @staticmethod
    def update_password(user_id: str, password_hash: str) -> QueryResult:
        """비밀번호 변경"""
        query = """
            UPDATE users
            SET password_hash = %s, updated_at = NOW()
            WHERE user_id = %s
        """
        return query, [password_hash, user_id]
    
    @staticmethod
    def deactivate(user_id: str) -> QueryResult:
        """사용자 비활성화"""
        query = """
            UPDATE users
            SET status = 'inactive', updated_at = NOW()
            WHERE user_id = %s
        """
        return query, [user_id]
    
    @staticmethod
    def delete(user_id: str) -> QueryResult:
        """사용자 삭제 (물리 삭제)"""
        query = "DELETE FROM users WHERE user_id = %s"
        return query, [user_id]
    
    @staticmethod
    def count(status: Optional[str] = None) -> QueryResult:
        """사용자 수"""
        if status:
            query = "SELECT COUNT(*) as cnt FROM users WHERE status = %s"
            return query, [status]
        else:
            query = "SELECT COUNT(*) as cnt FROM users"
            return query, []


# ===========================================
# 문서 쿼리
# ===========================================

class DocumentQueries:
    """문서 관련 쿼리"""
    
    TABLE = "documents"
    
    @staticmethod
    def get_by_id(doc_id: str) -> QueryResult:
        """ID로 문서 조회"""
        query = """
            SELECT d.*, u.username as author_name
            FROM documents d
            LEFT JOIN users u ON d.author_id = u.user_id
            WHERE d.doc_id = %s
        """
        return query, [doc_id]
    
    @staticmethod
    def get_by_path(file_path: str) -> QueryResult:
        """경로로 문서 조회"""
        query = """
            SELECT * FROM documents
            WHERE file_path = %s
        """
        return query, [file_path]
    
    @staticmethod
    def list_by_classification(
        classification: str,
        status: str = "published",
        order_by: str = "created_at DESC"
    ) -> QueryResult:
        """보안등급별 문서 목록"""
        query = f"""
            SELECT d.*, u.username as author_name
            FROM documents d
            LEFT JOIN users u ON d.author_id = u.user_id
            WHERE d.classification = %s AND d.status = %s
            ORDER BY {order_by}
        """
        return query, [classification, status]
    
    @staticmethod
    def search(
        title: Optional[str] = None,
        author_id: Optional[str] = None,
        classification: Optional[str] = None,
        status: Optional[str] = None,
        doc_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        order_by: str = "created_at DESC"
    ) -> QueryResult:
        """문서 검색"""
        conditions = []
        params = []
        
        if title:
            conditions.append("title LIKE %s")
            params.append(f"%{title}%")
        
        if author_id:
            conditions.append("author_id = %s")
            params.append(author_id)
        
        if classification:
            conditions.append("classification = %s")
            params.append(classification)
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if doc_type:
            conditions.append("doc_type = %s")
            params.append(doc_type)
        
        if tags:
            # JSON 배열에서 태그 검색 (MariaDB JSON 함수 사용)
            for tag in tags:
                conditions.append("JSON_CONTAINS(tags, %s)")
                params.append(f'"{tag}"')
        
        if created_from:
            conditions.append("created_at >= %s")
            params.append(created_from)
        
        if created_to:
            conditions.append("created_at <= %s")
            params.append(created_to)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT d.*, u.username as author_name
            FROM documents d
            LEFT JOIN users u ON d.author_id = u.user_id
            WHERE {where_clause}
            ORDER BY {order_by}
        """
        return query, params
    
    @staticmethod
    def create(
        doc_id: str,
        title: str,
        content: str,
        author_id: str,
        classification: str = "public",
        doc_type: str = "general",
        file_path: str = "",
        file_size: int = 0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> QueryResult:
        """문서 생성"""
        import json
        
        query = """
            INSERT INTO documents (
                doc_id, title, content, author_id, classification,
                doc_type, file_path, file_size, tags, metadata,
                status, version, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                'draft', 1, NOW(), NOW()
            )
        """
        params = [
            doc_id, title, content, author_id, classification,
            doc_type, file_path, file_size,
            json.dumps(tags or []),
            json.dumps(metadata or {})
        ]
        return query, params
    
    @staticmethod
    def update(doc_id: str, **fields) -> QueryResult:
        """문서 업데이트"""
        import json
        
        allowed_fields = ["title", "content", "classification", "doc_type",
                         "file_path", "file_size", "tags", "metadata", "status"]
        
        set_parts = []
        params = []
        
        for field, value in fields.items():
            if field in allowed_fields:
                if field in ["tags", "metadata"]:
                    value = json.dumps(value)
                set_parts.append(f"{field} = %s")
                params.append(value)
        
        set_parts.append("updated_at = NOW()")
        params.append(doc_id)
        
        query = f"""
            UPDATE documents
            SET {", ".join(set_parts)}
            WHERE doc_id = %s
        """
        return query, params
    
    @staticmethod
    def update_status(doc_id: str, status: str) -> QueryResult:
        """문서 상태 변경"""
        query = """
            UPDATE documents
            SET status = %s, updated_at = NOW()
            WHERE doc_id = %s
        """
        return query, [status, doc_id]
    
    @staticmethod
    def increment_version(doc_id: str) -> QueryResult:
        """문서 버전 증가"""
        query = """
            UPDATE documents
            SET version = version + 1, updated_at = NOW()
            WHERE doc_id = %s
        """
        return query, [doc_id]
    
    @staticmethod
    def delete(doc_id: str) -> QueryResult:
        """문서 삭제"""
        query = "DELETE FROM documents WHERE doc_id = %s"
        return query, [doc_id]
    
    @staticmethod
    def soft_delete(doc_id: str) -> QueryResult:
        """문서 소프트 삭제"""
        query = """
            UPDATE documents
            SET status = 'deleted', updated_at = NOW()
            WHERE doc_id = %s
        """
        return query, [doc_id]


# ===========================================
# 권한 쿼리
# ===========================================

class PermissionQueries:
    """권한 관련 쿼리"""
    
    TABLE = "permissions"
    
    @staticmethod
    def get_by_id(perm_id: str) -> QueryResult:
        """권한 조회"""
        query = """
            SELECT * FROM permissions
            WHERE perm_id = %s
        """
        return query, [perm_id]
    
    @staticmethod
    def get_user_permissions(user_id: str) -> QueryResult:
        """사용자 권한 목록"""
        query = """
            SELECT p.*, d.title as doc_title
            FROM permissions p
            LEFT JOIN documents d ON p.doc_id = d.doc_id
            WHERE p.user_id = %s
            ORDER BY p.created_at DESC
        """
        return query, [user_id]
    
    @staticmethod
    def get_document_permissions(doc_id: str) -> QueryResult:
        """문서 권한 목록"""
        query = """
            SELECT p.*, u.username
            FROM permissions p
            LEFT JOIN users u ON p.user_id = u.user_id
            WHERE p.doc_id = %s
            ORDER BY p.created_at DESC
        """
        return query, [doc_id]
    
    @staticmethod
    def check_permission(
        user_id: str,
        doc_id: str,
        action: str
    ) -> QueryResult:
        """권한 확인"""
        query = """
            SELECT * FROM permissions
            WHERE user_id = %s AND doc_id = %s AND action = %s
        """
        return query, [user_id, doc_id, action]
    
    @staticmethod
    def grant(
        perm_id: str,
        user_id: str,
        doc_id: str,
        action: str,
        granted_by: str,
        expires_at: Optional[datetime] = None
    ) -> QueryResult:
        """권한 부여"""
        query = """
            INSERT INTO permissions (
                perm_id, user_id, doc_id, action, granted_by,
                expires_at, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        return query, [perm_id, user_id, doc_id, action, granted_by, expires_at]
    
    @staticmethod
    def revoke(perm_id: str) -> QueryResult:
        """권한 취소"""
        query = "DELETE FROM permissions WHERE perm_id = %s"
        return query, [perm_id]
    
    @staticmethod
    def revoke_all_for_document(doc_id: str) -> QueryResult:
        """문서의 모든 권한 취소"""
        query = "DELETE FROM permissions WHERE doc_id = %s"
        return query, [doc_id]
    
    @staticmethod
    def revoke_all_for_user(user_id: str) -> QueryResult:
        """사용자의 모든 권한 취소"""
        query = "DELETE FROM permissions WHERE user_id = %s"
        return query, [user_id]
    
    @staticmethod
    def cleanup_expired() -> QueryResult:
        """만료된 권한 정리"""
        query = """
            DELETE FROM permissions
            WHERE expires_at IS NOT NULL AND expires_at < NOW()
        """
        return query, []


# ===========================================
# Tool 쿼리
# ===========================================

class ToolQueries:
    """MCP Tool 관련 쿼리"""
    
    TABLE = "tools"
    
    @staticmethod
    def get_by_id(tool_id: str) -> QueryResult:
        """Tool ID로 조회"""
        query = """
            SELECT * FROM tools
            WHERE tool_id = %s
        """
        return query, [tool_id]
    
    @staticmethod
    def get_by_name(name: str) -> QueryResult:
        """이름으로 조회"""
        query = """
            SELECT * FROM tools
            WHERE name = %s AND status = 'active'
        """
        return query, [name]
    
    @staticmethod
    def list_by_server(server_id: str) -> QueryResult:
        """서버별 Tool 목록"""
        query = """
            SELECT * FROM tools
            WHERE server_id = %s AND status = 'active'
            ORDER BY name
        """
        return query, [server_id]
    
    @staticmethod
    def list_by_category(category: str) -> QueryResult:
        """카테고리별 Tool 목록"""
        query = """
            SELECT * FROM tools
            WHERE category = %s AND status = 'active'
            ORDER BY name
        """
        return query, [category]
    
    @staticmethod
    def list_all(
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> QueryResult:
        """전체 Tool 목록"""
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if category:
            conditions.append("category = %s")
            params.append(category)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM tools
            WHERE {where_clause}
            ORDER BY name
        """
        return query, params
    
    @staticmethod
    def create(
        tool_id: str,
        server_id: str,
        name: str,
        description: str,
        input_schema: Dict,
        category: str = "general",
        required_role: str = "junior"
    ) -> QueryResult:
        """Tool 등록"""
        import json
        
        query = """
            INSERT INTO tools (
                tool_id, server_id, name, description, input_schema,
                category, required_role, status, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', NOW(), NOW())
        """
        params = [tool_id, server_id, name, description,
                  json.dumps(input_schema), category, required_role]
        return query, params
    
    @staticmethod
    def update(tool_id: str, **fields) -> QueryResult:
        """Tool 정보 업데이트"""
        import json
        
        allowed_fields = ["name", "description", "input_schema", "category",
                         "required_role", "status"]
        
        set_parts = []
        params = []
        
        for field, value in fields.items():
            if field in allowed_fields:
                if field == "input_schema":
                    value = json.dumps(value)
                set_parts.append(f"{field} = %s")
                params.append(value)
        
        set_parts.append("updated_at = NOW()")
        params.append(tool_id)
        
        query = f"""
            UPDATE tools
            SET {", ".join(set_parts)}
            WHERE tool_id = %s
        """
        return query, params
    
    @staticmethod
    def delete(tool_id: str) -> QueryResult:
        """Tool 삭제"""
        query = "DELETE FROM tools WHERE tool_id = %s"
        return query, [tool_id]


# ===========================================
# Server 쿼리
# ===========================================

class ServerQueries:
    """MCP Server 관련 쿼리"""
    
    TABLE = "servers"
    
    @staticmethod
    def get_by_id(server_id: str) -> QueryResult:
        """Server ID로 조회"""
        query = """
            SELECT * FROM servers
            WHERE server_id = %s
        """
        return query, [server_id]
    
    @staticmethod
    def get_by_name(name: str) -> QueryResult:
        """이름으로 조회"""
        query = """
            SELECT * FROM servers
            WHERE name = %s
        """
        return query, [name]
    
    @staticmethod
    def list_active() -> QueryResult:
        """활성 서버 목록"""
        query = """
            SELECT * FROM servers
            WHERE status = 'active'
            ORDER BY name
        """
        return query, []
    
    @staticmethod
    def list_all(status: Optional[str] = None) -> QueryResult:
        """전체 서버 목록"""
        if status:
            query = """
                SELECT * FROM servers
                WHERE status = %s
                ORDER BY name
            """
            return query, [status]
        else:
            query = """
                SELECT * FROM servers
                ORDER BY name
            """
            return query, []
    
    @staticmethod
    def create(
        server_id: str,
        name: str,
        description: str,
        command: str,
        args: List[str],
        env: Optional[Dict] = None,
        category: str = "general"
    ) -> QueryResult:
        """Server 등록"""
        import json
        
        query = """
            INSERT INTO servers (
                server_id, name, description, command, args, env,
                category, status, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', NOW(), NOW())
        """
        params = [server_id, name, description, command,
                  json.dumps(args), json.dumps(env or {}), category]
        return query, params
    
    @staticmethod
    def update(server_id: str, **fields) -> QueryResult:
        """Server 정보 업데이트"""
        import json
        
        allowed_fields = ["name", "description", "command", "args", "env",
                         "category", "status"]
        
        set_parts = []
        params = []
        
        for field, value in fields.items():
            if field in allowed_fields:
                if field in ["args", "env"]:
                    value = json.dumps(value)
                set_parts.append(f"{field} = %s")
                params.append(value)
        
        set_parts.append("updated_at = NOW()")
        params.append(server_id)
        
        query = f"""
            UPDATE servers
            SET {", ".join(set_parts)}
            WHERE server_id = %s
        """
        return query, params
    
    @staticmethod
    def update_status(server_id: str, status: str) -> QueryResult:
        """Server 상태 변경"""
        query = """
            UPDATE servers
            SET status = %s, updated_at = NOW()
            WHERE server_id = %s
        """
        return query, [status, server_id]
    
    @staticmethod
    def delete(server_id: str) -> QueryResult:
        """Server 삭제"""
        query = "DELETE FROM servers WHERE server_id = %s"
        return query, [server_id]


# ===========================================
# 감사 로그 쿼리
# ===========================================

class AuditLogQueries:
    """감사 로그 관련 쿼리"""
    
    TABLE = "audit_logs"
    
    @staticmethod
    def get_by_id(log_id: str) -> QueryResult:
        """로그 ID로 조회"""
        query = """
            SELECT * FROM audit_logs
            WHERE log_id = %s
        """
        return query, [log_id]
    
    @staticmethod
    def search(
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        order_by: str = "created_at DESC"
    ) -> QueryResult:
        """감사 로그 검색"""
        conditions = []
        params = []
        
        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)
        
        if action:
            conditions.append("action = %s")
            params.append(action)
        
        if resource_type:
            conditions.append("resource_type = %s")
            params.append(resource_type)
        
        if resource_id:
            conditions.append("resource_id = %s")
            params.append(resource_id)
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if from_date:
            conditions.append("created_at >= %s")
            params.append(from_date)
        
        if to_date:
            conditions.append("created_at <= %s")
            params.append(to_date)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT al.*, u.username
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.user_id
            WHERE {where_clause}
            ORDER BY {order_by}
        """
        return query, params
    
    @staticmethod
    def create(
        log_id: str,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict] = None,
        status: str = "success",
        ip_address: str = "",
        user_agent: str = ""
    ) -> QueryResult:
        """감사 로그 생성"""
        import json
        
        query = """
            INSERT INTO audit_logs (
                log_id, user_id, action, resource_type, resource_id,
                details, status, ip_address, user_agent, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        params = [log_id, user_id, action, resource_type, resource_id,
                  json.dumps(details or {}), status, ip_address, user_agent]
        return query, params
    
    @staticmethod
    def delete_old(days: int = 90) -> QueryResult:
        """오래된 로그 삭제"""
        query = """
            DELETE FROM audit_logs
            WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        return query, [days]
    
    @staticmethod
    def count_by_user(user_id: str, action: Optional[str] = None) -> QueryResult:
        """사용자별 로그 수"""
        if action:
            query = """
                SELECT COUNT(*) as cnt FROM audit_logs
                WHERE user_id = %s AND action = %s
            """
            return query, [user_id, action]
        else:
            query = """
                SELECT COUNT(*) as cnt FROM audit_logs
                WHERE user_id = %s
            """
            return query, [user_id]


# ===========================================
# 문서 버전 쿼리
# ===========================================

class DocumentVersionQueries:
    """문서 버전 관련 쿼리"""
    
    TABLE = "document_versions"
    
    @staticmethod
    def get_by_id(version_id: str) -> QueryResult:
        """버전 ID로 조회"""
        query = """
            SELECT * FROM document_versions
            WHERE version_id = %s
        """
        return query, [version_id]
    
    @staticmethod
    def list_by_document(doc_id: str) -> QueryResult:
        """문서별 버전 목록"""
        query = """
            SELECT dv.*, u.username as modified_by_name
            FROM document_versions dv
            LEFT JOIN users u ON dv.modified_by = u.user_id
            WHERE dv.doc_id = %s
            ORDER BY dv.version DESC
        """
        return query, [doc_id]
    
    @staticmethod
    def get_latest(doc_id: str) -> QueryResult:
        """최신 버전 조회"""
        query = """
            SELECT * FROM document_versions
            WHERE doc_id = %s
            ORDER BY version DESC
            LIMIT 1
        """
        return query, [doc_id]
    
    @staticmethod
    def get_version(doc_id: str, version: int) -> QueryResult:
        """특정 버전 조회"""
        query = """
            SELECT * FROM document_versions
            WHERE doc_id = %s AND version = %s
        """
        return query, [doc_id, version]
    
    @staticmethod
    def create(
        version_id: str,
        doc_id: str,
        version: int,
        content: str,
        modified_by: str,
        change_summary: str = ""
    ) -> QueryResult:
        """버전 생성"""
        query = """
            INSERT INTO document_versions (
                version_id, doc_id, version, content,
                modified_by, change_summary, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        params = [version_id, doc_id, version, content,
                  modified_by, change_summary]
        return query, params
    
    @staticmethod
    def delete_old_versions(doc_id: str, keep_count: int = 10) -> QueryResult:
        """오래된 버전 삭제 (최근 N개만 유지)"""
        query = """
            DELETE FROM document_versions
            WHERE doc_id = %s
            AND version_id NOT IN (
                SELECT version_id FROM (
                    SELECT version_id FROM document_versions
                    WHERE doc_id = %s
                    ORDER BY version DESC
                    LIMIT %s
                ) as keep_versions
            )
        """
        return query, [doc_id, doc_id, keep_count]


# ===========================================
# 접근 요청 쿼리
# ===========================================

class AccessRequestQueries:
    """접근 요청 관련 쿼리"""
    
    TABLE = "access_requests"
    
    @staticmethod
    def get_by_id(request_id: str) -> QueryResult:
        """요청 ID로 조회"""
        query = """
            SELECT ar.*, 
                   u.username as requester_name,
                   d.title as doc_title,
                   au.username as approver_name
            FROM access_requests ar
            LEFT JOIN users u ON ar.requester_id = u.user_id
            LEFT JOIN documents d ON ar.doc_id = d.doc_id
            LEFT JOIN users au ON ar.approved_by = au.user_id
            WHERE ar.request_id = %s
        """
        return query, [request_id]
    
    @staticmethod
    def list_pending() -> QueryResult:
        """대기 중인 요청 목록"""
        query = """
            SELECT ar.*, 
                   u.username as requester_name,
                   d.title as doc_title
            FROM access_requests ar
            LEFT JOIN users u ON ar.requester_id = u.user_id
            LEFT JOIN documents d ON ar.doc_id = d.doc_id
            WHERE ar.status = 'pending'
            ORDER BY ar.created_at ASC
        """
        return query, []
    
    @staticmethod
    def list_by_requester(requester_id: str) -> QueryResult:
        """요청자별 목록"""
        query = """
            SELECT ar.*, d.title as doc_title
            FROM access_requests ar
            LEFT JOIN documents d ON ar.doc_id = d.doc_id
            WHERE ar.requester_id = %s
            ORDER BY ar.created_at DESC
        """
        return query, [requester_id]
    
    @staticmethod
    def list_by_document(doc_id: str) -> QueryResult:
        """문서별 요청 목록"""
        query = """
            SELECT ar.*, u.username as requester_name
            FROM access_requests ar
            LEFT JOIN users u ON ar.requester_id = u.user_id
            WHERE ar.doc_id = %s
            ORDER BY ar.created_at DESC
        """
        return query, [doc_id]
    
    @staticmethod
    def create(
        request_id: str,
        requester_id: str,
        doc_id: str,
        requested_action: str,
        reason: str
    ) -> QueryResult:
        """접근 요청 생성"""
        query = """
            INSERT INTO access_requests (
                request_id, requester_id, doc_id, requested_action,
                reason, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, 'pending', NOW())
        """
        params = [request_id, requester_id, doc_id, requested_action, reason]
        return query, params
    
    @staticmethod
    def approve(
        request_id: str,
        approved_by: str,
        comment: str = ""
    ) -> QueryResult:
        """요청 승인"""
        query = """
            UPDATE access_requests
            SET status = 'approved', 
                approved_by = %s, 
                approver_comment = %s,
                processed_at = NOW()
            WHERE request_id = %s
        """
        return query, [approved_by, comment, request_id]
    
    @staticmethod
    def reject(
        request_id: str,
        rejected_by: str,
        comment: str = ""
    ) -> QueryResult:
        """요청 거절"""
        query = """
            UPDATE access_requests
            SET status = 'rejected', 
                approved_by = %s, 
                approver_comment = %s,
                processed_at = NOW()
            WHERE request_id = %s
        """
        return query, [rejected_by, comment, request_id]
    
    @staticmethod
    def cancel(request_id: str) -> QueryResult:
        """요청 취소 (요청자가)"""
        query = """
            UPDATE access_requests
            SET status = 'cancelled', processed_at = NOW()
            WHERE request_id = %s AND status = 'pending'
        """
        return query, [request_id]
    
    @staticmethod
    def check_duplicate(
        requester_id: str,
        doc_id: str,
        requested_action: str
    ) -> QueryResult:
        """중복 요청 확인"""
        query = """
            SELECT * FROM access_requests
            WHERE requester_id = %s 
            AND doc_id = %s 
            AND requested_action = %s
            AND status = 'pending'
        """
        return query, [requester_id, doc_id, requested_action]


# ===========================================
# Public API
# ===========================================

__all__ = [
    "QueryResult",
    "UserQueries",
    "DocumentQueries",
    "PermissionQueries",
    "ToolQueries",
    "ServerQueries",
    "AuditLogQueries",
    "DocumentVersionQueries",
    "AccessRequestQueries",
]

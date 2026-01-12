"""
권한 관리 엔진
==============

RBAC(Role-Based Access Control) 기반 권한 관리를 제공합니다.

역할 계층 (5단계) - SR.md 기준:
- junior (1): 신입 - 읽기만 가능
- staff (2): 일반 사원 - 읽기/쓰기 가능
- manager (3): 팀 관리자 - 권한 관리 가능
- executive (4): 임원 - 시스템 설정 가능
- admin (5): 시스템 관리자 - 전체 권한

보안 등급 (5단계):
- public (1): 공개
- internal (2): 내부용
- confidential (3): 기밀
- secret (4): 비밀
- top_secret (5): 극비

사용 예:
    from shared.permissions import PermissionEngine
    
    engine = PermissionEngine(db)
    
    # 권한 확인
    can_read = engine.can_access(user_id, doc_id, "read")
    
    # 역할 검증
    is_admin = engine.has_role(user, "admin")
    
    # 문서 접근 가능 여부
    can_view = engine.can_view_document(user, document)
"""

from typing import Any, Optional, Dict, List, Set
from dataclasses import dataclass
from enum import Enum, IntEnum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ===========================================
# 열거형 정의
# ===========================================

class Role(IntEnum):
    """사용자 역할 (SR.md 기준)"""
    JUNIOR = 1       # 신입
    STAFF = 2        # 일반 사원
    MANAGER = 3      # 팀 관리자
    EXECUTIVE = 4    # 임원
    ADMIN = 5        # 시스템 관리자


class Classification(IntEnum):
    """보안 등급"""
    PUBLIC = 1
    INTERNAL = 2
    CONFIDENTIAL = 3
    SECRET = 4
    TOP_SECRET = 5


class Action(str, Enum):
    """수행 가능한 액션"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SHARE = "share"
    MANAGE = "manage"
    ADMIN = "admin"


# ===========================================
# 역할-문자열 매핑
# ===========================================

ROLE_MAP = {
    "junior": Role.JUNIOR,
    "staff": Role.STAFF,
    "manager": Role.MANAGER,
    "executive": Role.EXECUTIVE,
    "admin": Role.ADMIN,
}

ROLE_REVERSE_MAP = {v: k for k, v in ROLE_MAP.items()}

CLASSIFICATION_MAP = {
    "public": Classification.PUBLIC,
    "internal": Classification.INTERNAL,
    "confidential": Classification.CONFIDENTIAL,
    "secret": Classification.SECRET,
    "top_secret": Classification.TOP_SECRET,
}

CLASSIFICATION_REVERSE_MAP = {v: k for k, v in CLASSIFICATION_MAP.items()}


# ===========================================
# 역할별 권한 정의
# ===========================================

# 각 역할이 수행할 수 있는 액션
ROLE_PERMISSIONS: Dict[Role, Set[Action]] = {
    Role.JUNIOR: {Action.READ},
    Role.STAFF: {Action.READ, Action.WRITE},
    Role.MANAGER: {Action.READ, Action.WRITE, Action.DELETE, Action.SHARE, Action.MANAGE},
    Role.EXECUTIVE: {Action.READ, Action.WRITE, Action.DELETE, Action.SHARE, Action.MANAGE, Action.ADMIN},
    Role.ADMIN: {Action.READ, Action.WRITE, Action.DELETE, Action.SHARE, Action.MANAGE, Action.ADMIN},
}

# 각 역할이 접근할 수 있는 최대 보안 등급
ROLE_CLASSIFICATION_LIMIT: Dict[Role, Classification] = {
    Role.JUNIOR: Classification.INTERNAL,
    Role.STAFF: Classification.CONFIDENTIAL,
    Role.MANAGER: Classification.SECRET,
    Role.EXECUTIVE: Classification.SECRET,
    Role.ADMIN: Classification.TOP_SECRET,
}


# ===========================================
# 데이터 클래스
# ===========================================

@dataclass
class User:
    """사용자 정보"""
    user_id: str
    username: str
    role: str  # "junior", "staff", "manager", "executive", "admin"
    classification_level: int  # 1-5
    department: str = ""
    status: str = "active"
    
    @property
    def role_enum(self) -> Role:
        return ROLE_MAP.get(self.role, Role.JUNIOR)
    
    @property
    def classification_enum(self) -> Classification:
        return Classification(self.classification_level)


@dataclass
class Document:
    """문서 정보"""
    doc_id: str
    title: str
    author_id: str
    classification: str  # "public", "internal", "confidential", "secret", "top_secret"
    status: str = "published"
    
    @property
    def classification_enum(self) -> Classification:
        return CLASSIFICATION_MAP.get(self.classification, Classification.PUBLIC)


@dataclass
class Permission:
    """권한 정보"""
    perm_id: str
    user_id: str
    doc_id: str
    action: str
    granted_by: str
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


# ===========================================
# 권한 엔진
# ===========================================

class PermissionEngine:
    """
    RBAC 권한 관리 엔진
    
    역할 기반 권한 + 문서별 개별 권한을 지원합니다.
    """
    
    def __init__(self, db=None, cache=None):
        """
        초기화
        
        Args:
            db: DatabaseManager 인스턴스
            cache: Cache 인스턴스 (선택)
        """
        self.db = db
        self.cache = cache
        
        logger.info("PermissionEngine initialized")
    
    # ===========================================
    # 역할 검증
    # ===========================================
    
    def has_role(self, user: User, required_role: str) -> bool:
        """
        사용자가 필요한 역할 이상인지 확인
        
        Args:
            user: 사용자
            required_role: 필요한 역할 문자열
        
        Returns:
            역할 보유 여부
        """
        user_role = ROLE_MAP.get(user.role, Role.JUNIOR)
        required = ROLE_MAP.get(required_role, Role.JUNIOR)
        
        return user_role >= required
    
    def has_role_level(self, user: User, level: int) -> bool:
        """
        사용자가 특정 역할 레벨 이상인지 확인
        
        Args:
            user: 사용자
            level: 역할 레벨 (1-5)
        """
        return user.role_enum >= level
    
    def get_role_permissions(self, role: str) -> Set[str]:
        """
        역할의 권한 목록
        
        Returns:
            액션 문자열 집합
        """
        role_enum = ROLE_MAP.get(role, Role.JUNIOR)
        permissions = ROLE_PERMISSIONS.get(role_enum, set())
        return {p.value for p in permissions}
    
    # ===========================================
    # 보안 등급 검증
    # ===========================================
    
    def has_classification_level(
        self,
        user: User,
        required_classification: str
    ) -> bool:
        """
        사용자가 필요한 보안 등급 이상인지 확인
        
        Args:
            user: 사용자
            required_classification: 필요한 보안 등급 문자열
        
        Returns:
            접근 가능 여부
        """
        required = CLASSIFICATION_MAP.get(required_classification, Classification.PUBLIC)
        return user.classification_level >= required
    
    def get_max_classification(self, user: User) -> str:
        """
        사용자가 접근 가능한 최대 보안 등급
        
        역할 기반 제한과 개인 등급 중 낮은 것 반환
        """
        role_limit = ROLE_CLASSIFICATION_LIMIT.get(user.role_enum, Classification.INTERNAL)
        user_level = Classification(user.classification_level)
        
        effective_level = min(role_limit, user_level)
        
        return CLASSIFICATION_REVERSE_MAP.get(effective_level, "public")
    
    # ===========================================
    # 문서 접근 권한
    # ===========================================
    
    def can_view_document(self, user: User, document: Document) -> bool:
        """
        문서 열람 가능 여부
        
        조건:
        1. 사용자 보안 등급 >= 문서 보안 등급
        2. 사용자 역할이 read 액션 보유
        3. (선택) 문서별 개별 권한 확인
        """
        # 비활성 사용자
        if user.status != "active":
            return False
        
        # 삭제된 문서
        if document.status == "deleted":
            return False
        
        # 보안 등급 확인
        doc_level = document.classification_enum
        if user.classification_level < doc_level:
            logger.debug(f"User {user.user_id} lacks classification for doc {document.doc_id}")
            return False
        
        # 역할 기반 권한 확인
        role_perms = ROLE_PERMISSIONS.get(user.role_enum, set())
        if Action.READ not in role_perms:
            logger.debug(f"User {user.user_id} lacks read permission")
            return False
        
        # 개별 권한 확인 (DB에서 추가 권한 부여된 경우)
        if self.db:
            if self._check_explicit_permission(user.user_id, document.doc_id, "read"):
                return True
        
        return True
    
    def can_edit_document(self, user: User, document: Document) -> bool:
        """
        문서 편집 가능 여부
        
        조건:
        1. 열람 가능
        2. 역할이 write 액션 보유
        3. 또는 문서 작성자
        """
        if not self.can_view_document(user, document):
            return False
        
        # 작성자는 항상 편집 가능
        if user.user_id == document.author_id:
            return True
        
        # 역할 확인
        role_perms = ROLE_PERMISSIONS.get(user.role_enum, set())
        if Action.WRITE not in role_perms:
            return False
        
        return True
    
    def can_delete_document(self, user: User, document: Document) -> bool:
        """
        문서 삭제 가능 여부
        
        조건:
        1. 열람 가능
        2. 역할이 delete 액션 보유
        3. 또는 문서 작성자 + staff 이상
        """
        if not self.can_view_document(user, document):
            return False
        
        # 작성자이고 staff 이상
        if user.user_id == document.author_id and user.role_enum >= Role.STAFF:
            return True
        
        # manager 이상
        role_perms = ROLE_PERMISSIONS.get(user.role_enum, set())
        if Action.DELETE not in role_perms:
            return False
        
        return True
    
    def can_share_document(self, user: User, document: Document) -> bool:
        """
        문서 공유 가능 여부
        
        조건:
        1. 열람 가능
        2. 역할이 share 액션 보유
        3. 또는 문서 작성자
        """
        if not self.can_view_document(user, document):
            return False
        
        # 작성자
        if user.user_id == document.author_id:
            return True
        
        # manager 이상
        role_perms = ROLE_PERMISSIONS.get(user.role_enum, set())
        return Action.SHARE in role_perms
    
    def can_manage_document(self, user: User, document: Document) -> bool:
        """
        문서 관리 가능 여부 (권한 부여/취소)
        
        조건:
        1. 역할이 manage 액션 보유
        2. 해당 문서 접근 가능
        """
        if not self.can_view_document(user, document):
            return False
        
        role_perms = ROLE_PERMISSIONS.get(user.role_enum, set())
        return Action.MANAGE in role_perms
    
    # ===========================================
    # 액션 기반 권한 확인
    # ===========================================
    
    def can_perform(
        self,
        user: User,
        document: Document,
        action: str
    ) -> bool:
        """
        특정 액션 수행 가능 여부
        
        Args:
            user: 사용자
            document: 문서
            action: 액션 문자열 ("read", "write", "delete", "share", "manage")
        
        Returns:
            수행 가능 여부
        """
        action_handlers = {
            "read": self.can_view_document,
            "write": self.can_edit_document,
            "delete": self.can_delete_document,
            "share": self.can_share_document,
            "manage": self.can_manage_document,
        }
        
        handler = action_handlers.get(action)
        if handler:
            return handler(user, document)
        
        logger.warning(f"Unknown action: {action}")
        return False
    
    def check_access(
        self,
        user_id: str,
        doc_id: str,
        action: str
    ) -> Dict[str, Any]:
        """
        접근 권한 상세 확인 (DB 조회 포함)
        
        Returns:
            {
                "allowed": 허용 여부,
                "reason": 사유,
                "user": 사용자 정보,
                "document": 문서 정보
            }
        """
        if not self.db:
            return {
                "allowed": False,
                "reason": "Database not configured",
            }
        
        # 캐시 확인
        if self.cache:
            cache_key = f"access:{user_id}:{doc_id}:{action}"
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        # 사용자 조회
        from shared.queries import UserQueries, DocumentQueries
        
        query, params = UserQueries.get_by_id(user_id)
        user_data = self.db.fetch_one(query, params)
        
        if not user_data:
            result = {"allowed": False, "reason": "User not found"}
            self._cache_result(cache_key, result)
            return result
        
        user = User(
            user_id=user_data["user_id"],
            username=user_data["username"],
            role=user_data["role"],
            classification_level=user_data["classification_level"],
            department=user_data.get("department", ""),
            status=user_data["status"]
        )
        
        # 문서 조회
        query, params = DocumentQueries.get_by_id(doc_id)
        doc_data = self.db.fetch_one(query, params)
        
        if not doc_data:
            result = {"allowed": False, "reason": "Document not found"}
            self._cache_result(cache_key, result)
            return result
        
        document = Document(
            doc_id=doc_data["doc_id"],
            title=doc_data["title"],
            author_id=doc_data["author_id"],
            classification=doc_data["classification"],
            status=doc_data["status"]
        )
        
        # 권한 확인
        allowed = self.can_perform(user, document, action)
        
        reason = "Access granted" if allowed else self._get_denial_reason(user, document, action)
        
        result = {
            "allowed": allowed,
            "reason": reason,
            "user": {
                "user_id": user.user_id,
                "role": user.role,
                "classification_level": user.classification_level
            },
            "document": {
                "doc_id": document.doc_id,
                "classification": document.classification,
                "author_id": document.author_id
            }
        }
        
        self._cache_result(cache_key, result)
        
        return result
    
    def _get_denial_reason(
        self,
        user: User,
        document: Document,
        action: str
    ) -> str:
        """접근 거부 사유 분석"""
        if user.status != "active":
            return "User is not active"
        
        if document.status == "deleted":
            return "Document is deleted"
        
        if user.classification_level < document.classification_enum:
            return f"Insufficient classification level (user: {user.classification_level}, required: {document.classification_enum.value})"
        
        role_perms = ROLE_PERMISSIONS.get(user.role_enum, set())
        action_enum = Action(action) if action in [a.value for a in Action] else None
        
        if action_enum and action_enum not in role_perms:
            return f"Role '{user.role}' does not have '{action}' permission"
        
        return "Access denied"
    
    def _cache_result(self, cache_key: str, result: Dict):
        """결과 캐싱"""
        if self.cache:
            self.cache.set(cache_key, result, ttl=60)  # 1분
    
    # ===========================================
    # 개별 권한 관리
    # ===========================================
    
    def _check_explicit_permission(
        self,
        user_id: str,
        doc_id: str,
        action: str
    ) -> bool:
        """DB에서 명시적 권한 확인"""
        if not self.db:
            return False
        
        from shared.queries import PermissionQueries
        
        query, params = PermissionQueries.check_permission(user_id, doc_id, action)
        perm = self.db.fetch_one(query, params)
        
        if perm:
            # 만료 확인
            if perm.get("expires_at"):
                if datetime.now() > perm["expires_at"]:
                    return False
            return True
        
        return False
    
    def grant_permission(
        self,
        granter: User,
        target_user_id: str,
        doc_id: str,
        action: str,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        권한 부여
        
        Args:
            granter: 권한 부여자
            target_user_id: 대상 사용자 ID
            doc_id: 문서 ID
            action: 액션
            expires_at: 만료 일시
        
        Returns:
            {
                "success": 성공 여부,
                "perm_id": 권한 ID,
                "message": 메시지
            }
        """
        if not self.db:
            return {"success": False, "message": "Database not configured"}
        
        # 권한 부여자 검증 (manager 이상)
        if not self.has_role(granter, "manager"):
            return {"success": False, "message": "Insufficient role to grant permissions"}
        
        from shared.queries import PermissionQueries
        from shared.utils import generate_id
        
        # 중복 확인
        query, params = PermissionQueries.check_permission(target_user_id, doc_id, action)
        existing = self.db.fetch_one(query, params)
        
        if existing:
            return {"success": False, "message": "Permission already exists"}
        
        # 권한 생성
        perm_id = generate_id("PERM")
        query, params = PermissionQueries.grant(
            perm_id, target_user_id, doc_id, action,
            granter.user_id, expires_at
        )
        
        try:
            self.db.execute(query, params)
            
            # 캐시 무효화
            if self.cache:
                self.cache.delete(f"access:{target_user_id}:{doc_id}:{action}")
            
            logger.info(f"Permission granted: {perm_id} ({target_user_id} -> {doc_id}:{action})")
            
            return {
                "success": True,
                "perm_id": perm_id,
                "message": "Permission granted successfully"
            }
        
        except Exception as e:
            logger.error(f"Failed to grant permission: {e}")
            return {"success": False, "message": str(e)}
    
    def revoke_permission(
        self,
        revoker: User,
        perm_id: str
    ) -> Dict[str, Any]:
        """
        권한 취소
        
        Args:
            revoker: 권한 취소자
            perm_id: 권한 ID
        
        Returns:
            {
                "success": 성공 여부,
                "message": 메시지
            }
        """
        if not self.db:
            return {"success": False, "message": "Database not configured"}
        
        # 권한 취소자 검증
        if not self.has_role(revoker, "manager"):
            return {"success": False, "message": "Insufficient role to revoke permissions"}
        
        from shared.queries import PermissionQueries
        
        # 권한 조회
        query, params = PermissionQueries.get_by_id(perm_id)
        perm = self.db.fetch_one(query, params)
        
        if not perm:
            return {"success": False, "message": "Permission not found"}
        
        # 삭제
        query, params = PermissionQueries.revoke(perm_id)
        
        try:
            self.db.execute(query, params)
            
            # 캐시 무효화
            if self.cache:
                self.cache.delete(f"access:{perm['user_id']}:{perm['doc_id']}:{perm['action']}")
            
            logger.info(f"Permission revoked: {perm_id}")
            
            return {"success": True, "message": "Permission revoked successfully"}
        
        except Exception as e:
            logger.error(f"Failed to revoke permission: {e}")
            return {"success": False, "message": str(e)}
    
    # ===========================================
    # Tool 권한
    # ===========================================
    
    def can_use_tool(
        self,
        user: User,
        tool_required_role: str
    ) -> bool:
        """
        Tool 사용 가능 여부
        
        Args:
            user: 사용자
            tool_required_role: Tool에 필요한 최소 역할
        
        Returns:
            사용 가능 여부
        """
        return self.has_role(user, tool_required_role)
    
    def filter_tools_by_permission(
        self,
        user: User,
        tools: List[Dict]
    ) -> List[Dict]:
        """
        사용자가 접근 가능한 Tool만 필터링
        
        Args:
            user: 사용자
            tools: Tool 목록 (각 Tool에 required_role 필드 필요)
        
        Returns:
            필터링된 Tool 목록
        """
        return [
            tool for tool in tools
            if self.can_use_tool(user, tool.get("required_role", "junior"))
        ]
    
    # ===========================================
    # 유틸리티
    # ===========================================
    
    def get_user_permissions_summary(self, user: User) -> Dict[str, Any]:
        """
        사용자 권한 요약
        
        Returns:
            {
                "role": 역할,
                "role_level": 역할 레벨,
                "classification_level": 보안 등급,
                "max_classification": 최대 접근 가능 등급,
                "actions": 수행 가능 액션 목록
            }
        """
        role_perms = ROLE_PERMISSIONS.get(user.role_enum, set())
        
        return {
            "role": user.role,
            "role_level": user.role_enum.value,
            "classification_level": user.classification_level,
            "max_classification": self.get_max_classification(user),
            "actions": [p.value for p in role_perms]
        }


# ===========================================
# Public API
# ===========================================

__all__ = [
    # 열거형
    "Role",
    "Classification",
    "Action",
    
    # 매핑
    "ROLE_MAP",
    "CLASSIFICATION_MAP",
    "ROLE_PERMISSIONS",
    
    # 데이터 클래스
    "User",
    "Document",
    "Permission",
    
    # 엔진
    "PermissionEngine",
]

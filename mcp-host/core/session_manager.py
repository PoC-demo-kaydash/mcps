"""
세션 관리

사용자 세션 생성/검증/관리
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from models.session import Session
from shared.database import DatabaseManager
from shared.queries import UserQueries
from shared.logging_config import get_logger

logger = get_logger(__name__)


class SessionManager:
    """
    세션 관리자
    
    메모리 기반 세션 저장 및 관리
    """
    
    def __init__(self, config, db_manager: DatabaseManager):
        """
        Args:
            config: Config 인스턴스
            db_manager: DatabaseManager 인스턴스
        """
        self.config = config
        self.db_manager = db_manager
        self.sessions: Dict[str, Session] = {}
        self.user_queries = UserQueries(db_manager)
        self.logger = logger
    
    async def create_session(self, username: str, password: str) -> Optional[Session]:
        """
        세션 생성 (인증)
        
        Args:
            username: 사용자 ID
            password: 비밀번호
        
        Returns:
            Session: 세션 정보 또는 None
        """
        try:
            # 사용자 인증
            user = await self.user_queries.authenticate(username, password)
            if not user:
                self.logger.warning(f"Authentication failed: {username}")
                return None
            
            # 세션 ID 생성
            session_id = str(uuid.uuid4())
            
            # 세션 생성
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=self.config.host.session_timeout)
            
            session = Session(
                session_id=session_id,
                user_id=user["user_id"],
                user_role=user["role"],
                user_team=user.get("team"),
                created_at=now,
                expires_at=expires_at,
                last_activity=now
            )
            
            # 메모리에 저장
            self.sessions[session_id] = session
            
            self.logger.info(f"✓ Session created: {session_id} (user: {username})")
            return session
        
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        세션 조회 및 갱신
        
        Args:
            session_id: 세션 ID
        
        Returns:
            Session: 세션 정보 또는 None
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        # 만료 확인
        now = datetime.utcnow()
        if now > session.expires_at:
            self.logger.warning(f"Session expired: {session_id}")
            del self.sessions[session_id]
            return None
        
        # 마지막 활동 시각 갱신
        session.last_activity = now
        
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """
        세션 삭제 (로그아웃)
        
        Args:
            session_id: 세션 ID
        
        Returns:
            bool: 성공 여부
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"✓ Session deleted: {session_id}")
            return True
        return False
    
    def get_user_context(self, session_id: str) -> Optional[dict]:
        """
        사용자 컨텍스트 조회 (Tool 실행용)
        
        Args:
            session_id: 세션 ID
        
        Returns:
            dict: 사용자 컨텍스트 또는 None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return {
            "user_id": session.user_id,
            "user_role": session.user_role,
            "user_team": session.user_team
        }
    
    def cleanup_expired_sessions(self) -> int:
        """
        만료된 세션 정리
        
        Returns:
            int: 정리된 세션 수
        """
        now = datetime.utcnow()
        expired = [
            session_id for session_id, session in self.sessions.items()
            if now > session.expires_at
        ]
        
        for session_id in expired:
            del self.sessions[session_id]
        
        if expired:
            self.logger.info(f"Cleaned up {len(expired)} expired sessions")
        
        return len(expired)
    
    def list_active_sessions(self) -> list:
        """
        활성 세션 목록
        
        Returns:
            list: 활성 세션 목록
        """
        now = datetime.utcnow()
        return [
            {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "user_role": session.user_role,
                "created_at": session.created_at,
                "expires_at": session.expires_at,
                "last_activity": session.last_activity
            }
            for session in self.sessions.values()
            if now <= session.expires_at
        ]

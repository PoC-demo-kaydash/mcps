"""
스토리지 서비스

로컬 스토리지 관리 (브라우저)
"""

from typing import Optional


class StorageService:
    """
    스토리지 서비스
    
    Note: Reflex는 Python으로 작성하지만 브라우저 로컬 스토리지는
    JavaScript를 통해 접근해야 합니다. 
    실제 구현은 rx.local_storage 또는 JavaScript interop 사용 필요.
    여기서는 인터페이스만 정의합니다.
    """
    
    @staticmethod
    def set_token(token: str):
        """
        토큰 저장
        
        Args:
            token: JWT 토큰
        """
        # 실제 구현은 rx.local_storage.setItem("token", token) 사용
        # 또는 State에서 직접 처리
        pass
    
    @staticmethod
    def get_token() -> Optional[str]:
        """
        토큰 조회
        
        Returns:
            JWT 토큰 또는 None
        """
        # 실제 구현은 rx.local_storage.getItem("token") 사용
        return None
    
    @staticmethod
    def remove_token():
        """토큰 삭제"""
        # 실제 구현은 rx.local_storage.removeItem("token") 사용
        pass
    
    @staticmethod
    def set_session_id(session_id: str):
        """
        세션 ID 저장
        
        Args:
            session_id: 세션 ID
        """
        pass
    
    @staticmethod
    def get_session_id() -> Optional[str]:
        """
        세션 ID 조회
        
        Returns:
            세션 ID 또는 None
        """
        return None
    
    @staticmethod
    def remove_session_id():
        """세션 ID 삭제"""
        pass

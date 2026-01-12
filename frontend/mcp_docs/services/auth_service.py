"""
인증 서비스

사용자 인증 관련 비즈니스 로직
"""

from typing import Dict
from frontend.services.api_client import APIClient


class AuthService:
    """인증 서비스"""
    
    async def create_session(self, user_id: str) -> Dict:
        """
        세션 생성 (로그인)
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            세션 정보
        """
        client = APIClient()
        result = await client.post(
            "/api/v1/sessions",
            json={"user_id": user_id}
        )
        
        if result.get("status") != "success":
            raise Exception(result.get("error", {}).get("message", "세션 생성 실패"))
        
        return result.get("data", {})
    
    async def get_session(self, session_id: str, token: str) -> Dict:
        """
        세션 조회
        
        Args:
            session_id: 세션 ID
            token: JWT 토큰
            
        Returns:
            세션 정보
        """
        client = APIClient(token)
        result = await client.get(f"/api/v1/sessions/{session_id}")
        
        if result.get("status") != "success":
            raise Exception(result.get("error", {}).get("message", "세션 조회 실패"))
        
        return result.get("data", {})
    
    async def delete_session(self, session_id: str, token: str):
        """
        세션 삭제 (로그아웃)
        
        Args:
            session_id: 세션 ID
            token: JWT 토큰
        """
        client = APIClient(token)
        result = await client.delete(f"/api/v1/sessions/{session_id}")
        
        if result.get("status") != "success":
            raise Exception(result.get("error", {}).get("message", "세션 삭제 실패"))

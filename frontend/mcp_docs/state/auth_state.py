"""
인증 State

사용자 인증 및 세션 관리
"""

import reflex as rx
from typing import Dict
import os

from frontend.state.base import BaseState


class AuthState(BaseState):
    """인증 State"""
    
    # 로그인 여부
    is_authenticated: bool = False
    
    # 사용자 정보
    user: Dict = {}
    
    # 세션 ID
    session_id: str = ""
    
    # 토큰
    token: str = ""
    
    # 로그인 폼
    user_id: str = ""
    
    def set_user_id(self, user_id: str):
        """사용자 ID 설정"""
        self.user_id = user_id
    
    async def login(self):
        """로그인"""
        
        if not self.user_id:
            self.set_error("사용자 ID를 입력하세요")
            return
        
        self.set_loading(True)
        self.clear_messages()
        
        try:
            # API 클라이언트는 Phase 3에서 구현
            # 임시로 하드코딩
            import httpx
            
            api_url = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_url}/api/v1/sessions",
                    json={"user_id": self.user_id},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("status") == "success":
                        data = result.get("data", {})
                        
                        # 상태 업데이트
                        self.is_authenticated = True
                        self.user = data.get("user", {})
                        self.session_id = data.get("session_id", "")
                        self.token = data.get("token", "")
                        
                        self.set_success("로그인 성공")
                        
                        # 대시보드로 이동
                        return rx.redirect("/dashboard")
                    else:
                        error = result.get("error", {})
                        self.set_error(error.get("message", "로그인 실패"))
                else:
                    self.set_error(f"로그인 실패: HTTP {response.status_code}")
        
        except Exception as e:
            self.set_error(f"로그인 실패: {str(e)}")
        
        finally:
            self.set_loading(False)
    
    async def logout(self):
        """로그아웃"""
        
        self.set_loading(True)
        
        try:
            # 세션 삭제 API 호출 (Phase 3에서 서비스 레이어로 분리)
            if self.session_id and self.token:
                import httpx
                
                api_url = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
                
                async with httpx.AsyncClient() as client:
                    await client.delete(
                        f"{api_url}/api/v1/sessions/{self.session_id}",
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=30.0
                    )
            
            # 상태 초기화
            self.is_authenticated = False
            self.user = {}
            self.session_id = ""
            self.token = ""
            self.user_id = ""
            
            self.set_success("로그아웃 되었습니다")
            
            # 로그인 페이지로 이동
            return rx.redirect("/login")
        
        except Exception as e:
            self.set_error(f"로그아웃 실패: {str(e)}")
        
        finally:
            self.set_loading(False)
    
    def check_auth(self):
        """인증 확인 (로컬 스토리지 체크는 Phase 3에서 구현)"""
        # 브라우저 로컬 스토리지 체크는 JavaScript 필요
        # Phase 3에서 storage_service로 구현
        pass

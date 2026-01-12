"""
기본 State

모든 State의 부모 클래스
"""

import reflex as rx


class BaseState(rx.State):
    """기본 State - 로딩 및 메시지 관리"""
    
    # 로딩 상태
    is_loading: bool = False
    
    # 에러 메시지
    error_message: str = ""
    
    # 성공 메시지
    success_message: str = ""
    
    def set_loading(self, loading: bool):
        """로딩 상태 설정"""
        self.is_loading = loading
    
    def set_error(self, message: str):
        """에러 메시지 설정"""
        self.error_message = message
        self.success_message = ""
    
    def set_success(self, message: str):
        """성공 메시지 설정"""
        self.success_message = message
        self.error_message = ""
    
    def clear_messages(self):
        """메시지 초기화"""
        self.error_message = ""
        self.success_message = ""

"""
UI State

UI 상태 관리 (사이드바, 모달 등)
"""

import reflex as rx


class UIState(rx.State):
    """UI State"""
    
    # 사이드바 열림 상태
    sidebar_open: bool = True
    
    # 모달 열림 상태
    modal_open: bool = False
    
    # 모달 제목
    modal_title: str = ""
    
    # 모달 내용
    modal_content: str = ""
    
    def toggle_sidebar(self):
        """사이드바 토글"""
        self.sidebar_open = not self.sidebar_open
    
    def open_modal(self, title: str = "", content: str = ""):
        """모달 열기"""
        self.modal_open = True
        self.modal_title = title
        self.modal_content = content
    
    def close_modal(self):
        """모달 닫기"""
        self.modal_open = False
        self.modal_title = ""
        self.modal_content = ""

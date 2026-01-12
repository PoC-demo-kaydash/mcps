"""
전체 레이아웃 컴포넌트

헤더 + 사이드바 + 컨텐츠 + 푸터
"""

import reflex as rx
from frontend.components.layout.header import header
from frontend.components.layout.sidebar import sidebar
from frontend.components.layout.footer import footer
from frontend.state.auth_state import AuthState


def layout(*children, show_sidebar: bool = True) -> rx.Component:
    """
    전체 레이아웃
    
    Args:
        children: 메인 컨텐츠
        show_sidebar: 사이드바 표시 여부
        
    Returns:
        레이아웃 컴포넌트
    """
    
    return rx.box(
        header(),
        rx.hstack(
            # 사이드바 (로그인 시 & show_sidebar=True)
            rx.cond(
                AuthState.is_authenticated & show_sidebar,
                sidebar(),
                rx.box(),
            ),
            
            # 메인 컨텐츠
            rx.box(
                *children,
                flex="1",
                padding="4",
                overflow_y="auto",
            ),
            
            spacing="0",
            align="stretch",
            width="100%",
        ),
        footer(),
        min_height="100vh",
        display="flex",
        flex_direction="column",
    )

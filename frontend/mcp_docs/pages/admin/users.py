"""
사용자 관리 페이지

사용자 목록 및 권한 관리
"""

import reflex as rx
from frontend.state.auth_state import AuthState
from frontend.components.layout.layout import layout


def admin_users() -> rx.Component:
    """사용자 관리 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 권한 체크
                rx.cond(
                    AuthState.user.get("role") == "admin",
                    rx.vstack(
                        rx.heading("사용자 관리", size="xl"),
                        
                        # 사용자 목록 (구현 예정)
                        rx.text(
                            "사용자 목록 테이블 (구현 예정)",
                            color="gray.600",
                        ),
                        
                        spacing="6",
                        width="100%",
                    ),
                    rx.callout(
                        "관리자 권한이 필요합니다.",
                        icon="alert_circle",
                        color_scheme="red",
                    ),
                ),
                
                spacing="6",
                width="100%",
            ),
            padding_y="8",
        ),
    )

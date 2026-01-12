"""
통계 페이지

시스템 통계 및 감사 로그
"""

import reflex as rx
from frontend.state.auth_state import AuthState
from frontend.components.layout.layout import layout


def admin_stats() -> rx.Component:
    """통계 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 권한 체크
                rx.cond(
                    AuthState.user.get("role") == "admin",
                    rx.vstack(
                        rx.heading("시스템 통계", size="xl"),
                        
                        # 통계 (구현 예정)
                        rx.text(
                            "시스템 통계 및 감사 로그 (구현 예정)",
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

"""
사이드바 컴포넌트

좌측 네비게이션 메뉴
"""

import reflex as rx
from frontend.state.auth_state import AuthState


def sidebar() -> rx.Component:
    """사이드바 컴포넌트"""
    
    return rx.box(
        rx.vstack(
            # 네비게이션 링크
            rx.link(
                rx.hstack(
                    rx.text("🏠", font_size="20px"),
                    rx.text("대시보드"),
                    spacing="3",
                    padding="3",
                    border_radius="md",
                    width="100%",
                    _hover={"background": "gray.100"},
                ),
                href="/dashboard",
                width="100%",
            ),
            
            rx.link(
                rx.hstack(
                    rx.text("📄", font_size="20px"),
                    rx.text("문서"),
                    spacing="3",
                    padding="3",
                    border_radius="md",
                    width="100%",
                    _hover={"background": "gray.100"},
                ),
                href="/documents",
                width="100%",
            ),
            
            rx.link(
                rx.hstack(
                    rx.text("🔍", font_size="20px"),
                    rx.text("검색"),
                    spacing="3",
                    padding="3",
                    border_radius="md",
                    width="100%",
                    _hover={"background": "gray.100"},
                ),
                href="/search",
                width="100%",
            ),
            
            # Admin 메뉴 (조건부)
            rx.cond(
                AuthState.user.get("role") == "admin",
                rx.vstack(
                    rx.divider(),
                    rx.text(
                        "관리자",
                        font_weight="bold",
                        font_size="sm",
                        color="gray.600",
                    ),
                    
                    rx.link(
                        rx.hstack(
                            rx.text("👥", font_size="20px"),
                            rx.text("사용자"),
                            spacing="3",
                            padding="3",
                            border_radius="md",
                            width="100%",
                            _hover={"background": "gray.100"},
                        ),
                        href="/admin/users",
                        width="100%",
                    ),
                    
                    rx.link(
                        rx.hstack(
                            rx.text("📊", font_size="20px"),
                            rx.text("통계"),
                            spacing="3",
                            padding="3",
                            border_radius="md",
                            width="100%",
                            _hover={"background": "gray.100"},
                        ),
                        href="/admin/stats",
                        width="100%",
                    ),
                    
                    spacing="2",
                    width="100%",
                ),
                rx.box(),
            ),
            
            spacing="2",
            width="100%",
            align="stretch",
        ),
        width="250px",
        padding="4",
        border_right="1px solid",
        border_color="gray.200",
        min_height="calc(100vh - 72px)",
    )

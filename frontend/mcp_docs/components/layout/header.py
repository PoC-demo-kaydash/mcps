"""
헤더 컴포넌트

상단 네비게이션 및 사용자 메뉴
"""

import reflex as rx
from frontend.state.auth_state import AuthState


def header() -> rx.Component:
    """헤더 컴포넌트"""
    
    return rx.box(
        rx.hstack(
            # 로고
            rx.link(
                rx.hstack(
                    rx.text("📄", font_size="24px"),
                    rx.heading("MCP Docs", size="md"),
                    spacing="2",
                ),
                href="/",
            ),
            
            rx.spacer(),
            
            # 네비게이션 & 사용자 메뉴
            rx.cond(
                AuthState.is_authenticated,
                rx.hstack(
                    rx.link("대시보드", href="/dashboard"),
                    rx.link("문서", href="/documents"),
                    rx.link("검색", href="/search"),
                    
                    # 사용자 이름 & 로그아웃
                    rx.menu(
                        rx.menu_button(
                            rx.hstack(
                                rx.avatar(size="sm"),
                                rx.text(AuthState.user_id),
                                spacing="2",
                            ),
                        ),
                        rx.menu_list(
                            rx.menu_item("내 정보"),
                            rx.menu_divider(),
                            rx.menu_item(
                                "로그아웃",
                                on_click=AuthState.logout,
                            ),
                        ),
                    ),
                    
                    spacing="6",
                ),
                rx.button(
                    "로그인",
                    on_click=rx.redirect("/login"),
                    color_scheme="blue",
                ),
            ),
            
            align="center",
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding_x="4",
        ),
        padding_y="4",
        border_bottom="1px solid",
        border_color="gray.200",
        background="white",
        position="sticky",
        top="0",
        z_index="10",
    )

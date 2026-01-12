"""
대시보드 페이지

사용자 대시보드
"""

import reflex as rx
from frontend.state.auth_state import AuthState
from frontend.components.layout.layout import layout


def dashboard() -> rx.Component:
    """대시보드 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 환영 메시지
                rx.heading(
                    rx.cond(
                        AuthState.user_id != "",
                        f"환영합니다, {AuthState.user_id}님!",
                        "대시보드",
                    ),
                    size="xl",
                ),
                
                # 통계 카드
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text("내 문서", font_weight="bold"),
                            rx.heading("24", size="2xl"),
                            rx.text("전체 문서 수", font_size="sm", color="gray.600"),
                            spacing="1",
                        ),
                        padding="6",
                        border="1px solid",
                        border_color="gray.200",
                        border_radius="md",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("오늘 조회", font_weight="bold"),
                            rx.heading("128", size="2xl"),
                            rx.text("오늘 조회된 문서", font_size="sm", color="gray.600"),
                            spacing="1",
                        ),
                        padding="6",
                        border="1px solid",
                        border_color="gray.200",
                        border_radius="md",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("최근 수정", font_weight="bold"),
                            rx.heading("3", size="2xl"),
                            rx.text("최근 7일간 수정", font_size="sm", color="gray.600"),
                            spacing="1",
                        ),
                        padding="6",
                        border="1px solid",
                        border_color="gray.200",
                        border_radius="md",
                    ),
                    spacing="6",
                    width="100%",
                ),
                
                # 최근 문서
                rx.heading("최근 문서", size="md"),
                rx.divider(),
                rx.text("최근 문서가 여기에 표시됩니다.", color="gray.500"),
                
                # 빠른 액션
                rx.hstack(
                    rx.button(
                        rx.hstack(
                            rx.text("➕"),
                            rx.text("새 문서"),
                            spacing="2",
                        ),
                        on_click=rx.redirect("/documents/create"),
                        color_scheme="blue",
                    ),
                    rx.button(
                        rx.hstack(
                            rx.text("🔍"),
                            rx.text("검색"),
                            spacing="2",
                        ),
                        on_click=rx.redirect("/search"),
                        color_scheme="green",
                    ),
                    spacing="4",
                ),
                
                spacing="6",
                width="100%",
            ),
            padding_y="8",
        ),
    )

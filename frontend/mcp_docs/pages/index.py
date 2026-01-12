"""
홈 페이지

시스템 소개 및 시작 페이지
"""

import reflex as rx
from frontend.components.layout.layout import layout


def index() -> rx.Component:
    """홈 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 헤더
                rx.heading(
                    "MCP 문서 관리 시스템",
                    size="2xl",
                    color="blue.600",
                ),
                rx.text(
                    "Model Context Protocol 기반 문서 관리 및 검색 시스템",
                    font_size="lg",
                    color="gray.600",
                ),
                
                # 주요 기능
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text("📄", font_size="40px"),
                            rx.heading("문서 관리", size="md"),
                            rx.text(
                                "문서 생성, 수정, 삭제 및 버전 관리",
                                text_align="center",
                            ),
                            spacing="3",
                        ),
                        padding="6",
                        border="1px solid",
                        border_color="gray.200",
                        border_radius="md",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("🔍", font_size="40px"),
                            rx.heading("전문 검색", size="md"),
                            rx.text(
                                "강력한 검색 기능으로 문서 빠르게 찾기",
                                text_align="center",
                            ),
                            spacing="3",
                        ),
                        padding="6",
                        border="1px solid",
                        border_color="gray.200",
                        border_radius="md",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("🔒", font_size="40px"),
                            rx.heading("권한 관리", size="md"),
                            rx.text(
                                "세밀한 권한 관리로 보안 강화",
                                text_align="center",
                            ),
                            spacing="3",
                        ),
                        padding="6",
                        border="1px solid",
                        border_color="gray.200",
                        border_radius="md",
                    ),
                    spacing="6",
                ),
                
                # CTA
                rx.button(
                    "시작하기",
                    on_click=rx.redirect("/login"),
                    size="lg",
                    color_scheme="blue",
                ),
                
                spacing="8",
                align="center",
            ),
            padding_y="16",
        ),
        show_sidebar=False,
    )

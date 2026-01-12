"""
푸터 컴포넌트

하단 정보 영역
"""

import reflex as rx


def footer() -> rx.Component:
    """푸터 컴포넌트"""
    
    return rx.box(
        rx.hstack(
            rx.text("© 2026 MCP Docs. All rights reserved.", font_size="sm", color="gray.600"),
            rx.spacer(),
            rx.hstack(
                rx.link("도움말", href="#", font_size="sm", color="gray.600"),
                rx.link("문의", href="#", font_size="sm", color="gray.600"),
                spacing="4",
            ),
            align="center",
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding_x="4",
        ),
        padding_y="4",
        border_top="1px solid",
        border_color="gray.200",
        background="white",
    )

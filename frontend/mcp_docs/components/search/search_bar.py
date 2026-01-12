"""
검색바 컴포넌트

문서 검색 입력
"""

import reflex as rx
from frontend.state.search_state import SearchState


def search_bar() -> rx.Component:
    """검색바 컴포넌트"""
    
    return rx.form(
        rx.hstack(
            rx.input(
                placeholder="문서 검색...",
                value=SearchState.query,
                on_change=SearchState.set_query,
                size="lg",
                flex="1",
            ),
            rx.button(
                rx.cond(
                    SearchState.is_loading,
                    rx.spinner(size="sm"),
                    rx.hstack(
                        rx.text("🔍"),
                        rx.text("검색"),
                        spacing="2",
                    ),
                ),
                on_click=SearchState.search,
                color_scheme="blue",
                size="lg",
                is_loading=SearchState.is_loading,
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
        on_submit=SearchState.search,
    )

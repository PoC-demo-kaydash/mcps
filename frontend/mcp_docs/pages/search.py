"""
검색 페이지

문서 검색
"""

import reflex as rx
from frontend.state.search_state import SearchState
from frontend.components.layout.layout import layout
from frontend.components.search.search_bar import search_bar
from frontend.components.search.result_item import search_result_item


def search() -> rx.Component:
    """검색 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 검색바
                search_bar(),
                
                # 필터
                rx.hstack(
                    rx.select(
                        ["전체", "documentation", "guide", "standard"],
                        placeholder="카테고리",
                        value=SearchState.category_filter,
                        on_change=SearchState.set_category_filter,
                    ),
                    spacing="3",
                ),
                
                # 에러 메시지
                rx.cond(
                    SearchState.error_message != "",
                    rx.callout(
                        SearchState.error_message,
                        icon="alert_circle",
                        color_scheme="red",
                    ),
                ),
                
                # 검색 결과
                rx.cond(
                    SearchState.is_loading,
                    rx.center(rx.spinner(size="xl"), padding="8"),
                    rx.vstack(
                        rx.cond(
                            SearchState.total > 0,
                            rx.vstack(
                                rx.text(
                                    f"{SearchState.total}개의 결과",
                                    font_weight="bold",
                                ),
                                rx.foreach(
                                    SearchState.results,
                                    search_result_item,
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            rx.center(
                                rx.text(
                                    "검색 결과가 없습니다",
                                    color="gray.500",
                                ),
                                padding="8",
                            ),
                        ),
                        width="100%",
                    ),
                ),
                
                spacing="6",
                width="100%",
            ),
            padding_y="8",
        ),
    )

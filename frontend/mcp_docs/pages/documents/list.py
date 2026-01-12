"""
문서 목록 페이지

문서 목록 조회 및 필터링
"""

import reflex as rx
from frontend.state.document_state import DocumentState
from frontend.components.layout.layout import layout
from frontend.components.document.list_item import document_list_item


def documents_list() -> rx.Component:
    """문서 목록 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 헤더
                rx.hstack(
                    rx.heading("문서 목록", size="xl"),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(
                            rx.text("➕"),
                            rx.text("새 문서"),
                            spacing="2",
                        ),
                        on_click=rx.redirect("/documents/create"),
                        color_scheme="blue",
                    ),
                    width="100%",
                ),
                
                # 필터
                rx.hstack(
                    rx.select(
                        ["전체", "public", "team", "department", "confidential"],
                        placeholder="공개 범위",
                        value=DocumentState.classification,
                        on_change=DocumentState.set_classification,
                    ),
                    rx.input(
                        placeholder="카테고리",
                        value=DocumentState.category,
                        on_change=DocumentState.set_category,
                    ),
                    rx.button(
                        "검색",
                        on_click=DocumentState.load_documents,
                        color_scheme="green",
                    ),
                    spacing="3",
                    width="100%",
                ),
                
                # 에러/성공 메시지
                rx.cond(
                    DocumentState.error_message != "",
                    rx.callout(
                        DocumentState.error_message,
                        icon="alert_circle",
                        color_scheme="red",
                    ),
                ),
                rx.cond(
                    DocumentState.success_message != "",
                    rx.callout(
                        DocumentState.success_message,
                        icon="check",
                        color_scheme="green",
                    ),
                ),
                
                # 로딩 또는 문서 목록
                rx.cond(
                    DocumentState.is_loading,
                    rx.center(
                        rx.spinner(size="xl"),
                        padding="8",
                    ),
                    rx.vstack(
                        rx.foreach(
                            DocumentState.documents,
                            document_list_item,
                        ),
                        spacing="4",
                        width="100%",
                    ),
                ),
                
                # 페이지네이션
                rx.hstack(
                    rx.text(f"총 {DocumentState.total}개"),
                    rx.spacer(),
                    rx.hstack(
                        rx.button(
                            "이전",
                            on_click=DocumentState.set_page(
                                DocumentState.page - 1
                            ),
                            is_disabled=DocumentState.page <= 1,
                        ),
                        rx.text(f"{DocumentState.page} 페이지"),
                        rx.button(
                            "다음",
                            on_click=DocumentState.set_page(
                                DocumentState.page + 1
                            ),
                            is_disabled=(
                                DocumentState.page * DocumentState.page_size
                                >= DocumentState.total
                            ),
                        ),
                        spacing="2",
                    ),
                    width="100%",
                ),
                
                spacing="6",
                width="100%",
            ),
            padding_y="8",
            on_mount=DocumentState.load_documents,
        ),
    )

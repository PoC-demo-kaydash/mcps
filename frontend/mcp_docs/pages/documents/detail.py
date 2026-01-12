"""
문서 상세 페이지

문서 내용 조회
"""

import reflex as rx
from frontend.state.document_state import DocumentState
from frontend.components.layout.layout import layout
from frontend.components.document.viewer import document_viewer


def document_detail(doc_id: str) -> rx.Component:
    """문서 상세 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 헤더
                rx.hstack(
                    rx.button(
                        "←",
                        on_click=rx.redirect("/documents"),
                        variant="ghost",
                    ),
                    rx.heading(
                        DocumentState.current_document.get("title", "문서"),
                        size="xl",
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.button(
                            "✏️ 수정",
                            on_click=rx.redirect(f"/documents/{doc_id}/edit"),
                            variant="outline",
                        ),
                        rx.button(
                            "🗑️ 삭제",
                            on_click=DocumentState.delete_document(doc_id),
                            color_scheme="red",
                            variant="outline",
                        ),
                        spacing="2",
                    ),
                    width="100%",
                ),
                
                # 메타 정보
                rx.hstack(
                    rx.badge(
                        DocumentState.current_document.get("classification", "")
                    ),
                    rx.badge(
                        DocumentState.current_document.get("category", ""),
                        color_scheme="green",
                    ),
                    rx.text(
                        f"작성자: {DocumentState.current_document.get('author_name', '')}"
                    ),
                    rx.text(
                        f"버전: {DocumentState.current_document.get('version', '')}"
                    ),
                    spacing="3",
                ),
                
                # 문서 내용
                rx.cond(
                    DocumentState.is_loading,
                    rx.center(rx.spinner(size="xl"), padding="8"),
                    document_viewer(DocumentState.current_document),
                ),
                
                spacing="6",
                width="100%",
            ),
            padding_y="8",
            on_mount=lambda: DocumentState.load_document(doc_id),
        ),
    )

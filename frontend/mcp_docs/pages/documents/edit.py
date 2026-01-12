"""
문서 수정 페이지

기존 문서 수정
"""

import reflex as rx
from frontend.state.document_state import DocumentState
from frontend.components.layout.layout import layout


def document_edit(doc_id: str) -> rx.Component:
    """문서 수정 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 헤더
                rx.hstack(
                    rx.button(
                        "←",
                        on_click=rx.redirect(f"/documents/{doc_id}"),
                        variant="ghost",
                    ),
                    rx.heading("문서 수정", size="xl"),
                    width="100%",
                ),
                
                # 에러 메시지
                rx.cond(
                    DocumentState.error_message != "",
                    rx.callout(
                        DocumentState.error_message,
                        icon="alert_circle",
                        color_scheme="red",
                    ),
                ),
                
                # 문서 폼 (create.py와 유사, 기존 데이터 로드 필요)
                rx.text(
                    "문서 수정 폼 (구현 예정)",
                    color="gray.600",
                ),
                
                spacing="6",
                width="100%",
            ),
            max_width="800px",
            padding_y="8",
            on_mount=lambda: DocumentState.load_document(doc_id),
        ),
    )

"""
문서 생성 페이지

새 문서 작성
"""

import reflex as rx
from frontend.state.document_state import DocumentState
from frontend.components.layout.layout import layout


def document_create() -> rx.Component:
    """문서 생성 페이지"""
    
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
                    rx.heading("새 문서 작성", size="xl"),
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
                
                # 문서 폼
                rx.form(
                    rx.vstack(
                        # 제목
                        rx.form_control(
                            rx.form_label("제목"),
                            rx.input(
                                placeholder="문서 제목을 입력하세요",
                                value=DocumentState.doc_title,
                                on_change=DocumentState.set_doc_title,
                                size="lg",
                            ),
                            is_required=True,
                        ),
                        
                        # 공개 범위
                        rx.form_control(
                            rx.form_label("공개 범위"),
                            rx.select(
                                ["public", "team", "department", "confidential"],
                                value=DocumentState.doc_classification,
                                on_change=DocumentState.set_doc_classification,
                            ),
                            is_required=True,
                        ),
                        
                        # 카테고리
                        rx.form_control(
                            rx.form_label("카테고리"),
                            rx.input(
                                placeholder="카테고리를 입력하세요",
                                value=DocumentState.doc_category,
                                on_change=DocumentState.set_doc_category,
                            ),
                            is_required=True,
                        ),
                        
                        # 태그
                        rx.form_control(
                            rx.form_label("태그"),
                            rx.input(
                                placeholder="태그를 쉼표로 구분하여 입력하세요",
                                value=DocumentState.doc_tags,
                                on_change=DocumentState.set_doc_tags,
                            ),
                        ),
                        
                        # 내용
                        rx.form_control(
                            rx.form_label("내용 (Markdown)"),
                            rx.text_area(
                                placeholder="문서 내용을 Markdown으로 작성하세요",
                                value=DocumentState.doc_content,
                                on_change=DocumentState.set_doc_content,
                                min_height="400px",
                            ),
                            is_required=True,
                        ),
                        
                        # 버튼
                        rx.hstack(
                            rx.button(
                                "취소",
                                on_click=rx.redirect("/documents"),
                                variant="outline",
                            ),
                            rx.button(
                                rx.cond(
                                    DocumentState.is_loading,
                                    rx.spinner(size="sm"),
                                    "생성",
                                ),
                                on_click=DocumentState.create_document,
                                color_scheme="blue",
                                is_loading=DocumentState.is_loading,
                            ),
                            spacing="3",
                        ),
                        
                        spacing="4",
                        width="100%",
                    ),
                    width="100%",
                ),
                
                spacing="6",
                width="100%",
            ),
            max_width="800px",
            padding_y="8",
        ),
    )

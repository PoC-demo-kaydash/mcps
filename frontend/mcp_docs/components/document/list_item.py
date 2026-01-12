"""
문서 목록 아이템 컴포넌트

문서 목록의 개별 아이템
"""

import reflex as rx


def document_list_item(document: dict) -> rx.Component:
    """
    문서 목록 아이템
    
    Args:
        document: 문서 데이터
        
    Returns:
        아이템 컴포넌트
    """
    
    return rx.link(
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.heading(document.get("title", "제목 없음"), size="md"),
                        rx.spacer(),
                        rx.badge(document.get("classification", "public")),
                        width="100%",
                    ),
                    
                    rx.text(
                        document.get("content", "")[:200] + "...",
                        color="gray.600",
                        no_of_lines=2,
                    ),
                    
                    rx.hstack(
                        rx.badge(
                            document.get("category", "일반"),
                            color_scheme="green",
                        ),
                        rx.text(
                            f"작성자: {document.get('author_name', 'Unknown')}",
                            font_size="sm",
                            color="gray.500",
                        ),
                        rx.text(
                            f"버전: {document.get('version', 1)}",
                            font_size="sm",
                            color="gray.500",
                        ),
                        spacing="3",
                    ),
                    
                    spacing="2",
                    align="start",
                    width="100%",
                ),
                
                rx.text("›", font_size="24px", color="gray.400"),
                
                width="100%",
            ),
            padding="4",
            border="1px solid",
            border_color="gray.200",
            border_radius="md",
            _hover={"background": "gray.50"},
            cursor="pointer",
        ),
        href=f"/documents/{document.get('id')}",
        width="100%",
    )

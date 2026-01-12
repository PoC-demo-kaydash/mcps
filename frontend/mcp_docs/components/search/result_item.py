"""
검색 결과 아이템 컴포넌트

검색 결과 개별 아이템
"""

import reflex as rx


def search_result_item(result: dict) -> rx.Component:
    """
    검색 결과 아이템
    
    Args:
        result: 검색 결과 데이터
        
    Returns:
        아이템 컴포넌트
    """
    
    return rx.link(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading(result.get("title", "제목 없음"), size="md"),
                    rx.spacer(),
                    rx.badge(result.get("classification", "public")),
                    width="100%",
                ),
                
                # 하이라이트된 내용
                rx.text(
                    result.get("highlight", result.get("content", ""))[:200],
                    color="gray.600",
                    no_of_lines=2,
                ),
                
                rx.hstack(
                    rx.badge(
                        result.get("category", "일반"),
                        color_scheme="green",
                    ),
                    rx.text(
                        f"작성자: {result.get('author_name', 'Unknown')}",
                        font_size="sm",
                        color="gray.500",
                    ),
                    rx.text(
                        f"점수: {result.get('score', 0):.2f}",
                        font_size="sm",
                        color="gray.500",
                    ),
                    spacing="3",
                ),
                
                spacing="2",
                align="start",
                width="100%",
            ),
            padding="4",
            border="1px solid",
            border_color="gray.200",
            border_radius="md",
            _hover={"background": "gray.50"},
            cursor="pointer",
        ),
        href=f"/documents/{result.get('doc_id')}",
        width="100%",
    )

"""
문서 뷰어 컴포넌트

Markdown 렌더링
"""

import reflex as rx


def document_viewer(document: dict) -> rx.Component:
    """
    문서 뷰어
    
    Args:
        document: 문서 데이터
        
    Returns:
        뷰어 컴포넌트
    """
    
    return rx.box(
        rx.markdown(document.get("content", "내용이 없습니다.")),
        padding="6",
        border="1px solid",
        border_color="gray.200",
        border_radius="md",
        background="white",
        width="100%",
    )

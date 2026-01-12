"""
문서 에디터 컴포넌트

Markdown 에디터
"""

import reflex as rx
from typing import Any


def document_editor(value: str, on_change: Any) -> rx.Component:
    """
    문서 에디터
    
    Args:
        value: 현재 값
        on_change: 변경 핸들러
        
    Returns:
        에디터 컴포넌트
    """
    
    return rx.text_area(
        value=value,
        on_change=on_change,
        placeholder="Markdown으로 문서를 작성하세요...",
        min_height="400px",
        font_family="monospace",
    )

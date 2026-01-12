"""
모달 컴포넌트

모달 다이얼로그
"""

import reflex as rx
from typing import Any


def modal(is_open: bool, on_close: Any, title: str, *children) -> rx.Component:
    """
    모달 컴포넌트
    
    Args:
        is_open: 모달 열림 상태
        on_close: 닫기 핸들러
        title: 모달 제목
        children: 모달 내용
        
    Returns:
        모달 컴포넌트
    """
    
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_header(title),
                rx.modal_body(
                    *children,
                ),
                rx.modal_footer(
                    rx.button(
                        "닫기",
                        on_click=on_close,
                    ),
                ),
            ),
        ),
        is_open=is_open,
        on_close=on_close,
    )

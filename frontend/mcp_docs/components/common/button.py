"""
버튼 컴포넌트

재사용 가능한 버튼 스타일
"""

import reflex as rx
from typing import Any


def primary_button(text: str, on_click: Any = None, **kwargs) -> rx.Component:
    """Primary 버튼"""
    return rx.button(
        text,
        on_click=on_click,
        color_scheme="blue",
        **kwargs,
    )


def secondary_button(text: str, on_click: Any = None, **kwargs) -> rx.Component:
    """Secondary 버튼"""
    return rx.button(
        text,
        on_click=on_click,
        variant="outline",
        **kwargs,
    )


def danger_button(text: str, on_click: Any = None, **kwargs) -> rx.Component:
    """Danger 버튼"""
    return rx.button(
        text,
        on_click=on_click,
        color_scheme="red",
        variant="outline",
        **kwargs,
    )

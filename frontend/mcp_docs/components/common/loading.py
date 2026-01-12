"""
로딩 컴포넌트

로딩 스피너
"""

import reflex as rx


def loading_spinner(size: str = "xl") -> rx.Component:
    """
    로딩 스피너
    
    Args:
        size: 스피너 크기
        
    Returns:
        스피너 컴포넌트
    """
    return rx.spinner(size=size)


def full_page_loading() -> rx.Component:
    """전체 페이지 로딩"""
    return rx.center(
        rx.vstack(
            rx.spinner(size="xl"),
            rx.text("로딩 중...", font_size="lg", color="gray.600"),
            spacing="4",
        ),
        height="100vh",
    )

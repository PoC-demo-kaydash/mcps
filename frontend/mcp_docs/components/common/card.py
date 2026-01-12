"""
카드 컴포넌트

컨텐츠 컨테이너 카드
"""

import reflex as rx


def card(*children, **kwargs) -> rx.Component:
    """
    카드 컴포넌트
    
    Args:
        children: 카드 내용
        kwargs: 추가 속성
        
    Returns:
        카드 컴포넌트
    """
    default_props = {
        "padding": "4",
        "border": "1px solid",
        "border_color": "gray.200",
        "border_radius": "md",
        "background": "white",
    }
    
    return rx.box(
        *children,
        **{**default_props, **kwargs},
    )

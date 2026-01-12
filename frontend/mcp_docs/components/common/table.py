"""
테이블 컴포넌트

데이터 테이블
"""

import reflex as rx
from typing import List


def data_table(headers: List[str], rows: List[List], **kwargs) -> rx.Component:
    """
    데이터 테이블
    
    Args:
        headers: 헤더 목록
        rows: 행 데이터
        kwargs: 추가 속성
        
    Returns:
        테이블 컴포넌트
    """
    
    return rx.table_container(
        rx.table(
            rx.thead(
                rx.tr(
                    *[rx.th(header) for header in headers]
                )
            ),
            rx.tbody(
                *[
                    rx.tr(
                        *[rx.td(cell) for cell in row]
                    )
                    for row in rows
                ]
            ),
            variant="simple",
            **kwargs,
        )
    )

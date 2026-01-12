"""
로그인 페이지

사용자 인증
"""

import reflex as rx
from frontend.state.auth_state import AuthState


def login() -> rx.Component:
    """로그인 페이지"""
    
    return rx.center(
        rx.box(
            rx.vstack(
                # 제목
                rx.heading("로그인", size="xl"),
                
                # 에러/성공 메시지
                rx.cond(
                    AuthState.error_message != "",
                    rx.callout(
                        AuthState.error_message,
                        icon="alert_circle",
                        color_scheme="red",
                    ),
                ),
                rx.cond(
                    AuthState.success_message != "",
                    rx.callout(
                        AuthState.success_message,
                        icon="check",
                        color_scheme="green",
                    ),
                ),
                
                # 로그인 폼
                rx.form_control(
                    rx.form_label("사용자 ID"),
                    rx.input(
                        placeholder="사용자 ID를 입력하세요",
                        value=AuthState.user_id,
                        on_change=AuthState.set_user_id,
                        is_disabled=AuthState.is_loading,
                    ),
                    is_required=True,
                ),
                
                # 로그인 버튼
                rx.button(
                    rx.cond(
                        AuthState.is_loading,
                        rx.spinner(size="sm"),
                        "로그인",
                    ),
                    on_click=AuthState.login,
                    width="100%",
                    color_scheme="blue",
                    is_loading=AuthState.is_loading,
                ),
                
                spacing="4",
                width="100%",
            ),
            padding="8",
            max_width="400px",
            border="1px solid",
            border_color="gray.200",
            border_radius="md",
        ),
        height="100vh",
    )

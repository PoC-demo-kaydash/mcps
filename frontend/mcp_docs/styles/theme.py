"""
테마

애플리케이션 테마 설정
"""

import reflex as rx


# 색상 팔레트
colors = {
    "primary": {
        "50": "#E6F2FF",
        "100": "#BAE0FF",
        "200": "#7CC4FA",
        "300": "#47A3F3",
        "400": "#2186EB",
        "500": "#0967D2",
        "600": "#0552B5",
        "700": "#03449E",
        "800": "#01337D",
        "900": "#002159",
    },
    "gray": {
        "50": "#F7FAFC",
        "100": "#EDF2F7",
        "200": "#E2E8F0",
        "300": "#CBD5E0",
        "400": "#A0AEC0",
        "500": "#718096",
        "600": "#4A5568",
        "700": "#2D3748",
        "800": "#1A202C",
        "900": "#171923",
    },
}


# 테마 설정
theme = rx.theme(
    appearance="light",
    accent_color="blue",
    gray_color="gray",
    radius="medium",
    scaling="100%",
)


# 글로벌 스타일
global_styles = {
    "body": {
        "font_family": "system-ui, -apple-system, sans-serif",
        "background": colors["gray"]["50"],
    },
    "a": {
        "text_decoration": "none",
        "_hover": {
            "text_decoration": "none",
        },
    },
}

"""
Reflex 설정 파일

Frontend 애플리케이션의 기본 설정
"""

import reflex as rx


config = rx.Config(
    app_name="mcp_docs",
    api_url="http://localhost:8000",
    deploy_url="https://mcp-docs.example.com",
    backend_port=8000,
    frontend_port=3000,
    db_url="sqlite:///reflex.db",
    env=rx.Env.DEV,
)

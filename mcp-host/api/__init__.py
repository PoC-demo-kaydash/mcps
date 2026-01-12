"""
MCP Host REST API

FastAPI 라우트 및 미들웨어
"""

from .routes import router
from .middleware import setup_middleware

__all__ = [
    "router",
    "setup_middleware",
]

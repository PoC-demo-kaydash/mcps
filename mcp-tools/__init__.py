"""
mcp-tools 패키지

MCP Tool 정의 및 관리 모듈
"""

__version__ = "1.0.0"

# 기본 클래스
from .base import BaseTool, AsyncBaseTool, ToolMetadata, measure_execution_time
from .validator import ValidationError, ToolValidator
from .registry import (
    ToolRegistry,
    get_registry,
    register_tool,
    get_tool,
    list_all_tools
)

__all__ = [
    # 기본 클래스
    "BaseTool",
    "AsyncBaseTool",
    "ToolMetadata",
    "measure_execution_time",
    
    # 검증
    "ValidationError",
    "ToolValidator",
    
    # 레지스트리
    "ToolRegistry",
    "get_registry",
    "register_tool",
    "get_tool",
    "list_all_tools",
]


def get_version():
    """패키지 버전 반환"""
    return __version__

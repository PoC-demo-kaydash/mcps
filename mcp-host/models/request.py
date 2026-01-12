"""
Tool 실행 요청/응답 모델

Tool 실행, Tool 목록 관련 데이터 모델
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ToolExecuteRequest(BaseModel):
    """Tool 실행 요청"""
    tool_name: str = Field(..., description="Tool 이름")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool 인자")
    session_id: Optional[str] = Field(None, description="세션 ID (옵션)")


class ToolExecuteResponse(BaseModel):
    """Tool 실행 응답"""
    tool_name: str = Field(..., description="Tool 이름")
    status: str = Field(..., description="실행 상태 (success, error)")
    result: Optional[Any] = Field(None, description="실행 결과")
    error: Optional[Dict[str, Any]] = Field(None, description="에러 정보")
    execution_time: float = Field(..., description="실행 시간 (초)")


class ToolInfo(BaseModel):
    """Tool 메타데이터"""
    name: str = Field(..., description="Tool 이름")
    server: str = Field(..., description="소속 Server")
    category: str = Field(..., description="카테고리")
    description: str = Field(..., description="설명")
    input_schema: Dict[str, Any] = Field(..., description="입력 스키마")
    required_permissions: List[str] = Field(default_factory=list, description="필수 권한")
    available: bool = Field(True, description="사용 가능 여부")


class ToolListResponse(BaseModel):
    """Tool 목록 응답"""
    tools: List[ToolInfo] = Field(..., description="Tool 목록")
    total: int = Field(..., description="전체 Tool 수")
    available: int = Field(..., description="사용 가능한 Tool 수")

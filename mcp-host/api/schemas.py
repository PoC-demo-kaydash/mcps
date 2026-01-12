"""
API 스키마

API 응답 표준 스키마
"""

from typing import Any, Optional, Dict
from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    """성공 응답"""
    status: str = Field(default="success", description="응답 상태")
    data: Any = Field(..., description="응답 데이터")


class ErrorDetail(BaseModel):
    """에러 상세"""
    code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="상세 정보")


class ErrorResponse(BaseModel):
    """에러 응답"""
    status: str = Field(default="error", description="응답 상태")
    error: ErrorDetail = Field(..., description="에러 정보")


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답"""
    status: str = Field(..., description="상태 (healthy, degraded, unhealthy)")
    timestamp: str = Field(..., description="체크 시각")
    version: str = Field(..., description="버전")
    servers: Dict[str, Any] = Field(..., description="Server 상태")

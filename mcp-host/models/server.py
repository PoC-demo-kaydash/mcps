"""
Server 모델

Server 상태, 액션 관련 데이터 모델
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ServerInfo(BaseModel):
    """Server 정보"""
    name: str = Field(..., description="Server 이름")
    status: str = Field(..., description="Server 상태 (running, stopped, error)")
    pid: Optional[int] = Field(None, description="프로세스 ID")
    uptime: Optional[float] = Field(None, description="가동 시간 (초)")
    restart_count: int = Field(0, description="재시작 횟수")
    last_error: Optional[str] = Field(None, description="마지막 에러 메시지")
    enabled: bool = Field(True, description="활성화 여부")
    auto_start: bool = Field(True, description="자동 시작 여부")


class ServerListResponse(BaseModel):
    """Server 목록 응답"""
    servers: List[ServerInfo] = Field(..., description="Server 목록")
    total: int = Field(..., description="전체 Server 수")
    running: int = Field(..., description="실행 중인 Server 수")


class ServerActionRequest(BaseModel):
    """Server 액션 요청"""
    server_name: str = Field(..., description="Server 이름")
    action: str = Field(..., description="액션 (start, stop, restart)")


class ServerActionResponse(BaseModel):
    """Server 액션 응답"""
    server_name: str = Field(..., description="Server 이름")
    action: str = Field(..., description="실행된 액션")
    status: str = Field(..., description="결과 상태 (success, error)")
    message: Optional[str] = Field(None, description="메시지")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="실행 시각")

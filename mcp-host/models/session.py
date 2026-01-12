"""
Session 모델

세션 생성, 응답, 정보 관련 데이터 모델
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """세션 생성 요청"""
    username: str = Field(..., description="사용자 ID", min_length=1)
    password: str = Field(..., description="비밀번호", min_length=1)


class SessionResponse(BaseModel):
    """세션 생성 응답"""
    session_id: str = Field(..., description="세션 ID")
    user_id: str = Field(..., description="사용자 ID")
    user_role: str = Field(..., description="사용자 역할")
    user_team: Optional[str] = Field(None, description="사용자 팀")
    expires_at: datetime = Field(..., description="세션 만료 시각")


class SessionInfo(BaseModel):
    """세션 정보 조회 응답"""
    session_id: str = Field(..., description="세션 ID")
    user_id: str = Field(..., description="사용자 ID")
    user_role: str = Field(..., description="사용자 역할")
    user_team: Optional[str] = Field(None, description="사용자 팀")
    created_at: datetime = Field(..., description="세션 생성 시각")
    expires_at: datetime = Field(..., description="세션 만료 시각")
    last_activity: datetime = Field(..., description="마지막 활동 시각")


@dataclass
class Session:
    """
    세션 데이터 (내부용)
    
    메모리에 저장되는 세션 정보
    """
    session_id: str
    user_id: str
    user_role: str
    user_team: Optional[str]
    created_at: datetime
    expires_at: datetime
    last_activity: datetime

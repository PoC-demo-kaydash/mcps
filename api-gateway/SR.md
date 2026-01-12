# API Gateway 설계서

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/api-gateway/`  
**목적**: FastAPI 기반 API Gateway 전체 설계

***

## 목차

1. [개요](#1-개요)
2. [아키텍처](#2-아키텍처)
3. [디렉토리 구조](#3-디렉토리-구조)
4. [핵심 컴포넌트](#4-핵심-컴포넌트)
5. [라우팅](#5-라우팅)
6. [인증 및 인가](#6-인증-및-인가)
7. [미들웨어](#7-미들웨어)
8. [에러 핸들링](#8-에러-핸들링)
9. [API 문서화](#9-api-문서화)
10. [설정 및 배포](#10-설정-및-배포)

***

## 1. 개요

### 1.1 API Gateway 역할

```
┌─────────────────────────────────────────┐
│         API Gateway 역할                 │
├─────────────────────────────────────────┤
│                                          │
│  [Client]                                │
│     │                                    │
│     ▼                                    │
│  [API Gateway]                           │
│     ├─ 인증/인가                         │
│     ├─ Rate Limiting                     │
│     ├─ CORS 처리                         │
│     ├─ 로깅/모니터링                     │
│     ├─ 에러 핸들링                       │
│     └─ 라우팅                            │
│         │                                │
│         ├─────┬─────┬─────┐            │
│         ▼     ▼     ▼     ▼            │
│     [Host] [DB] [ES] [Cache]            │
│                                          │
└─────────────────────────────────────────┘
```

### 1.2 주요 기능

| 기능 | 설명 | 구현 방식 |
|------|------|----------|
| **라우팅** | 요청을 적절한 서비스로 전달 | FastAPI Router |
| **인증** | 사용자 인증 처리 | JWT Token |
| **인가** | 권한 확인 | Role-based Access Control |
| **Rate Limiting** | 요청 빈도 제한 | Redis + slowapi |
| **CORS** | Cross-Origin 요청 처리 | FastAPI Middleware |
| **로깅** | 요청/응답 로깅 | Custom Middleware |
| **캐싱** | 응답 캐싱 | Redis |
| **모니터링** | 메트릭 수집 | Prometheus |

### 1.3 기술 스택

```yaml
Framework: FastAPI 0.104+
Python: 3.11+
Server: Uvicorn
Authentication: JWT (PyJWT)
Rate Limiting: slowapi
Caching: Redis
Validation: Pydantic
Documentation: OpenAPI (Swagger)
```

***

## 2. 아키텍처

### 2.1 레이어 구조

```
┌─────────────────────────────────────────┐
│           API Gateway Layers             │
├─────────────────────────────────────────┤
│                                          │
│  [Presentation Layer]                    │
│    └─ FastAPI Routers                   │
│        ├─ /api/v1/sessions              │
│        ├─ /api/v1/tools                 │
│        ├─ /api/v1/documents             │
│        └─ /api/v1/admin                 │
│                                          │
│  [Middleware Layer]                      │
│    ├─ CORS Middleware                   │
│    ├─ Rate Limit Middleware             │
│    ├─ Auth Middleware                   │
│    ├─ Logging Middleware                │
│    └─ Error Handler Middleware          │
│                                          │
│  [Business Layer]                        │
│    ├─ Session Service                   │
│    ├─ Tool Service                      │
│    ├─ Auth Service                      │
│    └─ Cache Service                     │
│                                          │
│  [Integration Layer]                     │
│    ├─ MCP Host Client                   │
│    ├─ Database Client                   │
│    ├─ Redis Client                      │
│    └─ Elasticsearch Client              │
│                                          │
└─────────────────────────────────────────┘
```

### 2.2 요청 흐름

```
Client Request
    │
    ▼
[CORS Middleware] ──────────────┐
    │                            │
    ▼                            │
[Rate Limit Middleware] ────────┤
    │                            │
    ▼                            │
[Auth Middleware] ──────────────┤
    │                            │
    ▼                            │
[Logging Middleware] ───────────┤
    │                            │
    ▼                            │
[Router]                         │
    │                            │
    ▼                            │
[Service Layer]                  │
    │                            │
    ▼                            │
[MCP Host / Database]            │
    │                            │
    ▼                            │
Response ◄───────────────────────┘
```

***

## 3. 디렉토리 구조

```
api-gateway/
├── main.py                      # FastAPI 애플리케이션 엔트리포인트
├── config.py                    # 설정 관리
├── requirements.txt             # 의존성
│
├── app/
│   ├── __init__.py
│   │
│   ├── core/                    # 핵심 컴포넌트
│   │   ├── __init__.py
│   │   ├── config.py           # 설정 클래스
│   │   ├── security.py         # 보안 (JWT, 암호화)
│   │   ├── dependencies.py     # FastAPI 의존성
│   │   └── exceptions.py       # 커스텀 예외
│   │
│   ├── middleware/              # 미들웨어
│   │   ├── __init__.py
│   │   ├── cors.py             # CORS 처리
│   │   ├── rate_limit.py       # Rate Limiting
│   │   ├── auth.py             # 인증 미들웨어
│   │   ├── logging.py          # 로깅 미들웨어
│   │   └── error_handler.py    # 에러 핸들러
│   │
│   ├── api/                     # API 라우터
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py     # 세션 관리
│   │   │   ├── tools.py        # Tool 실행
│   │   │   ├── documents.py    # 문서 관리
│   │   │   ├── users.py        # 사용자 관리
│   │   │   └── admin.py        # 관리자 기능
│   │   └── health.py           # 헬스체크
│   │
│   ├── services/                # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── session_service.py  # 세션 서비스
│   │   ├── tool_service.py     # Tool 서비스
│   │   ├── auth_service.py     # 인증 서비스
│   │   ├── cache_service.py    # 캐시 서비스
│   │   └── mcp_client.py       # MCP Host 클라이언트
│   │
│   ├── models/                  # Pydantic 모델
│   │   ├── __init__.py
│   │   ├── request.py          # 요청 모델
│   │   ├── response.py         # 응답 모델
│   │   └── schemas.py          # 공통 스키마
│   │
│   └── utils/                   # 유틸리티
│       ├── __init__.py
│       ├── logger.py           # 로거 설정
│       └── metrics.py          # 메트릭 수집
│
├── tests/                       # 테스트
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api.py
│   └── test_middleware.py
│
└── docs/                        # 문서
    └── api_spec.yaml           # OpenAPI Spec
```

***

## 4. 핵심 컴포넌트

### 4.1 main.py (애플리케이션 엔트리포인트)

```python
# api-gateway/main.py
"""
API Gateway - FastAPI 애플리케이션

MCP Host와 클라이언트 사이의 게이트웨이 역할
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.api import health
from app.api.v1 import sessions, tools, documents, users, admin
from app.utils.logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기"""
    # 시작
    logger.info("API Gateway 시작")
    logger.info(f"환경: {settings.ENVIRONMENT}")
    logger.info(f"디버그: {settings.DEBUG}")
    
    yield
    
    # 종료
    logger.info("API Gateway 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="MCP API Gateway",
    description="Model Context Protocol API Gateway",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None
)


# ============================================
# 미들웨어 등록 (순서 중요!)
# ============================================

# 1. CORS (가장 먼저)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Error Handler
app.add_middleware(ErrorHandlerMiddleware)

# 3. Logging
app.add_middleware(LoggingMiddleware)

# 4. Auth
app.add_middleware(AuthMiddleware)

# 5. Rate Limit (마지막)
app.add_middleware(RateLimitMiddleware)


# ============================================
# 라우터 등록
# ============================================

# Health check
app.include_router(
    health.router,
    tags=["Health"]
)

# API v1
app.include_router(
    sessions.router,
    prefix="/api/v1",
    tags=["Sessions"]
)

app.include_router(
    tools.router,
    prefix="/api/v1",
    tags=["Tools"]
)

app.include_router(
    documents.router,
    prefix="/api/v1",
    tags=["Documents"]
)

app.include_router(
    users.router,
    prefix="/api/v1",
    tags=["Users"]
)

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["Admin"]
)


# ============================================
# Root 엔드포인트
# ============================================

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "MCP API Gateway",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


# ============================================
# 실행
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
```

### 4.2 config.py (설정 관리)

```python
# api-gateway/app/core/config.py
"""
설정 관리

환경 변수 기반 설정
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 환경
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # 서버
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    LOG_LEVEL: str = "INFO"
    
    # MCP Host
    MCP_HOST_URL: str = "http://localhost:8000"
    MCP_HOST_TIMEOUT: int = 30
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "mcps_db"
    DB_USER: str = "mcps_user"
    DB_PASSWORD: str = "password"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24시간
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # 요청 수
    RATE_LIMIT_PERIOD: int = 60     # 기간 (초)
    
    # 캐싱
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 300  # 5분
    
    # 모니터링
    METRICS_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 설정 인스턴스 생성
settings = Settings()
```

### 4.3 security.py (보안)

```python
# api-gateway/app/core/security.py
"""
보안 관련 기능

JWT 토큰 생성/검증, 비밀번호 해싱 등
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError


# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Dict:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("토큰이 만료되었습니다")
    
    except jwt.InvalidTokenError:
        raise AuthenticationError("유효하지 않은 토큰입니다")


def create_session_token(user_id: str, session_id: str) -> str:
    """세션 토큰 생성"""
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "type": "session"
    }
    
    return create_access_token(data)


def verify_session_token(token: str) -> Dict:
    """세션 토큰 검증"""
    payload = verify_token(token)
    
    if payload.get("type") != "session":
        raise AuthenticationError("세션 토큰이 아닙니다")
    
    return payload
```

### 4.4 exceptions.py (커스텀 예외)

```python
# api-gateway/app/core/exceptions.py
"""
커스텀 예외 정의
"""

from typing import Optional, Dict, Any


class APIGatewayException(Exception):
    """API Gateway 기본 예외"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(APIGatewayException):
    """인증 오류"""
    
    def __init__(self, message: str = "인증에 실패했습니다", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_FAILED",
            details=details
        )


class AuthorizationError(APIGatewayException):
    """인가 오류"""
    
    def __init__(self, message: str = "권한이 없습니다", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_FAILED",
            details=details
        )


class RateLimitExceeded(APIGatewayException):
    """Rate Limit 초과"""
    
    def __init__(self, message: str = "요청 한도를 초과했습니다", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )


class ValidationError(APIGatewayException):
    """유효성 검증 오류"""
    
    def __init__(self, message: str = "유효하지 않은 요청입니다", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )


class ServiceUnavailable(APIGatewayException):
    """서비스 불가"""
    
    def __init__(self, message: str = "서비스를 사용할 수 없습니다", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details=details
        )
```

### 4.5 dependencies.py (FastAPI 의존성)

```python
# api-gateway/app/core/dependencies.py
"""
FastAPI 의존성

공통으로 사용되는 의존성 정의
"""

from fastapi import Request, Depends, Header
from typing import Optional

from app.core.security import verify_session_token
from app.core.exceptions import AuthenticationError
from app.services.session_service import SessionService
from app.services.cache_service import CacheService


async def get_session_service() -> SessionService:
    """세션 서비스 의존성"""
    return SessionService()


async def get_cache_service() -> CacheService:
    """캐시 서비스 의존성"""
    return CacheService()


async def get_current_user(
    authorization: Optional[str] = Header(None),
    session_service: SessionService = Depends(get_session_service)
) -> dict:
    """현재 사용자 정보 조회"""
    
    if not authorization:
        raise AuthenticationError("인증 토큰이 필요합니다")
    
    # Bearer 토큰 추출
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("유효하지 않은 토큰 형식입니다")
    
    token = authorization[7:]  # "Bearer " 제거
    
    # 토큰 검증
    try:
        payload = verify_session_token(token)
        user_id = payload.get("user_id")
        session_id = payload.get("session_id")
        
        if not user_id or not session_id:
            raise AuthenticationError("유효하지 않은 토큰입니다")
        
        # 세션 확인
        session = await session_service.get_session(session_id)
        
        if not session:
            raise AuthenticationError("세션이 존재하지 않습니다")
        
        if session["user_id"] != user_id:
            raise AuthenticationError("세션 정보가 일치하지 않습니다")
        
        # 사용자 정보 반환
        return {
            "user_id": user_id,
            "session_id": session_id,
            "user": session.get("user", {})
        }
    
    except Exception as e:
        raise AuthenticationError(f"인증 실패: {str(e)}")


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    session_service: SessionService = Depends(get_session_service)
) -> Optional[dict]:
    """현재 사용자 정보 조회 (선택)"""
    
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization, session_service)
    except:
        return None


def require_role(required_role: str):
    """역할 확인 의존성"""
    
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user["user"].get("role")
        
        role_hierarchy = {
            "junior": 0,
            "staff": 1,
            "manager": 2,
            "admin": 3
        }
        
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 99):
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError(f"{required_role} 이상의 권한이 필요합니다")
        
        return current_user
    
    return role_checker
```

***

## 5. 라우팅

### 5.1 health.py (헬스체크)

```python
# api-gateway/app/api/health.py
"""
헬스체크 API
"""

from fastapi import APIRouter, Response, status
import httpx
from datetime import datetime

from app.core.config import settings
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/health")
async def health_check():
    """헬스체크"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "api-gateway",
        "version": "1.0.0",
        "dependencies": {}
    }
    
    # MCP Host 확인
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.MCP_HOST_URL}/health",
                timeout=5.0
            )
            
            if response.status_code == 200:
                health_status["dependencies"]["mcp_host"] = "healthy"
            else:
                health_status["dependencies"]["mcp_host"] = "unhealthy"
                health_status["status"] = "degraded"
    
    except Exception as e:
        logger.error(f"MCP Host 헬스체크 실패: {e}")
        health_status["dependencies"]["mcp_host"] = "unavailable"
        health_status["status"] = "degraded"
    
    # Redis 확인 (선택)
    try:
        from app.services.cache_service import CacheService
        cache = CacheService()
        await cache.ping()
        health_status["dependencies"]["redis"] = "healthy"
    except:
        health_status["dependencies"]["redis"] = "unavailable"
        health_status["status"] = "degraded"
    
    # 상태 코드 결정
    status_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(
        content=str(health_status),
        status_code=status_code,
        media_type="application/json"
    )


@router.get("/ping")
async def ping():
    """간단한 핑"""
    return {"status": "pong"}
```

### 5.2 sessions.py (세션 관리)

```python
# api-gateway/app/api/v1/sessions.py
"""
세션 관리 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from app.core.dependencies import get_current_user, get_session_service
from app.services.session_service import SessionService
from app.models.request import CreateSessionRequest
from app.models.response import SessionResponse
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="세션 생성",
    description="새로운 사용자 세션을 생성합니다"
)
async def create_session(
    request: CreateSessionRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """세션 생성"""
    
    try:
        result = await session_service.create_session(request.user_id)
        
        return SessionResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"세션 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 생성 실패: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="세션 조회",
    description="세션 정보를 조회합니다"
)
async def get_session(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """세션 조회"""
    
    # 권한 확인 (자신의 세션만 조회 가능)
    if current_user["session_id"] != session_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 세션을 조회할 수 없습니다"
        )
    
    try:
        session = await session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다"
            )
        
        return SessionResponse(
            status="success",
            data=session
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"세션 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 조회 실패: {str(e)}"
        )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="세션 삭제",
    description="세션을 삭제합니다"
)
async def delete_session(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """세션 삭제"""
    
    # 권한 확인
    if current_user["session_id"] != session_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 세션을 삭제할 수 없습니다"
        )
    
    try:
        await session_service.delete_session(session_id)
        
        return {
            "status": "success",
            "message": "세션이 삭제되었습니다"
        }
    
    except Exception as e:
        logger.error(f"세션 삭제 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 삭제 실패: {str(e)}"
        )
```

### 5.3 tools.py (Tool 실행)

```python
# api-gateway/app/api/v1/tools.py
"""
Tool 실행 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List

from app.core.dependencies import get_current_user
from app.services.tool_service import ToolService
from app.models.request import ExecuteToolRequest
from app.models.response import ToolResponse, ToolListResponse
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get(
    "/tools/list",
    response_model=ToolListResponse,
    summary="Tool 목록 조회",
    description="사용 가능한 Tool 목록을 조회합니다"
)
async def list_tools(
    category: str = None,
    current_user: Dict = Depends(get_current_user)
):
    """Tool 목록 조회"""
    
    try:
        tool_service = ToolService()
        tools = await tool_service.list_tools(
            user_context=current_user["user"],
            category=category
        )
        
        return ToolListResponse(
            status="success",
            data={
                "tools": tools,
                "total": len(tools)
            }
        )
    
    except Exception as e:
        logger.error(f"Tool 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool 목록 조회 실패: {str(e)}"
        )


@router.post(
    "/tools/execute",
    response_model=ToolResponse,
    summary="Tool 실행",
    description="지정된 Tool을 실행합니다"
)
async def execute_tool(
    request: ExecuteToolRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Tool 실행"""
    
    try:
        tool_service = ToolService()
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name=request.tool,
            arguments=request.arguments,
            user_context=current_user["user"]
        )
        
        return ToolResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"Tool 실행 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool 실행 실패: {str(e)}"
        )


@router.get(
    "/tools/{tool_name}",
    response_model=ToolResponse,
    summary="Tool 정보 조회",
    description="특정 Tool의 상세 정보를 조회합니다"
)
async def get_tool_info(
    tool_name: str,
    current_user: Dict = Depends(get_current_user)
):
    """Tool 정보 조회"""
    
    try:
        tool_service = ToolService()
        tool_info = await tool_service.get_tool_info(
            tool_name=tool_name,
            user_context=current_user["user"]
        )
        
        if not tool_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool을 찾을 수 없습니다: {tool_name}"
            )
        
        return ToolResponse(
            status="success",
            data=tool_info
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Tool 정보 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool 정보 조회 실패: {str(e)}"
        )
```


### 5.4 documents.py (문서 관리)

```python
# api-gateway/app/api/v1/documents.py
"""
문서 관리 API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Optional, List

from app.core.dependencies import get_current_user
from app.services.tool_service import ToolService
from app.models.request import CreateDocumentRequest, UpdateDocumentRequest
from app.models.response import DocumentResponse, DocumentListResponse
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="문서 목록 조회",
    description="문서 목록을 조회합니다"
)
async def list_documents(
    classification: Optional[str] = Query(None, description="공개 범위"),
    category: Optional[str] = Query(None, description="카테고리"),
    limit: int = Query(20, ge=1, le=100, description="페이지 크기"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: Dict = Depends(get_current_user)
):
    """문서 목록 조회"""
    
    try:
        tool_service = ToolService()
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="list_documents",
            arguments={
                "classification": [classification] if classification else None,
                "category": category,
                "limit": limit,
                "offset": offset
            },
            user_context=current_user["user"]
        )
        
        return DocumentListResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"문서 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 목록 조회 실패: {str(e)}"
        )


@router.get(
    "/documents/{doc_id}",
    response_model=DocumentResponse,
    summary="문서 조회",
    description="문서 상세 정보를 조회합니다"
)
async def get_document(
    doc_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """문서 조회"""
    
    try:
        tool_service = ToolService()
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="get_document",
            arguments={"doc_id": doc_id},
            user_context=current_user["user"]
        )
        
        return DocumentResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"문서 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 조회 실패: {str(e)}"
        )


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="문서 생성",
    description="새 문서를 생성합니다"
)
async def create_document(
    request: CreateDocumentRequest,
    current_user: Dict = Depends(get_current_user)
):
    """문서 생성"""
    
    try:
        tool_service = ToolService()
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="create_document",
            arguments=request.dict(exclude_none=True),
            user_context=current_user["user"]
        )
        
        return DocumentResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"문서 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 생성 실패: {str(e)}"
        )


@router.put(
    "/documents/{doc_id}",
    response_model=DocumentResponse,
    summary="문서 수정",
    description="문서를 수정합니다"
)
async def update_document(
    doc_id: str,
    request: UpdateDocumentRequest,
    current_user: Dict = Depends(get_current_user)
):
    """문서 수정"""
    
    try:
        tool_service = ToolService()
        
        arguments = {"doc_id": doc_id}
        arguments.update(request.dict(exclude_none=True))
        
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="update_document",
            arguments=arguments,
            user_context=current_user["user"]
        )
        
        return DocumentResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"문서 수정 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 수정 실패: {str(e)}"
        )


@router.delete(
    "/documents/{doc_id}",
    status_code=status.HTTP_200_OK,
    summary="문서 삭제",
    description="문서를 삭제합니다"
)
async def delete_document(
    doc_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """문서 삭제"""
    
    try:
        tool_service = ToolService()
        await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="delete_document",
            arguments={"doc_id": doc_id},
            user_context=current_user["user"]
        )
        
        return {
            "status": "success",
            "message": "문서가 삭제되었습니다"
        }
    
    except Exception as e:
        logger.error(f"문서 삭제 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 삭제 실패: {str(e)}"
        )


@router.get(
    "/documents/{doc_id}/versions",
    response_model=DocumentResponse,
    summary="문서 버전 목록",
    description="문서의 버전 히스토리를 조회합니다"
)
async def get_document_versions(
    doc_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """문서 버전 목록"""
    
    try:
        tool_service = ToolService()
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="get_document_versions",
            arguments={"doc_id": doc_id},
            user_context=current_user["user"]
        )
        
        return DocumentResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"문서 버전 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 버전 조회 실패: {str(e)}"
        )
```

### 5.5 users.py (사용자 관리)

```python
# api-gateway/app/api/v1/users.py
"""
사용자 관리 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from app.core.dependencies import get_current_user, require_role
from app.services.tool_service import ToolService
from app.models.response import UserResponse
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get(
    "/users/me",
    response_model=UserResponse,
    summary="내 정보 조회",
    description="현재 로그인한 사용자의 정보를 조회합니다"
)
async def get_my_info(
    current_user: Dict = Depends(get_current_user)
):
    """내 정보 조회"""
    
    return UserResponse(
        status="success",
        data=current_user["user"]
    )


@router.get(
    "/users/me/permissions",
    response_model=UserResponse,
    summary="내 권한 조회",
    description="현재 사용자의 권한 정보를 조회합니다"
)
async def get_my_permissions(
    current_user: Dict = Depends(get_current_user)
):
    """내 권한 조회"""
    
    try:
        tool_service = ToolService()
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="get_my_permissions",
            arguments={},
            user_context=current_user["user"]
        )
        
        return UserResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"권한 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"권한 조회 실패: {str(e)}"
        )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="사용자 정보 조회",
    description="특정 사용자의 정보를 조회합니다"
)
async def get_user_info(
    user_id: str,
    current_user: Dict = Depends(require_role("manager"))
):
    """사용자 정보 조회 (Manager 이상)"""
    
    try:
        tool_service = ToolService()
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="get_user",
            arguments={"user_id": user_id},
            user_context=current_user["user"]
        )
        
        return UserResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"사용자 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 조회 실패: {str(e)}"
        )
```

### 5.6 admin.py (관리자 기능)

```python
# api-gateway/app/api/v1/admin.py
"""
관리자 API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Optional

from app.core.dependencies import get_current_user, require_role
from app.services.tool_service import ToolService
from app.models.response import AdminResponse
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get(
    "/stats",
    response_model=AdminResponse,
    summary="시스템 통계",
    description="시스템 전체 통계를 조회합니다"
)
async def get_system_stats(
    current_user: Dict = Depends(require_role("admin"))
):
    """시스템 통계 (Admin 전용)"""
    
    try:
        tool_service = ToolService()
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="get_system_stats",
            arguments={},
            user_context=current_user["user"]
        )
        
        return AdminResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"시스템 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 통계 조회 실패: {str(e)}"
        )


@router.get(
    "/audit-logs",
    response_model=AdminResponse,
    summary="감사 로그 조회",
    description="시스템 감사 로그를 조회합니다"
)
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="사용자 ID"),
    action: Optional[str] = Query(None, description="액션"),
    limit: int = Query(50, ge=1, le=1000, description="페이지 크기"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: Dict = Depends(require_role("admin"))
):
    """감사 로그 조회 (Admin 전용)"""
    
    try:
        tool_service = ToolService()
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="get_audit_logs",
            arguments={
                "user_id": user_id,
                "action": action,
                "limit": limit,
                "offset": offset
            },
            user_context=current_user["user"]
        )
        
        return AdminResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"감사 로그 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"감사 로그 조회 실패: {str(e)}"
        )


@router.post(
    "/permissions/grant",
    response_model=AdminResponse,
    summary="권한 부여",
    description="사용자에게 특정 문서에 대한 권한을 부여합니다"
)
async def grant_permission(
    user_id: str,
    doc_id: str,
    permission_type: str,
    current_user: Dict = Depends(require_role("manager"))
):
    """권한 부여 (Manager 이상)"""
    
    try:
        tool_service = ToolService()
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="grant_permission",
            arguments={
                "user_id": user_id,
                "doc_id": doc_id,
                "permission_type": permission_type
            },
            user_context=current_user["user"]
        )
        
        return AdminResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"권한 부여 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"권한 부여 실패: {str(e)}"
        )


@router.delete(
    "/permissions/revoke",
    response_model=AdminResponse,
    summary="권한 회수",
    description="사용자의 특정 문서에 대한 권한을 회수합니다"
)
async def revoke_permission(
    user_id: str,
    doc_id: str,
    permission_type: str,
    current_user: Dict = Depends(require_role("manager"))
):
    """권한 회수 (Manager 이상)"""
    
    try:
        tool_service = ToolService()
        result = await tool_service.execute_tool(
            session_id=current_user["session_id"],
            tool_name="revoke_permission",
            arguments={
                "user_id": user_id,
                "doc_id": doc_id,
                "permission_type": permission_type
            },
            user_context=current_user["user"]
        )
        
        return AdminResponse(
            status="success",
            data=result
        )
    
    except Exception as e:
        logger.error(f"권한 회수 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"권한 회수 실패: {str(e)}"
        )
```

***

## 6. 인증 및 인가

### 6.1 인증 서비스

```python
# api-gateway/app/services/auth_service.py
"""
인증 서비스

사용자 인증 및 토큰 관리
"""

import httpx
from typing import Dict, Optional

from app.core.config import settings
from app.core.security import create_session_token
from app.core.exceptions import AuthenticationError
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AuthService:
    """인증 서비스"""
    
    def __init__(self):
        self.mcp_host_url = settings.MCP_HOST_URL
        self.timeout = settings.MCP_HOST_TIMEOUT
    
    async def authenticate_user(self, user_id: str) -> Dict:
        """사용자 인증"""
        
        try:
            # MCP Host의 인증 Tool 호출
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mcp_host_url}/api/tools/execute",
                    json={
                        "tool": "authenticate",
                        "arguments": {"user_id": user_id}
                    },
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    raise AuthenticationError("인증 실패")
                
                result = response.json()
                
                if result.get("status") != "success":
                    raise AuthenticationError(
                        result.get("error", {}).get("message", "인증 실패")
                    )
                
                return result.get("data", {})
        
        except httpx.HTTPError as e:
            logger.error(f"인증 요청 실패: {e}")
            raise AuthenticationError(f"인증 서비스 오류: {str(e)}")
    
    async def create_token(self, user_id: str, session_id: str) -> str:
        """토큰 생성"""
        
        return create_session_token(user_id, session_id)
    
    async def validate_token(self, token: str) -> Dict:
        """토큰 검증"""
        
        from app.core.security import verify_session_token
        
        try:
            payload = verify_session_token(token)
            return payload
        
        except Exception as e:
            logger.error(f"토큰 검증 실패: {e}")
            raise AuthenticationError(f"유효하지 않은 토큰: {str(e)}")
```

### 6.2 세션 서비스

```python
# api-gateway/app/services/session_service.py
"""
세션 서비스

세션 생성, 조회, 삭제 관리
"""

import httpx
from typing import Dict, Optional
import uuid

from app.core.config import settings
from app.services.auth_service import AuthService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SessionService:
    """세션 서비스"""
    
    def __init__(self):
        self.mcp_host_url = settings.MCP_HOST_URL
        self.timeout = settings.MCP_HOST_TIMEOUT
        self.auth_service = AuthService()
    
    async def create_session(self, user_id: str) -> Dict:
        """세션 생성"""
        
        # 1. 사용자 인증
        user_info = await self.auth_service.authenticate_user(user_id)
        
        # 2. 세션 ID 생성
        session_id = f"SESSION_{uuid.uuid4().hex}"
        
        # 3. MCP Host에 세션 생성 요청
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mcp_host_url}/api/sessions",
                json={"user_id": user_id},
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                raise Exception(f"세션 생성 실패: {response.status_code}")
            
            result = response.json()
            mcp_session_id = result.get("session_id")
        
        # 4. JWT 토큰 생성
        token = await self.auth_service.create_token(user_id, mcp_session_id)
        
        return {
            "session_id": mcp_session_id,
            "user_id": user_id,
            "user": user_info.get("user", {}),
            "token": token,
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60  # 초 단위
        }
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """세션 조회"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.mcp_host_url}/api/sessions/{session_id}",
                    timeout=self.timeout
                )
                
                if response.status_code == 404:
                    return None
                
                if response.status_code != 200:
                    raise Exception(f"세션 조회 실패: {response.status_code}")
                
                result = response.json()
                return result
        
        except httpx.HTTPError as e:
            logger.error(f"세션 조회 실패: {e}")
            return None
    
    async def delete_session(self, session_id: str):
        """세션 삭제"""
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.mcp_host_url}/api/sessions/{session_id}",
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 204]:
                raise Exception(f"세션 삭제 실패: {response.status_code}")
```

***

## 7. 미들웨어

### 7.1 CORS 미들웨어

```python
# api-gateway/app/middleware/cors.py
"""
CORS 미들웨어

FastAPI의 기본 CORSMiddleware 사용
main.py에서 설정
"""

# main.py에서 이미 설정됨
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
```

### 7.2 Rate Limit 미들웨어

```python
# api-gateway/app/middleware/rate_limit.py
"""
Rate Limit 미들웨어

요청 빈도 제한
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time
from typing import Dict
import redis

from app.core.config import settings
from app.core.exceptions import RateLimitExceeded
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate Limit 미들웨어"""
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.requests = settings.RATE_LIMIT_REQUESTS
        self.period = settings.RATE_LIMIT_PERIOD
        
        # Redis 연결
        if self.enabled:
            try:
                self.redis = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                    decode_responses=True
                )
            except Exception as e:
                logger.warning(f"Redis 연결 실패, Rate Limit 비활성화: {e}")
                self.enabled = False
    
    async def dispatch(self, request: Request, call_next):
        """요청 처리"""
        
        # Rate Limit 비활성화
        if not self.enabled:
            return await call_next(request)
        
        # 헬스체크 제외
        if request.url.path in ["/health", "/ping"]:
            return await call_next(request)
        
        # 클라이언트 식별 (IP 주소)
        client_ip = request.client.host
        
        # Rate Limit 확인
        try:
            if not self._check_rate_limit(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={
                        "status": "error",
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"요청 한도를 초과했습니다. {self.period}초당 {self.requests}회로 제한됩니다."
                        }
                    }
                )
        
        except Exception as e:
            logger.error(f"Rate Limit 확인 실패: {e}")
        
        # 요청 처리
        response = await call_next(request)
        
        return response
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Rate Limit 확인"""
        
        key = f"rate_limit:{client_ip}"
        
        try:
            # 현재 요청 수
            current = self.redis.get(key)
            
            if current is None:
                # 첫 요청
                self.redis.setex(key, self.period, 1)
                return True
            
            current = int(current)
            
            if current >= self.requests:
                # 한도 초과
                return False
            
            # 카운트 증가
            self.redis.incr(key)
            return True
        
        except Exception as e:
            logger.error(f"Rate Limit 체크 실패: {e}")
            return True  # 에러 시 허용
```

### 7.3 Auth 미들웨어

```python
# api-gateway/app/middleware/auth.py
"""
Auth 미들웨어

인증이 필요한 엔드포인트에 대한 토큰 검증
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Auth 미들웨어"""
    
    # 인증 불필요 경로
    PUBLIC_PATHS = [
        "/",
        "/health",
        "/ping",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/sessions"  # 세션 생성은 인증 불필요
    ]
    
    async def dispatch(self, request: Request, call_next):
        """요청 처리"""
        
        path = request.url.path
        
        # Public 경로는 패스
        if any(path.startswith(p) for p in self.PUBLIC_PATHS):
            return await call_next(request)
        
        # Authorization 헤더 확인
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error": {
                        "code": "AUTHENTICATION_REQUIRED",
                        "message": "인증이 필요합니다"
                    }
                }
            )
        
        # 실제 토큰 검증은 dependencies.py의 get_current_user에서 수행
        # 여기서는 Authorization 헤더 존재만 확인
        
        response = await call_next(request)
        return response
```

### 7.4 Logging 미들웨어

```python
# api-gateway/app/middleware/logging.py
"""
Logging 미들웨어

요청/응답 로깅
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import json

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        """요청 처리"""
        
        # 시작 시간
        start_time = time.time()
        
        # 요청 정보
        request_info = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query) if request.url.query else None,
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }
        
        logger.info(f"Request: {json.dumps(request_info)}")
        
        # 요청 처리
        response = await call_next(request)
        
        # 처리 시간
        process_time = time.time() - start_time
        
        # 응답 정보
        response_info = {
            "status_code": response.status_code,
            "process_time": f"{process_time:.3f}s"
        }
        
        logger.info(f"Response: {json.dumps(response_info)}")
        
        # 처리 시간을 헤더에 추가
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
```

### 7.5 Error Handler 미들웨어

```python
# api-gateway/app/middleware/error_handler.py
"""
Error Handler 미들웨어

전역 에러 핸들링
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import traceback

from app.core.exceptions import APIGatewayException
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Error Handler 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        """요청 처리"""
        
        try:
            response = await call_next(request)
            return response
        
        except APIGatewayException as e:
            # 커스텀 예외
            logger.error(f"API Gateway Exception: {e.message}")
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "status": "error",
                    "error": {
                        "code": e.error_code,
                        "message": e.message,
                        "details": e.details
                    }
                }
            )
        
        except Exception as e:
            # 예상치 못한 예외
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "내부 서버 오류가 발생했습니다",
                        "details": {}
                    }
                }
            )
```

***

## 8. 에러 핸들링

### 8.1 에러 응답 포맷

```python
# api-gateway/app/models/response.py
"""
응답 모델
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorDetail(BaseModel):
    """에러 상세"""
    code: str
    message: str
    details: Dict[str, Any] = {}


class ErrorResponse(BaseModel):
    """에러 응답"""
    status: str = "error"
    error: ErrorDetail


class SuccessResponse(BaseModel):
    """성공 응답"""
    status: str = "success"
    data: Optional[Dict[str, Any]] = None


class SessionResponse(SuccessResponse):
    """세션 응답"""
    pass


class ToolResponse(SuccessResponse):
    """Tool 응답"""
    pass


class ToolListResponse(SuccessResponse):
    """Tool 목록 응답"""
    pass


class DocumentResponse(SuccessResponse):
    """문서 응답"""
    pass


class DocumentListResponse(SuccessResponse):
    """문서 목록 응답"""
    pass


class UserResponse(SuccessResponse):
    """사용자 응답"""
    pass


class AdminResponse(SuccessResponse):
    """관리자 응답"""
    pass
```

### 8.2 FastAPI 예외 핸들러

```python
# api-gateway/app/core/exception_handlers.py
"""
FastAPI 예외 핸들러
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import APIGatewayException
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def api_gateway_exception_handler(
    request: Request,
    exc: APIGatewayException
):
    """API Gateway 예외 핸들러"""
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    """유효성 검증 예외 핸들러"""
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "요청 데이터가 유효하지 않습니다",
                "details": exc.errors()
            }
        }
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
):
    """HTTP 예외 핸들러"""
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {}
            }
        }
    )


# main.py에 등록
# app.add_exception_handler(APIGatewayException, api_gateway_exception_handler)
# app.add_exception_handler(RequestValidationError, validation_exception_handler)
# app.add_exception_handler(StarletteHTTPException, http_exception_handler)
```

***

## 9. API 문서화

### 9.1 OpenAPI 설정

```python
# main.py에서 이미 설정됨

app = FastAPI(
    title="MCP API Gateway",
    description="Model Context Protocol API Gateway",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None
)
```

### 9.2 API 문서 예시

```yaml
# api-gateway/docs/api_spec.yaml
# OpenAPI 3.0 Specification

openapi: 3.0.0
info:
  title: MCP API Gateway
  description: Model Context Protocol API Gateway
  version: 1.0.0
  contact:
    name: API Support
    email: support@example.com

servers:
  - url: http://localhost:8080
    description: Development server
  - url: https://api.example.com
    description: Production server

tags:
  - name: Health
    description: 헬스체크
  - name: Sessions
    description: 세션 관리
  - name: Tools
    description: Tool 실행
  - name: Documents
    description: 문서 관리
  - name: Users
    description: 사용자 관리
  - name: Admin
    description: 관리자 기능

paths:
  /health:
    get:
      tags:
        - Health
      summary: 헬스체크
      description: API Gateway 상태 확인
      responses:
        '200':
          description: 정상
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: healthy
                  timestamp:
                    type: string
                    format: date-time
                  service:
                    type: string
                    example: api-gateway

  /api/v1/sessions:
    post:
      tags:
        - Sessions
      summary: 세션 생성
      description: 새로운 사용자 세션 생성
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - user_id
              properties:
                user_id:
                  type: string
                  example: U001
      responses:
        '201':
          description: 세션 생성 성공
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SessionResponse'

components:
  schemas:
    SessionResponse:
      type: object
      properties:
        status:
          type: string
          example: success
        data:
          type: object
          properties:
            session_id:
              type: string
            user_id:
              type: string
            token:
              type: string
            expires_in:
              type: integer

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - BearerAuth: []
```

***

## 10. 설정 및 배포

### 10.1 환경 변수 (.env)

```bash
# api-gateway/.env
# 환경 변수 설정

# 환경
ENVIRONMENT=production
DEBUG=false

# 서버
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO

# MCP Host
MCP_HOST_URL=http://localhost:8000
MCP_HOST_TIMEOUT=30

# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mcps_db
DB_USER=mcps_user
DB_PASSWORD=your_db_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password

# JWT
JWT_SECRET_KEY=your-secret-key-change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS=["http://localhost:3000","https://app.example.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# 캐싱
CACHE_ENABLED=true
CACHE_TTL=300

# 모니터링
METRICS_ENABLED=true
```

### 10.2 requirements.txt

```txt
# api-gateway/requirements.txt
# Python 의존성

# FastAPI
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# HTTP Client
httpx==0.25.2

# Authentication
pyjwt==2.8.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Redis
redis==5.0.1

# Database (선택)
pymysql==1.1.0

# Utilities
python-dotenv==1.0.0

# Logging
python-json-logger==2.0.7

# Monitoring (선택)
prometheus-client==0.19.0
```

### 10.3 Dockerfile

```dockerfile
# api-gateway/Dockerfile
# API Gateway Docker 이미지

FROM python:3.11-slim

# 작업 디렉토리
WORKDIR /app

# 시스템 패키지
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# 사용자 생성
RUN useradd -m -u 1000 gateway && \
    chown -R gateway:gateway /app

USER gateway

# 포트 노출
EXPOSE 8080

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 10.4 docker-compose.yml

```yaml
# api-gateway/docker-compose.yml
# Docker Compose 설정

version: '3.8'

services:
  api-gateway:
    build: .
    container_name: mcp-api-gateway
    ports:
      - "8080:8080"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - MCP_HOST_URL=http://mcp-host:8000
      - REDIS_HOST=redis
      - DB_HOST=mariadb
    depends_on:
      - redis
      - mariadb
    restart: unless-stopped
    networks:
      - mcp-network

  redis:
    image: redis:7-alpine
    container_name: mcp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - mcp-network

  mariadb:
    image: mariadb:10.11
    container_name: mcp-mariadb
    environment:
      - MYSQL_ROOT_PASSWORD=root_password
      - MYSQL_DATABASE=mcps_db
      - MYSQL_USER=mcps_user
      - MYSQL_PASSWORD=mcps_password
    ports:
      - "3306:3306"
    volumes:
      - mariadb-data:/var/lib/mysql
    restart: unless-stopped
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge

volumes:
  redis-data:
  mariadb-data:
```

### 10.5 Systemd 서비스

```ini
# /etc/systemd/system/mcp-api-gateway.service
# Systemd 서비스 파일

[Unit]
Description=MCP API Gateway
After=network.target redis.service mariadb.service

[Service]
Type=simple
User=mcps
Group=mcps
WorkingDirectory=/app/poc/mcps/api-gateway
EnvironmentFile=/app/poc/mcps/api-gateway/.env
ExecStart=/app/poc/mcps/api-gateway/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=append:/app/poc/mcps/data/logs/api-gateway/api_gateway.log
StandardError=append:/app/poc/mcps/data/logs/api-gateway/api_gateway_error.log

[Install]
WantedBy=multi-user.target
```

### 10.6 배포 스크립트

```bash
#!/bin/bash
# api-gateway/deploy.sh
# API Gateway 배포 스크립트

set -e

echo "=== API Gateway 배포 ==="

# 1. 의존성 설치
echo "의존성 설치..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 환경 변수 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다"
    exit 1
fi

# 3. 테스트 실행 (선택)
echo "테스트 실행..."
pytest tests/ -v || true

# 4. Systemd 서비스 재시작
echo "서비스 재시작..."
sudo systemctl daemon-reload
sudo systemctl restart mcp-api-gateway

# 5. 상태 확인
sleep 3
sudo systemctl status mcp-api-gateway --no-pager

# 6. 헬스체크
echo "헬스체크..."
curl -f http://localhost:8080/health

echo ""
echo "✅ 배포 완료"
```

***

## 11. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

***

## 12. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| **작성자** | | | |
| **검토자** | | | |
| **승인자** | | | |

***

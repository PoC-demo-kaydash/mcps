"""
미들웨어

로깅, CORS 미들웨어
"""

import time
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from shared.logging_config import get_logger

logger = get_logger(__name__)


def setup_middleware(app: FastAPI):
    """
    미들웨어 설정
    
    Args:
        app: FastAPI 앱
    """
    # CORS 미들웨어
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 개발 환경용, 운영 환경에서는 제한 필요
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 요청 로깅 미들웨어
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """요청/응답 로깅"""
        start_time = time.time()
        
        # 요청 로깅
        logger.info(
            f"→ {request.method} {request.url.path} "
            f"(client: {request.client.host if request.client else 'unknown'})"
        )
        
        # 요청 처리
        try:
            response = await call_next(request)
            
            # 응답 로깅
            duration = time.time() - start_time
            logger.info(
                f"← {request.method} {request.url.path} "
                f"[{response.status_code}] ({duration:.3f}s)"
            )
            
            return response
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"✗ {request.method} {request.url.path} "
                f"ERROR: {e} ({duration:.3f}s)"
            )
            raise
    
    logger.info("✓ Middleware configured")

"""
MCP Host Main Application

FastAPI 기반 MCP Host 서버
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import get_config
from core import ServerManager, SessionManager, Router, ToolExecutor
from api import router, setup_middleware
from api.routes import setup_dependencies
from utils.metrics import metrics
from shared.database import DatabaseManager
from shared.logging_config import setup_logging, get_logger

# 로깅 설정
setup_logging()
logger = get_logger(__name__)

# 전역 변수
server_manager = None
session_manager = None
tool_router = None
executor = None
db_manager = None
config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 수명 주기 관리
    
    시작/종료 이벤트 처리
    """
    global server_manager, session_manager, tool_router, executor, db_manager, config
    
    # ==================== 시작 ====================
    logger.info("=" * 60)
    logger.info("MCP Host Starting...")
    logger.info("=" * 60)
    
    try:
        # 설정 로드
        logger.info("Loading configuration...")
        config = get_config()
        
        # Database 연결
        logger.info("Connecting to database...")
        db_manager = DatabaseManager(
            host=config.database.host,
            port=config.database.port,
            database=config.database.database,
            user=config.database.user,
            password=config.database.password,
            charset=config.database.charset
        )
        await db_manager.initialize()
        
        # 핵심 컴포넌트 초기화
        logger.info("Initializing components...")
        
        # Server 관리자
        server_manager = ServerManager(config)
        
        # 세션 관리자
        session_manager = SessionManager(config, db_manager)
        
        # Tool 라우터
        tool_router = Router(config)
        
        # Tool 실행기
        executor = ToolExecutor(server_manager, tool_router)
        
        # API 의존성 주입
        setup_dependencies(server_manager, session_manager, tool_router, executor, metrics)
        
        # Server 시작
        logger.info("Starting MCP servers...")
        results = server_manager.start_all()
        logger.info(f"✓ Started {len(results['success'])} servers")
        
        if results['failed']:
            logger.warning(f"Failed to start {len(results['failed'])} servers: {results['failed']}")
        
        # 세션 정리 백그라운드 태스크
        async def cleanup_sessions():
            while True:
                await asyncio.sleep(300)  # 5분마다
                session_manager.cleanup_expired_sessions()
        
        # 백그라운드 태스크 시작
        cleanup_task = asyncio.create_task(cleanup_sessions())
        
        logger.info("=" * 60)
        logger.info("✓ MCP Host Started Successfully")
        logger.info(f"✓ Listening on {config.host.host}:{config.host.port}")
        logger.info("=" * 60)
        
        yield
        
        # ==================== 종료 ====================
        logger.info("=" * 60)
        logger.info("MCP Host Shutting Down...")
        logger.info("=" * 60)
        
        # 백그라운드 태스크 취소
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        
        # Server 중지
        logger.info("Stopping MCP servers...")
        server_manager.stop_all()
        
        # Database 연결 종료
        logger.info("Closing database connection...")
        await db_manager.close()
        
        logger.info("=" * 60)
        logger.info("✓ MCP Host Stopped")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Failed to start MCP Host: {e}")
        sys.exit(1)


# FastAPI 앱 생성
app = FastAPI(
    title="MCP Host",
    description="Model Context Protocol Host API",
    version="1.0.0",
    lifespan=lifespan
)

# 미들웨어 설정
setup_middleware(app)

# 라우터 등록
app.include_router(router)


# 루트 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": "MCP Host",
        "version": "1.0.0",
        "status": "running"
    }


# 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 에러 핸들러"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "SERVER_ERROR",
                "message": "Internal server error"
            }
        }
    )


# 시그널 핸들러
def signal_handler(signum, frame):
    """시그널 핸들러 (SIGINT, SIGTERM)"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    import uvicorn
    
    # 설정 로드 (CLI 실행용)
    config = get_config()
    
    # uvicorn 실행
    uvicorn.run(
        "main:app",
        host=config.host.host,
        port=config.host.port,
        log_level=config.host.log_level.lower(),
        reload=config.host.debug
    )

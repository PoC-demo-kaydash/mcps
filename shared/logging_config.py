"""
통합 로깅 설정
==============

모든 컴포넌트에서 사용하는 표준화된 로깅 설정을 제공합니다.

기능:
- 표준 로거 설정
- 파일 로테이션
- JSON/Text 포맷 지원
- 컴포넌트별 로거
- 로그 컨텍스트 (추가 필드)

사용 예:
    from shared.logging_config import setup_logging, get_logger
    
    # 컴포넌트 로거 설정
    logger = setup_logging("mcp-host")
    logger.info("Application started")
    
    # 모듈별 로거
    logger = get_logger(__name__)
    logger.debug("Processing document")
"""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
import time


# ===========================================
# 포맷터 클래스
# ===========================================

class JSONFormatter(logging.Formatter):
    """JSON 포맷 로거"""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그를 JSON으로 포맷팅"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 추가 필드 (LogContext에서 설정)
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        # 예외 정보
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """텍스트 포맷 로거"""
    
    def __init__(self):
        fmt = "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        super().__init__(fmt=fmt, datefmt=datefmt)


class ColoredTextFormatter(logging.Formatter):
    """컬러 텍스트 포맷 로거 (터미널용)"""
    
    # ANSI 색상 코드
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def __init__(self):
        fmt = "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        super().__init__(fmt=fmt, datefmt=datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        # 색상 적용
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# ===========================================
# 로거 설정 함수
# ===========================================

def setup_logging(
    component: str,
    log_dir: Optional[Path] = None,
    level: str = "INFO",
    format_type: str = "text",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 10,
    use_color: bool = True
) -> logging.Logger:
    """
    로거 설정
    
    Args:
        component: 컴포넌트 이름 (mcp-host, api-gateway, frontend 등)
        log_dir: 로그 디렉토리 (None이면 파일 로깅 비활성화)
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 포맷 타입 ("text" | "json")
        max_bytes: 파일 최대 크기
        backup_count: 백업 파일 개수
        use_color: 터미널 컬러 사용 여부
    
    Returns:
        logging.Logger
    
    Example:
        logger = setup_logging(
            "mcp-host",
            log_dir=Path("/app/poc/mcps/data/logs/mcp-host"),
            level="INFO"
        )
        logger.info("Application started")
    """
    logger = logging.getLogger(component)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 기존 핸들러 제거
    logger.handlers.clear()
    
    # 부모 로거 전파 방지
    logger.propagate = False
    
    # 포맷터 선택
    if format_type == "json":
        formatter = JSONFormatter()
        console_formatter = formatter
    else:
        formatter = TextFormatter()
        console_formatter = ColoredTextFormatter() if use_color else formatter
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 일반 로그
        app_log_file = log_dir / f"{component}.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        app_handler.setFormatter(formatter)
        logger.addHandler(app_handler)
        
        # 에러 로그 (ERROR 이상만)
        error_log_file = log_dir / f"{component}_error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    logger.info(
        f"Logger initialized: {component} "
        f"(level={level}, format={format_type})"
    )
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    로거 가져오기
    
    Args:
        name: 로거 이름 (보통 __name__)
    
    Returns:
        logging.Logger
    
    Example:
        logger = get_logger(__name__)
        logger.info("Processing document")
    """
    return logging.getLogger(name)


# ===========================================
# 로그 컨텍스트
# ===========================================

class LogContext:
    """
    로그 컨텍스트 (추가 필드)
    
    컨텍스트 매니저로 사용하여 로그에 추가 정보를 자동으로 포함합니다.
    
    Example:
        with LogContext(user_id="U001", request_id="req_123"):
            logger.info("User logged in")
            logger.info("Document accessed")
            # 모든 로그에 user_id, request_id 자동 포함
    """
    
    def __init__(self, **fields):
        self.fields = fields
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.fields.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


# ===========================================
# 미리 정의된 로거 접근자
# ===========================================

def get_mcp_host_logger() -> logging.Logger:
    """MCP Host 로거"""
    return get_logger("mcp-host")


def get_api_gateway_logger() -> logging.Logger:
    """API Gateway 로거"""
    return get_logger("api-gateway")


def get_frontend_logger() -> logging.Logger:
    """Frontend 로거"""
    return get_logger("frontend")


def get_mcp_server_logger(server_name: str) -> logging.Logger:
    """MCP Server 로거"""
    return get_logger(f"mcp-server.{server_name}")


# ===========================================
# 유틸리티 함수
# ===========================================

def set_log_level(logger_name: str, level: str):
    """
    로그 레벨 동적 변경
    
    Args:
        logger_name: 로거 이름
        level: 새 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.info(f"Log level changed to {level}")


def configure_global_logging(
    level: str = "INFO",
    format_type: str = "text"
):
    """
    전역 로깅 설정
    
    Args:
        level: 기본 로그 레벨
        format_type: 포맷 타입
    """
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 기존 핸들러 제거
    root_logger.handlers.clear()
    
    # 포맷터
    if format_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = ColoredTextFormatter()
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("pymysql").setLevel(logging.WARNING)


# ===========================================
# 데코레이터
# ===========================================

def log_exceptions(logger: Optional[logging.Logger] = None):
    """
    예외 로깅 데코레이터
    
    함수에서 발생하는 예외를 자동으로 로깅합니다.
    
    Example:
        @log_exceptions()
        def risky_function():
            raise ValueError("Something went wrong")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger(func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _logger.exception(
                    f"Exception in {func.__name__}: {e}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def log_execution_time(logger: Optional[logging.Logger] = None, threshold_ms: float = 0):
    """
    실행 시간 로깅 데코레이터
    
    함수 실행 시간을 로깅합니다.
    
    Args:
        logger: 로거 (None이면 모듈 로거 사용)
        threshold_ms: 이 시간(ms) 이상일 때만 로깅 (0이면 항상)
    
    Example:
        @log_execution_time()
        def slow_function():
            time.sleep(2)
        
        @log_execution_time(threshold_ms=1000)  # 1초 이상만 로깅
        def maybe_slow_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger(func.__module__)
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            execution_time = (time.time() - start_time) * 1000
            
            if execution_time >= threshold_ms:
                _logger.info(
                    f"{func.__name__} executed in {execution_time:.2f}ms"
                )
            
            return result
        return wrapper
    return decorator


def log_function_call(logger: Optional[logging.Logger] = None, log_args: bool = False):
    """
    함수 호출 로깅 데코레이터
    
    함수 호출 시작/종료를 로깅합니다.
    
    Args:
        logger: 로거
        log_args: 인자도 로깅할지 여부
    
    Example:
        @log_function_call(log_args=True)
        def process_document(doc_id, user_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger(func.__module__)
            
            if log_args:
                _logger.debug(
                    f"Calling {func.__name__}(args={args}, kwargs={kwargs})"
                )
            else:
                _logger.debug(f"Calling {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                _logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                _logger.debug(f"{func.__name__} failed: {e}")
                raise
        
        return wrapper
    return decorator


# ===========================================
# Public API
# ===========================================

__all__ = [
    # 설정
    "setup_logging",
    "get_logger",
    "configure_global_logging",
    "set_log_level",
    
    # 포맷터
    "JSONFormatter",
    "TextFormatter",
    "ColoredTextFormatter",
    
    # 컨텍스트
    "LogContext",
    
    # 컴포넌트 로거
    "get_mcp_host_logger",
    "get_api_gateway_logger",
    "get_frontend_logger",
    "get_mcp_server_logger",
    
    # 데코레이터
    "log_exceptions",
    "log_execution_time",
    "log_function_call",
]

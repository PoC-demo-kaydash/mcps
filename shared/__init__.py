"""
MCP 에코시스템 공유 모듈
=========================

모든 컴포넌트(MCP Host, MCP Servers, API Gateway, Frontend)가 
공통으로 사용하는 핵심 기능을 제공합니다.

사용 예:
    from shared import initialize, CONFIG
    from shared.database import DatabaseManager
    from shared.elasticsearch import ElasticsearchManager
    from shared.permissions import PermissionEngine
    from shared import queries
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ===========================================
# 환경 변수 로드
# ===========================================

# .env 파일 경로 탐색 (shared 폴더의 상위 디렉토리)
_current_dir = Path(__file__).parent
_env_path = _current_dir.parent / ".env"

if _env_path.exists():
    load_dotenv(_env_path)
else:
    # 환경 변수가 없으면 .env.example 시도
    _env_example_path = _current_dir.parent / ".env.example"
    if _env_example_path.exists():
        load_dotenv(_env_example_path)

# ===========================================
# 전역 설정
# ===========================================

CONFIG = {
    # Application
    "app": {
        "name": os.getenv("APP_NAME", "mcps"),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "env": os.getenv("APP_ENV", "development"),
        "debug": os.getenv("DEBUG", "true").lower() == "true",
        "base_dir": Path(os.getenv("BASE_DIR", "/app/poc/mcps")),
    },
    
    # Database (MariaDB)
    "database": {
        "host": os.getenv("MARIADB_HOST", "localhost"),
        "port": int(os.getenv("MARIADB_PORT", "3306")),
        "user": os.getenv("MARIADB_USER", "mcps_user"),
        "password": os.getenv("MARIADB_PASSWORD", ""),
        "database": os.getenv("MARIADB_DATABASE", "mcps_db"),
        "charset": os.getenv("MARIADB_CHARSET", "utf8mb4"),
        "ssl": int(os.getenv("MARIADB_SSL", "0")),
        "connect_timeout": int(os.getenv("MARIADB_CONNECT_TIMEOUT", "10")),
        "read_timeout": int(os.getenv("MARIADB_READ_TIMEOUT", "30")),
        "write_timeout": int(os.getenv("MARIADB_WRITE_TIMEOUT", "30")),
        "pool_size": {
            "min": int(os.getenv("MARIADB_POOL_MIN", "5")),
            "max": int(os.getenv("MARIADB_POOL_MAX", "20")),
        },
    },
    
    # Elasticsearch
    "elasticsearch": {
        "host": os.getenv("ES_HOST", "http://localhost:9200"),
        "user": os.getenv("ES_USER", ""),
        "password": os.getenv("ES_PASSWORD", ""),
        "ssl_enable": os.getenv("ES_SSL_ENABLE", "N").upper() == "Y",
        "ssl_verify_skip": os.getenv("ES_SSL_VERIFY_SKIP", "Y").upper() == "Y",
        "timeout": int(os.getenv("ES_TIMEOUT", "30")),
        "index_prefix": os.getenv("ES_INDEX_PREFIX", "mcps"),
    },
    
    # JWT
    "jwt": {
        "secret_key": os.getenv("JWT_SECRET_KEY", "change_me_in_production"),
        "algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
        "expiration_minutes": int(os.getenv("JWT_EXPIRATION_MINUTES", "60")),
    },
    
    # Logging
    "logging": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "format": os.getenv("LOG_FORMAT", "text"),
        "dir": Path(os.getenv("LOG_DIR", "/app/poc/mcps/data/logs")),
        "max_bytes": int(os.getenv("LOG_MAX_BYTES", "10485760")),
        "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "10")),
    },
    
    # Cache
    "cache": {
        "max_size": int(os.getenv("CACHE_MAX_SIZE", "1000")),
        "default_ttl": int(os.getenv("CACHE_DEFAULT_TTL", "300")),
    },
    
    # MCP
    "mcp": {
        "stdio_timeout": int(os.getenv("MCP_STDIO_TIMEOUT", "30")),
        "server_restart_delay": int(os.getenv("MCP_SERVER_RESTART_DELAY", "5")),
    },
    
    # Rate Limiting
    "rate_limit": {
        "per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "100")),
    },
    
    # Network
    "network": {
        "api_gateway": {
            "host": os.getenv("API_GATEWAY_HOST", "0.0.0.0"),
            "port": int(os.getenv("API_GATEWAY_PORT", "8000")),
        },
        "mcp_host": {
            "host": os.getenv("MCP_HOST_HOST", "127.0.0.1"),
            "port": int(os.getenv("MCP_HOST_PORT", "8080")),
        },
        "frontend": {
            "host": os.getenv("FRONTEND_HOST", "0.0.0.0"),
            "port": int(os.getenv("FRONTEND_PORT", "8501")),
        },
    },
}

# ===========================================
# 싱글톤 인스턴스
# ===========================================

# 지연 초기화를 위한 전역 변수
_db_manager = None
_es_manager = None
_permission_engine = None
_initialized = False


def initialize():
    """
    공유 모듈 초기화
    
    모든 싱글톤 인스턴스를 생성합니다.
    애플리케이션 시작 시 한 번만 호출합니다.
    
    Returns:
        dict: {
            "db": DatabaseManager,
            "es": ElasticsearchManager,
            "permissions": PermissionEngine
        }
    
    Example:
        from shared import initialize
        
        components = initialize()
        db = components["db"]
    """
    global _db_manager, _es_manager, _permission_engine, _initialized
    
    if _initialized:
        return {
            "db": _db_manager,
            "es": _es_manager,
            "permissions": _permission_engine,
        }
    
    from .database import DatabaseManager
    from .elasticsearch import ElasticsearchManager
    from .permissions import PermissionEngine
    
    _db_manager = DatabaseManager(CONFIG["database"])
    _es_manager = ElasticsearchManager(CONFIG["elasticsearch"])
    _permission_engine = PermissionEngine()
    
    _initialized = True
    
    return {
        "db": _db_manager,
        "es": _es_manager,
        "permissions": _permission_engine,
    }


def get_db():
    """DatabaseManager 인스턴스 반환"""
    global _db_manager
    if _db_manager is None:
        from .database import DatabaseManager
        _db_manager = DatabaseManager(CONFIG["database"])
    return _db_manager


def get_es():
    """ElasticsearchManager 인스턴스 반환"""
    global _es_manager
    if _es_manager is None:
        from .elasticsearch import ElasticsearchManager
        _es_manager = ElasticsearchManager(CONFIG["elasticsearch"])
    return _es_manager


def get_permission_engine():
    """PermissionEngine 인스턴스 반환"""
    global _permission_engine
    if _permission_engine is None:
        from .permissions import PermissionEngine
        _permission_engine = PermissionEngine()
    return _permission_engine


def cleanup():
    """
    리소스 정리
    
    애플리케이션 종료 시 호출합니다.
    """
    global _db_manager, _es_manager, _initialized
    
    if _db_manager:
        _db_manager.close()
        _db_manager = None
    
    if _es_manager:
        _es_manager.close()
        _es_manager = None
    
    _initialized = False


# ===========================================
# 버전 정보
# ===========================================

__version__ = CONFIG["app"]["version"]
__author__ = "MCP Ecosystem Team"

# ===========================================
# Public API
# ===========================================

__all__ = [
    # 설정
    "CONFIG",
    
    # 초기화
    "initialize",
    "cleanup",
    
    # 싱글톤 접근자
    "get_db",
    "get_es",
    "get_permission_engine",
    
    # 버전
    "__version__",
]

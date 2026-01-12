#!/bin/bash
# scripts/config.sh
# 공통 설정 파일

# ==============================================
# 프로젝트 경로
# ==============================================

export PROJECT_ROOT="/app/poc/mcps"
export SCRIPTS_DIR="${PROJECT_ROOT}/scripts"
export DATA_DIR="${PROJECT_ROOT}/data"
export LOGS_DIR="${DATA_DIR}/logs"
export BACKUP_DIR="${DATA_DIR}/backups"
export UPLOAD_DIR="${DATA_DIR}/uploads"

# 하위 디렉토리
export DB_DATA_DIR="${DATA_DIR}/database"
export ES_DATA_DIR="${DATA_DIR}/elasticsearch"

# ==============================================
# Python 설정
# ==============================================

export PYTHON_VERSION="3.11"
export VENV_DIR="${PROJECT_ROOT}/venv"
export PYTHON_BIN="${VENV_DIR}/bin/python"
export PIP_BIN="${VENV_DIR}/bin/pip"

# ==============================================
# Database 설정
# ==============================================

export DB_HOST="localhost"
export DB_PORT="3306"
export DB_NAME="mcps_db"
export DB_USER="mcps_user"
export DB_PASSWORD="mcps_password_2026"
export DB_ROOT_PASSWORD="root_password_2026"

# Database 연결 문자열
export DB_URL="mysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# ==============================================
# Redis 설정
# ==============================================

export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_PASSWORD=""
export REDIS_DB="0"

# Redis 연결 문자열
if [ -n "$REDIS_PASSWORD" ]; then
    export REDIS_URL="redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}"
else
    export REDIS_URL="redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}"
fi

# ==============================================
# Elasticsearch 설정
# ==============================================

export ES_HOST="localhost"
export ES_PORT="9200"
export ES_CLUSTER_NAME="mcps-cluster"
export ES_NODE_NAME="node-1"

# Elasticsearch URL
export ES_URL="http://${ES_HOST}:${ES_PORT}"

# ==============================================
# 서비스 포트
# ==============================================

export MCP_HOST_PORT="8000"
export API_GATEWAY_PORT="8080"
export FRONTEND_PORT="3000"
export FRONTEND_BACKEND_PORT="8001"

# ==============================================
# 서비스 이름
# ==============================================

export SERVICE_MCP_HOST="mcp-host"
export SERVICE_API_GATEWAY="mcp-api-gateway"
export SERVICE_FRONTEND="mcp-frontend"

# ==============================================
# 로그 설정
# ==============================================

export LOG_LEVEL="INFO"
export LOG_RETENTION_DAYS="30"
export LOG_MAX_SIZE="100M"

# 서비스별 로그 디렉토리
export LOG_MCP_HOST="${LOGS_DIR}/mcp-host"
export LOG_API_GATEWAY="${LOGS_DIR}/api-gateway"
export LOG_FRONTEND="${LOGS_DIR}/frontend"

# ==============================================
# 백업 설정
# ==============================================

export BACKUP_RETENTION_DAYS="7"
export BACKUP_COMPRESS="true"
export BACKUP_ENCRYPTION="false"

# ==============================================
# 시스템 요구사항
# ==============================================

export MIN_DISK_SPACE_GB="20"
export MIN_MEMORY_GB="4"
export RECOMMENDED_MEMORY_GB="8"

# ==============================================
# 타임아웃 설정
# ==============================================

export SERVICE_START_TIMEOUT="30"
export SERVICE_STOP_TIMEOUT="10"
export DB_CONNECT_TIMEOUT="10"
export ES_START_TIMEOUT="60"
export URL_CHECK_TIMEOUT="30"

# ==============================================
# 개발/운영 환경
# ==============================================

export ENVIRONMENT="${ENVIRONMENT:-development}"

# 환경별 설정
if [ "$ENVIRONMENT" = "production" ]; then
    export LOG_LEVEL="WARNING"
    export BACKUP_RETENTION_DAYS="30"
    export BACKUP_ENCRYPTION="true"
fi

# ==============================================
# 색상 코드 (utils/colors.sh에서도 정의)
# ==============================================

export COLOR_RED='\033[0;31m'
export COLOR_GREEN='\033[0;32m'
export COLOR_YELLOW='\033[1;33m'
export COLOR_BLUE='\033[0;34m'
export COLOR_MAGENTA='\033[0;35m'
export COLOR_CYAN='\033[0;36m'
export COLOR_NC='\033[0m' # No Color

# ==============================================
# 설정 검증
# ==============================================

validate_config() {
    local ERRORS=0
    
    # 필수 디렉토리 확인
    if [ ! -d "$PROJECT_ROOT" ]; then
        echo "ERROR: PROJECT_ROOT does not exist: $PROJECT_ROOT" >&2
        ERRORS=$((ERRORS + 1))
    fi
    
    # Python 버전 확인
    if ! command -v python${PYTHON_VERSION} &> /dev/null; then
        echo "WARNING: Python ${PYTHON_VERSION} not found" >&2
    fi
    
    return $ERRORS
}

# ==============================================
# 설정 출력 (디버그용)
# ==============================================

print_config() {
    echo "======================================"
    echo "  MCP 시스템 설정"
    echo "======================================"
    echo ""
    echo "프로젝트:"
    echo "  ROOT: $PROJECT_ROOT"
    echo "  SCRIPTS: $SCRIPTS_DIR"
    echo "  DATA: $DATA_DIR"
    echo ""
    echo "Python:"
    echo "  VERSION: $PYTHON_VERSION"
    echo "  VENV: $VENV_DIR"
    echo ""
    echo "Database:"
    echo "  HOST: $DB_HOST:$DB_PORT"
    echo "  NAME: $DB_NAME"
    echo "  USER: $DB_USER"
    echo ""
    echo "Redis:"
    echo "  HOST: $REDIS_HOST:$REDIS_PORT"
    echo ""
    echo "Elasticsearch:"
    echo "  HOST: $ES_HOST:$ES_PORT"
    echo "  CLUSTER: $ES_CLUSTER_NAME"
    echo ""
    echo "서비스 포트:"
    echo "  MCP Host: $MCP_HOST_PORT"
    echo "  API Gateway: $API_GATEWAY_PORT"
    echo "  Frontend: $FRONTEND_PORT"
    echo ""
    echo "환경: $ENVIRONMENT"
    echo "======================================"
}

# 자동 검증 (선택)
# validate_config

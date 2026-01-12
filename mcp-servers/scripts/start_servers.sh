#!/bin/bash
# mcp-servers/scripts/start_servers.sh
# 전체 MCP 서버 시작 스크립트

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVERS_DIR="${PROJECT_ROOT}"
LOG_DIR="/app/poc/mcps/logs/mcp-servers"

# 색상 코드
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_NC='\033[0m'

log_info() {
    echo -e "${COLOR_YELLOW}[INFO]${COLOR_NC} $1"
}

log_success() {
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_NC} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_NC} $1"
}

print_banner() {
    echo "=========================================="
    echo "  MCP Servers 시작"
    echo "=========================================="
    echo ""
}

# 로그 디렉토리 생성
mkdir -p "${LOG_DIR}"/{auth_server,document_server,search_server,version_server,audit_server}

# Python 환경 활성화
if [ -f "/app/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/app/miniconda3/etc/profile.d/conda.sh"
    conda activate mcp_env
else
    log_error "Conda 환경을 찾을 수 없습니다."
    exit 1
fi

# 서버 목록 (시작 순서)
SERVERS=(
    "auth_server:Auth Server"
    "document_server:Document Server"
    "search_server:Search Server"
    "version_server:Version Server"
    "audit_server:Audit Server"
)

print_banner

# 서버 시작 함수
start_server() {
    local SERVER_NAME=$1
    local DISPLAY_NAME=$2
    local SERVER_DIR="${SERVERS_DIR}/${SERVER_NAME}"
    local PID_FILE="/tmp/mcp_${SERVER_NAME}.pid"
    
    log_info "[$((++COUNTER))/5] ${DISPLAY_NAME} 시작 중..."
    
    if [ ! -f "${SERVER_DIR}/main.py" ]; then
        log_error "${DISPLAY_NAME} main.py를 찾을 수 없습니다: ${SERVER_DIR}/main.py"
        return 1
    fi
    
    # 이미 실행 중인지 확인
    if [ -f "${PID_FILE}" ]; then
        OLD_PID=$(cat "${PID_FILE}")
        if ps -p "${OLD_PID}" > /dev/null 2>&1; then
            log_error "${DISPLAY_NAME}가 이미 실행 중입니다 (PID: ${OLD_PID})"
            return 1
        else
            rm -f "${PID_FILE}"
        fi
    fi
    
    # 서버 시작 (백그라운드)
    cd "${SERVER_DIR}"
    nohup python main.py \
        > "${LOG_DIR}/${SERVER_NAME}/stdout.log" 2>&1 &
    
    SERVER_PID=$!
    echo "${SERVER_PID}" > "${PID_FILE}"
    
    # 시작 확인 (2초 대기)
    sleep 2
    
    if ps -p "${SERVER_PID}" > /dev/null 2>&1; then
        log_success "${DISPLAY_NAME} 시작 완료 (PID: ${SERVER_PID})"
        return 0
    else
        log_error "${DISPLAY_NAME} 시작 실패"
        rm -f "${PID_FILE}"
        return 1
    fi
}

# 카운터 초기화
COUNTER=0
FAILED=0

# 모든 서버 시작
for SERVER_INFO in "${SERVERS[@]}"; do
    IFS=':' read -r SERVER_NAME DISPLAY_NAME <<< "$SERVER_INFO"
    
    if ! start_server "${SERVER_NAME}" "${DISPLAY_NAME}"; then
        FAILED=$((FAILED + 1))
    fi
    
    sleep 1
done

echo ""
echo "=========================================="

if [ ${FAILED} -eq 0 ]; then
    log_success "모든 MCP 서버가 시작되었습니다"
    echo ""
    echo "상태 확인: ./scripts/status.sh"
    echo "중지: ./scripts/stop_servers.sh"
    exit 0
else
    log_error "${FAILED}개 서버 시작 실패"
    echo ""
    echo "로그 확인: ${LOG_DIR}"
    exit 1
fi

#!/bin/bash
# mcp-servers/scripts/stop_servers.sh
# 전체 MCP 서버 중지 스크립트

set -e

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
    echo "  MCP Servers 중지"
    echo "=========================================="
    echo ""
}

# 서버 목록 (중지 순서: 역순)
SERVERS=(
    "audit_server:Audit Server"
    "version_server:Version Server"
    "search_server:Search Server"
    "document_server:Document Server"
    "auth_server:Auth Server"
)

print_banner

# 서버 중지 함수
stop_server() {
    local SERVER_NAME=$1
    local DISPLAY_NAME=$2
    local PID_FILE="/tmp/mcp_${SERVER_NAME}.pid"
    
    log_info "[$((++COUNTER))/5] ${DISPLAY_NAME} 중지 중..."
    
    if [ ! -f "${PID_FILE}" ]; then
        log_error "${DISPLAY_NAME}가 실행 중이지 않습니다"
        return 1
    fi
    
    SERVER_PID=$(cat "${PID_FILE}")
    
    # 프로세스 존재 확인
    if ! ps -p "${SERVER_PID}" > /dev/null 2>&1; then
        log_error "${DISPLAY_NAME} 프로세스를 찾을 수 없습니다 (PID: ${SERVER_PID})"
        rm -f "${PID_FILE}"
        return 1
    fi
    
    # Graceful shutdown (SIGTERM)
    kill -TERM "${SERVER_PID}" 2>/dev/null || true
    
    # 종료 대기 (최대 5초)
    WAIT_COUNT=0
    while ps -p "${SERVER_PID}" > /dev/null 2>&1; do
        sleep 1
        WAIT_COUNT=$((WAIT_COUNT + 1))
        
        if [ ${WAIT_COUNT} -ge 5 ]; then
            log_info "${DISPLAY_NAME} 강제 종료 중..."
            kill -KILL "${SERVER_PID}" 2>/dev/null || true
            break
        fi
    done
    
    # PID 파일 삭제
    rm -f "${PID_FILE}"
    
    log_success "${DISPLAY_NAME} 중지 완료"
    return 0
}

# 카운터 초기화
COUNTER=0
FAILED=0

# 모든 서버 중지
for SERVER_INFO in "${SERVERS[@]}"; do
    IFS=':' read -r SERVER_NAME DISPLAY_NAME <<< "$SERVER_INFO"
    
    if ! stop_server "${SERVER_NAME}" "${DISPLAY_NAME}"; then
        FAILED=$((FAILED + 1))
    fi
    
    sleep 0.5
done

echo ""
echo "=========================================="

if [ ${FAILED} -eq 0 ]; then
    log_success "모든 MCP 서버가 중지되었습니다"
    exit 0
else
    log_error "${FAILED}개 서버 중지 실패"
    exit 1
fi

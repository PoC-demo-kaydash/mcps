#!/bin/bash
# mcp-servers/scripts/status.sh
# MCP 서버 상태 확인 스크립트

# 색상 코드
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_BLUE='\033[0;34m'
COLOR_NC='\033[0m'

print_banner() {
    echo "=========================================="
    echo "  MCP Servers 상태"
    echo "=========================================="
    echo ""
}

# 서버 목록
SERVERS=(
    "auth_server:Auth Server"
    "document_server:Document Server"
    "search_server:Search Server"
    "version_server:Version Server"
    "audit_server:Audit Server"
)

print_banner

# 서버 상태 확인 함수
check_server_status() {
    local SERVER_NAME=$1
    local DISPLAY_NAME=$2
    local PID_FILE="/tmp/mcp_${SERVER_NAME}.pid"
    local LOG_FILE="/app/poc/mcps/logs/mcp-servers/${SERVER_NAME}/stdout.log"
    
    echo -e "${COLOR_BLUE}[${DISPLAY_NAME}]${COLOR_NC}"
    
    if [ ! -f "${PID_FILE}" ]; then
        echo -e "  상태: ${COLOR_RED}●${COLOR_NC} 중지됨"
        echo ""
        return
    fi
    
    SERVER_PID=$(cat "${PID_FILE}")
    
    # 프로세스 존재 확인
    if ! ps -p "${SERVER_PID}" > /dev/null 2>&1; then
        echo -e "  상태: ${COLOR_RED}●${COLOR_NC} 중지됨 (PID 파일 존재하나 프로세스 없음)"
        rm -f "${PID_FILE}"
        echo ""
        return
    fi
    
    # 실행 중
    echo -e "  상태: ${COLOR_GREEN}●${COLOR_NC} 실행 중"
    echo "  PID: ${SERVER_PID}"
    
    # 메모리 사용량
    if command -v ps &> /dev/null; then
        MEM_USAGE=$(ps -o rss= -p "${SERVER_PID}" 2>/dev/null | awk '{printf "%.1f MB", $1/1024}')
        if [ -n "${MEM_USAGE}" ]; then
            echo "  메모리: ${MEM_USAGE}"
        fi
    fi
    
    # 실행 시간
    if command -v ps &> /dev/null; then
        ELAPSED=$(ps -o etime= -p "${SERVER_PID}" 2>/dev/null | xargs)
        if [ -n "${ELAPSED}" ]; then
            echo "  실행 시간: ${ELAPSED}"
        fi
    fi
    
    # 최근 로그 에러 확인
    if [ -f "${LOG_FILE}" ]; then
        ERROR_COUNT=$(grep -ci "error\|exception\|traceback" "${LOG_FILE}" 2>/dev/null | tail -1 || echo "0")
        if [ "${ERROR_COUNT}" -gt 0 ]; then
            echo -e "  최근 에러: ${COLOR_RED}${ERROR_COUNT}건${COLOR_NC}"
        else
            echo -e "  최근 에러: ${COLOR_GREEN}없음${COLOR_NC}"
        fi
    fi
    
    echo ""
}

# 모든 서버 상태 확인
RUNNING_COUNT=0
for SERVER_INFO in "${SERVERS[@]}"; do
    IFS=':' read -r SERVER_NAME DISPLAY_NAME <<< "$SERVER_INFO"
    check_server_status "${SERVER_NAME}" "${DISPLAY_NAME}"
    
    # 실행 중인 서버 카운트
    PID_FILE="/tmp/mcp_${SERVER_NAME}.pid"
    if [ -f "${PID_FILE}" ]; then
        SERVER_PID=$(cat "${PID_FILE}")
        if ps -p "${SERVER_PID}" > /dev/null 2>&1; then
            RUNNING_COUNT=$((RUNNING_COUNT + 1))
        fi
    fi
done

echo "=========================================="
echo "실행 중인 서버: ${RUNNING_COUNT}/5"
echo ""

if [ ${RUNNING_COUNT} -eq 5 ]; then
    echo -e "${COLOR_GREEN}모든 서버가 정상 실행 중입니다${COLOR_NC}"
elif [ ${RUNNING_COUNT} -eq 0 ]; then
    echo -e "${COLOR_RED}모든 서버가 중지되어 있습니다${COLOR_NC}"
    echo ""
    echo "시작: ./scripts/start_servers.sh"
else
    echo -e "${COLOR_YELLOW}일부 서버만 실행 중입니다${COLOR_NC}"
    echo ""
    echo "시작: ./scripts/start_servers.sh"
    echo "중지: ./scripts/stop_servers.sh"
fi

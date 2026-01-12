#!/bin/bash
# scripts/manage/status.sh
# 시스템 상태 확인 스크립트

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

print_banner "MCP 시스템 상태"

# 서비스 상태
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "서비스 상태:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SERVICES=(
    "mariadb:MariaDB"
    "redis:Redis"
    "elasticsearch:Elasticsearch"
    "${SERVICE_MCP_HOST}:MCP Host"
    "${SERVICE_API_GATEWAY}:API Gateway"
    "${SERVICE_FRONTEND}:Frontend"
)

for SERVICE_INFO in "${SERVICES[@]}"; do
    IFS=':' read -r SERVICE_NAME DISPLAY_NAME <<< "$SERVICE_INFO"
    
    if is_service_running "${SERVICE_NAME}"; then
        printf "  %-20s ${COLOR_GREEN}●${COLOR_NC} 실행 중\n" "${DISPLAY_NAME}:"
    else
        printf "  %-20s ${COLOR_RED}●${COLOR_NC} 중지됨\n" "${DISPLAY_NAME}:"
    fi
done

echo ""

# 포트 상태
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "포트 상태:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PORTS=(
    "${MCP_HOST_PORT}:MCP Host"
    "${API_GATEWAY_PORT}:API Gateway"
    "${FRONTEND_PORT}:Frontend"
    "${DB_PORT}:MariaDB"
    "${REDIS_PORT}:Redis"
    "${ES_PORT}:Elasticsearch"
)

for PORT_INFO in "${PORTS[@]}"; do
    IFS=':' read -r PORT DISPLAY_NAME <<< "$PORT_INFO"
    
    if is_port_in_use "$PORT"; then
        printf "  %-20s ${COLOR_GREEN}●${COLOR_NC} :%-6s (LISTEN)\n" "${DISPLAY_NAME}:" "${PORT}"
    else
        printf "  %-20s ${COLOR_RED}●${COLOR_NC} :%-6s (CLOSED)\n" "${DISPLAY_NAME}:" "${PORT}"
    fi
done

echo ""

# 디스크 사용량
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "디스크 사용량:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
df -h "${PROJECT_ROOT}" | tail -1 | awk '{printf "  사용: %s / 전체: %s (%s)\n", $3, $2, $5}'

echo ""

# 메모리 사용량
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "메모리 사용량:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
free -h | grep "^Mem:" | awk '{printf "  사용: %s / 전체: %s\n", $3, $2}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

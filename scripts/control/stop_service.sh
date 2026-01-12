#!/bin/bash
# scripts/control/stop_service.sh
# 개별 서비스 중지 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

# 사용법
if [ $# -eq 0 ]; then
    echo "Usage: $0 <service>"
    echo ""
    echo "Available services:"
    echo "  - mariadb"
    echo "  - redis"
    echo "  - elasticsearch"
    echo "  - ${SERVICE_MCP_HOST}"
    echo "  - ${SERVICE_API_GATEWAY}"
    echo "  - ${SERVICE_FRONTEND}"
    exit 1
fi

SERVICE=$1

log_info "${SERVICE} 중지 중..."

if is_service_running "${SERVICE}"; then
    systemctl stop "${SERVICE}"
    log_success "${SERVICE} 중지 완료"
else
    log_info "${SERVICE}가 실행 중이 아닙니다"
fi

systemctl status "${SERVICE}" --no-pager || true

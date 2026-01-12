#!/bin/bash
# scripts/control/start_service.sh
# 개별 서비스 시작 스크립트

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

log_info "${SERVICE} 시작 중..."

if is_service_running "${SERVICE}"; then
    log_info "${SERVICE}가 이미 실행 중입니다"
    systemctl status "${SERVICE}" --no-pager
else
    systemctl start "${SERVICE}"
    
    if wait_for_service "${SERVICE}" ${SERVICE_START_TIMEOUT}; then
        log_success "${SERVICE} 시작 완료"
        systemctl status "${SERVICE}" --no-pager
    else
        log_error "${SERVICE} 시작 실패"
        systemctl status "${SERVICE}" --no-pager
        exit 1
    fi
fi

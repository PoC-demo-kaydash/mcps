#!/bin/bash
# scripts/health/check_services.sh
# 서비스 실행 상태 확인

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

EXIT_CODE=0

SERVICES=(
    "${SERVICE_MCP_HOST}"
    "${SERVICE_API_GATEWAY}"
    "${SERVICE_FRONTEND}"
)

for SERVICE in "${SERVICES[@]}"; do
    if is_service_running "${SERVICE}"; then
        log_success "${SERVICE} 실행 중"
    else
        log_error "${SERVICE} 중지됨"
        EXIT_CODE=1
    fi
done

exit ${EXIT_CODE}

#!/bin/bash
# scripts/health/check_connectivity.sh
# 네트워크 연결 확인

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

EXIT_CODE=0

# 서비스 URL
URLS=(
    "http://localhost:${MCP_HOST_PORT}/health:MCP Host"
    "http://localhost:${API_GATEWAY_PORT}/health:API Gateway"
    "http://localhost:${FRONTEND_PORT}:Frontend"
)

for URL_INFO in "${URLS[@]}"; do
    IFS=':' read -r URL DISPLAY_NAME <<< "$URL_INFO"
    
    if check_url_health "${URL}" 200; then
        log_success "${DISPLAY_NAME} 연결 정상"
    else
        log_error "${DISPLAY_NAME} 연결 실패"
        EXIT_CODE=1
    fi
done

exit ${EXIT_CODE}

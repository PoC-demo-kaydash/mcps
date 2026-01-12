#!/bin/bash
# scripts/health/healthcheck.sh
# 전체 헬스체크

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"

print_banner "MCP 헬스체크"

EXIT_CODE=0

# 데이터베이스
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "데이터베이스 확인 중..."
if bash "${SCRIPT_DIR}/check_database.sh" 2>&1; then
    :
else
    EXIT_CODE=1
fi

# 서비스
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "서비스 확인 중..."
if bash "${SCRIPT_DIR}/check_services.sh" 2>&1; then
    :
else
    EXIT_CODE=1
fi

# 연결
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "연결 확인 중..."
if bash "${SCRIPT_DIR}/check_connectivity.sh" 2>&1; then
    :
else
    EXIT_CODE=1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ${EXIT_CODE} -eq 0 ]; then
    log_success "모든 헬스체크 통과"
else
    log_error "일부 헬스체크 실패"
fi

exit ${EXIT_CODE}

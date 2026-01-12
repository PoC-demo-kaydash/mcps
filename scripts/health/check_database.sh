#!/bin/bash
# scripts/health/check_database.sh
# 데이터베이스 연결 확인

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"

# MySQL 연결 확인
if mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASSWORD}" -e "SELECT 1;" &>/dev/null; then
    log_success "데이터베이스 연결 정상"
    exit 0
else
    log_error "데이터베이스 연결 실패"
    exit 1
fi

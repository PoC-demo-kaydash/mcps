#!/bin/bash
# scripts/backup/backup.sh
# 백업 스크립트 (기존 backup_database.sh 통합)

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"

log_info "백업 시작..."

# 백업 디렉토리 생성
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"
mkdir -p "${BACKUP_PATH}"

# 데이터베이스 백업
log_info "데이터베이스 백업 중..."
mysqldump -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASSWORD}" \
    --single-transaction --routines --triggers --events \
    "${DB_NAME}" > "${BACKUP_PATH}/database.sql"
log_success "데이터베이스 백업 완료"

# 설정 파일 백업
log_info "설정 파일 백업 중..."
cp -r "${PROJECT_ROOT}/config" "${BACKUP_PATH}/" 2>/dev/null || true
log_success "설정 파일 백업 완료"

# 압축
log_info "백업 압축 중..."
cd "${BACKUP_DIR}"
tar -czf "${TIMESTAMP}.tar.gz" "${TIMESTAMP}"
rm -rf "${TIMESTAMP}"
log_success "백업 압축 완료: ${BACKUP_DIR}/${TIMESTAMP}.tar.gz"

# 오래된 백업 삭제
log_info "오래된 백업 삭제 중... (보관 기간: ${BACKUP_RETENTION_DAYS}일)"
find "${BACKUP_DIR}" -type f -name "*.tar.gz" -mtime +${BACKUP_RETENTION_DAYS} -delete 2>/dev/null || true

log_success "백업 완료!"

#!/bin/bash
# scripts/backup/restore.sh
# 복구 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "사용 가능한 백업 파일:"
    ls -lh "${BACKUP_DIR}"/*.tar.gz 2>/dev/null || echo "  (백업 없음)"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "${BACKUP_FILE}" ]; then
    log_error "백업 파일을 찾을 수 없습니다: ${BACKUP_FILE}"
    exit 1
fi

log_warning "복구를 시작합니다. 기존 데이터가 삭제됩니다!"
if ! confirm "계속하시겠습니까?"; then
    log_info "복구가 취소되었습니다."
    exit 0
fi

# 서비스 중지
log_info "서비스 중지 중..."
bash "${SCRIPTS_DIR}/control/stop_all.sh"

# 백업 파일 압축 해제
log_info "백업 파일 압축 해제 중..."
TEMP_DIR=$(mktemp -d)
tar -xzf "${BACKUP_FILE}" -C "${TEMP_DIR}"
BACKUP_DIR_NAME=$(basename "${BACKUP_FILE}" .tar.gz)

# 데이터베이스 복구
log_info "데이터베이스 복구 중..."
mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASSWORD}" \
    "${DB_NAME}" < "${TEMP_DIR}/${BACKUP_DIR_NAME}/database.sql"
log_success "데이터베이스 복구 완료"

# 설정 파일 복구
if [ -d "${TEMP_DIR}/${BACKUP_DIR_NAME}/config" ]; then
    log_info "설정 파일 복구 중..."
    cp -r "${TEMP_DIR}/${BACKUP_DIR_NAME}/config"/* "${PROJECT_ROOT}/config/" 2>/dev/null || true
    log_success "설정 파일 복구 완료"
fi

# 임시 디렉토리 삭제
rm -rf "${TEMP_DIR}"

# 서비스 시작
log_info "서비스 시작 중..."
bash "${SCRIPTS_DIR}/control/start_all.sh"

log_success "복구 완료!"

#!/bin/bash
# scripts/manage/cleanup.sh
# 시스템 정리 스크립트 (기존 daily_cleanup.sh 통합)

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"

log_info "시스템 정리 시작..."

# 오래된 로그 삭제
log_info "오래된 로그 삭제 중... (보관 기간: ${LOG_RETENTION_DAYS}일)"
find "${LOGS_DIR}" -type f -name "*.log" -mtime +${LOG_RETENTION_DAYS} -delete 2>/dev/null || true
find "${LOGS_DIR}" -type f -name "*.log.*" -mtime +${LOG_RETENTION_DAYS} -delete 2>/dev/null || true
log_success "오래된 로그 삭제 완료"

# 오래된 백업 삭제
log_info "오래된 백업 삭제 중... (보관 기간: ${BACKUP_RETENTION_DAYS}일)"
find "${BACKUP_DIR}" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete 2>/dev/null || true
log_success "오래된 백업 삭제 완료"

# 임시 파일 삭제
log_info "임시 파일 삭제 중..."
find "${PROJECT_ROOT}" -type f -name "*.pyc" -delete 2>/dev/null || true
find "${PROJECT_ROOT}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${PROJECT_ROOT}" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
log_success "임시 파일 삭제 완료"

# 디스크 사용량 표시
log_info "디스크 사용량:"
df -h "${PROJECT_ROOT}"

log_success "시스템 정리 완료!"

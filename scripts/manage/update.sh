#!/bin/bash
# scripts/manage/update.sh
# 시스템 업데이트 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

log_info "시스템 업데이트 시작..."

# 서비스 중지
log_info "서비스 중지 중..."
bash "${SCRIPTS_DIR}/control/stop_all.sh"

# 백업
log_info "백업 생성 중..."
if [ -f "${SCRIPTS_DIR}/backup/backup.sh" ]; then
    bash "${SCRIPTS_DIR}/backup/backup.sh" || log_warning "백업 실패"
fi

# Python 패키지 업데이트
log_info "Python 패키지 업데이트 중..."
source "${VENV_DIR}/bin/activate"

for SERVICE_DIR in mcp-host api-gateway frontend; do
    REQ_FILE="${PROJECT_ROOT}/${SERVICE_DIR}/requirements.txt"
    if [ -f "$REQ_FILE" ]; then
        log_info "${SERVICE_DIR} 패키지 업데이트..."
        pip install --upgrade -r "$REQ_FILE" || log_warning "${SERVICE_DIR} 업데이트 실패"
    fi
done

log_success "Python 패키지 업데이트 완료"

# 서비스 시작
log_info "서비스 시작 중..."
bash "${SCRIPTS_DIR}/control/start_all.sh"

log_success "시스템 업데이트 완료!"

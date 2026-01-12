#!/bin/bash
# scripts/control/restart_all.sh
# 전체 서비스 재시작 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"

print_banner "MCP 시스템 재시작"

# 중지
log_info "서비스 중지 중..."
bash "${SCRIPTS_DIR}/control/stop_all.sh"

# 대기
log_info "5초 대기 중..."
sleep 5

# 시작
log_info "서비스 시작 중..."
bash "${SCRIPTS_DIR}/control/start_all.sh"

log_success "시스템 재시작 완료!"

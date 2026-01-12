#!/bin/bash
# scripts/control/stop_all.sh
# 전체 서비스 중지 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

print_banner "MCP 시스템 중지"

# ==============================================
# [1/4] Frontend 중지
# ==============================================

print_section "[1/4] Frontend 중지"

if is_service_running ${SERVICE_FRONTEND}; then
    log_info "Frontend 중지 중..."
    systemctl stop ${SERVICE_FRONTEND}
    log_success "Frontend 중지 완료"
else
    log_info "Frontend가 실행 중이 아닙니다"
fi

# ==============================================
# [2/4] API Gateway 중지
# ==============================================

print_section "[2/4] API Gateway 중지"

if is_service_running ${SERVICE_API_GATEWAY}; then
    log_info "API Gateway 중지 중..."
    systemctl stop ${SERVICE_API_GATEWAY}
    log_success "API Gateway 중지 완료"
else
    log_info "API Gateway가 실행 중이 아닙니다"
fi

# ==============================================
# [3/4] MCP Host 중지
# ==============================================

print_section "[3/4] MCP Host 중지"

if is_service_running ${SERVICE_MCP_HOST}; then
    log_info "MCP Host 중지 중..."
    systemctl stop ${SERVICE_MCP_HOST}
    log_success "MCP Host 중지 완료"
else
    log_info "MCP Host가 실행 중이 아닙니다"
fi

# ==============================================
# [4/4] 인프라 서비스 중지 (선택)
# ==============================================

print_section "[4/4] 인프라 서비스 중지 (선택)"

if confirm "인프라 서비스(MariaDB, Redis, Elasticsearch)도 중지하시겠습니까?" "n"; then
    if is_service_running elasticsearch; then
        log_info "Elasticsearch 중지 중..."
        systemctl stop elasticsearch
        log_success "Elasticsearch 중지 완료"
    fi
    
    if is_service_running redis; then
        log_info "Redis 중지 중..."
        systemctl stop redis
        log_success "Redis 중지 완료"
    fi
    
    if is_service_running mariadb; then
        log_info "MariaDB 중지 중..."
        systemctl stop mariadb
        log_success "MariaDB 중지 완료"
    fi
else
    log_info "인프라 서비스는 계속 실행됩니다"
fi

# ==============================================
# 완료
# ==============================================

print_banner "서비스 중지 완료"

log_success "======================================"
log_success "  시스템 중지됨"
log_success "======================================"
echo ""
log_info "시스템 재시작:"
log_info "  sudo bash ${SCRIPTS_DIR}/control/start_all.sh"
echo ""

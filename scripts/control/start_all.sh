#!/bin/bash
# scripts/control/start_all.sh
# 전체 서비스 시작 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

print_banner "MCP 시스템 시작"

# ==============================================
# [1/4] 인프라 서비스 시작
# ==============================================

print_section "[1/4] 인프라 서비스 시작"

# MariaDB
if ! is_service_running mariadb; then
    log_info "MariaDB 시작 중..."
    systemctl start mariadb
    wait_for_service mariadb 10
    log_success "MariaDB 시작 완료"
else
    log_info "MariaDB 이미 실행 중"
fi

# Redis
if ! is_service_running redis; then
    log_info "Redis 시작 중..."
    systemctl start redis
    wait_for_service redis 5
    log_success "Redis 시작 완료"
else
    log_info "Redis 이미 실행 중"
fi

# Elasticsearch
if ! is_service_running elasticsearch; then
    log_info "Elasticsearch 시작 중... (최대 60초 대기)"
    systemctl start elasticsearch
    
    if wait_for_url "${ES_URL}" 60; then
        log_success "Elasticsearch 시작 완료"
    else
        log_error "Elasticsearch 시작 실패 또는 타임아웃"
    fi
else
    log_info "Elasticsearch 이미 실행 중"
fi

# ==============================================
# [2/4] MCP Host 시작
# ==============================================

print_section "[2/4] MCP Host 시작"

if ! is_service_running ${SERVICE_MCP_HOST}; then
    log_info "MCP Host 시작 중..."
    systemctl start ${SERVICE_MCP_HOST}
    
    if wait_for_service ${SERVICE_MCP_HOST} ${SERVICE_START_TIMEOUT}; then
        sleep 2
        log_success "MCP Host 시작 완료"
    else
        log_error "MCP Host 시작 실패"
    fi
else
    log_info "MCP Host 이미 실행 중"
fi

# ==============================================
# [3/4] API Gateway 시작
# ==============================================

print_section "[3/4] API Gateway 시작"

if ! is_service_running ${SERVICE_API_GATEWAY}; then
    log_info "API Gateway 시작 중..."
    systemctl start ${SERVICE_API_GATEWAY}
    
    if wait_for_service ${SERVICE_API_GATEWAY} ${SERVICE_START_TIMEOUT}; then
        sleep 2
        log_success "API Gateway 시작 완료"
    else
        log_error "API Gateway 시작 실패"
    fi
else
    log_info "API Gateway 이미 실행 중"
fi

# ==============================================
# [4/4] Frontend 시작
# ==============================================

print_section "[4/4] Frontend 시작"

if ! is_service_running ${SERVICE_FRONTEND}; then
    log_info "Frontend 시작 중..."
    systemctl start ${SERVICE_FRONTEND}
    
    if wait_for_service ${SERVICE_FRONTEND} ${SERVICE_START_TIMEOUT}; then
        sleep 3
        log_success "Frontend 시작 완료"
    else
        log_error "Frontend 시작 실패"
    fi
else
    log_info "Frontend 이미 실행 중"
fi

# ==============================================
# 헬스체크
# ==============================================

echo ""
log_info "헬스체크 수행 중..."
sleep 2

if [ -f "${SCRIPTS_DIR}/health/healthcheck.sh" ]; then
    bash "${SCRIPTS_DIR}/health/healthcheck.sh" || log_warning "일부 헬스체크 실패"
fi

# ==============================================
# 완료
# ==============================================

print_banner "모든 서비스 시작 완료!"

log_success "======================================"
log_success "  시스템 실행 중"
log_success "======================================"
echo ""
log_info "접속 정보:"
log_info "  - Frontend: http://localhost:${FRONTEND_PORT}"
log_info "  - API Gateway: http://localhost:${API_GATEWAY_PORT}"
log_info "  - MCP Host: http://localhost:${MCP_HOST_PORT}"
echo ""
log_info "상태 확인:"
log_info "  sudo bash ${SCRIPTS_DIR}/manage/status.sh"
echo ""

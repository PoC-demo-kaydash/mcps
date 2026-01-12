#!/bin/bash
# scripts/install/setup.sh
# 마스터 설치 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

print_banner "MCP 문서 관리 시스템 설치 시작"

OVERALL_STATUS=0

# ==============================================
# [1/7] 환경 확인
# ==============================================

print_section "[1/7] 환경 확인"

if bash "${SCRIPTS_DIR}/env/check_env.sh"; then
    log_success "환경 확인 완료"
else
    log_error "환경 확인 실패"
    log_info "문제를 해결한 후 다시 시도하세요"
    exit 1
fi

# ==============================================
# [2/7] Python 설치
# ==============================================

print_section "[2/7] Python 설치"

if bash "${SCRIPTS_DIR}/install/install_python.sh"; then
    log_success "Python 설치 완료"
else
    log_error "Python 설치 실패"
    OVERALL_STATUS=1
fi

# ==============================================
# [3/7] Database 설치
# ==============================================

print_section "[3/7] MariaDB 설치"

if bash "${SCRIPTS_DIR}/install/install_database.sh"; then
    log_success "MariaDB 설치 완료"
else
    log_error "MariaDB 설치 실패"
    OVERALL_STATUS=1
fi

# ==============================================
# [4/7] Redis 설치
# ==============================================

print_section "[4/7] Redis 설치"

if bash "${SCRIPTS_DIR}/install/install_redis.sh"; then
    log_success "Redis 설치 완료"
else
    log_error "Redis 설치 실패"
    OVERALL_STATUS=1
fi

# ==============================================
# [5/7] Elasticsearch 설치
# ==============================================

print_section "[5/7] Elasticsearch 설치"

if bash "${SCRIPTS_DIR}/install/install_elasticsearch.sh"; then
    log_success "Elasticsearch 설치 완료"
else
    log_error "Elasticsearch 설치 실패"
    OVERALL_STATUS=1
fi

# 인프라 설치 실패 시 중단
if [ $OVERALL_STATUS -ne 0 ]; then
    log_error "인프라 설치 중 오류 발생. 설치를 중단합니다"
    exit $OVERALL_STATUS
fi

# ==============================================
# [6/7] 서비스 설치
# ==============================================

print_section "[6/7] MCP 서비스 설치"

if bash "${SCRIPTS_DIR}/install/install_services.sh"; then
    log_success "서비스 설치 완료"
else
    log_error "서비스 설치 실패"
    OVERALL_STATUS=1
fi

# ==============================================
# [7/7] 초기화
# ==============================================

print_section "[7/7] 시스템 초기화"

if [ -f "${SCRIPTS_DIR}/init/init_all.sh" ]; then
    if confirm "데이터베이스 및 Elasticsearch를 초기화하시겠습니까?" "y"; then
        if bash "${SCRIPTS_DIR}/init/init_all.sh"; then
            log_success "시스템 초기화 완료"
        else
            log_error "시스템 초기화 실패"
            OVERALL_STATUS=1
        fi
    else
        log_info "초기화를 건너뜁니다"
        log_info "나중에 수동으로 실행: sudo bash ${SCRIPTS_DIR}/init/init_all.sh"
    fi
else
    log_warning "초기화 스크립트를 찾을 수 없습니다"
    log_info "Phase 3 구현 후 수동으로 실행하세요"
fi

# ==============================================
# 완료
# ==============================================

echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
    print_banner "설치 완료!"
    
    log_success "======================================"
    log_success "  모든 구성요소 설치 완료"
    log_success "======================================"
    echo ""
    log_info "다음 단계:"
    echo ""
    log_info "1. 시스템 시작:"
    log_info "   sudo bash ${SCRIPTS_DIR}/control/start_all.sh"
    echo ""
    log_info "2. 상태 확인:"
    log_info "   sudo bash ${SCRIPTS_DIR}/manage/status.sh"
    echo ""
    log_info "3. 접속 URL:"
    log_info "   - Frontend: http://localhost:${FRONTEND_PORT}"
    log_info "   - API Gateway: http://localhost:${API_GATEWAY_PORT}"
    log_info "   - MCP Host: http://localhost:${MCP_HOST_PORT}"
    echo ""
else
    print_banner "설치 중 오류 발생"
    
    log_error "======================================"
    log_error "  일부 구성요소 설치 실패"
    log_error "======================================"
    echo ""
    log_info "문제 해결:"
    echo ""
    log_info "1. 로그 확인:"
    log_info "   journalctl -xe"
    echo ""
    log_info "2. 개별 설치 재시도:"
    log_info "   sudo bash ${SCRIPTS_DIR}/install/install_<component>.sh"
    echo ""
    log_info "3. 환경 재확인:"
    log_info "   sudo bash ${SCRIPTS_DIR}/env/check_env.sh"
    echo ""
fi

exit $OVERALL_STATUS

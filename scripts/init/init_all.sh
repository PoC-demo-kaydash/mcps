#!/bin/bash
# scripts/init/init_all.sh
# 전체 초기화 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

print_banner "시스템 초기화 시작"

OVERALL_STATUS=0

# ==============================================
# [1/3] Database 초기화
# ==============================================

print_section "[1/3] Database 초기화"

if bash "${SCRIPTS_DIR}/init/init_database.sh"; then
    log_success "Database 초기화 완료"
else
    log_error "Database 초기화 실패"
    OVERALL_STATUS=1
fi

echo ""

# ==============================================
# [2/3] Elasticsearch 초기화
# ==============================================

print_section "[2/3] Elasticsearch 초기화"

if bash "${SCRIPTS_DIR}/init/init_elasticsearch.sh"; then
    log_success "Elasticsearch 초기화 완료"
else
    log_error "Elasticsearch 초기화 실패"
    OVERALL_STATUS=1
fi

echo ""

# ==============================================
# [3/3] 초기 데이터 생성
# ==============================================

print_section "[3/3] 초기 데이터 생성"

if bash "${SCRIPTS_DIR}/init/init_data.sh"; then
    log_success "초기 데이터 생성 완료"
else
    log_warning "초기 데이터 생성 일부 실패 (계속 진행)"
fi

echo ""

# ==============================================
# 완료
# ==============================================

if [ $OVERALL_STATUS -eq 0 ]; then
    print_banner "시스템 초기화 완료!"
    
    log_success "======================================"
    log_success "  모든 초기화 완료"
    log_success "======================================"
    echo ""
    log_info "다음 단계:"
    echo ""
    log_info "1. 서비스 시작:"
    log_info "   sudo bash ${SCRIPTS_DIR}/control/start_all.sh"
    echo ""
    log_info "2. 상태 확인:"
    log_info "   sudo bash ${SCRIPTS_DIR}/manage/status.sh"
    echo ""
else
    print_banner "초기화 중 오류 발생"
    
    log_error "======================================"
    log_error "  일부 초기화 실패"
    log_error "======================================"
    echo ""
    log_info "개별 초기화 재시도:"
    log_info "  sudo bash ${SCRIPTS_DIR}/init/init_database.sh"
    log_info "  sudo bash ${SCRIPTS_DIR}/init/init_elasticsearch.sh"
    echo ""
fi

exit $OVERALL_STATUS

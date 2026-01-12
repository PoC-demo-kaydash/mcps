#!/bin/bash
# scripts/init/init_data.sh
# 초기 데이터 생성 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

log_info "초기 데이터 생성 시작..."

# 가상환경 활성화
if [ -f "${VENV_DIR}/bin/activate" ]; then
    source "${VENV_DIR}/bin/activate"
else
    log_error "가상환경을 찾을 수 없습니다: ${VENV_DIR}"
    exit 1
fi

# ==============================================
# 샘플 문서 생성 (선택)
# ==============================================

if confirm "샘플 문서를 생성하시겠습니까?" "n"; then
    if [ -f "${SCRIPTS_DIR}/generate_sample_documents.py" ]; then
        log_info "샘플 문서 생성 중..."
        cd "${SCRIPTS_DIR}"
        
        if python generate_sample_documents.py; then
            log_success "샘플 문서 생성 완료"
        else
            log_warning "샘플 문서 생성 실패"
        fi
    else
        log_warning "generate_sample_documents.py를 찾을 수 없습니다"
    fi
fi

# ==============================================
# 샘플 감사 로그 생성 (선택)
# ==============================================

if confirm "샘플 감사 로그를 생성하시겠습니까?" "n"; then
    if [ -f "${SCRIPTS_DIR}/generate_sample_audit_logs.py" ]; then
        log_info "샘플 감사 로그 생성 중..."
        cd "${SCRIPTS_DIR}"
        
        if python generate_sample_audit_logs.py; then
            log_success "샘플 감사 로그 생성 완료"
        else
            log_warning "샘플 감사 로그 생성 실패"
        fi
    else
        log_warning "generate_sample_audit_logs.py를 찾을 수 없습니다"
    fi
fi

# ==============================================
# Elasticsearch 동기화 (선택)
# ==============================================

if confirm "데이터를 Elasticsearch에 동기화하시겠습니까?" "n"; then
    # 문서 동기화
    if [ -f "${SCRIPTS_DIR}/sync_documents_to_es.py" ]; then
        log_info "문서 Elasticsearch 동기화 중..."
        cd "${SCRIPTS_DIR}"
        
        if python sync_documents_to_es.py; then
            log_success "문서 동기화 완료"
        else
            log_warning "문서 동기화 실패"
        fi
    else
        log_warning "sync_documents_to_es.py를 찾을 수 없습니다"
    fi
    
    # 감사 로그 동기화
    if [ -f "${SCRIPTS_DIR}/sync_audit_logs_to_es.py" ]; then
        log_info "감사 로그 Elasticsearch 동기화 중..."
        cd "${SCRIPTS_DIR}"
        
        if python sync_audit_logs_to_es.py; then
            log_success "감사 로그 동기화 완료"
        else
            log_warning "감사 로그 동기화 실패"
        fi
    else
        log_warning "sync_audit_logs_to_es.py를 찾을 수 없습니다"
    fi
fi

log_success "======================================"
log_success "  초기 데이터 생성 완료"
log_success "======================================"
log_info ""
log_info "데이터 확인:"
log_info "  mysql -u ${DB_USER} -p'${DB_PASSWORD}' ${DB_NAME} -e 'SELECT COUNT(*) FROM documents;'"
log_info "  curl ${ES_URL}/documents/_count"

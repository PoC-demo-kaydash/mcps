#!/bin/bash
# scripts/install/install_python.sh
# Python 설치 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

log_info "Python ${PYTHON_VERSION} 설치 시작..."

# ==============================================
# Python 설치 확인
# ==============================================

if command_exists python${PYTHON_VERSION}; then
    INSTALLED_VERSION=$(python${PYTHON_VERSION} --version 2>&1 | awk '{print $2}')
    log_info "Python ${INSTALLED_VERSION} 이미 설치됨"
else
    log_info "Python ${PYTHON_VERSION} 설치 중..."
    
    # RHEL 8/9에서 Python 설치
    dnf install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-devel python${PYTHON_VERSION}-pip
    
    if command_exists python${PYTHON_VERSION}; then
        log_success "Python ${PYTHON_VERSION} 설치 완료"
    else
        log_error "Python 설치 실패"
        exit 1
    fi
fi

# ==============================================
# pip 업그레이드
# ==============================================

log_info "pip 업그레이드 중..."
python${PYTHON_VERSION} -m pip install --upgrade pip

# ==============================================
# 가상환경 생성
# ==============================================

if [ ! -d "${VENV_DIR}" ]; then
    log_info "가상환경 생성 중: ${VENV_DIR}"
    python${PYTHON_VERSION} -m venv "${VENV_DIR}"
    log_success "가상환경 생성 완료"
else
    log_info "가상환경 이미 존재: ${VENV_DIR}"
fi

# ==============================================
# 가상환경 활성화 및 기본 패키지 설치
# ==============================================

log_info "가상환경 패키지 설치 중..."
source "${VENV_DIR}/bin/activate"

# 기본 패키지 업그레이드
pip install --upgrade pip setuptools wheel

log_success "Python 설치 완료!"
log_info "Python: $(python --version)"
log_info "pip: $(pip --version)"
log_info "가상환경: ${VENV_DIR}"

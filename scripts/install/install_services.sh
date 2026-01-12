#!/bin/bash
# scripts/install/install_services.sh
# MCP 서비스 설치 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

log_info "MCP 서비스 설치 시작..."

# ==============================================
# 디렉토리 생성
# ==============================================

log_info "디렉토리 생성 중..."

# 데이터 디렉토리
ensure_directory "${DATA_DIR}" root:root 755
ensure_directory "${LOGS_DIR}" root:root 755
ensure_directory "${BACKUP_DIR}" root:root 755
ensure_directory "${UPLOAD_DIR}" root:root 755

# 서비스별 로그 디렉토리
ensure_directory "${LOG_MCP_HOST}" root:root 755
ensure_directory "${LOG_API_GATEWAY}" root:root 755
ensure_directory "${LOG_FRONTEND}" root:root 755

log_success "디렉토리 생성 완료"

# ==============================================
# Python 패키지 설치
# ==============================================

log_info "Python 패키지 설치 중..."

# 가상환경 확인
if [ ! -d "${VENV_DIR}" ]; then
    log_error "가상환경이 없습니다. install_python.sh를 먼저 실행하세요"
    exit 1
fi

# 가상환경 활성화
source "${VENV_DIR}/bin/activate"

# requirements.txt 위치 목록
REQUIREMENTS_FILES=(
    "${PROJECT_ROOT}/shared/requirements.txt"
    "${PROJECT_ROOT}/mcp-host/requirements.txt"
    "${PROJECT_ROOT}/api-gateway/requirements.txt"
    "${PROJECT_ROOT}/frontend/requirements.txt"
    "${PROJECT_ROOT}/mcp-servers/core/auth_server/requirements.txt"
    "${PROJECT_ROOT}/mcp-servers/core/document_server/requirements.txt"
    "${PROJECT_ROOT}/mcp-servers/core/search_server/requirements.txt"
    "${PROJECT_ROOT}/mcp-servers/core/audit_server/requirements.txt"
    "${PROJECT_ROOT}/mcp-servers/core/version_server/requirements.txt"
)

# 각 requirements.txt 설치
for REQ_FILE in "${REQUIREMENTS_FILES[@]}"; do
    if [ -f "$REQ_FILE" ]; then
        log_info "설치 중: $REQ_FILE"
        pip install -r "$REQ_FILE" || log_warning "일부 패키지 설치 실패: $REQ_FILE"
    else
        log_warning "파일 없음: $REQ_FILE"
    fi
done

# Frontend reflex 초기화
if [ -f "${PROJECT_ROOT}/frontend/rxconfig.py" ]; then
    log_info "Reflex 초기화 중..."
    cd "${PROJECT_ROOT}/frontend"
    
    if command_exists reflex; then
        reflex init || log_warning "Reflex 초기화 경고 (무시 가능)"
    fi
    
    cd "${PROJECT_ROOT}"
fi

log_success "Python 패키지 설치 완료"

# ==============================================
# Systemd 서비스 파일 생성
# ==============================================

log_info "Systemd 서비스 파일 생성 중..."

# MCP Host 서비스
cat > /etc/systemd/system/${SERVICE_MCP_HOST}.service << EOF
[Unit]
Description=MCP Host Service
Documentation=https://github.com/modelcontextprotocol/
After=network.target mariadb.service redis.service elasticsearch.service
Wants=mariadb.service redis.service elasticsearch.service

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_ROOT}/mcp-host
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONPATH=${PROJECT_ROOT}"
ExecStart=${VENV_DIR}/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:${LOG_MCP_HOST}/service.log
StandardError=append:${LOG_MCP_HOST}/error.log

# 리소스 제한
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

log_success "${SERVICE_MCP_HOST} 서비스 파일 생성"

# API Gateway 서비스
cat > /etc/systemd/system/${SERVICE_API_GATEWAY}.service << EOF
[Unit]
Description=MCP API Gateway
Documentation=https://github.com/modelcontextprotocol/
After=network.target ${SERVICE_MCP_HOST}.service
Wants=${SERVICE_MCP_HOST}.service

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_ROOT}/api-gateway
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONPATH=${PROJECT_ROOT}"
ExecStart=${VENV_DIR}/bin/uvicorn main:app --host 0.0.0.0 --port ${API_GATEWAY_PORT}
Restart=always
RestartSec=10
StandardOutput=append:${LOG_API_GATEWAY}/service.log
StandardError=append:${LOG_API_GATEWAY}/error.log

# 리소스 제한
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

log_success "${SERVICE_API_GATEWAY} 서비스 파일 생성"

# Frontend 서비스
cat > /etc/systemd/system/${SERVICE_FRONTEND}.service << EOF
[Unit]
Description=MCP Frontend (Reflex)
Documentation=https://reflex.dev/
After=network.target ${SERVICE_API_GATEWAY}.service
Wants=${SERVICE_API_GATEWAY}.service

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_ROOT}/frontend
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONPATH=${PROJECT_ROOT}"
ExecStart=${VENV_DIR}/bin/reflex run --env prod
Restart=always
RestartSec=10
StandardOutput=append:${LOG_FRONTEND}/service.log
StandardError=append:${LOG_FRONTEND}/error.log

# 리소스 제한
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

log_success "${SERVICE_FRONTEND} 서비스 파일 생성"

# Systemd 리로드
log_info "Systemd 리로드 중..."
systemctl daemon-reload

log_success "======================================"
log_success "  MCP 서비스 설치 완료"
log_success "======================================"
log_info "서비스 목록:"
log_info "  - ${SERVICE_MCP_HOST}"
log_info "  - ${SERVICE_API_GATEWAY}"
log_info "  - ${SERVICE_FRONTEND}"
log_info ""
log_info "서비스 관리:"
log_info "  sudo systemctl start ${SERVICE_MCP_HOST}"
log_info "  sudo systemctl status ${SERVICE_MCP_HOST}"
log_info "  sudo systemctl enable ${SERVICE_MCP_HOST}"

#!/bin/bash
# scripts/env/check_env.sh
# 환경 확인 스크립트

set -e

# 공통 설정 및 유틸리티 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

print_banner "환경 확인 시작"

OVERALL_STATUS=0

# ==============================================
# OS 확인
# ==============================================

check_os() {
    log_info "OS 확인 중..."
    
    if [ -f /etc/redhat-release ]; then
        OS_VERSION=$(cat /etc/redhat-release)
        log_success "OS: ${OS_VERSION}"
        
        # RHEL/Rocky/CentOS 8 확인
        if echo "$OS_VERSION" | grep -qE "release 8|release 9"; then
            log_success "지원되는 OS 버전입니다"
            return 0
        else
            log_warning "RHEL/Rocky/CentOS 8.x 이상 권장"
            return 0
        fi
    else
        log_error "RHEL 기반 시스템이 아닙니다"
        return 1
    fi
}

# ==============================================
# 권한 확인
# ==============================================

check_permissions() {
    log_info "권한 확인 중..."
    
    if [ "$EUID" -eq 0 ]; then
        log_success "root 권한 확인"
        return 0
    else
        log_error "root 권한이 필요합니다. sudo로 실행하세요"
        return 1
    fi
}

# ==============================================
# 디스크 공간 확인
# ==============================================

check_disk_space() {
    log_info "디스크 공간 확인 중..."
    
    local AVAILABLE_GB=$(get_disk_free_gb "${PROJECT_ROOT}")
    
    if [ "$AVAILABLE_GB" -lt "$MIN_DISK_SPACE_GB" ]; then
        log_error "디스크 공간 부족: ${AVAILABLE_GB}GB (최소 ${MIN_DISK_SPACE_GB}GB 필요)"
        return 1
    fi
    
    log_success "디스크 공간: ${AVAILABLE_GB}GB 사용 가능"
    return 0
}

# ==============================================
# 메모리 확인
# ==============================================

check_memory() {
    log_info "메모리 확인 중..."
    
    local TOTAL_MEMORY_GB=$(get_memory_gb)
    
    if [ "$TOTAL_MEMORY_GB" -lt "$MIN_MEMORY_GB" ]; then
        log_error "메모리 부족: ${TOTAL_MEMORY_GB}GB (최소 ${MIN_MEMORY_GB}GB 필요)"
        return 1
    elif [ "$TOTAL_MEMORY_GB" -lt "$RECOMMENDED_MEMORY_GB" ]; then
        log_warning "메모리: ${TOTAL_MEMORY_GB}GB (권장: ${RECOMMENDED_MEMORY_GB}GB)"
        return 0
    else
        log_success "메모리: ${TOTAL_MEMORY_GB}GB"
        return 0
    fi
}

# ==============================================
# 네트워크 확인
# ==============================================

check_network() {
    log_info "네트워크 확인 중..."
    
    # 인터넷 연결 확인
    if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
        log_success "인터넷 연결 확인"
    else
        log_warning "인터넷 연결 없음 (오프라인 설치 가능)"
    fi
    
    # 포트 사용 확인
    local PORTS=(
        "${MCP_HOST_PORT}:MCP Host"
        "${API_GATEWAY_PORT}:API Gateway"
        "${FRONTEND_PORT}:Frontend"
        "${DB_PORT}:MariaDB"
        "${REDIS_PORT}:Redis"
        "${ES_PORT}:Elasticsearch"
    )
    
    local PORT_CONFLICTS=0
    
    for PORT_INFO in "${PORTS[@]}"; do
        IFS=':' read -r PORT NAME <<< "$PORT_INFO"
        
        if is_port_in_use "$PORT"; then
            log_warning "포트 ${PORT} (${NAME})가 이미 사용 중입니다"
            PORT_CONFLICTS=$((PORT_CONFLICTS + 1))
        fi
    done
    
    if [ $PORT_CONFLICTS -eq 0 ]; then
        log_success "모든 필수 포트 사용 가능"
    fi
    
    return 0
}

# ==============================================
# 필수 패키지 확인
# ==============================================

check_packages() {
    log_info "필수 패키지 확인 중..."
    
    local REQUIRED_PACKAGES=(
        "curl"
        "wget"
        "git"
        "gcc"
        "make"
        "openssl-devel"
        "bzip2-devel"
        "libffi-devel"
        "zlib-devel"
        "readline-devel"
        "sqlite-devel"
    )
    
    local MISSING_PACKAGES=()
    
    for PKG in "${REQUIRED_PACKAGES[@]}"; do
        if ! is_package_installed "$PKG"; then
            MISSING_PACKAGES+=("$PKG")
        fi
    done
    
    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        log_warning "누락된 패키지: ${MISSING_PACKAGES[*]}"
        log_info "다음 명령으로 설치: sudo dnf install -y ${MISSING_PACKAGES[*]}"
        return 0
    else
        log_success "모든 필수 패키지 설치됨"
        return 0
    fi
}

# ==============================================
# SELinux 확인
# ==============================================

check_selinux() {
    log_info "SELinux 확인 중..."
    
    if command_exists getenforce; then
        local SELINUX_STATUS=$(getenforce)
        
        case "$SELINUX_STATUS" in
            Enforcing)
                log_warning "SELinux가 Enforcing 모드입니다. 권한 문제가 발생할 수 있습니다"
                log_info "필요시 Permissive 모드로 변경: sudo setenforce 0"
                ;;
            Permissive)
                log_info "SELinux: Permissive 모드"
                ;;
            Disabled)
                log_info "SELinux: 비활성화됨"
                ;;
        esac
    fi
    
    return 0
}

# ==============================================
# 방화벽 확인
# ==============================================

check_firewall() {
    log_info "방화벽 확인 중..."
    
    if systemctl is-active --quiet firewalld; then
        log_info "firewalld 실행 중"
        log_info "필요시 포트 개방:"
        echo "  sudo firewall-cmd --permanent --add-port=${MCP_HOST_PORT}/tcp"
        echo "  sudo firewall-cmd --permanent --add-port=${API_GATEWAY_PORT}/tcp"
        echo "  sudo firewall-cmd --permanent --add-port=${FRONTEND_PORT}/tcp"
        echo "  sudo firewall-cmd --reload"
    else
        log_info "firewalld 비활성화됨"
    fi
    
    return 0
}

# ==============================================
# 실행
# ==============================================

main() {
    echo ""
    
    # 각 체크 실행
    check_os || OVERALL_STATUS=1
    echo ""
    
    check_permissions || OVERALL_STATUS=1
    echo ""
    
    check_disk_space || OVERALL_STATUS=1
    echo ""
    
    check_memory || OVERALL_STATUS=1
    echo ""
    
    check_network
    echo ""
    
    check_packages
    echo ""
    
    check_selinux
    echo ""
    
    check_firewall
    echo ""
    
    # 결과 출력
    if [ $OVERALL_STATUS -eq 0 ]; then
        print_banner "환경 확인 성공!"
        log_success "모든 필수 요구사항을 충족했습니다"
    else
        print_banner "환경 확인 실패"
        log_error "일부 요구사항을 충족하지 못했습니다"
        log_info "문제를 해결한 후 다시 시도하세요"
    fi
    
    return $OVERALL_STATUS
}

# 스크립트 실행
main "$@"

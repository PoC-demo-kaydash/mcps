#!/bin/bash
# scripts/utils/common.sh
# 공통 유틸리티 함수

# ==============================================
# 서비스 관련 함수
# ==============================================

# 서비스 실행 확인
is_service_running() {
    local SERVICE=$1
    systemctl is-active --quiet "${SERVICE}"
}

# 서비스 활성화 확인
is_service_enabled() {
    local SERVICE=$1
    systemctl is-enabled --quiet "${SERVICE}"
}

# 서비스 대기 (타임아웃 포함)
wait_for_service() {
    local SERVICE=$1
    local TIMEOUT=${2:-30}
    local COUNT=0
    
    while [ $COUNT -lt $TIMEOUT ]; do
        if is_service_running "${SERVICE}"; then
            return 0
        fi
        
        sleep 1
        COUNT=$((COUNT + 1))
    done
    
    return 1
}

# ==============================================
# 네트워크 관련 함수
# ==============================================

# 포트 사용 확인
is_port_in_use() {
    local PORT=$1
    netstat -tuln 2>/dev/null | grep -q ":${PORT} " || \
    ss -tuln 2>/dev/null | grep -q ":${PORT} "
}

# URL 응답 대기
wait_for_url() {
    local URL=$1
    local TIMEOUT=${2:-30}
    local COUNT=0
    
    while [ $COUNT -lt $TIMEOUT ]; do
        if curl -s -f "${URL}" > /dev/null 2>&1; then
            return 0
        fi
        
        sleep 1
        COUNT=$((COUNT + 1))
    done
    
    return 1
}

# URL 헬스체크
check_url_health() {
    local URL=$1
    local EXPECTED_CODE=${2:-200}
    
    local HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${URL}" 2>/dev/null)
    
    if [ "$HTTP_CODE" = "$EXPECTED_CODE" ]; then
        return 0
    else
        return 1
    fi
}

# ==============================================
# 명령어 관련 함수
# ==============================================

# 명령어 존재 확인
command_exists() {
    command -v "$1" &> /dev/null
}

# 패키지 설치 확인 (RPM)
is_package_installed() {
    local PACKAGE=$1
    rpm -q "$PACKAGE" &> /dev/null
}

# ==============================================
# 파일/디렉토리 관련 함수
# ==============================================

# 파일 백업
backup_file() {
    local FILE=$1
    local BACKUP_SUFFIX=${2:-".backup.$(date +%Y%m%d_%H%M%S)"}
    
    if [ -f "${FILE}" ]; then
        cp "${FILE}" "${FILE}${BACKUP_SUFFIX}"
        return 0
    fi
    
    return 1
}

# 디렉토리 백업
backup_directory() {
    local DIR=$1
    local BACKUP_SUFFIX=${2:-".backup.$(date +%Y%m%d_%H%M%S)"}
    
    if [ -d "${DIR}" ]; then
        cp -r "${DIR}" "${DIR}${BACKUP_SUFFIX}"
        return 0
    fi
    
    return 1
}

# 안전한 디렉토리 생성
ensure_directory() {
    local DIR=$1
    local OWNER=${2:-}
    local PERMS=${3:-755}
    
    if [ ! -d "${DIR}" ]; then
        mkdir -p "${DIR}"
        chmod "${PERMS}" "${DIR}"
        
        if [ -n "$OWNER" ]; then
            chown "$OWNER" "${DIR}"
        fi
    fi
}

# ==============================================
# 시스템 정보 함수
# ==============================================

# OS 정보 가져오기
get_os_info() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$NAME $VERSION"
    elif [ -f /etc/redhat-release ]; then
        cat /etc/redhat-release
    else
        echo "Unknown"
    fi
}

# 메모리 크기 (GB)
get_memory_gb() {
    free -g | awk '/^Mem:/{print $2}'
}

# 디스크 여유 공간 (GB)
get_disk_free_gb() {
    local PATH=${1:-/}
    df -BG "$PATH" | tail -1 | awk '{print $4}' | sed 's/G//'
}

# CPU 코어 수
get_cpu_cores() {
    nproc
}

# ==============================================
# 문자열 처리 함수
# ==============================================

# 문자열 trim
trim() {
    local VAR="$*"
    VAR="${VAR#"${VAR%%[![:space:]]*}"}"
    VAR="${VAR%"${VAR##*[![:space:]]}"}"
    echo -n "$VAR"
}

# 소문자 변환
to_lower() {
    echo "$1" | tr '[:upper:]' '[:lower:]'
}

# 대문자 변환
to_upper() {
    echo "$1" | tr '[:lower:]' '[:upper:]'
}

# ==============================================
# 사용자 입력 함수
# ==============================================

# yes/no 확인
confirm() {
    local PROMPT=${1:-"계속하시겠습니까?"}
    local DEFAULT=${2:-"n"}
    
    if [ "$DEFAULT" = "y" ] || [ "$DEFAULT" = "Y" ]; then
        PROMPT="$PROMPT [Y/n]: "
    else
        PROMPT="$PROMPT [y/N]: "
    fi
    
    read -p "$PROMPT" -n 1 -r
    echo
    
    if [ "$DEFAULT" = "y" ] || [ "$DEFAULT" = "Y" ]; then
        [[ ! $REPLY =~ ^[Nn]$ ]]
    else
        [[ $REPLY =~ ^[Yy]$ ]]
    fi
}

# 입력 대기 (타임아웃)
read_with_timeout() {
    local PROMPT=$1
    local TIMEOUT=${2:-10}
    local DEFAULT=${3:-}
    
    read -t "$TIMEOUT" -p "$PROMPT" INPUT || INPUT="$DEFAULT"
    echo "$INPUT"
}

# ==============================================
# 프로세스 관련 함수
# ==============================================

# PID로 프로세스 존재 확인
is_process_running() {
    local PID=$1
    kill -0 "$PID" 2>/dev/null
}

# 프로세스 이름으로 PID 찾기
get_pid_by_name() {
    local PROCESS_NAME=$1
    pgrep -f "$PROCESS_NAME" | head -1
}

# 프로세스 종료 대기
wait_for_process_exit() {
    local PID=$1
    local TIMEOUT=${2:-30}
    local COUNT=0
    
    while [ $COUNT -lt $TIMEOUT ]; do
        if ! is_process_running "$PID"; then
            return 0
        fi
        
        sleep 1
        COUNT=$((COUNT + 1))
    done
    
    return 1
}

# ==============================================
# 에러 핸들링
# ==============================================

# 에러 시 종료
die() {
    echo -e "${COLOR_RED}[FATAL]${COLOR_NC} $1" >&2
    exit "${2:-1}"
}

# 명령 실행 및 에러 처리
run_command() {
    local DESCRIPTION=$1
    shift
    
    if [ -n "$DESCRIPTION" ]; then
        echo "실행 중: $DESCRIPTION"
    fi
    
    if "$@"; then
        return 0
    else
        local EXIT_CODE=$?
        echo "실패: $DESCRIPTION (종료 코드: $EXIT_CODE)" >&2
        return $EXIT_CODE
    fi
}

# ==============================================
# 버전 비교
# ==============================================

# 버전 비교 (version1 >= version2이면 0 반환)
version_ge() {
    local VER1=$1
    local VER2=$2
    
    # 버전 문자열을 비교
    printf '%s\n%s\n' "$VER2" "$VER1" | sort -V -C
}

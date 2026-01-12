#!/bin/bash
# scripts/utils/logger.sh
# 로깅 유틸리티

# 색상 로드
if [ -f "$(dirname "${BASH_SOURCE[0]}")/colors.sh" ]; then
    source "$(dirname "${BASH_SOURCE[0]}")/colors.sh"
else
    # Fallback 색상
    COLOR_RED='\033[0;31m'
    COLOR_GREEN='\033[0;32m'
    COLOR_YELLOW='\033[1;33m'
    COLOR_BLUE='\033[0;34m'
    COLOR_NC='\033[0m'
fi

# 로그 레벨
export LOG_LEVEL_DEBUG=0
export LOG_LEVEL_INFO=1
export LOG_LEVEL_WARNING=2
export LOG_LEVEL_ERROR=3

# 현재 로그 레벨 (기본: INFO)
CURRENT_LOG_LEVEL=${LOG_LEVEL:-$LOG_LEVEL_INFO}

# 로그 함수
log_debug() {
    if [ "$CURRENT_LOG_LEVEL" -le "$LOG_LEVEL_DEBUG" ]; then
        echo -e "${COLOR_CYAN}[DEBUG]${COLOR_NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    fi
}

log_info() {
    if [ "$CURRENT_LOG_LEVEL" -le "$LOG_LEVEL_INFO" ]; then
        echo -e "${COLOR_BLUE}[INFO]${COLOR_NC} $1"
    fi
}

log_success() {
    if [ "$CURRENT_LOG_LEVEL" -le "$LOG_LEVEL_INFO" ]; then
        echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_NC} $1"
    fi
}

log_warning() {
    if [ "$CURRENT_LOG_LEVEL" -le "$LOG_LEVEL_WARNING" ]; then
        echo -e "${COLOR_YELLOW}[WARNING]${COLOR_NC} $1" >&2
    fi
}

log_error() {
    if [ "$CURRENT_LOG_LEVEL" -le "$LOG_LEVEL_ERROR" ]; then
        echo -e "${COLOR_RED}[ERROR]${COLOR_NC} $1" >&2
    fi
}

# 로그 파일에도 기록
log_to_file() {
    local LOG_FILE=$1
    local MESSAGE=$2
    
    if [ -n "$LOG_FILE" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $MESSAGE" >> "$LOG_FILE"
    fi
}

# 진행률 표시
show_progress() {
    local CURRENT=$1
    local TOTAL=$2
    local PERCENT=$((CURRENT * 100 / TOTAL))
    local FILLED=$((PERCENT / 2))
    local EMPTY=$((50 - FILLED))
    
    printf "\r진행률: [%s%s] %d%%" \
        "$(printf '#%.0s' $(seq 1 $FILLED))" \
        "$(printf ' %.0s' $(seq 1 $EMPTY))" \
        "$PERCENT"
}

# 스피너 애니메이션
show_spinner() {
    local PID=$1
    local DELAY=0.1
    local SPINSTR='|/-\'
    
    while ps -p $PID > /dev/null 2>&1; do
        local TEMP=${SPINSTR#?}
        printf " [%c]  " "$SPINSTR"
        local SPINSTR=$TEMP${SPINSTR%"$TEMP"}
        sleep $DELAY
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# 배너 출력
print_banner() {
    local MESSAGE=$1
    local WIDTH=60
    
    echo ""
    echo -e "${COLOR_BLUE}$(printf '=%.0s' $(seq 1 $WIDTH))${COLOR_NC}"
    echo -e "${COLOR_BLUE}  $MESSAGE${COLOR_NC}"
    echo -e "${COLOR_BLUE}$(printf '=%.0s' $(seq 1 $WIDTH))${COLOR_NC}"
    echo ""
}

# 섹션 헤더
print_section() {
    local MESSAGE=$1
    echo ""
    echo -e "${COLOR_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_NC}"
    echo -e "${COLOR_CYAN}  $MESSAGE${COLOR_NC}"
    echo -e "${COLOR_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_NC}"
    echo ""
}

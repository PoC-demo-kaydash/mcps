#!/bin/bash
# scripts/manage/logs.sh
# 로그 조회 스크립트

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"

# 사용법
usage() {
    echo "Usage: $0 [service] [options]"
    echo ""
    echo "Services:"
    echo "  mcp-host        MCP Host 로그"
    echo "  api-gateway     API Gateway 로그"
    echo "  frontend        Frontend 로그"
    echo "  mariadb         MariaDB 로그"
    echo "  redis           Redis 로그"
    echo "  elasticsearch   Elasticsearch 로그"
    echo ""
    echo "Options:"
    echo "  -f, --follow    실시간 로그 추적"
    echo "  -n NUM          최근 NUM 줄 표시 (기본: 50)"
    echo "  -e, --error     에러 로그만 표시"
}

if [ $# -eq 0 ]; then
    usage
    exit 1
fi

SERVICE=$1
shift

FOLLOW=false
LINES=50
ERROR_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n)
            LINES=$2
            shift 2
            ;;
        -e|--error)
            ERROR_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# 로그 파일 결정
case ${SERVICE} in
    mcp-host)
        LOG_FILE="${LOG_MCP_HOST}/$([ "$ERROR_ONLY" = true ] && echo 'error.log' || echo 'service.log')"
        ;;
    api-gateway)
        LOG_FILE="${LOG_API_GATEWAY}/$([ "$ERROR_ONLY" = true ] && echo 'error.log' || echo 'service.log')"
        ;;
    frontend)
        LOG_FILE="${LOG_FRONTEND}/$([ "$ERROR_ONLY" = true ] && echo 'error.log' || echo 'service.log')"
        ;;
    mariadb)
        LOG_FILE="/var/log/mariadb/mariadb.log"
        ;;
    redis)
        LOG_FILE="/var/log/redis/redis.log"
        ;;
    elasticsearch)
        LOG_FILE="/var/log/elasticsearch/${ES_CLUSTER_NAME}.log"
        ;;
    *)
        echo "Unknown service: ${SERVICE}"
        usage
        exit 1
        ;;
esac

if [ ! -f "${LOG_FILE}" ]; then
    log_error "로그 파일을 찾을 수 없습니다: ${LOG_FILE}"
    exit 1
fi

log_info "로그 파일: ${LOG_FILE}"
echo ""

if [ "${FOLLOW}" = true ]; then
    tail -f -n ${LINES} "${LOG_FILE}"
else
    tail -n ${LINES} "${LOG_FILE}"
fi

#!/bin/bash
# scripts/install/install_redis.sh
# Redis 설치 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

log_info "Redis 설치 시작..."

# ==============================================
# Redis 설치
# ==============================================

if systemctl is-active --quiet redis; then
    log_info "Redis 이미 실행 중"
    SKIP_INSTALL=true
elif is_package_installed "redis"; then
    log_info "Redis 이미 설치됨"
    SKIP_INSTALL=true
else
    SKIP_INSTALL=false
fi

if [ "$SKIP_INSTALL" = false ]; then
    log_info "EPEL 저장소 활성화 중..."
    dnf install -y epel-release
    
    log_info "Redis 설치 중..."
    dnf install -y redis
    
    log_success "Redis 설치 완료"
fi

# ==============================================
# 서비스 시작
# ==============================================

if ! systemctl is-enabled --quiet redis; then
    log_info "Redis 서비스 활성화 중..."
    systemctl enable redis
fi

if ! systemctl is-active --quiet redis; then
    log_info "Redis 시작 중..."
    systemctl start redis
    sleep 2
fi

if systemctl is-active --quiet redis; then
    log_success "Redis 실행 중"
else
    log_error "Redis 시작 실패"
    exit 1
fi

# ==============================================
# 설정
# ==============================================

log_info "Redis 설정 중..."

# 기존 설정 백업
if [ -f /etc/redis/redis.conf ]; then
    backup_file /etc/redis/redis.conf
fi

# Redis 설정
cat > /etc/redis/redis.conf << EOF
# ==============================================
# 네트워크
# ==============================================
bind 127.0.0.1
port ${REDIS_PORT}
protected-mode yes
tcp-backlog 511
timeout 0
tcp-keepalive 300

# ==============================================
# 일반 설정
# ==============================================
daemonize no
supervised systemd
pidfile /var/run/redis/redis.pid
loglevel notice
logfile /var/log/redis/redis.log
databases 16

# ==============================================
# 스냅샷
# ==============================================
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# ==============================================
# 메모리 관리
# ==============================================
maxmemory 1gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# ==============================================
# AOF 영속성
# ==============================================
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# ==============================================
# 보안
# ==============================================
# requirepass ${REDIS_PASSWORD}

# ==============================================
# 성능
# ==============================================
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 0
EOF

# Redis 재시작
log_info "Redis 재시작 중..."
systemctl restart redis
sleep 2

if systemctl is-active --quiet redis; then
    log_success "Redis 설정 완료"
else
    log_error "Redis 재시작 실패"
    exit 1
fi

# ==============================================
# 연결 테스트
# ==============================================

log_info "Redis 연결 테스트 중..."

if redis-cli ping > /dev/null 2>&1; then
    log_success "Redis 연결 성공"
else
    log_error "Redis 연결 실패"
    exit 1
fi

# ==============================================
# 설치 정보 출력
# ==============================================

REDIS_VERSION=$(redis-server --version | awk '{print $3}' | cut -d'=' -f2)

log_success "======================================"
log_success "  Redis 설치 완료"
log_success "======================================"
log_info "버전: ${REDIS_VERSION}"
log_info "포트: ${REDIS_PORT}"
log_info "상태: $(systemctl is-active redis)"
log_info ""
log_info "연결 테스트:"
log_info "  redis-cli ping"

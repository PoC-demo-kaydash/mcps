#!/bin/bash
# scripts/install/install_database.sh
# MariaDB 설치 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

log_info "MariaDB 설치 시작..."

# ==============================================
# MariaDB 설치 확인
# ==============================================

if systemctl is-active --quiet mariadb; then
    log_info "MariaDB 이미 실행 중"
    SKIP_INSTALL=true
elif is_package_installed "MariaDB-server"; then
    log_info "MariaDB 이미 설치됨"
    SKIP_INSTALL=true
else
    SKIP_INSTALL=false
fi

if [ "$SKIP_INSTALL" = false ]; then
    log_info "MariaDB 저장소 추가 중..."
    
    # MariaDB 10.11 저장소 추가
    cat > /etc/yum.repos.d/mariadb.repo << 'EOF'
[mariadb]
name = MariaDB
baseurl = https://rpm.mariadb.org/10.11/rhel/$releasever/$basearch
module_hotfixes = 1
gpgkey = https://rpm.mariadb.org/RPM-GPG-KEY-MariaDB
gpgcheck = 1
enabled = 1
EOF
    
    log_info "MariaDB 설치 중..."
    dnf install -y MariaDB-server MariaDB-client
    
    log_success "MariaDB 설치 완료"
fi

# ==============================================
# 서비스 시작
# ==============================================

if ! systemctl is-enabled --quiet mariadb; then
    log_info "MariaDB 서비스 활성화 중..."
    systemctl enable mariadb
fi

if ! systemctl is-active --quiet mariadb; then
    log_info "MariaDB 시작 중..."
    systemctl start mariadb
    sleep 3
fi

if systemctl is-active --quiet mariadb; then
    log_success "MariaDB 실행 중"
else
    log_error "MariaDB 시작 실패"
    exit 1
fi

# ==============================================
# 보안 설정
# ==============================================

log_info "MariaDB 보안 설정 중..."

# Root 비밀번호 설정 및 보안 강화
mysql -u root << EOF
-- Root 비밀번호 설정
ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_ROOT_PASSWORD}';

-- 익명 사용자 삭제
DELETE FROM mysql.user WHERE User='';

-- 원격 root 로그인 제한
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');

-- 테스트 데이터베이스 삭제
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';

-- 권한 적용
FLUSH PRIVILEGES;
EOF

log_success "MariaDB 보안 설정 완료"

# ==============================================
# 성능 튜닝
# ==============================================

log_info "MariaDB 설정 튜닝 중..."

# 기존 설정 백업
if [ -f /etc/my.cnf.d/mcps.cnf ]; then
    backup_file /etc/my.cnf.d/mcps.cnf
fi

# 튜닝 설정 파일 생성
cat > /etc/my.cnf.d/mcps.cnf << 'EOF'
[mysqld]
# ==============================================
# 문자셋
# ==============================================
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# ==============================================
# 연결 설정
# ==============================================
max_connections = 500
max_connect_errors = 100
connect_timeout = 10

# ==============================================
# InnoDB 설정
# ==============================================
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
innodb_log_buffer_size = 16M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT
innodb_file_per_table = 1

# ==============================================
# 쿼리 캐시 (MariaDB 10.x에서는 deprecated)
# ==============================================
query_cache_size = 0
query_cache_type = 0

# ==============================================
# 로그 설정
# ==============================================
log_error = /var/log/mariadb/error.log
slow_query_log = 1
slow_query_log_file = /var/log/mariadb/slow.log
long_query_time = 2
log_queries_not_using_indexes = 0

# ==============================================
# 기타 설정
# ==============================================
tmp_table_size = 64M
max_heap_table_size = 64M
thread_cache_size = 50
table_open_cache = 4000

[client]
default-character-set = utf8mb4

[mysql]
default-character-set = utf8mb4
EOF

# 로그 디렉토리 생성
ensure_directory /var/log/mariadb mysql:mysql 755

# MariaDB 재시작
log_info "MariaDB 재시작 중..."
systemctl restart mariadb
sleep 3

if systemctl is-active --quiet mariadb; then
    log_success "MariaDB 설정 완료"
else
    log_error "MariaDB 재시작 실패"
    exit 1
fi

# ==============================================
# 설치 정보 출력
# ==============================================

MARIADB_VERSION=$(mysql -V | awk '{print $5}' | sed 's/,//')

log_success "======================================"
log_success "  MariaDB 설치 완료"
log_success "======================================"
log_info "버전: ${MARIADB_VERSION}"
log_info "포트: ${DB_PORT}"
log_info "상태: $(systemctl is-active mariadb)"
log_info ""
log_info "연결 테스트:"
log_info "  mysql -u root -p'${DB_ROOT_PASSWORD}'"

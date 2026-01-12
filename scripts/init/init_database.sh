#!/bin/bash
# scripts/init/init_database.sh
# Database 초기화 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

log_info "Database 초기화 시작..."

# ==============================================
# MariaDB 실행 확인
# ==============================================

if ! systemctl is-active --quiet mariadb; then
    log_error "MariaDB가 실행 중이 아닙니다"
    log_info "MariaDB 시작: sudo systemctl start mariadb"
    exit 1
fi

log_success "MariaDB 실행 중 확인"

# ==============================================
# Database 및 사용자 생성
# ==============================================

log_info "Database 및 사용자 생성 중..."

mysql -u root -p"${DB_ROOT_PASSWORD}" << EOF
-- Database 생성
CREATE DATABASE IF NOT EXISTS ${DB_NAME}
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 사용자 생성
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';

-- 권한 부여
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';

-- 권한 적용
FLUSH PRIVILEGES;
EOF

log_success "Database 및 사용자 생성 완료"

# ==============================================
# Python 스크립트로 스키마 생성
# ==============================================

log_info "Python 스크립트로 스키마 초기화 중..."

# 가상환경 활성화
if [ -f "${VENV_DIR}/bin/activate" ]; then
    source "${VENV_DIR}/bin/activate"
else
    log_error "가상환경을 찾을 수 없습니다: ${VENV_DIR}"
    exit 1
fi

# init_database.py 실행
if [ -f "${SCRIPTS_DIR}/init_database.py" ]; then
    cd "${SCRIPTS_DIR}"
    
    if python init_database.py; then
        log_success "스키마 초기화 완료"
    else
        log_error "init_database.py 실행 실패"
        exit 1
    fi
else
    log_warning "init_database.py를 찾을 수 없습니다"
    log_info "수동으로 SQL 파일 실행:"
    
    # SQL 파일 직접 실행 (대체 방법)
    SQL_FILES=(
        "${DB_DATA_DIR}/schema.sql"
        "${DB_DATA_DIR}/indexes.sql"
        "${DB_DATA_DIR}/triggers.sql"
        "${DB_DATA_DIR}/procedures.sql"
        "${DB_DATA_DIR}/views.sql"
    )
    
    for SQL_FILE in "${SQL_FILES[@]}"; do
        if [ -f "$SQL_FILE" ]; then
            log_info "실행 중: $SQL_FILE"
            mysql -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} < "$SQL_FILE" || log_warning "실행 실패: $SQL_FILE"
        else
            log_warning "파일 없음: $SQL_FILE"
        fi
    done
fi

# ==============================================
# 초기 데이터 (seed_data.sql)
# ==============================================

log_info "초기 데이터 생성 중..."

if [ -f "${DB_DATA_DIR}/seed_data.sql" ]; then
    mysql -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} < "${DB_DATA_DIR}/seed_data.sql"
    log_success "초기 데이터 생성 완료"
else
    log_warning "seed_data.sql을 찾을 수 없습니다"
fi

# ==============================================
# 테이블 확인
# ==============================================

log_info "생성된 테이블 확인 중..."

TABLES=$(mysql -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} -e "SHOW TABLES;" -s --skip-column-names)

if [ -n "$TABLES" ]; then
    log_success "생성된 테이블:"
    echo "$TABLES" | while read TABLE; do
        log_info "  - $TABLE"
    done
else
    log_warning "생성된 테이블이 없습니다"
fi

log_success "======================================"
log_success "  Database 초기화 완료"
log_success "======================================"
log_info "Database: ${DB_NAME}"
log_info "User: ${DB_USER}"
log_info ""
log_info "연결 테스트:"
log_info "  mysql -u ${DB_USER} -p'${DB_PASSWORD}' ${DB_NAME}"

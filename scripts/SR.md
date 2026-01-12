# Scripts 전체 가이드

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/scripts/`  
**목적**: 시스템 설치, 실행, 관리 스크립트 전체 가이드

***

## 목차

1. [개요](#1-개요)
2. [스크립트 구조](#2-스크립트-구조)
3. [환경 설정 스크립트](#3-환경-설정-스크립트)
4. [설치 스크립트](#4-설치-스크립트)
5. [초기화 스크립트](#5-초기화-스크립트)
6. [실행 스크립트](#6-실행-스크립트)
7. [관리 스크립트](#7-관리-스크립트)
8. [헬스체크 스크립트](#8-헬스체크-스크립트)
9. [백업 및 복구](#9-백업-및-복구)
10. [유틸리티 스크립트](#10-유틸리티-스크립트)

***

## 1. 개요

### 1.1 스크립트 목적

```
┌─────────────────────────────────────────┐
│           스크립트 계층 구조             │
├─────────────────────────────────────────┤
│                                          │
│  [환경 설정]                             │
│    └─ check_env.sh                      │
│                                          │
│  [설치]                                  │
│    ├─ setup.sh (마스터)                 │
│    ├─ install_python.sh                 │
│    ├─ install_database.sh               │
│    └─ install_services.sh               │
│                                          │
│  [초기화]                                │
│    ├─ init_database.sh                  │
│    ├─ init_elasticsearch.sh             │
│    └─ init_data.sh                      │
│                                          │
│  [실행]                                  │
│    ├─ start_all.sh                      │
│    ├─ stop_all.sh                       │
│    └─ restart_all.sh                    │
│                                          │
│  [관리]                                  │
│    ├─ status.sh                         │
│    ├─ logs.sh                           │
│    └─ cleanup.sh                        │
│                                          │
│  [백업/복구]                             │
│    ├─ backup.sh                         │
│    └─ restore.sh                        │
│                                          │
└─────────────────────────────────────────┘
```

### 1.2 주요 특징

| 특징 | 설명 |
|------|------|
| **멱등성** | 여러 번 실행해도 같은 결과 |
| **에러 처리** | 모든 단계에서 에러 체크 |
| **로깅** | 상세한 로그 기록 |
| **롤백** | 실패 시 이전 상태로 복구 |
| **검증** | 설치/실행 후 검증 |

### 1.3 실행 환경

```yaml
OS: RHEL 8.x
Shell: Bash 4.2+
User: root 또는 sudo 권한
Python: 3.11+
```

***

## 2. 스크립트 구조

```
scripts/
├── README.md                    # 스크립트 사용 가이드
├── config.sh                    # 공통 설정
│
├── env/                         # 환경 설정
│   ├── check_env.sh            # 환경 확인
│   └── setup_env.sh            # 환경 변수 설정
│
├── install/                     # 설치
│   ├── setup.sh                # 마스터 설치 스크립트
│   ├── install_python.sh       # Python 설치
│   ├── install_database.sh     # Database 설치
│   ├── install_redis.sh        # Redis 설치
│   ├── install_elasticsearch.sh # Elasticsearch 설치
│   └── install_services.sh     # 서비스 설치
│
├── init/                        # 초기화
│   ├── init_all.sh             # 전체 초기화
│   ├── init_database.sh        # Database 초기화
│   ├── init_elasticsearch.sh   # Elasticsearch 초기화
│   └── init_data.sh            # 초기 데이터
│
├── control/                     # 실행 제어
│   ├── start_all.sh            # 전체 시작
│   ├── stop_all.sh             # 전체 중지
│   ├── restart_all.sh          # 전체 재시작
│   ├── start_service.sh        # 개별 서비스 시작
│   └── stop_service.sh         # 개별 서비스 중지
│
├── manage/                      # 관리
│   ├── status.sh               # 상태 확인
│   ├── logs.sh                 # 로그 조회
│   ├── cleanup.sh              # 정리
│   └── update.sh               # 업데이트
│
├── backup/                      # 백업/복구
│   ├── backup.sh               # 백업
│   ├── restore.sh              # 복구
│   └── backup_config.sh        # 백업 설정
│
├── health/                      # 헬스체크
│   ├── healthcheck.sh          # 전체 헬스체크
│   ├── check_database.sh       # Database 체크
│   ├── check_services.sh       # 서비스 체크
│   └── check_connectivity.sh   # 연결 체크
│
└── utils/                       # 유틸리티
    ├── logger.sh               # 로깅 함수
    ├── colors.sh               # 색상 출력
    └── common.sh               # 공통 함수
```

***

## 3. 환경 설정 스크립트

### 3.1 config.sh (공통 설정)

```bash
#!/bin/bash
# scripts/config.sh
# 공통 설정 파일

# ==============================================
# 프로젝트 경로
# ==============================================

export PROJECT_ROOT="/app/poc/mcps"
export SCRIPTS_DIR="${PROJECT_ROOT}/scripts"
export DATA_DIR="${PROJECT_ROOT}/data"
export LOGS_DIR="${DATA_DIR}/logs"
export BACKUP_DIR="${DATA_DIR}/backups"

# ==============================================
# Python 설정
# ==============================================

export PYTHON_VERSION="3.11"
export VENV_DIR="${PROJECT_ROOT}/venv"

# ==============================================
# Database 설정
# ==============================================

export DB_HOST="localhost"
export DB_PORT="3306"
export DB_NAME="mcps_db"
export DB_USER="mcps_user"
export DB_PASSWORD="CHANGE_ME"
export DB_ROOT_PASSWORD="CHANGE_ME"

# ==============================================
# Redis 설정
# ==============================================

export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_PASSWORD=""

# ==============================================
# Elasticsearch 설정
# ==============================================

export ES_HOST="localhost"
export ES_PORT="9200"
export ES_CLUSTER_NAME="mcps-cluster"

# ==============================================
# 서비스 포트
# ==============================================

export MCP_HOST_PORT="8000"
export API_GATEWAY_PORT="8080"
export FRONTEND_PORT="3000"

# ==============================================
# 로그 설정
# ==============================================

export LOG_LEVEL="INFO"
export LOG_RETENTION_DAYS="30"

# ==============================================
# 백업 설정
# ==============================================

export BACKUP_RETENTION_DAYS="7"
export BACKUP_COMPRESS="true"

# ==============================================
# 색상 코드
# ==============================================

export COLOR_RED='\033[0;31m'
export COLOR_GREEN='\033[0;32m'
export COLOR_YELLOW='\033[1;33m'
export COLOR_BLUE='\033[0;34m'
export COLOR_NC='\033[0m' # No Color
```

### 3.2 check_env.sh (환경 확인)

```bash
#!/bin/bash
# scripts/env/check_env.sh
# 환경 확인 스크립트

set -e

# 공통 설정 로드
source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "환경 확인 시작..."

# ==============================================
# OS 확인
# ==============================================

check_os() {
    log_info "OS 확인 중..."
    
    if [ -f /etc/redhat-release ]; then
        OS_VERSION=$(cat /etc/redhat-release)
        log_success "OS: ${OS_VERSION}"
        
        if [[ ! "$OS_VERSION" =~ "Red Hat Enterprise Linux" ]] && [[ ! "$OS_VERSION" =~ "Rocky Linux" ]]; then
            log_warning "지원되지 않는 OS입니다. RHEL 8 권장"
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
    
    if [ "$EUID" -ne 0 ]; then
        log_error "root 권한이 필요합니다. sudo로 실행하세요"
        return 1
    fi
    
    log_success "권한 확인 완료"
}

# ==============================================
# 디스크 공간 확인
# ==============================================

check_disk_space() {
    log_info "디스크 공간 확인 중..."
    
    REQUIRED_SPACE_GB=20
    AVAILABLE_SPACE_GB=$(df -BG ${PROJECT_ROOT} | tail -1 | awk '{print $4}' | sed 's/G//')
    
    if [ "$AVAILABLE_SPACE_GB" -lt "$REQUIRED_SPACE_GB" ]; then
        log_error "디스크 공간 부족: ${AVAILABLE_SPACE_GB}GB (최소 ${REQUIRED_SPACE_GB}GB 필요)"
        return 1
    fi
    
    log_success "디스크 공간: ${AVAILABLE_SPACE_GB}GB"
}

# ==============================================
# 메모리 확인
# ==============================================

check_memory() {
    log_info "메모리 확인 중..."
    
    REQUIRED_MEMORY_GB=8
    TOTAL_MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    
    if [ "$TOTAL_MEMORY_GB" -lt "$REQUIRED_MEMORY_GB" ]; then
        log_warning "메모리 부족: ${TOTAL_MEMORY_GB}GB (권장: ${REQUIRED_MEMORY_GB}GB)"
    else
        log_success "메모리: ${TOTAL_MEMORY_GB}GB"
    fi
}

# ==============================================
# 네트워크 확인
# ==============================================

check_network() {
    log_info "네트워크 확인 중..."
    
    # 인터넷 연결 확인
    if ping -c 1 8.8.8.8 &> /dev/null; then
        log_success "인터넷 연결 확인"
    else
        log_warning "인터넷 연결 없음 (오프라인 설치 가능)"
    fi
    
    # 포트 사용 확인
    PORTS=(${MCP_HOST_PORT} ${API_GATEWAY_PORT} ${FRONTEND_PORT} ${DB_PORT} ${REDIS_PORT} ${ES_PORT})
    
    for PORT in "${PORTS[@]}"; do
        if netstat -tuln | grep -q ":${PORT} "; then
            log_warning "포트 ${PORT}가 이미 사용 중입니다"
        fi
    done
}

# ==============================================
# 필수 패키지 확인
# ==============================================

check_packages() {
    log_info "필수 패키지 확인 중..."
    
    REQUIRED_PACKAGES=(
        "curl"
        "wget"
        "git"
        "gcc"
        "make"
        "openssl-devel"
        "bzip2-devel"
        "libffi-devel"
        "zlib-devel"
    )
    
    MISSING_PACKAGES=()
    
    for PKG in "${REQUIRED_PACKAGES[@]}"; do
        if ! rpm -q "$PKG" &> /dev/null; then
            MISSING_PACKAGES+=("$PKG")
        fi
    done
    
    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        log_warning "누락된 패키지: ${MISSING_PACKAGES[*]}"
        log_info "다음 명령으로 설치: sudo dnf install -y ${MISSING_PACKAGES[*]}"
    else
        log_success "모든 필수 패키지 설치됨"
    fi
}

# ==============================================
# 실행
# ==============================================

main() {
    check_os || exit 1
    check_permissions || exit 1
    check_disk_space || exit 1
    check_memory
    check_network
    check_packages
    
    log_success "환경 확인 완료!"
}

main "$@"
```

***

## 4. 설치 스크립트

### 4.1 setup.sh (마스터 설치)

```bash
#!/bin/bash
# scripts/install/setup.sh
# 마스터 설치 스크립트

set -e

# 공통 설정 로드
source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "=========================================="
log_info "  MCP 문서 관리 시스템 설치 시작"
log_info "=========================================="

# ==============================================
# 환경 확인
# ==============================================

log_info "[1/7] 환경 확인..."
bash "${SCRIPTS_DIR}/env/check_env.sh" || {
    log_error "환경 확인 실패"
    exit 1
}

# ==============================================
# Python 설치
# ==============================================

log_info "[2/7] Python 설치..."
bash "${SCRIPTS_DIR}/install/install_python.sh" || {
    log_error "Python 설치 실패"
    exit 1
}

# ==============================================
# Database 설치
# ==============================================

log_info "[3/7] Database 설치..."
bash "${SCRIPTS_DIR}/install/install_database.sh" || {
    log_error "Database 설치 실패"
    exit 1
}

# ==============================================
# Redis 설치
# ==============================================

log_info "[4/7] Redis 설치..."
bash "${SCRIPTS_DIR}/install/install_redis.sh" || {
    log_error "Redis 설치 실패"
    exit 1
}

# ==============================================
# Elasticsearch 설치
# ==============================================

log_info "[5/7] Elasticsearch 설치..."
bash "${SCRIPTS_DIR}/install/install_elasticsearch.sh" || {
    log_error "Elasticsearch 설치 실패"
    exit 1
}

# ==============================================
# 서비스 설치
# ==============================================

log_info "[6/7] 서비스 설치..."
bash "${SCRIPTS_DIR}/install/install_services.sh" || {
    log_error "서비스 설치 실패"
    exit 1
}

# ==============================================
# 초기화
# ==============================================

log_info "[7/7] 시스템 초기화..."
bash "${SCRIPTS_DIR}/init/init_all.sh" || {
    log_error "초기화 실패"
    exit 1
}

# ==============================================
# 완료
# ==============================================

log_success "=========================================="
log_success "  설치 완료!"
log_success "=========================================="
log_info ""
log_info "다음 명령으로 시스템을 시작하세요:"
log_info "  sudo bash ${SCRIPTS_DIR}/control/start_all.sh"
log_info ""
```

### 4.2 install_python.sh (Python 설치)

```bash
#!/bin/bash
# scripts/install/install_python.sh
# Python 설치 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "Python ${PYTHON_VERSION} 설치 시작..."

# ==============================================
# Python 설치 확인
# ==============================================

if command -v python${PYTHON_VERSION} &> /dev/null; then
    INSTALLED_VERSION=$(python${PYTHON_VERSION} --version | awk '{print $2}')
    log_info "Python ${INSTALLED_VERSION} 이미 설치됨"
else
    log_info "Python ${PYTHON_VERSION} 설치 중..."
    
    # RHEL 8에서는 dnf로 설치
    dnf install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-devel python${PYTHON_VERSION}-pip
    
    log_success "Python ${PYTHON_VERSION} 설치 완료"
fi

# ==============================================
# pip 업그레이드
# ==============================================

log_info "pip 업그레이드..."
python${PYTHON_VERSION} -m pip install --upgrade pip

# ==============================================
# 가상환경 생성
# ==============================================

if [ ! -d "${VENV_DIR}" ]; then
    log_info "가상환경 생성..."
    python${PYTHON_VERSION} -m venv "${VENV_DIR}"
    log_success "가상환경 생성 완료: ${VENV_DIR}"
else
    log_info "가상환경 이미 존재: ${VENV_DIR}"
fi

# ==============================================
# 가상환경 활성화 및 패키지 설치
# ==============================================

log_info "Python 패키지 설치..."
source "${VENV_DIR}/bin/activate"

# 공통 패키지
pip install --upgrade pip setuptools wheel

# 프로젝트별 패키지 설치는 각 서비스 설치 스크립트에서 수행

log_success "Python 설치 완료"
```

### 4.3 install_database.sh (Database 설치)

```bash
#!/bin/bash
# scripts/install/install_database.sh
# MariaDB 설치 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "MariaDB 설치 시작..."

# ==============================================
# MariaDB 설치
# ==============================================

if systemctl is-active --quiet mariadb; then
    log_info "MariaDB 이미 실행 중"
else
    log_info "MariaDB 설치 중..."
    
    # MariaDB 10.11 저장소 추가
    cat > /etc/yum.repos.d/mariadb.repo << EOF
[mariadb]
name = MariaDB
baseurl = https://rpm.mariadb.org/10.11/rhel/8/x86_64/
gpgkey = https://rpm.mariadb.org/RPM-GPG-KEY-MariaDB
gpgcheck = 1
enabled = 1
EOF
    
    # 설치
    dnf install -y MariaDB-server MariaDB-client
    
    # 서비스 시작
    systemctl enable mariadb
    systemctl start mariadb
    
    log_success "MariaDB 설치 완료"
fi

# ==============================================
# 보안 설정
# ==============================================

log_info "MariaDB 보안 설정..."

# Root 비밀번호 설정
mysql -u root << EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_ROOT_PASSWORD}';
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
EOF

log_success "MariaDB 보안 설정 완료"

# ==============================================
# 설정 튜닝
# ==============================================

log_info "MariaDB 설정 튜닝..."

cat > /etc/my.cnf.d/mcps.cnf << EOF
[mysqld]
# 기본 설정
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# 성능 튜닝
max_connections = 500
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2

# 로그
slow_query_log = 1
slow_query_log_file = /var/log/mariadb/slow.log
long_query_time = 2

[client]
default-character-set = utf8mb4
EOF

# 재시작
systemctl restart mariadb

log_success "MariaDB 설정 완료"
```

### 4.4 install_redis.sh (Redis 설치)

```bash
#!/bin/bash
# scripts/install/install_redis.sh
# Redis 설치 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "Redis 설치 시작..."

# ==============================================
# Redis 설치
# ==============================================

if systemctl is-active --quiet redis; then
    log_info "Redis 이미 실행 중"
else
    log_info "Redis 설치 중..."
    
    # EPEL 저장소 활성화
    dnf install -y epel-release
    
    # Redis 설치
    dnf install -y redis
    
    # 서비스 시작
    systemctl enable redis
    systemctl start redis
    
    log_success "Redis 설치 완료"
fi

# ==============================================
# 설정
# ==============================================

log_info "Redis 설정..."

# 설정 백업
cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# 설정 수정
cat > /etc/redis/redis.conf << EOF
# Network
bind 127.0.0.1
port ${REDIS_PORT}
protected-mode yes

# General
daemonize no
supervised systemd
pidfile /var/run/redis/redis.pid
loglevel notice
logfile /var/log/redis/redis.log

# Snapshotting
save 900 1
save 300 10
save 60 10000
dir /var/lib/redis

# Memory
maxmemory 1gb
maxmemory-policy allkeys-lru

# Persistence
appendonly yes
appendfilename "appendonly.aof"
EOF

# 재시작
systemctl restart redis

log_success "Redis 설정 완료"
```

### 4.5 install_elasticsearch.sh (Elasticsearch 설치)

```bash
#!/bin/bash
# scripts/install/install_elasticsearch.sh
# Elasticsearch 설치 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "Elasticsearch 설치 시작..."

# ==============================================
# Elasticsearch 설치
# ==============================================

if systemctl is-active --quiet elasticsearch; then
    log_info "Elasticsearch 이미 실행 중"
else
    log_info "Elasticsearch 설치 중..."
    
    # GPG 키 추가
    rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch
    
    # 저장소 추가
    cat > /etc/yum.repos.d/elasticsearch.repo << EOF
[elasticsearch]
name=Elasticsearch repository for 8.x packages
baseurl=https://artifacts.elastic.co/packages/8.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
EOF
    
    # 설치
    dnf install -y elasticsearch
    
    log_success "Elasticsearch 설치 완료"
fi

# ==============================================
# 설정
# ==============================================

log_info "Elasticsearch 설정..."

cat > /etc/elasticsearch/elasticsearch.yml << EOF
# Cluster
cluster.name: ${ES_CLUSTER_NAME}
node.name: node-1

# Network
network.host: 0.0.0.0
http.port: ${ES_PORT}

# Discovery
discovery.type: single-node

# Security (개발 환경)
xpack.security.enabled: false

# Memory
bootstrap.memory_lock: true

# Paths
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
EOF

# JVM 힙 설정
cat > /etc/elasticsearch/jvm.options.d/heap.options << EOF
-Xms2g
-Xmx2g
EOF

# 메모리 락 설정
mkdir -p /etc/systemd/system/elasticsearch.service.d
cat > /etc/systemd/system/elasticsearch.service.d/override.conf << EOF
[Service]
LimitMEMLOCK=infinity
EOF

# 서비스 시작
systemctl daemon-reload
systemctl enable elasticsearch
systemctl start elasticsearch

log_info "Elasticsearch 시작 대기 중..."
sleep 30

# 상태 확인
if curl -s "http://localhost:${ES_PORT}" > /dev/null; then
    log_success "Elasticsearch 설정 완료"
else
    log_error "Elasticsearch 시작 실패"
    exit 1
fi
```

### 4.6 install_services.sh (서비스 설치)

```bash
#!/bin/bash
# scripts/install/install_services.sh
# MCP 서비스 설치 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "MCP 서비스 설치 시작..."

# ==============================================
# 디렉토리 생성
# ==============================================

log_info "디렉토리 생성..."

mkdir -p "${PROJECT_ROOT}"/{mcp-host,api-gateway,frontend}
mkdir -p "${DATA_DIR}"/{logs,backups,uploads}
mkdir -p "${LOGS_DIR}"/{mcp-host,api-gateway,frontend}

# ==============================================
# MCP Host 설치
# ==============================================

log_info "MCP Host 설치..."

cd "${PROJECT_ROOT}/mcp-host"
source "${VENV_DIR}/bin/activate"

# requirements.txt가 있으면 설치
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
    log_success "MCP Host 패키지 설치 완료"
fi

# ==============================================
# API Gateway 설치
# ==============================================

log_info "API Gateway 설치..."

cd "${PROJECT_ROOT}/api-gateway"
source "${VENV_DIR}/bin/activate"

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
    log_success "API Gateway 패키지 설치 완료"
fi

# ==============================================
# Frontend 설치
# ==============================================

log_info "Frontend 설치..."

cd "${PROJECT_ROOT}/frontend"
source "${VENV_DIR}/bin/activate"

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
    log_success "Frontend 패키지 설치 완료"
fi

# Reflex 초기화
if command -v reflex &> /dev/null; then
    reflex init
    log_success "Reflex 초기화 완료"
fi

# ==============================================
# Systemd 서비스 등록
# ==============================================

log_info "Systemd 서비스 등록..."

# MCP Host 서비스
cat > /etc/systemd/system/mcp-host.service << EOF
[Unit]
Description=MCP Host Service
After=network.target mariadb.service redis.service elasticsearch.service

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_ROOT}/mcp-host
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin"
ExecStart=${VENV_DIR}/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:${LOGS_DIR}/mcp-host/service.log
StandardError=append:${LOGS_DIR}/mcp-host/error.log

[Install]
WantedBy=multi-user.target
EOF

# API Gateway 서비스
cat > /etc/systemd/system/mcp-api-gateway.service << EOF
[Unit]
Description=MCP API Gateway
After=network.target mcp-host.service

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_ROOT}/api-gateway
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin"
ExecStart=${VENV_DIR}/bin/uvicorn main:app --host 0.0.0.0 --port ${API_GATEWAY_PORT}
Restart=always
RestartSec=10
StandardOutput=append:${LOGS_DIR}/api-gateway/service.log
StandardError=append:${LOGS_DIR}/api-gateway/error.log

[Install]
WantedBy=multi-user.target
EOF

# Frontend 서비스
cat > /etc/systemd/system/mcp-frontend.service << EOF
[Unit]
Description=MCP Frontend
After=network.target mcp-api-gateway.service

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_ROOT}/frontend
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin"
ExecStart=${VENV_DIR}/bin/reflex run --env prod
Restart=always
RestartSec=10
StandardOutput=append:${LOGS_DIR}/frontend/service.log
StandardError=append:${LOGS_DIR}/frontend/error.log

[Install]
WantedBy=multi-user.target
EOF

# Systemd 리로드
systemctl daemon-reload

log_success "서비스 설치 완료"
```

***

## 5. 초기화 스크립트

### 5.1 init_all.sh (전체 초기화)

```bash
#!/bin/bash
# scripts/init/init_all.sh
# 전체 초기화 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "시스템 초기화 시작..."

# ==============================================
# Database 초기화
# ==============================================

log_info "[1/3] Database 초기화..."
bash "${SCRIPTS_DIR}/init/init_database.sh" || {
    log_error "Database 초기화 실패"
    exit 1
}

# ==============================================
# Elasticsearch 초기화
# ==============================================

log_info "[2/3] Elasticsearch 초기화..."
bash "${SCRIPTS_DIR}/init/init_elasticsearch.sh" || {
    log_error "Elasticsearch 초기화 실패"
    exit 1
}

# ==============================================
# 초기 데이터
# ==============================================

log_info "[3/3] 초기 데이터 생성..."
bash "${SCRIPTS_DIR}/init/init_data.sh" || {
    log_error "초기 데이터 생성 실패"
    exit 1
}

log_success "시스템 초기화 완료!"
```

### 5.2 init_database.sh (Database 초기화)

```bash
#!/bin/bash
# scripts/init/init_database.sh
# Database 초기화 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "Database 초기화 시작..."

# ==============================================
# Database 및 사용자 생성
# ==============================================

log_info "Database 및 사용자 생성..."

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
# 테이블 생성
# ==============================================

log_info "테이블 생성..."

# DDL 스크립트 실행
if [ -f "${PROJECT_ROOT}/data/database/02_create_tables.sql" ]; then
    mysql -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} < "${PROJECT_ROOT}/data/database/02_create_tables.sql"
    log_success "테이블 생성 완료"
else
    log_warning "DDL 스크립트를 찾을 수 없습니다"
fi

# ==============================================
# 인덱스 생성
# ==============================================

log_info "인덱스 생성..."

if [ -f "${PROJECT_ROOT}/data/database/03_create_indexes.sql" ]; then
    mysql -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} < "${PROJECT_ROOT}/data/database/03_create_indexes.sql"
    log_success "인덱스 생성 완료"
fi

log_success "Database 초기화 완료"
```

### 5.3 init_elasticsearch.sh (Elasticsearch 초기화)

```bash
#!/bin/bash
# scripts/init/init_elasticsearch.sh
# Elasticsearch 초기화 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "Elasticsearch 초기화 시작..."

# ==============================================
# Elasticsearch 대기
# ==============================================

log_info "Elasticsearch 준비 대기..."

MAX_RETRIES=30
RETRY_COUNT=0

until curl -s "http://localhost:${ES_PORT}" > /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        log_error "Elasticsearch가 시작되지 않았습니다"
        exit 1
    fi
    
    log_info "대기 중... (${RETRY_COUNT}/${MAX_RETRIES})"
    sleep 2
done

log_success "Elasticsearch 준비 완료"

# ==============================================
# 인덱스 생성
# ==============================================

log_info "인덱스 생성..."

# documents 인덱스
curl -X PUT "http://localhost:${ES_PORT}/documents" \
    -H 'Content-Type: application/json' \
    -d '{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
      "analyzer": {
        "korean": {
          "type": "custom",
          "tokenizer": "nori_tokenizer",
          "filter": ["lowercase"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "doc_id": {"type": "keyword"},
      "title": {
        "type": "text",
        "analyzer": "korean",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "content": {
        "type": "text",
        "analyzer": "korean"
      },
      "classification": {"type": "keyword"},
      "category": {"type": "keyword"},
      "tags": {"type": "keyword"},
      "author_id": {"type": "keyword"},
      "team": {"type": "keyword"},
      "department": {"type": "keyword"},
      "created_at": {"type": "date"},
      "updated_at": {"type": "date"}
    }
  }
}'

log_success "Elasticsearch 초기화 완료"
```

### 5.4 init_data.sh (초기 데이터)

```bash
#!/bin/bash
# scripts/init/init_data.sh
# 초기 데이터 생성 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "초기 데이터 생성 시작..."

# ==============================================
# 테스트 사용자 생성
# ==============================================

log_info "테스트 사용자 생성..."

mysql -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} << EOF
-- Admin
INSERT INTO users (id, name, email, role, department, status)
VALUES ('U001', 'Admin User', 'admin@example.com', 'admin', 'IT', 'active')
ON DUPLICATE KEY UPDATE name=name;

-- Manager
INSERT INTO users (id, name, email, role, team, department, status)
VALUES ('U002', 'Manager User', 'manager@example.com', 'manager', 'Dev Team', 'Engineering', 'active')
ON DUPLICATE KEY UPDATE name=name;

-- Staff
INSERT INTO users (id, name, email, role, team, department, status)
VALUES ('U003', 'Staff User', 'staff@example.com', 'staff', 'Dev Team', 'Engineering', 'active')
ON DUPLICATE KEY UPDATE name=name;

-- Junior
INSERT INTO users (id, name, email, role, team, department, status)
VALUES ('U004', 'Junior User', 'junior@example.com', 'junior', 'Dev Team', 'Engineering', 'active')
ON DUPLICATE KEY UPDATE name=name;
EOF

log_success "테스트 사용자 생성 완료"

# ==============================================
# 샘플 문서 생성 (선택)
# ==============================================

log_info "샘플 문서 생성 (선택)..."

if [ -f "${PROJECT_ROOT}/data/database/sample_data.sql" ]; then
    mysql -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} < "${PROJECT_ROOT}/data/database/sample_data.sql"
    log_success "샘플 데이터 생성 완료"
else
    log_info "샘플 데이터 스크립트 없음 (생략)"
fi

log_success "초기 데이터 생성 완료"
```



## 6. 실행 스크립트

### 6.1 start_all.sh (전체 시작)

```bash
#!/bin/bash
# scripts/control/start_all.sh
# 전체 서비스 시작 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "=========================================="
log_info "  MCP 시스템 시작"
log_info "=========================================="

# ==============================================
# 인프라 서비스 시작
# ==============================================

log_info "[1/4] 인프라 서비스 시작..."

# MariaDB
if ! systemctl is-active --quiet mariadb; then
    log_info "MariaDB 시작 중..."
    systemctl start mariadb
    sleep 3
    log_success "MariaDB 시작 완료"
else
    log_info "MariaDB 이미 실행 중"
fi

# Redis
if ! systemctl is-active --quiet redis; then
    log_info "Redis 시작 중..."
    systemctl start redis
    sleep 2
    log_success "Redis 시작 완료"
else
    log_info "Redis 이미 실행 중"
fi

# Elasticsearch
if ! systemctl is-active --quiet elasticsearch; then
    log_info "Elasticsearch 시작 중..."
    systemctl start elasticsearch
    sleep 30
    log_success "Elasticsearch 시작 완료"
else
    log_info "Elasticsearch 이미 실행 중"
fi

# ==============================================
# MCP Host 시작
# ==============================================

log_info "[2/4] MCP Host 시작..."

if ! systemctl is-active --quiet mcp-host; then
    systemctl start mcp-host
    sleep 5
    
    if systemctl is-active --quiet mcp-host; then
        log_success "MCP Host 시작 완료"
    else
        log_error "MCP Host 시작 실패"
        exit 1
    fi
else
    log_info "MCP Host 이미 실행 중"
fi

# ==============================================
# API Gateway 시작
# ==============================================

log_info "[3/4] API Gateway 시작..."

if ! systemctl is-active --quiet mcp-api-gateway; then
    systemctl start mcp-api-gateway
    sleep 3
    
    if systemctl is-active --quiet mcp-api-gateway; then
        log_success "API Gateway 시작 완료"
    else
        log_error "API Gateway 시작 실패"
        exit 1
    fi
else
    log_info "API Gateway 이미 실행 중"
fi

# ==============================================
# Frontend 시작
# ==============================================

log_info "[4/4] Frontend 시작..."

if ! systemctl is-active --quiet mcp-frontend; then
    systemctl start mcp-frontend
    sleep 5
    
    if systemctl is-active --quiet mcp-frontend; then
        log_success "Frontend 시작 완료"
    else
        log_error "Frontend 시작 실패"
        exit 1
    fi
else
    log_info "Frontend 이미 실행 중"
fi

# ==============================================
# 헬스체크
# ==============================================

log_info "헬스체크 수행 중..."
sleep 5
bash "${SCRIPTS_DIR}/health/healthcheck.sh"

# ==============================================
# 완료
# ==============================================

log_success "=========================================="
log_success "  모든 서비스 시작 완료!"
log_success "=========================================="
log_info ""
log_info "접속 정보:"
log_info "  - Frontend: http://localhost:${FRONTEND_PORT}"
log_info "  - API Gateway: http://localhost:${API_GATEWAY_PORT}"
log_info "  - MCP Host: http://localhost:${MCP_HOST_PORT}"
log_info ""
log_info "상태 확인: sudo bash ${SCRIPTS_DIR}/manage/status.sh"
log_info ""
```

### 6.2 stop_all.sh (전체 중지)

```bash
#!/bin/bash
# scripts/control/stop_all.sh
# 전체 서비스 중지 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "=========================================="
log_info "  MCP 시스템 중지"
log_info "=========================================="

# ==============================================
# Frontend 중지
# ==============================================

log_info "[1/4] Frontend 중지..."

if systemctl is-active --quiet mcp-frontend; then
    systemctl stop mcp-frontend
    log_success "Frontend 중지 완료"
else
    log_info "Frontend가 실행 중이 아닙니다"
fi

# ==============================================
# API Gateway 중지
# ==============================================

log_info "[2/4] API Gateway 중지..."

if systemctl is-active --quiet mcp-api-gateway; then
    systemctl stop mcp-api-gateway
    log_success "API Gateway 중지 완료"
else
    log_info "API Gateway가 실행 중이 아닙니다"
fi

# ==============================================
# MCP Host 중지
# ==============================================

log_info "[3/4] MCP Host 중지..."

if systemctl is-active --quiet mcp-host; then
    systemctl stop mcp-host
    log_success "MCP Host 중지 완료"
else
    log_info "MCP Host가 실행 중이 아닙니다"
fi

# ==============================================
# 인프라 서비스 중지 (선택)
# ==============================================

log_info "[4/4] 인프라 서비스 중지 (선택)..."

read -p "인프라 서비스(MariaDB, Redis, Elasticsearch)도 중지하시겠습니까? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if systemctl is-active --quiet elasticsearch; then
        systemctl stop elasticsearch
        log_success "Elasticsearch 중지 완료"
    fi
    
    if systemctl is-active --quiet redis; then
        systemctl stop redis
        log_success "Redis 중지 완료"
    fi
    
    if systemctl is-active --quiet mariadb; then
        systemctl stop mariadb
        log_success "MariaDB 중지 완료"
    fi
fi

# ==============================================
# 완료
# ==============================================

log_success "=========================================="
log_success "  모든 서비스 중지 완료!"
log_success "=========================================="
```

### 6.3 restart_all.sh (전체 재시작)

```bash
#!/bin/bash
# scripts/control/restart_all.sh
# 전체 서비스 재시작 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "=========================================="
log_info "  MCP 시스템 재시작"
log_info "=========================================="

# 중지
log_info "서비스 중지 중..."
bash "${SCRIPTS_DIR}/control/stop_all.sh"

sleep 5

# 시작
log_info "서비스 시작 중..."
bash "${SCRIPTS_DIR}/control/start_all.sh"

log_success "시스템 재시작 완료!"
```

### 6.4 start_service.sh (개별 서비스 시작)

```bash
#!/bin/bash
# scripts/control/start_service.sh
# 개별 서비스 시작 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

# ==============================================
# 사용법
# ==============================================

if [ $# -eq 0 ]; then
    echo "Usage: $0 <service>"
    echo ""
    echo "Available services:"
    echo "  - mariadb"
    echo "  - redis"
    echo "  - elasticsearch"
    echo "  - mcp-host"
    echo "  - mcp-api-gateway"
    echo "  - mcp-frontend"
    exit 1
fi

SERVICE=$1

# ==============================================
# 서비스 시작
# ==============================================

log_info "${SERVICE} 시작 중..."

if systemctl is-active --quiet "${SERVICE}"; then
    log_info "${SERVICE}가 이미 실행 중입니다"
else
    systemctl start "${SERVICE}"
    sleep 3
    
    if systemctl is-active --quiet "${SERVICE}"; then
        log_success "${SERVICE} 시작 완료"
    else
        log_error "${SERVICE} 시작 실패"
        systemctl status "${SERVICE}" --no-pager
        exit 1
    fi
fi
```

### 6.5 stop_service.sh (개별 서비스 중지)

```bash
#!/bin/bash
# scripts/control/stop_service.sh
# 개별 서비스 중지 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

# ==============================================
# 사용법
# ==============================================

if [ $# -eq 0 ]; then
    echo "Usage: $0 <service>"
    echo ""
    echo "Available services:"
    echo "  - mariadb"
    echo "  - redis"
    echo "  - elasticsearch"
    echo "  - mcp-host"
    echo "  - mcp-api-gateway"
    echo "  - mcp-frontend"
    exit 1
fi

SERVICE=$1

# ==============================================
# 서비스 중지
# ==============================================

log_info "${SERVICE} 중지 중..."

if systemctl is-active --quiet "${SERVICE}"; then
    systemctl stop "${SERVICE}"
    log_success "${SERVICE} 중지 완료"
else
    log_info "${SERVICE}가 실행 중이 아닙니다"
fi
```

***

## 7. 관리 스크립트

### 7.1 status.sh (상태 확인)

```bash
#!/bin/bash
# scripts/manage/status.sh
# 시스템 상태 확인 스크립트

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

echo ""
log_info "=========================================="
log_info "  MCP 시스템 상태"
log_info "=========================================="
echo ""

# ==============================================
# 서비스 상태 확인
# ==============================================

SERVICES=(
    "mariadb:MariaDB"
    "redis:Redis"
    "elasticsearch:Elasticsearch"
    "mcp-host:MCP Host"
    "mcp-api-gateway:API Gateway"
    "mcp-frontend:Frontend"
)

echo "서비스 상태:"
echo "----------------------------------------"

for SERVICE_INFO in "${SERVICES[@]}"; do
    IFS=':' read -r SERVICE_NAME DISPLAY_NAME <<< "$SERVICE_INFO"
    
    if systemctl is-active --quiet "${SERVICE_NAME}"; then
        printf "  %-20s ${COLOR_GREEN}●${COLOR_NC} 실행 중\n" "${DISPLAY_NAME}:"
    else
        printf "  %-20s ${COLOR_RED}●${COLOR_NC} 중지됨\n" "${DISPLAY_NAME}:"
    fi
done

echo ""

# ==============================================
# 포트 확인
# ==============================================

echo "포트 상태:"
echo "----------------------------------------"

PORTS=(
    "${MCP_HOST_PORT}:MCP Host"
    "${API_GATEWAY_PORT}:API Gateway"
    "${FRONTEND_PORT}:Frontend"
    "${DB_PORT}:MariaDB"
    "${REDIS_PORT}:Redis"
    "${ES_PORT}:Elasticsearch"
)

for PORT_INFO in "${PORTS[@]}"; do
    IFS=':' read -r PORT DISPLAY_NAME <<< "$PORT_INFO"
    
    if netstat -tuln | grep -q ":${PORT} "; then
        printf "  %-20s ${COLOR_GREEN}●${COLOR_NC} :%-6s (LISTEN)\n" "${DISPLAY_NAME}:" "${PORT}"
    else
        printf "  %-20s ${COLOR_RED}●${COLOR_NC} :%-6s (CLOSED)\n" "${DISPLAY_NAME}:" "${PORT}"
    fi
done

echo ""

# ==============================================
# 디스크 사용량
# ==============================================

echo "디스크 사용량:"
echo "----------------------------------------"
df -h "${PROJECT_ROOT}" | tail -1 | awk '{printf "  사용: %s / 전체: %s (%s)\n", $3, $2, $5}'

echo ""

# ==============================================
# 메모리 사용량
# ==============================================

echo "메모리 사용량:"
echo "----------------------------------------"
free -h | grep "^Mem:" | awk '{printf "  사용: %s / 전체: %s\n", $3, $2}'

echo ""

# ==============================================
# 최근 로그
# ==============================================

echo "최근 에러 (최근 10개):"
echo "----------------------------------------"

for SERVICE in mcp-host api-gateway frontend; do
    LOG_FILE="${LOGS_DIR}/${SERVICE}/error.log"
    
    if [ -f "${LOG_FILE}" ]; then
        ERRORS=$(tail -10 "${LOG_FILE}" 2>/dev/null | grep -i "error" | wc -l)
        
        if [ ${ERRORS} -gt 0 ]; then
            echo "  ${SERVICE}: ${COLOR_YELLOW}${ERRORS}${COLOR_NC}개의 에러"
        fi
    fi
done

echo ""
log_info "=========================================="
echo ""
```

### 7.2 logs.sh (로그 조회)

```bash
#!/bin/bash
# scripts/manage/logs.sh
# 로그 조회 스크립트

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

# ==============================================
# 사용법
# ==============================================

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
    echo ""
    echo "Examples:"
    echo "  $0 mcp-host                # MCP Host 로그 표시"
    echo "  $0 api-gateway -f          # API Gateway 실시간 로그"
    echo "  $0 mcp-host -n 100         # 최근 100줄"
    echo "  $0 mcp-host --error        # 에러만"
}

# ==============================================
# 인수 파싱
# ==============================================

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

# ==============================================
# 로그 파일 결정
# ==============================================

case ${SERVICE} in
    mcp-host)
        if [ "${ERROR_ONLY}" = true ]; then
            LOG_FILE="${LOGS_DIR}/mcp-host/error.log"
        else
            LOG_FILE="${LOGS_DIR}/mcp-host/service.log"
        fi
        ;;
    api-gateway)
        if [ "${ERROR_ONLY}" = true ]; then
            LOG_FILE="${LOGS_DIR}/api-gateway/error.log"
        else
            LOG_FILE="${LOGS_DIR}/api-gateway/service.log"
        fi
        ;;
    frontend)
        if [ "${ERROR_ONLY}" = true ]; then
            LOG_FILE="${LOGS_DIR}/frontend/error.log"
        else
            LOG_FILE="${LOGS_DIR}/frontend/service.log"
        fi
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

# ==============================================
# 로그 표시
# ==============================================

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
```

### 7.3 cleanup.sh (정리)

```bash
#!/bin/bash
# scripts/manage/cleanup.sh
# 시스템 정리 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "시스템 정리 시작..."

# ==============================================
# 오래된 로그 삭제
# ==============================================

log_info "오래된 로그 삭제 중..."

find "${LOGS_DIR}" -type f -name "*.log" -mtime +${LOG_RETENTION_DAYS} -delete
find "${LOGS_DIR}" -type f -name "*.log.*" -mtime +${LOG_RETENTION_DAYS} -delete

log_success "오래된 로그 삭제 완료"

# ==============================================
# 오래된 백업 삭제
# ==============================================

log_info "오래된 백업 삭제 중..."

find "${BACKUP_DIR}" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete

log_success "오래된 백업 삭제 완료"

# ==============================================
# 임시 파일 삭제
# ==============================================

log_info "임시 파일 삭제 중..."

find "${PROJECT_ROOT}" -type f -name "*.pyc" -delete
find "${PROJECT_ROOT}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${PROJECT_ROOT}" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

log_success "임시 파일 삭제 완료"

# ==============================================
# 디스크 사용량 표시
# ==============================================

log_info "디스크 사용량:"
df -h "${PROJECT_ROOT}"

log_success "시스템 정리 완료!"
```

### 7.4 update.sh (업데이트)

```bash
#!/bin/bash
# scripts/manage/update.sh
# 시스템 업데이트 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "시스템 업데이트 시작..."

# ==============================================
# 서비스 중지
# ==============================================

log_info "서비스 중지 중..."
bash "${SCRIPTS_DIR}/control/stop_all.sh"

# ==============================================
# 백업
# ==============================================

log_info "백업 생성 중..."
bash "${SCRIPTS_DIR}/backup/backup.sh"

# ==============================================
# Git Pull (선택)
# ==============================================

if [ -d "${PROJECT_ROOT}/.git" ]; then
    log_info "코드 업데이트 중..."
    cd "${PROJECT_ROOT}"
    git pull
    log_success "코드 업데이트 완료"
fi

# ==============================================
# Python 패키지 업데이트
# ==============================================

log_info "Python 패키지 업데이트 중..."
source "${VENV_DIR}/bin/activate"

for SERVICE_DIR in mcp-host api-gateway frontend; do
    if [ -f "${PROJECT_ROOT}/${SERVICE_DIR}/requirements.txt" ]; then
        log_info "${SERVICE_DIR} 패키지 업데이트..."
        cd "${PROJECT_ROOT}/${SERVICE_DIR}"
        pip install --upgrade -r requirements.txt
    fi
done

log_success "Python 패키지 업데이트 완료"

# ==============================================
# Database 마이그레이션 (선택)
# ==============================================

if [ -f "${PROJECT_ROOT}/data/database/migrations/latest.sql" ]; then
    log_info "Database 마이그레이션..."
    mysql -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} < "${PROJECT_ROOT}/data/database/migrations/latest.sql"
    log_success "Database 마이그레이션 완료"
fi

# ==============================================
# 서비스 시작
# ==============================================

log_info "서비스 시작 중..."
bash "${SCRIPTS_DIR}/control/start_all.sh"

log_success "시스템 업데이트 완료!"
```

***

## 8. 헬스체크 스크립트

### 8.1 healthcheck.sh (전체 헬스체크)

```bash
#!/bin/bash
# scripts/health/healthcheck.sh
# 전체 헬스체크 스크립트

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "헬스체크 시작..."

OVERALL_STATUS=0

# ==============================================
# Database 체크
# ==============================================

log_info "Database 체크..."
if bash "${SCRIPTS_DIR}/health/check_database.sh"; then
    log_success "Database: OK"
else
    log_error "Database: FAIL"
    OVERALL_STATUS=1
fi

# ==============================================
# Redis 체크
# ==============================================

log_info "Redis 체크..."
if redis-cli ping > /dev/null 2>&1; then
    log_success "Redis: OK"
else
    log_error "Redis: FAIL"
    OVERALL_STATUS=1
fi

# ==============================================
# Elasticsearch 체크
# ==============================================

log_info "Elasticsearch 체크..."
if curl -s "http://localhost:${ES_PORT}" > /dev/null; then
    log_success "Elasticsearch: OK"
else
    log_error "Elasticsearch: FAIL"
    OVERALL_STATUS=1
fi

# ==============================================
# 서비스 체크
# ==============================================

log_info "서비스 체크..."
if bash "${SCRIPTS_DIR}/health/check_services.sh"; then
    log_success "Services: OK"
else
    log_error "Services: FAIL"
    OVERALL_STATUS=1
fi

# ==============================================
# 연결 체크
# ==============================================

log_info "연결 체크..."
if bash "${SCRIPTS_DIR}/health/check_connectivity.sh"; then
    log_success "Connectivity: OK"
else
    log_error "Connectivity: FAIL"
    OVERALL_STATUS=1
fi

# ==============================================
# 결과
# ==============================================

if [ ${OVERALL_STATUS} -eq 0 ]; then
    log_success "=========================================="
    log_success "  헬스체크 성공!"
    log_success "=========================================="
else
    log_error "=========================================="
    log_error "  헬스체크 실패!"
    log_error "=========================================="
fi

exit ${OVERALL_STATUS}
```

### 8.2 check_database.sh (Database 체크)

```bash
#!/bin/bash
# scripts/health/check_database.sh
# Database 헬스체크 스크립트

source "$(dirname "$0")/../config.sh"

# MariaDB 연결 테스트
if mysql -u ${DB_USER} -p"${DB_PASSWORD}" -e "SELECT 1" ${DB_NAME} > /dev/null 2>&1; then
    exit 0
else
    exit 1
fi
```

### 8.3 check_services.sh (서비스 체크)

```bash
#!/bin/bash
# scripts/health/check_services.sh
# 서비스 헬스체크 스크립트

source "$(dirname "$0")/../config.sh"

SERVICES=(
    "mcp-host"
    "mcp-api-gateway"
    "mcp-frontend"
)

ALL_OK=true

for SERVICE in "${SERVICES[@]}"; do
    if ! systemctl is-active --quiet "${SERVICE}"; then
        echo "Service ${SERVICE} is not running"
        ALL_OK=false
    fi
done

if [ "${ALL_OK}" = true ]; then
    exit 0
else
    exit 1
fi
```

### 8.4 check_connectivity.sh (연결 체크)

```bash
#!/bin/bash
# scripts/health/check_connectivity.sh
# 연결 헬스체크 스크립트

source "$(dirname "$0")/../config.sh"

ALL_OK=true

# MCP Host
if ! curl -s -f "http://localhost:${MCP_HOST_PORT}/health" > /dev/null; then
    echo "MCP Host health check failed"
    ALL_OK=false
fi

# API Gateway
if ! curl -s -f "http://localhost:${API_GATEWAY_PORT}/health" > /dev/null; then
    echo "API Gateway health check failed"
    ALL_OK=false
fi

# Frontend (선택)
# if ! curl -s -f "http://localhost:${FRONTEND_PORT}" > /dev/null; then
#     echo "Frontend health check failed"
#     ALL_OK=false
# fi

if [ "${ALL_OK}" = true ]; then
    exit 0
else
    exit 1
fi
```

***

## 9. 백업 및 복구

### 9.1 backup.sh (백업)

```bash
#!/bin/bash
# scripts/backup/backup.sh
# 백업 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/backup_${BACKUP_DATE}"

log_info "백업 시작: ${BACKUP_PATH}"

# 백업 디렉토리 생성
mkdir -p "${BACKUP_PATH}"

# ==============================================
# Database 백업
# ==============================================

log_info "Database 백업 중..."

mysqldump \
    -u ${DB_USER} \
    -p"${DB_PASSWORD}" \
    --single-transaction \
    --routines \
    --triggers \
    ${DB_NAME} > "${BACKUP_PATH}/database.sql"

log_success "Database 백업 완료"

# ==============================================
# Elasticsearch 백업 (선택)
# ==============================================

log_info "Elasticsearch 백업 중..."

curl -X POST "http://localhost:${ES_PORT}/_snapshot/backup/snapshot_${BACKUP_DATE}?wait_for_completion=true" || true

log_success "Elasticsearch 백업 완료"

# ==============================================
# 설정 파일 백업
# ==============================================

log_info "설정 파일 백업 중..."

mkdir -p "${BACKUP_PATH}/config"

# 환경 변수 파일
for SERVICE_DIR in mcp-host api-gateway frontend; do
    if [ -f "${PROJECT_ROOT}/${SERVICE_DIR}/.env" ]; then
        cp "${PROJECT_ROOT}/${SERVICE_DIR}/.env" "${BACKUP_PATH}/config/${SERVICE_DIR}.env"
    fi
done

# Systemd 서비스 파일
cp /etc/systemd/system/mcp-*.service "${BACKUP_PATH}/config/" 2>/dev/null || true

log_success "설정 파일 백업 완료"

# ==============================================
# 압축 (선택)
# ==============================================

if [ "${BACKUP_COMPRESS}" = "true" ]; then
    log_info "백업 압축 중..."
    
    cd "${BACKUP_DIR}"
    tar -czf "backup_${BACKUP_DATE}.tar.gz" "backup_${BACKUP_DATE}"
    rm -rf "backup_${BACKUP_DATE}"
    
    log_success "백업 압축 완료: backup_${BACKUP_DATE}.tar.gz"
else
    log_success "백업 완료: ${BACKUP_PATH}"
fi

# ==============================================
# 오래된 백업 삭제
# ==============================================

log_info "오래된 백업 삭제 중..."
find "${BACKUP_DIR}" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete

log_success "백업 완료!"
```

### 9.2 restore.sh (복구)

```bash
#!/bin/bash
# scripts/backup/restore.sh
# 복구 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

# ==============================================
# 사용법
# ==============================================

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file_or_directory>"
    echo ""
    echo "Examples:"
    echo "  $0 /app/poc/mcps/data/backups/backup_20260108_120000"
    echo "  $0 /app/poc/mcps/data/backups/backup_20260108_120000.tar.gz"
    exit 1
fi

BACKUP_PATH=$1

# ==============================================
# 백업 파일 확인
# ==============================================

if [ ! -e "${BACKUP_PATH}" ]; then
    log_error "백업을 찾을 수 없습니다: ${BACKUP_PATH}"
    exit 1
fi

# ==============================================
# 압축 파일 해제
# ==============================================

if [[ "${BACKUP_PATH}" == *.tar.gz ]]; then
    log_info "백업 파일 압축 해제 중..."
    
    EXTRACT_DIR="${BACKUP_DIR}/restore_temp"
    mkdir -p "${EXTRACT_DIR}"
    
    tar -xzf "${BACKUP_PATH}" -C "${EXTRACT_DIR}"
    
    # 압축 해제된 디렉토리 찾기
    BACKUP_PATH=$(find "${EXTRACT_DIR}" -maxdepth 1 -type d -name "backup_*" | head -1)
    
    log_success "압축 해제 완료"
fi

# ==============================================
# 확인
# ==============================================

log_warning "=========================================="
log_warning "  경고: 복구 작업을 시작합니다"
log_warning "  현재 데이터가 삭제될 수 있습니다"
log_warning "=========================================="

read -p "계속하시겠습니까? (yes/no): " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    log_info "복구 작업이 취소되었습니다"
    exit 0
fi

# ==============================================
# 서비스 중지
# ==============================================

log_info "서비스 중지 중..."
bash "${SCRIPTS_DIR}/control/stop_all.sh"

# ==============================================
# Database 복구
# ==============================================

log_info "Database 복구 중..."

if [ -f "${BACKUP_PATH}/database.sql" ]; then
    mysql -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} < "${BACKUP_PATH}/database.sql"
    log_success "Database 복구 완료"
else
    log_error "Database 백업 파일을 찾을 수 없습니다"
fi

# ==============================================
# 설정 파일 복구
# ==============================================

log_info "설정 파일 복구 중..."

if [ -d "${BACKUP_PATH}/config" ]; then
    # 환경 변수 파일
    for SERVICE_DIR in mcp-host api-gateway frontend; do
        if [ -f "${BACKUP_PATH}/config/${SERVICE_DIR}.env" ]; then
            cp "${BACKUP_PATH}/config/${SERVICE_DIR}.env" "${PROJECT_ROOT}/${SERVICE_DIR}/.env"
        fi
    done
    
    # Systemd 서비스 파일
    cp "${BACKUP_PATH}/config/"mcp-*.service /etc/systemd/system/ 2>/dev/null || true
    systemctl daemon-reload
    
    log_success "설정 파일 복구 완료"
fi

# ==============================================
# 서비스 시작
# ==============================================

log_info "서비스 시작 중..."
bash "${SCRIPTS_DIR}/control/start_all.sh"

# ==============================================
# 임시 파일 정리
# ==============================================

if [[ "${1}" == *.tar.gz ]]; then
    rm -rf "${EXTRACT_DIR}"
fi

log_success "=========================================="
log_success "  복구 완료!"
log_success "=========================================="
```

***

## 10. 유틸리티 스크립트

### 10.1 logger.sh (로깅 함수)

```bash
#!/bin/bash
# scripts/utils/logger.sh
# 로깅 유틸리티

# 색상 정의
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_NC} $1"
}

log_success() {
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_NC} $1"
}

log_warning() {
    echo -e "${COLOR_YELLOW}[WARNING]${COLOR_NC} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_NC} $1"
}
```

### 10.2 common.sh (공통 함수)

```bash
#!/bin/bash
# scripts/utils/common.sh
# 공통 유틸리티 함수

# 서비스 실행 확인
is_service_running() {
    local SERVICE=$1
    systemctl is-active --quiet "${SERVICE}"
}

# 포트 사용 확인
is_port_in_use() {
    local PORT=$1
    netstat -tuln | grep -q ":${PORT} "
}

# 명령어 존재 확인
command_exists() {
    command -v "$1" &> /dev/null
}

# 파일 백업
backup_file() {
    local FILE=$1
    if [ -f "${FILE}" ]; then
        cp "${FILE}" "${FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
}

# 진행률 표시
show_progress() {
    local CURRENT=$1
    local TOTAL=$2
    local PERCENT=$((CURRENT * 100 / TOTAL))
    printf "\r진행률: [%-50s] %d%%" $(printf '#%.0s' $(seq 1 $((PERCENT / 2)))) ${PERCENT}
}

# 대기 (타임아웃 포함)
wait_for_service() {
    local SERVICE=$1
    local TIMEOUT=${2:-30}
    local COUNT=0
    
    while [ ${COUNT} -lt ${TIMEOUT} ]; do
        if is_service_running "${SERVICE}"; then
            return 0
        fi
        
        sleep 1
        COUNT=$((COUNT + 1))
    done
    
    return 1
}

# URL 응답 대기
wait_for_url() {
    local URL=$1
    local TIMEOUT=${2:-30}
    local COUNT=0
    
    while [ ${COUNT} -lt ${TIMEOUT} ]; do
        if curl -s -f "${URL}" > /dev/null 2>&1; then
            return 0
        fi
        
        sleep 1
        COUNT=$((COUNT + 1))
    done
    
    return 1
}
```

### 10.3 README.md (사용 가이드)

```markdown
# MCP Scripts 사용 가이드

## 설치

전체 시스템 설치:
```bash
sudo bash scripts/install/setup.sh
```

## 실행

### 전체 시작
```bash
sudo bash scripts/control/start_all.sh
```

### 전체 중지
```bash
sudo bash scripts/control/stop_all.sh
```

### 재시작
```bash
sudo bash scripts/control/restart_all.sh
```

### 개별 서비스
```bash
# 시작
sudo bash scripts/control/start_service.sh mcp-host

# 중지
sudo bash scripts/control/stop_service.sh mcp-host
```

## 관리

### 상태 확인
```bash
sudo bash scripts/manage/status.sh
```

### 로그 확인
```bash
# 일반 로그
sudo bash scripts/manage/logs.sh mcp-host

# 실시간 로그
sudo bash scripts/manage/logs.sh mcp-host -f

# 에러 로그만
sudo bash scripts/manage/logs.sh mcp-host --error

# 최근 100줄
sudo bash scripts/manage/logs.sh mcp-host -n 100
```

### 정리
```bash
sudo bash scripts/manage/cleanup.sh
```

### 업데이트
```bash
sudo bash scripts/manage/update.sh
```

## 백업 및 복구

### 백업
```bash
sudo bash scripts/backup/backup.sh
```

### 복구
```bash
sudo bash scripts/backup/restore.sh /path/to/backup
```

## 헬스체크

```bash
sudo bash scripts/health/healthcheck.sh
```

## 문제 해결

### 서비스가 시작되지 않을 때
```bash
# 상태 확인
sudo systemctl status mcp-host

# 로그 확인
sudo bash scripts/manage/logs.sh mcp-host --error

# 재시작
sudo bash scripts/control/restart_all.sh
```

### 포트 충돌
```bash
# 포트 사용 확인
sudo netstat -tuln | grep :8000

# 프로세스 종료
sudo kill -9 $(lsof -ti:8000)
```

### Database 연결 실패
```bash
# MariaDB 상태 확인
sudo systemctl status mariadb

# 연결 테스트
mysql -u mcps_user -p mcps_db
```
```

***

## 11. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

***

## 12. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| **작성자** | | | |
| **검토자** | | | |
| **승인자** | | | |

***

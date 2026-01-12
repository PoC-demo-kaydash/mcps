# 배포 및 운영 가이드 설계서

***

# 07. MCP 에코시스템 - 배포 및 운영 가이드

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/`  
**목적**: 시스템 배포, 운영, 모니터링 가이드

***

## 목차

1. [개요](#1-개요)
2. [시스템 요구사항](#2-시스템-요구사항)
3. [초기 설치](#3-초기-설치)
4. [배포 절차](#4-배포-절차)
5. [운영 관리](#5-운영-관리)
6. [모니터링](#6-모니터링)
7. [백업 및 복구](#7-백업-및-복구)
8. [트러블슈팅](#8-트러블슈팅)

***

## 1. 개요

### 1.1 배포 전략

```
┌─────────────────────────────────────────────┐
│           배포 아키텍처                      │
├─────────────────────────────────────────────┤
│                                              │
│  [Load Balancer]                            │
│        │                                     │
│        ├─────┬─────────┬─────────┐         │
│        ▼     ▼         ▼         ▼         │
│    [Host1] [Host2] [Host3] [Host4]         │
│        │     │         │         │         │
│        └─────┴─────────┴─────────┘         │
│                  │                          │
│        ┌─────────┴─────────┐               │
│        ▼                   ▼               │
│  [Database Cluster]  [ES Cluster]          │
│                                              │
└─────────────────────────────────────────────┘
```

### 1.2 배포 환경

| 환경 | 목적 | 특징 |
|------|------|------|
| **Development** | 개발 환경 | 로컬 개발, 단일 서버 |
| **Staging** | 검증 환경 | 운영과 동일 구성, 테스트용 |
| **Production** | 운영 환경 | 고가용성, 이중화 |

### 1.3 배포 체크리스트

```markdown
## 배포 전 체크리스트

### 인프라
- [ ] 서버 준비 완료
- [ ] 네트워크 설정 완료
- [ ] 방화벽 규칙 설정
- [ ] SSL 인증서 준비

### 소프트웨어
- [ ] OS 업데이트 완료
- [ ] 필수 패키지 설치
- [ ] Python 3.11+ 설치
- [ ] MariaDB 10.11+ 설치
- [ ] Elasticsearch 8.11+ 설치

### 애플리케이션
- [ ] 소스 코드 배포
- [ ] 설정 파일 준비
- [ ] 환경 변수 설정
- [ ] 의존성 설치

### 보안
- [ ] 사용자 계정 생성
- [ ] 권한 설정
- [ ] 비밀번호 변경
- [ ] 방화벽 활성화

### 데이터
- [ ] Database 스키마 생성
- [ ] 초기 데이터 입력
- [ ] Elasticsearch 인덱스 생성
- [ ] 백업 설정

### 테스트
- [ ] 연결 테스트
- [ ] 기능 테스트
- [ ] 성능 테스트
- [ ] 보안 테스트

### 모니터링
- [ ] 로그 설정
- [ ] 모니터링 도구 설치
- [ ] 알람 설정
- [ ] 대시보드 구성
```

***

## 2. 시스템 요구사항

### 2.1 하드웨어 요구사항

#### Development (개발 환경)
```
CPU:    4 cores
Memory: 8 GB
Disk:   50 GB SSD
```

#### Staging (검증 환경)
```
CPU:    8 cores
Memory: 16 GB
Disk:   200 GB SSD
```

#### Production (운영 환경)
```
[MCP Host]
CPU:    8 cores
Memory: 16 GB
Disk:   100 GB SSD
Count:  2+ (이중화)

[Database]
CPU:    8 cores
Memory: 32 GB
Disk:   500 GB SSD
Count:  3 (클러스터)

[Elasticsearch]
CPU:    8 cores
Memory: 32 GB
Disk:   1 TB SSD
Count:  3 (클러스터)
```

### 2.2 소프트웨어 요구사항

```yaml
# 운영 체제
OS: RHEL 8.x / Rocky Linux 8.x

# Python
Python: 3.11+
pip: 23.0+
venv: built-in

# Database
MariaDB: 10.11+

# Search Engine
Elasticsearch: 8.11+

# 웹 서버 (선택)
Nginx: 1.20+

# 프로세스 관리
systemd: 시스템 기본
```

### 2.3 네트워크 요구사항

```
포트 설정:

[MCP Host]
8000/tcp  - API 서버 (HTTP)
8443/tcp  - API 서버 (HTTPS, 선택)

[Database]
3306/tcp  - MariaDB

[Elasticsearch]
9200/tcp  - ES HTTP API
9300/tcp  - ES 내부 통신

[모니터링]
9090/tcp  - Prometheus (선택)
3000/tcp  - Grafana (선택)
```

***

## 3. 초기 설치

### 3.1 OS 설정

```bash
#!/bin/bash
# scripts/setup_os.sh
# OS 초기 설정

set -e

echo "=== OS 초기 설정 ==="

# 1. 시스템 업데이트
echo "시스템 업데이트..."
sudo dnf update -y

# 2. 필수 패키지 설치
echo "필수 패키지 설치..."
sudo dnf install -y \
    git \
    wget \
    curl \
    vim \
    net-tools \
    firewalld \
    python3.11 \
    python3.11-devel \
    python3.11-pip

# 3. Python 기본 버전 설정
sudo alternatives --set python3 /usr/bin/python3.11

# 4. 방화벽 설정
echo "방화벽 설정..."
sudo systemctl enable firewalld
sudo systemctl start firewalld

# MCP Host
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=8443/tcp

# Database
sudo firewall-cmd --permanent --add-port=3306/tcp

# Elasticsearch
sudo firewall-cmd --permanent --add-port=9200/tcp
sudo firewall-cmd --permanent --add-port=9300/tcp

sudo firewall-cmd --reload

# 5. SELinux 설정 (필요시)
# sudo setenforce 0
# sudo sed -i 's/^SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config

echo "✅ OS 초기 설정 완료"
```

### 3.2 MariaDB 설치

```bash
#!/bin/bash
# scripts/install_mariadb.sh
# MariaDB 설치 및 설정

set -e

echo "=== MariaDB 설치 ==="

# 1. MariaDB 저장소 추가
cat > /etc/yum.repos.d/mariadb.repo << 'EOF'
[mariadb]
name = MariaDB
baseurl = https://mirrors.xtom.com/mariadb/yum/10.11/rhel8-amd64
gpgkey=https://mirrors.xtom.com/mariadb/yum/RPM-GPG-KEY-MariaDB
gpgcheck=1
EOF

# 2. MariaDB 설치
sudo dnf install -y MariaDB-server MariaDB-client

# 3. MariaDB 시작
sudo systemctl enable mariadb
sudo systemctl start mariadb

# 4. 보안 설정
echo "MariaDB 보안 설정..."
sudo mysql_secure_installation << EOF

y
new_root_password
new_root_password
y
y
y
y
EOF

# 5. 설정 파일 생성
sudo tee /etc/my.cnf.d/mcps.cnf > /dev/null << 'EOF'
[mysqld]
# Character Set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# Connection
max_connections = 500
max_allowed_packet = 64M

# Performance
innodb_buffer_pool_size = 2G
innodb_log_file_size = 512M
innodb_flush_log_at_trx_commit = 2

# Logging
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# Binary Log (Replication)
server-id = 1
log_bin = /var/log/mysql/mysql-bin.log
binlog_format = ROW
expire_logs_days = 7
EOF

# 6. 재시작
sudo systemctl restart mariadb

echo "✅ MariaDB 설치 완료"
```

### 3.3 Elasticsearch 설치

```bash
#!/bin/bash
# scripts/install_elasticsearch.sh
# Elasticsearch 설치 및 설정

set -e

echo "=== Elasticsearch 설치 ==="

# 1. Elasticsearch 저장소 추가
sudo rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch

cat > /etc/yum.repos.d/elasticsearch.repo << 'EOF'
[elasticsearch]
name=Elasticsearch repository for 8.x packages
baseurl=https://artifacts.elastic.co/packages/8.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
EOF

# 2. Elasticsearch 설치
sudo dnf install -y elasticsearch

# 3. 설정 파일 수정
sudo tee /etc/elasticsearch/elasticsearch.yml > /dev/null << 'EOF'
# Cluster
cluster.name: mcps-cluster
node.name: node-1

# Network
network.host: 0.0.0.0
http.port: 9200

# Discovery (단일 노드)
discovery.type: single-node

# Security (PoC용 비활성화)
xpack.security.enabled: false
xpack.security.enrollment.enabled: false

# Memory
bootstrap.memory_lock: true

# Paths
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
EOF

# 4. JVM 힙 크기 설정
sudo sed -i 's/-Xms1g/-Xms4g/' /etc/elasticsearch/jvm.options
sudo sed -i 's/-Xmx1g/-Xmx4g/' /etc/elasticsearch/jvm.options

# 5. 시스템 제한 설정
sudo tee /etc/security/limits.d/elasticsearch.conf > /dev/null << 'EOF'
elasticsearch soft memlock unlimited
elasticsearch hard memlock unlimited
elasticsearch soft nofile 65536
elasticsearch hard nofile 65536
EOF

# 6. Systemd 설정
sudo mkdir -p /etc/systemd/system/elasticsearch.service.d
sudo tee /etc/systemd/system/elasticsearch.service.d/override.conf > /dev/null << 'EOF'
[Service]
LimitMEMLOCK=infinity
EOF

# 7. 시작
sudo systemctl daemon-reload
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# 8. 시작 대기
echo "Elasticsearch 시작 대기 중..."
sleep 30

# 9. 상태 확인
curl -X GET "localhost:9200/?pretty"

echo "✅ Elasticsearch 설치 완료"
```

### 3.4 사용자 및 디렉토리 설정

```bash
#!/bin/bash
# scripts/setup_user.sh
# 사용자 및 디렉토리 설정

set -e

echo "=== 사용자 및 디렉토리 설정 ==="

# 1. mcps 사용자 생성
sudo useradd -m -s /bin/bash mcps

# 2. 디렉토리 구조 생성
sudo mkdir -p /app/poc/mcps
sudo mkdir -p /app/poc/mcps/data/logs
sudo mkdir -p /app/poc/mcps/data/uploads
sudo mkdir -p /app/poc/mcps/data/backups

# 3. 소유권 설정
sudo chown -R mcps:mcps /app/poc/mcps

# 4. 권한 설정
sudo chmod -R 755 /app/poc/mcps
sudo chmod -R 770 /app/poc/mcps/data

echo "✅ 사용자 및 디렉토리 설정 완료"
```

***

## 4. 배포 절차

### 4.1 소스 코드 배포

```bash
#!/bin/bash
# scripts/deploy.sh
# 애플리케이션 배포 스크립트

set -e

VERSION=${1:-"main"}
DEPLOY_DIR="/app/poc/mcps"
BACKUP_DIR="/app/poc/mcps/data/backups"

echo "=== MCP 에코시스템 배포 ==="
echo "버전: $VERSION"

# 1. 백업 (기존 배포가 있는 경우)
if [ -d "$DEPLOY_DIR/shared" ]; then
    echo "기존 배포 백업..."
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    sudo -u mcps tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" \
        -C "$DEPLOY_DIR" \
        shared mcp-tools mcp-servers mcp-host config
    
    echo "✅ 백업 완료: backup_$TIMESTAMP.tar.gz"
fi

# 2. 소스 코드 다운로드
echo "소스 코드 다운로드..."
cd /tmp
rm -rf mcps-deploy
git clone -b $VERSION https://github.com/your-org/mcps.git mcps-deploy

# 3. 배포
echo "파일 복사..."
sudo -u mcps rsync -av \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='venv' \
    --exclude='.env' \
    /tmp/mcps-deploy/ \
    $DEPLOY_DIR/

# 4. 권한 설정
sudo chown -R mcps:mcps $DEPLOY_DIR
sudo chmod +x $DEPLOY_DIR/scripts/*.sh

echo "✅ 소스 코드 배포 완료"
```

### 4.2 환경 설정

```bash
#!/bin/bash
# scripts/configure.sh
# 환경 설정 스크립트

set -e

DEPLOY_DIR="/app/poc/mcps"

echo "=== 환경 설정 ==="

# 1. 환경 변수 파일 생성
sudo -u mcps tee $DEPLOY_DIR/.env > /dev/null << 'EOF'
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mcps_db
DB_USER=mcps_user
DB_PASSWORD=CHANGE_ME_DB_PASSWORD

# Elasticsearch
ES_HOST=localhost:9200
ES_TIMEOUT=30

# MCP Host
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=CHANGE_ME_SECRET_KEY
JWT_SECRET=CHANGE_ME_JWT_SECRET
EOF

echo "⚠️  .env 파일의 비밀번호를 변경하세요!"

# 2. 설정 파일 복사
if [ ! -f "$DEPLOY_DIR/config/services.json" ]; then
    sudo -u mcps cp $DEPLOY_DIR/config/services.json.example \
        $DEPLOY_DIR/config/services.json
fi

if [ ! -f "$DEPLOY_DIR/config/registry.json" ]; then
    sudo -u mcps cp $DEPLOY_DIR/config/registry.json.example \
        $DEPLOY_DIR/config/registry.json
fi

# 3. 로그 디렉토리 생성
sudo -u mcps mkdir -p $DEPLOY_DIR/data/logs/shared
sudo -u mcps mkdir -p $DEPLOY_DIR/data/logs/mcp-servers
sudo -u mcps mkdir -p $DEPLOY_DIR/data/logs/mcp-host

echo "✅ 환경 설정 완료"
```

### 4.3 의존성 설치

```bash
#!/bin/bash
# scripts/install_dependencies.sh
# 의존성 설치 스크립트

set -e

DEPLOY_DIR="/app/poc/mcps"

echo "=== 의존성 설치 ==="

# 1. 루트 의존성 설치
echo "루트 의존성 설치..."
cd $DEPLOY_DIR
sudo -u mcps python3 -m venv venv
sudo -u mcps ./venv/bin/pip install --upgrade pip
sudo -u mcps ./venv/bin/pip install -r requirements.txt

# 2. MCP Host 의존성
echo "MCP Host 의존성 설치..."
cd $DEPLOY_DIR/mcp-host
sudo -u mcps python3 -m venv venv
sudo -u mcps ./venv/bin/pip install --upgrade pip
sudo -u mcps ./venv/bin/pip install -r requirements.txt
sudo -u mcps ./venv/bin/pip install -r ../requirements.txt

# 3. MCP Servers 의존성
for server in auth_server search_server document_server version_server audit_server; do
    echo "Server 의존성 설치: $server"
    cd $DEPLOY_DIR/mcp-servers/core/$server
    
    sudo -u mcps python3 -m venv venv
    sudo -u mcps ./venv/bin/pip install --upgrade pip
    sudo -u mcps ./venv/bin/pip install -r requirements.txt 2>/dev/null || true
    sudo -u mcps ./venv/bin/pip install -r ../../../../requirements.txt
done

echo "✅ 의존성 설치 완료"
```

### 4.4 Database 초기화

```bash
#!/bin/bash
# scripts/init_database.sh
# Database 초기화 스크립트

set -e

DEPLOY_DIR="/app/poc/mcps"

echo "=== Database 초기화 ==="

# 환경 변수 로드
source $DEPLOY_DIR/.env

# 1. Database 생성
echo "Database 생성..."
mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

# 2. 스키마 생성
echo "스키마 생성..."
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < $DEPLOY_DIR/database/schema.sql

# 3. 초기 데이터 입력
echo "초기 데이터 입력..."
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < $DEPLOY_DIR/database/seed_data.sql

# 4. 확인
echo "테이블 확인..."
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "SHOW TABLES;"

echo "✅ Database 초기화 완료"
```

### 4.5 Elasticsearch 초기화

```bash
#!/bin/bash
# scripts/init_elasticsearch.sh
# Elasticsearch 초기화 스크립트

set -e

DEPLOY_DIR="/app/poc/mcps"
ES_HOST="localhost:9200"

echo "=== Elasticsearch 초기화 ==="

# 1. 인덱스 생성
echo "documents 인덱스 생성..."
curl -X PUT "http://$ES_HOST/documents" -H 'Content-Type: application/json' -d@- << 'EOF'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "korean": {
          "type": "custom",
          "tokenizer": "nori_tokenizer",
          "filter": ["lowercase", "nori_part_of_speech"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "doc_id": {
        "type": "keyword"
      },
      "title": {
        "type": "text",
        "analyzer": "korean",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "content": {
        "type": "text",
        "analyzer": "korean"
      },
      "classification": {
        "type": "keyword"
      },
      "category": {
        "type": "keyword"
      },
      "tags": {
        "type": "keyword"
      },
      "author_id": {
        "type": "keyword"
      },
      "created_at": {
        "type": "date"
      },
      "updated_at": {
        "type": "date"
      }
    }
  }
}
EOF

echo ""
echo "✅ Elasticsearch 초기화 완료"
```

### 4.6 Systemd 서비스 등록

```bash
#!/bin/bash
# scripts/install_services.sh
# Systemd 서비스 등록 스크립트

set -e

echo "=== Systemd 서비스 등록 ==="

# 1. MCP Host 서비스
cat > /etc/systemd/system/mcp-host.service << 'EOF'
[Unit]
Description=MCP Host Service
After=network.target mariadb.service elasticsearch.service

[Service]
Type=simple
User=mcps
Group=mcps
WorkingDirectory=/app/poc/mcps/mcp-host
EnvironmentFile=/app/poc/mcps/.env
ExecStart=/app/poc/mcps/mcp-host/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:/app/poc/mcps/data/logs/mcp-host/mcp_host.log
StandardError=append:/app/poc/mcps/data/logs/mcp-host/mcp_host_error.log

[Install]
WantedBy=multi-user.target
EOF

# 2. MCP Servers 서비스
for server in auth_server search_server document_server version_server audit_server; do
    cat > /etc/systemd/system/mcp-$server.service << EOF
[Unit]
Description=MCP $server
After=network.target mariadb.service elasticsearch.service

[Service]
Type=simple
User=mcps
Group=mcps
WorkingDirectory=/app/poc/mcps/mcp-servers/core/$server
EnvironmentFile=/app/poc/mcps/.env
ExecStart=/app/poc/mcps/mcp-servers/core/$server/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:/app/poc/mcps/data/logs/mcp-servers/${server}.log
StandardError=append:/app/poc/mcps/data/logs/mcp-servers/${server}_error.log

[Install]
WantedBy=multi-user.target
EOF
done

# 3. Daemon reload
systemctl daemon-reload

# 4. 서비스 활성화
systemctl enable mcp-host
for server in auth_server search_server document_server version_server audit_server; do
    systemctl enable mcp-$server
done

echo "✅ Systemd 서비스 등록 완료"
```

### 4.7 배포 확인

```bash
#!/bin/bash
# scripts/verify_deployment.sh
# 배포 확인 스크립트

set -e

echo "=== 배포 확인 ==="

# 1. 서비스 시작
echo "서비스 시작..."
systemctl start mcp-auth-server
systemctl start mcp-search-server
systemctl start mcp-document-server
systemctl start mcp-version-server
systemctl start mcp-audit-server

sleep 5

systemctl start mcp-host

sleep 5

# 2. 서비스 상태 확인
echo ""
echo "=== 서비스 상태 ==="
systemctl status mcp-host --no-pager
systemctl status mcp-auth-server --no-pager
systemctl status mcp-search-server --no-pager
systemctl status mcp-document-server --no-pager
systemctl status mcp-version-server --no-pager
systemctl status mcp-audit-server --no-pager

# 3. API 헬스 체크
echo ""
echo "=== API 헬스 체크 ==="
sleep 5
curl -s http://localhost:8000/health | jq .

# 4. Tool 목록 확인
echo ""
echo "=== Tool 목록 확인 ==="
curl -s http://localhost:8000/api/tools/list | jq '.total'

echo ""
echo "✅ 배포 확인 완료"
```

***

## 5. 운영 관리

### 5.1 서비스 관리 스크립트

```bash
#!/bin/bash
# scripts/manage_services.sh
# 서비스 관리 스크립트

ACTION=$1

SERVICES=(
    "mcp-auth-server"
    "mcp-search-server"
    "mcp-document-server"
    "mcp-version-server"
    "mcp-audit-server"
    "mcp-host"
)

case $ACTION in
    start)
        echo "=== 서비스 시작 ==="
        for service in "${SERVICES[@]}"; do
            echo "Starting $service..."
            systemctl start $service
        done
        ;;
    
    stop)
        echo "=== 서비스 중지 ==="
        # 역순으로 중지
        for ((idx=${#SERVICES[@]}-1 ; idx>=0 ; idx--)); do
            service="${SERVICES[idx]}"
            echo "Stopping $service..."
            systemctl stop $service
        done
        ;;
    
    restart)
        echo "=== 서비스 재시작 ==="
        $0 stop
        sleep 3
        $0 start
        ;;
    
    status)
        echo "=== 서비스 상태 ==="
        for service in "${SERVICES[@]}"; do
            systemctl status $service --no-pager | head -3
            echo ""
        done
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
```

### 5.2 로그 관리

```bash
#!/bin/bash
# scripts/manage_logs.sh
# 로그 관리 스크립트

LOG_DIR="/app/poc/mcps/data/logs"

ACTION=$1
DAYS=${2:-7}

case $ACTION in
    rotate)
        echo "=== 로그 로테이션 ==="
        find $LOG_DIR -name "*.log" -type f -exec sh -c '
            for file do
                if [ -f "$file" ]; then
                    timestamp=$(date +%Y%m%d_%H%M%S)
                    mv "$file" "${file}.${timestamp}"
                    touch "$file"
                    gzip "${file}.${timestamp}"
                fi
            done
        ' sh {} +
        echo "✅ 로그 로테이션 완료"
        ;;
    
    clean)
        echo "=== 오래된 로그 삭제 ($DAYS일 이전) ==="
        find $LOG_DIR -name "*.log.*.gz" -mtime +$DAYS -delete
        echo "✅ 로그 정리 완료"
        ;;
    
    view)
        SERVICE=$2
        if [ -z "$SERVICE" ]; then
            echo "Usage: $0 view SERVICE_NAME"
            exit 1
        fi
        
        LOG_FILE="$LOG_DIR/$SERVICE/${SERVICE}.log"
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "Log file not found: $LOG_FILE"
            exit 1
        fi
        ;;
    
    *)
        echo "Usage: $0 {rotate|clean [DAYS]|view SERVICE_NAME}"
        exit 1
        ;;
esac
```

### 5.3 데이터 관리

```python
# scripts/manage_data.py
"""
데이터 관리 스크립트

문서 정리, 인덱스 최적화 등
"""

import sys
from pathlib import Path

# PYTHONPATH 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
import argparse
from datetime import datetime, timedelta


def cleanup_old_versions(db: DatabaseManager, days: int = 90):
    """오래된 버전 정리"""
    print(f"=== 오래된 버전 정리 ({days}일 이전) ===")
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # 각 문서의 최근 5개 버전만 유지
    result = db.execute_query("""
        SELECT doc_id, COUNT(*) as version_count
        FROM document_versions
        GROUP BY doc_id
        HAVING version_count > 5
    """)
    
    total_deleted = 0
    
    for row in result:
        doc_id = row["doc_id"]
        
        # 오래된 버전 삭제 (최근 5개 제외)
        deleted = db.execute_update("""
            DELETE FROM document_versions
            WHERE doc_id = %s
            AND version NOT IN (
                SELECT version FROM (
                    SELECT version
                    FROM document_versions
                    WHERE doc_id = %s
                    ORDER BY version DESC
                    LIMIT 5
                ) AS recent
            )
            AND created_at < %s
        """, (doc_id, doc_id, cutoff_date))
        
        total_deleted += deleted
        
        if deleted > 0:
            print(f"  {doc_id}: {deleted}개 버전 삭제")
    
    print(f"✅ 총 {total_deleted}개 버전 삭제")


def cleanup_old_audit_logs(db: DatabaseManager, days: int = 180):
    """오래된 감사 로그 정리"""
    print(f"=== 오래된 감사 로그 정리 ({days}일 이전) ===")
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    deleted = db.execute_update("""
        DELETE FROM audit_logs
        WHERE created_at < %s
    """, (cutoff_date,))
    
    print(f"✅ {deleted}개 로그 삭제")


def optimize_elasticsearch(es: ElasticsearchManager):
    """Elasticsearch 최적화"""
    print("=== Elasticsearch 최적화 ===")
    
    index_name = "documents"
    
    # 1. Force merge
    print(f"Force merge: {index_name}")
    es.es.indices.forcemerge(index=index_name, max_num_segments=1)
    
    # 2. 인덱스 통계
    stats = es.es.indices.stats(index=index_name)
    doc_count = stats["indices"][index_name]["total"]["docs"]["count"]
    size_bytes = stats["indices"][index_name]["total"]["store"]["size_in_bytes"]
    size_mb = size_bytes / (1024 * 1024)
    
    print(f"  문서 수: {doc_count}")
    print(f"  크기: {size_mb:.2f} MB")
    
    print("✅ 최적화 완료")


def main():
    parser = argparse.ArgumentParser(description="데이터 관리")
    parser.add_argument(
        "action",
        choices=["cleanup_versions", "cleanup_logs", "optimize_es", "all"],
        help="실행할 작업"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="정리할 일수 (기본: 90)"
    )
    
    args = parser.parse_args()
    
    # Database 연결
    db_config = {
        "host": "localhost",
        "port": 3306,
        "database": "mcps_db",
        "user": "mcps_user",
        "password": "your_password",
        "charset": "utf8mb4",
        "pool_size": {"min": 1, "max": 5}
    }
    
    db = DatabaseManager(db_config)
    
    # Elasticsearch 연결
    es_config = {
        "hosts": ["localhost:9200"],
        "timeout": 30
    }
    
    es = ElasticsearchManager(es_config)
    
    try:
        if args.action == "cleanup_versions" or args.action == "all":
            cleanup_old_versions(db, args.days)
        
        if args.action == "cleanup_logs" or args.action == "all":
            cleanup_old_audit_logs(db, 180)
        
        if args.action == "optimize_es" or args.action == "all":
            optimize_elasticsearch(es)
        
        print("\n✅ 데이터 관리 완료")
    
    finally:
        db.close()
        es.close()


if __name__ == "__main__":
    main()
```



### 5.4 업데이트 절차

```bash
#!/bin/bash
# scripts/update.sh
# 시스템 업데이트 스크립트

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: $0 VERSION"
    exit 1
fi

echo "=== MCP 에코시스템 업데이트 ==="
echo "버전: $VERSION"
echo ""

# 1. 사전 확인
read -p "업데이트를 계속하시겠습니까? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 2. 백업
echo "시스템 백업..."
./scripts/backup.sh

# 3. 서비스 중지
echo "서비스 중지..."
./scripts/manage_services.sh stop

# 4. 코드 업데이트
echo "코드 업데이트..."
./scripts/deploy.sh $VERSION

# 5. 의존성 업데이트
echo "의존성 업데이트..."
./scripts/install_dependencies.sh

# 6. Database 마이그레이션 (필요시)
if [ -f "/app/poc/mcps/database/migrations/$VERSION.sql" ]; then
    echo "Database 마이그레이션..."
    source /app/poc/mcps/.env
    mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < /app/poc/mcps/database/migrations/$VERSION.sql
fi

# 7. 서비스 시작
echo "서비스 시작..."
./scripts/manage_services.sh start

# 8. 헬스 체크
echo "헬스 체크..."
sleep 10
curl -f http://localhost:8000/health || {
    echo "❌ 헬스 체크 실패"
    echo "롤백을 수행하시겠습니까?"
    read -p "(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./scripts/rollback.sh
    fi
    exit 1
}

echo ""
echo "✅ 업데이트 완료"
```

### 5.5 롤백 절차

```bash
#!/bin/bash
# scripts/rollback.sh
# 롤백 스크립트

set -e

BACKUP_DIR="/app/poc/mcps/data/backups"

echo "=== 롤백 ==="

# 1. 가장 최근 백업 찾기
LATEST_BACKUP=$(ls -t $BACKUP_DIR/backup_*.tar.gz | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ 백업 파일을 찾을 수 없습니다"
    exit 1
fi

echo "복구할 백업: $LATEST_BACKUP"
read -p "계속하시겠습니까? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 2. 서비스 중지
echo "서비스 중지..."
./scripts/manage_services.sh stop

# 3. 백업 복구
echo "백업 복구..."
cd /app/poc/mcps
sudo -u mcps tar -xzf $LATEST_BACKUP

# 4. 서비스 시작
echo "서비스 시작..."
./scripts/manage_services.sh start

# 5. 헬스 체크
echo "헬스 체크..."
sleep 10
curl -f http://localhost:8000/health

echo ""
echo "✅ 롤백 완료"
```

***

## 6. 모니터링

### 6.1 시스템 모니터링

```python
# scripts/monitor.py
"""
시스템 모니터링 스크립트

CPU, 메모리, 디스크, 네트워크 등 모니터링
"""

import psutil
import time
import json
from datetime import datetime
from pathlib import Path


class SystemMonitor:
    """시스템 모니터"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def collect_metrics(self) -> dict:
        """메트릭 수집"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": self.get_cpu_metrics(),
            "memory": self.get_memory_metrics(),
            "disk": self.get_disk_metrics(),
            "network": self.get_network_metrics(),
            "processes": self.get_process_metrics()
        }
    
    def get_cpu_metrics(self) -> dict:
        """CPU 메트릭"""
        return {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
            "load_avg": psutil.getloadavg()
        }
    
    def get_memory_metrics(self) -> dict:
        """메모리 메트릭"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total_gb": mem.total / (1024**3),
            "available_gb": mem.available / (1024**3),
            "used_gb": mem.used / (1024**3),
            "percent": mem.percent,
            "swap_percent": swap.percent
        }
    
    def get_disk_metrics(self) -> dict:
        """디스크 메트릭"""
        disk = psutil.disk_usage('/')
        
        return {
            "total_gb": disk.total / (1024**3),
            "used_gb": disk.used / (1024**3),
            "free_gb": disk.free / (1024**3),
            "percent": disk.percent
        }
    
    def get_network_metrics(self) -> dict:
        """네트워크 메트릭"""
        net = psutil.net_io_counters()
        
        return {
            "bytes_sent_mb": net.bytes_sent / (1024**2),
            "bytes_recv_mb": net.bytes_recv / (1024**2),
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv
        }
    
    def get_process_metrics(self) -> dict:
        """프로세스 메트릭"""
        mcps_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['username'] == 'mcps':
                    mcps_processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cpu_percent": proc.info['cpu_percent'],
                        "memory_percent": proc.info['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return {
            "total_processes": len(psutil.pids()),
            "mcps_processes": mcps_processes
        }
    
    def save_metrics(self, metrics: dict):
        """메트릭 저장"""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(metrics) + '\n')
    
    def print_summary(self, metrics: dict):
        """요약 출력"""
        print(f"\n=== 시스템 모니터링 ({metrics['timestamp']}) ===")
        
        print(f"\n[CPU]")
        print(f"  사용률: {metrics['cpu']['percent']:.1f}%")
        print(f"  Load Average: {', '.join(f'{x:.2f}' for x in metrics['cpu']['load_avg'])}")
        
        print(f"\n[메모리]")
        print(f"  총: {metrics['memory']['total_gb']:.1f} GB")
        print(f"  사용: {metrics['memory']['used_gb']:.1f} GB ({metrics['memory']['percent']:.1f}%)")
        print(f"  가용: {metrics['memory']['available_gb']:.1f} GB")
        
        print(f"\n[디스크]")
        print(f"  총: {metrics['disk']['total_gb']:.1f} GB")
        print(f"  사용: {metrics['disk']['used_gb']:.1f} GB ({metrics['disk']['percent']:.1f}%)")
        print(f"  여유: {metrics['disk']['free_gb']:.1f} GB")
        
        print(f"\n[프로세스]")
        print(f"  총 프로세스: {metrics['processes']['total_processes']}")
        print(f"  MCPS 프로세스: {len(metrics['processes']['mcps_processes'])}")
        
        for proc in metrics['processes']['mcps_processes']:
            print(f"    - {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu_percent']:.1f}%, MEM: {proc['memory_percent']:.1f}%")
    
    def check_alerts(self, metrics: dict) -> list:
        """알림 체크"""
        alerts = []
        
        # CPU 알림
        if metrics['cpu']['percent'] > 80:
            alerts.append({
                "level": "warning",
                "message": f"CPU 사용률 높음: {metrics['cpu']['percent']:.1f}%"
            })
        
        # 메모리 알림
        if metrics['memory']['percent'] > 80:
            alerts.append({
                "level": "warning",
                "message": f"메모리 사용률 높음: {metrics['memory']['percent']:.1f}%"
            })
        
        # 디스크 알림
        if metrics['disk']['percent'] > 80:
            alerts.append({
                "level": "warning",
                "message": f"디스크 사용률 높음: {metrics['disk']['percent']:.1f}%"
            })
        
        return alerts
    
    def run(self, interval: int = 60):
        """모니터링 시작"""
        print("시스템 모니터링 시작...")
        
        try:
            while True:
                metrics = self.collect_metrics()
                self.save_metrics(metrics)
                self.print_summary(metrics)
                
                # 알림 체크
                alerts = self.check_alerts(metrics)
                if alerts:
                    print("\n⚠️  알림:")
                    for alert in alerts:
                        print(f"  [{alert['level'].upper()}] {alert['message']}")
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n모니터링 중지")


def main():
    log_file = Path("/app/poc/mcps/data/logs/system_metrics.log")
    monitor = SystemMonitor(log_file)
    monitor.run(interval=60)


if __name__ == "__main__":
    main()
```

### 6.2 애플리케이션 모니터링

```python
# scripts/monitor_app.py
"""
애플리케이션 모니터링 스크립트

API 응답 시간, 에러율 등 모니터링
"""

import requests
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class AppMonitor:
    """애플리케이션 모니터"""
    
    def __init__(self, base_url: str, log_file: Path):
        self.base_url = base_url
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_id = None
    
    def check_health(self) -> Dict:
        """헬스 체크"""
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=5)
            elapsed = (time.time() - start) * 1000
            
            return {
                "status": "ok" if response.status_code == 200 else "error",
                "response_time_ms": elapsed,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_api(self) -> Dict:
        """API 체크"""
        results = {}
        
        # 1. 세션 생성
        try:
            start = time.time()
            response = requests.post(
                f"{self.base_url}/api/sessions",
                json={"user_id": "U002"},
                timeout=10
            )
            elapsed = (time.time() - start) * 1000
            
            results["create_session"] = {
                "status": "ok" if response.status_code == 201 else "error",
                "response_time_ms": elapsed,
                "status_code": response.status_code
            }
            
            if response.status_code == 201:
                self.session_id = response.json()["session_id"]
        except Exception as e:
            results["create_session"] = {
                "status": "error",
                "error": str(e)
            }
        
        # 2. Tool 목록 조회
        try:
            start = time.time()
            response = requests.get(
                f"{self.base_url}/api/tools/list",
                timeout=10
            )
            elapsed = (time.time() - start) * 1000
            
            results["list_tools"] = {
                "status": "ok" if response.status_code == 200 else "error",
                "response_time_ms": elapsed,
                "status_code": response.status_code,
                "tool_count": response.json().get("total", 0) if response.status_code == 200 else 0
            }
        except Exception as e:
            results["list_tools"] = {
                "status": "error",
                "error": str(e)
            }
        
        # 3. Tool 실행 (검색)
        if self.session_id:
            try:
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/api/tools/execute",
                    json={
                        "session_id": self.session_id,
                        "tool": "search_documents",
                        "arguments": {
                            "query": "test",
                            "limit": 5
                        }
                    },
                    timeout=30
                )
                elapsed = (time.time() - start) * 1000
                
                results["execute_tool"] = {
                    "status": "ok" if response.status_code == 200 else "error",
                    "response_time_ms": elapsed,
                    "status_code": response.status_code
                }
            except Exception as e:
                results["execute_tool"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    def collect_metrics(self) -> Dict:
        """메트릭 수집"""
        return {
            "timestamp": datetime.now().isoformat(),
            "health": self.check_health(),
            "api": self.check_api()
        }
    
    def save_metrics(self, metrics: Dict):
        """메트릭 저장"""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(metrics) + '\n')
    
    def print_summary(self, metrics: Dict):
        """요약 출력"""
        print(f"\n=== 애플리케이션 모니터링 ({metrics['timestamp']}) ===")
        
        # 헬스
        health = metrics['health']
        status_icon = "✅" if health['status'] == 'ok' else "❌"
        print(f"\n{status_icon} Health: {health['status']}")
        if 'response_time_ms' in health:
            print(f"  응답 시간: {health['response_time_ms']:.2f}ms")
        
        # API
        print(f"\n[API 체크]")
        for endpoint, result in metrics['api'].items():
            status_icon = "✅" if result['status'] == 'ok' else "❌"
            print(f"{status_icon} {endpoint}: {result['status']}")
            
            if 'response_time_ms' in result:
                print(f"    응답 시간: {result['response_time_ms']:.2f}ms")
            
            if 'error' in result:
                print(f"    에러: {result['error']}")
    
    def check_alerts(self, metrics: Dict) -> List[Dict]:
        """알림 체크"""
        alerts = []
        
        # 헬스 체크 실패
        if metrics['health']['status'] != 'ok':
            alerts.append({
                "level": "critical",
                "message": "Health check failed"
            })
        
        # API 응답 시간
        for endpoint, result in metrics['api'].items():
            if 'response_time_ms' in result and result['response_time_ms'] > 1000:
                alerts.append({
                    "level": "warning",
                    "message": f"{endpoint} 응답 시간 느림: {result['response_time_ms']:.2f}ms"
                })
        
        # API 에러
        for endpoint, result in metrics['api'].items():
            if result['status'] == 'error':
                alerts.append({
                    "level": "error",
                    "message": f"{endpoint} 실패"
                })
        
        return alerts
    
    def run(self, interval: int = 60):
        """모니터링 시작"""
        print("애플리케이션 모니터링 시작...")
        
        try:
            while True:
                metrics = self.collect_metrics()
                self.save_metrics(metrics)
                self.print_summary(metrics)
                
                # 알림 체크
                alerts = self.check_alerts(metrics)
                if alerts:
                    print("\n⚠️  알림:")
                    for alert in alerts:
                        print(f"  [{alert['level'].upper()}] {alert['message']}")
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n모니터링 중지")


def main():
    base_url = "http://localhost:8000"
    log_file = Path("/app/poc/mcps/data/logs/app_metrics.log")
    
    monitor = AppMonitor(base_url, log_file)
    monitor.run(interval=60)


if __name__ == "__main__":
    main()
```

### 6.3 모니터링 대시보드 (Grafana 연동 예시)

```python
# scripts/export_metrics_prometheus.py
"""
Prometheus 메트릭 내보내기

Grafana와 연동을 위한 Prometheus 포맷 메트릭
"""

from prometheus_client import start_http_server, Gauge, Counter
import time
import psutil
import requests


# 메트릭 정의
system_cpu_percent = Gauge('mcps_system_cpu_percent', 'CPU usage percentage')
system_memory_percent = Gauge('mcps_system_memory_percent', 'Memory usage percentage')
system_disk_percent = Gauge('mcps_system_disk_percent', 'Disk usage percentage')

api_health_status = Gauge('mcps_api_health_status', 'API health status (1=ok, 0=error)')
api_response_time = Gauge('mcps_api_response_time_ms', 'API response time in milliseconds', ['endpoint'])
api_request_total = Counter('mcps_api_request_total', 'Total API requests', ['endpoint', 'status'])


def collect_system_metrics():
    """시스템 메트릭 수집"""
    system_cpu_percent.set(psutil.cpu_percent(interval=1))
    system_memory_percent.set(psutil.virtual_memory().percent)
    system_disk_percent.set(psutil.disk_usage('/').percent)


def collect_api_metrics():
    """API 메트릭 수집"""
    base_url = "http://localhost:8000"
    
    # Health check
    try:
        start = time.time()
        response = requests.get(f"{base_url}/health", timeout=5)
        elapsed = (time.time() - start) * 1000
        
        api_health_status.set(1 if response.status_code == 200 else 0)
        api_response_time.labels(endpoint='health').set(elapsed)
        api_request_total.labels(endpoint='health', status=response.status_code).inc()
    except:
        api_health_status.set(0)


def main():
    # Prometheus 서버 시작 (포트 9090)
    start_http_server(9090)
    print("Prometheus 메트릭 서버 시작: http://localhost:9090")
    
    while True:
        collect_system_metrics()
        collect_api_metrics()
        time.sleep(15)  # 15초마다 수집


if __name__ == "__main__":
    main()
```

***

## 7. 백업 및 복구

### 7.1 백업 스크립트

```bash
#!/bin/bash
# scripts/backup.sh
# 전체 백업 스크립트

set -e

BACKUP_DIR="/app/poc/mcps/data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_$TIMESTAMP"

echo "=== 시스템 백업 ==="
echo "백업 시작: $(date)"

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# 1. 애플리케이션 백업
echo "애플리케이션 백업..."
cd /app/poc/mcps
tar -czf "$BACKUP_DIR/$BACKUP_NAME/app.tar.gz" \
    --exclude='venv' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='data/logs' \
    --exclude='data/backups' \
    shared mcp-tools mcp-servers mcp-host config

# 2. Database 백업
echo "Database 백업..."
source /app/poc/mcps/.env

mysqldump -u $DB_USER -p$DB_PASSWORD \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    $DB_NAME | gzip > "$BACKUP_DIR/$BACKUP_NAME/database.sql.gz"

# 3. Elasticsearch 백업 (스냅샷)
echo "Elasticsearch 백업..."
curl -X PUT "localhost:9200/_snapshot/mcps_backup" -H 'Content-Type: application/json' -d@- << EOF
{
  "type": "fs",
  "settings": {
    "location": "$BACKUP_DIR/$BACKUP_NAME/elasticsearch"
  }
}
EOF

curl -X PUT "localhost:9200/_snapshot/mcps_backup/snapshot_$TIMESTAMP?wait_for_completion=true"

# 4. 설정 파일 백업
echo "설정 파일 백업..."
cp /app/poc/mcps/.env "$BACKUP_DIR/$BACKUP_NAME/"
cp /etc/systemd/system/mcp-*.service "$BACKUP_DIR/$BACKUP_NAME/" 2>/dev/null || true

# 5. 백업 압축
echo "백업 압축..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# 6. 오래된 백업 삭제 (30일 이전)
echo "오래된 백업 정리..."
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete

BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)

echo ""
echo "✅ 백업 완료"
echo "백업 파일: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "백업 크기: $BACKUP_SIZE"
echo "백업 종료: $(date)"
```

### 7.2 복구 스크립트

```bash
#!/bin/bash
# scripts/restore.sh
# 백업 복구 스크립트

set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 BACKUP_FILE"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "백업 파일을 찾을 수 없습니다: $BACKUP_FILE"
    exit 1
fi

echo "=== 시스템 복구 ==="
echo "백업 파일: $BACKUP_FILE"
echo ""

read -p "복구를 계속하시겠습니까? 현재 데이터는 삭제됩니다. (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 1. 서비스 중지
echo "서비스 중지..."
/app/poc/mcps/scripts/manage_services.sh stop

# 2. 백업 압축 해제
echo "백업 압축 해제..."
TEMP_DIR="/tmp/mcps_restore_$$"
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

BACKUP_NAME=$(basename "$BACKUP_FILE" .tar.gz)
RESTORE_DIR="$TEMP_DIR/$BACKUP_NAME"

# 3. 애플리케이션 복구
echo "애플리케이션 복구..."
cd /app/poc/mcps
rm -rf shared mcp-tools mcp-servers mcp-host config
tar -xzf "$RESTORE_DIR/app.tar.gz"

# 4. Database 복구
echo "Database 복구..."
source "$RESTORE_DIR/.env"

# 기존 Database 삭제 및 재생성
mysql -u root -p << EOF
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

# 백업 복구
gunzip < "$RESTORE_DIR/database.sql.gz" | mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME

# 5. Elasticsearch 복구
echo "Elasticsearch 복구..."
# 인덱스 삭제
curl -X DELETE "localhost:9200/documents"

# 스냅샷 복구
curl -X POST "localhost:9200/_snapshot/mcps_backup/snapshot_*/restore?wait_for_completion=true"

# 6. 설정 파일 복구
echo "설정 파일 복구..."
cp "$RESTORE_DIR/.env" /app/poc/mcps/
cp "$RESTORE_DIR"/mcp-*.service /etc/systemd/system/ 2>/dev/null || true

# 7. 권한 설정
chown -R mcps:mcps /app/poc/mcps

# 8. 서비스 재시작
echo "서비스 시작..."
systemctl daemon-reload
/app/poc/mcps/scripts/manage_services.sh start

# 9. 정리
rm -rf "$TEMP_DIR"

echo ""
echo "✅ 복구 완료"
echo "헬스 체크를 수행하세요: curl http://localhost:8000/health"
```

### 7.3 자동 백업 설정 (Cron)

```bash
#!/bin/bash
# scripts/setup_cron_backup.sh
# Cron 자동 백업 설정

# 매일 새벽 2시에 백업
CRON_JOB="0 2 * * * /app/poc/mcps/scripts/backup.sh >> /app/poc/mcps/data/logs/backup.log 2>&1"

# Cron에 등록
(crontab -u mcps -l 2>/dev/null; echo "$CRON_JOB") | crontab -u mcps -

echo "✅ 자동 백업 설정 완료"
echo "스케줄: 매일 새벽 2시"
echo ""
echo "Cron 확인: crontab -u mcps -l"
```

***

## 8. 트러블슈팅

### 8.1 일반적인 문제

```markdown
# 트러블슈팅 가이드

## 1. 서비스가 시작되지 않음

### 증상
```bash
systemctl start mcp-host
Job for mcp-host.service failed...
```

### 원인 및 해결

#### 원인 1: 포트 충돌
```bash
# 포트 사용 확인
lsof -i :8000

# 프로세스 종료
kill -9 PID
```

#### 원인 2: 환경 변수 오류
```bash
# .env 파일 확인
cat /app/poc/mcps/.env

# 필수 변수 확인
grep -E "DB_|ES_|HOST" /app/poc/mcps/.env
```

#### 원인 3: 의존성 누락
```bash
# 의존성 재설치
cd /app/poc/mcps/mcp-host
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Database 연결 실패

### 증상
```
Can't connect to MySQL server on 'localhost'
```

### 해결
```bash
# MariaDB 상태 확인
systemctl status mariadb

# MariaDB 시작
systemctl start mariadb

# 연결 테스트
mysql -u mcps_user -p mcps_db
```

## 3. Elasticsearch 연결 실패

### 증상
```
ConnectionError: Connection refused
```

### 해결
```bash
# Elasticsearch 상태 확인
systemctl status elasticsearch

# 로그 확인
journalctl -u elasticsearch -n 50

# 재시작
systemctl restart elasticsearch

# 헬스 체크
curl http://localhost:9200/_cluster/health?pretty
```

## 4. 높은 CPU/메모리 사용률

### 원인 및 해결

#### 원인 1: 프로세스 폭주
```bash
# CPU 사용률 높은 프로세스 확인
top -u mcps

# 프로세스 재시작
systemctl restart mcp-host
```

#### 원인 2: 메모리 누수
```bash
# 메모리 사용 확인
ps aux | grep python | sort -k4 -r

# 서비스 재시작
systemctl restart mcp-*
```

#### 원인 3: Database 쿼리 최적화 필요
```sql
-- 느린 쿼리 확인
SELECT * FROM mysql.slow_log ORDER BY query_time DESC LIMIT 10;

-- 인덱스 확인
SHOW INDEX FROM documents;
```

## 5. API 응답 느림

### 진단
```bash
# API 응답 시간 측정
time curl http://localhost:8000/api/tools/list

# 로그 확인
tail -f /app/poc/mcps/data/logs/mcp-host/mcp_host.log
```

### 해결

#### Elasticsearch 최적화
```bash
# Force merge
curl -X POST "localhost:9200/documents/_forcemerge?max_num_segments=1"

# Cache 클리어
curl -X POST "localhost:9200/_cache/clear"
```

#### Database 최적화
```sql
-- 테이블 최적화
OPTIMIZE TABLE documents, document_versions, audit_logs;

-- 인덱스 재구성
ANALYZE TABLE documents;
```

## 6. 디스크 공간 부족

### 해결
```bash
# 디스크 사용량 확인
df -h

# 큰 파일 찾기
du -sh /app/poc/mcps/* | sort -h

# 로그 정리
/app/poc/mcps/scripts/manage_logs.sh clean 7

# 백업 정리
find /app/poc/mcps/data/backups -name "*.tar.gz" -mtime +30 -delete
```

## 7. 권한 오류

### 증상
```
Permission denied
```

### 해결
```bash
# 소유권 수정
chown -R mcps:mcps /app/poc/mcps

# 권한 수정
chmod -R 755 /app/poc/mcps
chmod -R 770 /app/poc/mcps/data
```
```

### 8.2 로그 분석

```bash
#!/bin/bash
# scripts/analyze_logs.sh
# 로그 분석 스크립트

LOG_DIR="/app/poc/mcps/data/logs"
LOG_FILE=$1

if [ -z "$LOG_FILE" ]; then
    echo "Usage: $0 LOG_FILE"
    echo "Example: $0 mcp-host/mcp_host.log"
    exit 1
fi

FULL_PATH="$LOG_DIR/$LOG_FILE"

if [ ! -f "$FULL_PATH" ]; then
    echo "로그 파일을 찾을 수 없습니다: $FULL_PATH"
    exit 1
fi

echo "=== 로그 분석: $LOG_FILE ==="
echo ""

# 1. 에러 수
echo "[에러 통계]"
ERROR_COUNT=$(grep -c "ERROR" "$FULL_PATH" || true)
WARNING_COUNT=$(grep -c "WARNING" "$FULL_PATH" || true)

echo "ERROR: $ERROR_COUNT"
echo "WARNING: $WARNING_COUNT"
echo ""

# 2. 최근 에러
echo "[최근 에러 (최대 10개)]"
grep "ERROR" "$FULL_PATH" | tail -10
echo ""

# 3. 가장 많이 발생한 에러
echo "[가장 많이 발생한 에러 TOP 5]"
grep "ERROR" "$FULL_PATH" | \
    awk -F'ERROR' '{print $2}' | \
    sort | uniq -c | sort -rn | head -5
echo ""

# 4. 시간대별 에러 분포
echo "[시간대별 에러 분포]"
grep "ERROR" "$FULL_PATH" | \
    awk '{print $1}' | \
    cut -d: -f1 | \
    sort | uniq -c
```

### 8.3 긴급 대응 절차

```markdown
# 긴급 대응 절차

## 1단계: 상황 파악 (1-2분)

### 체크리스트
- [ ] 서비스 상태 확인
- [ ] 에러 로그 확인
- [ ] 시스템 리소스 확인
- [ ] 외부 의존성 확인 (Database, Elasticsearch)

### 명령어
```bash
# 전체 상태 확인
./scripts/health_check.sh

# 서비스 상태
systemctl status mcp-*

# 리소스 확인
top
df -h
```

## 2단계: 임시 조치 (3-5분)

### 옵션 A: 서비스 재시작
```bash
./scripts/manage_services.sh restart
```

### 옵션 B: 특정 서버만 재시작
```bash
systemctl restart mcp-host
```

### 옵션 C: 롤백
```bash
./scripts/rollback.sh
```

## 3단계: 근본 원인 분석 (10-30분)

### 로그 분석
```bash
# 에러 로그 분석
./scripts/analyze_logs.sh mcp-host/mcp_host.log

# 최근 변경 사항 확인
git log --oneline -10
```

### Database 확인
```sql
-- 연결 수 확인
SHOW PROCESSLIST;

-- 느린 쿼리
SELECT * FROM mysql.slow_log ORDER BY query_time DESC LIMIT 10;
```

### Elasticsearch 확인
```bash
# 클러스터 상태
curl http://localhost:9200/_cluster/health?pretty

# 노드 통계
curl http://localhost:9200/_nodes/stats?pretty
```

## 4단계: 영구 해결 (시간 가변)

### 문제별 해결책
- **코드 버그**: 핫픽스 배포
- **설정 오류**: 설정 수정 및 재시작
- **리소스 부족**: 스케일 업/아웃
- **Database 문제**: 쿼리 최적화, 인덱스 추가
- **Elasticsearch 문제**: 인덱스 최적화, 클러스터 조정

## 5단계: 사후 검토

### 문서화
- [ ] 장애 보고서 작성
- [ ] 타임라인 정리
- [ ] 근본 원인 문서화
- [ ] 재발 방지 대책 수립
```

***

## 9. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

***

## 10. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| **작성자** | | | |
| **검토자** | | | |
| **승인자** | | | |

***

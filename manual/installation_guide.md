# 설치 가이드 상세

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 환경**: RHEL 8.x  
**목적**: 프로덕션 환경 설치 및 설정 상세 가이드

***

## 목차

1. [개요](#1-개요)
2. [사전 요구사항](#2-사전-요구사항)
3. [RHEL 8 환경 설정](#3-rhel-8-환경-설정)
4. [MariaDB 클러스터 설정](#4-mariadb-클러스터-설정)
5. [Elasticsearch 클러스터](#5-elasticsearch-클러스터)
6. [Redis 고가용성](#6-redis-고가용성)
7. [보안 설정](#7-보안-설정)
8. [성능 튜닝](#8-성능-튜닝)
9. [모니터링 설정](#9-모니터링-설정)
10. [트러블슈팅](#10-트러블슈팅)

***

## 1. 개요

### 1.1 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                   프로덕션 아키텍처                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [Load Balancer]                                        │
│         │                                                │
│         ├─────────┬─────────┬─────────┐                │
│         ▼         ▼         ▼         ▼                │
│    [App-1]   [App-2]   [App-3]   [App-N]               │
│         │         │         │         │                 │
│         └─────────┴─────────┴─────────┘                │
│                     │                                    │
│         ┌───────────┼───────────┐                       │
│         ▼           ▼           ▼                       │
│    [MariaDB]   [Redis]   [Elasticsearch]                │
│    Cluster     Sentinel  Cluster                        │
│     (3 nodes)  (3 nodes) (3 nodes)                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 1.2 설치 시나리오

| 시나리오 | 노드 수 | 용도 |
|---------|--------|------|
| **개발 환경** | 1 | 로컬 개발 및 테스트 |
| **스테이징** | 2-3 | 배포 전 검증 |
| **프로덕션** | 3+ | 고가용성 서비스 |

***

## 2. 사전 요구사항

### 2.1 하드웨어 요구사항

#### 최소 사양 (개발)
```yaml
CPU: 4 cores
Memory: 8 GB
Disk: 50 GB SSD
Network: 1 Gbps
```

#### 권장 사양 (프로덕션)
```yaml
CPU: 16 cores (32 threads)
Memory: 64 GB
Disk: 
  - OS: 100 GB SSD
  - Data: 500 GB+ NVMe SSD
  - Backup: 1 TB+ HDD
Network: 10 Gbps
```

### 2.2 소프트웨어 요구사항

```yaml
OS: RHEL 8.x (Rocky Linux 8.x 호환)
Kernel: 4.18+
Python: 3.11+
MariaDB: 10.11+
Redis: 7.0+
Elasticsearch: 8.x
```

### 2.3 네트워크 요구사항

#### 방화벽 포트

| 서비스 | 포트 | 프로토콜 | 용도 |
|--------|------|---------|------|
| SSH | 22 | TCP | 관리 |
| MCP Host | 8000 | TCP | API |
| API Gateway | 8080 | TCP | Gateway |
| Frontend | 3000 | TCP | Web UI |
| MariaDB | 3306 | TCP | Database |
| Redis | 6379 | TCP | Cache |
| Elasticsearch | 9200 | TCP | Search (HTTP) |
| Elasticsearch | 9300 | TCP | Cluster |

***

## 3. RHEL 8 환경 설정

### 3.1 기본 설정

```bash
#!/bin/bash
# RHEL 8 초기 설정

# ==============================================
# 시스템 업데이트
# ==============================================

echo "시스템 업데이트..."
dnf update -y

# ==============================================
# SELinux 설정
# ==============================================

echo "SELinux 설정..."

# Permissive 모드 (개발 환경)
# setenforce 0
# sed -i 's/^SELINUX=.*/SELINUX=permissive/' /etc/selinux/config

# 또는 필요한 컨텍스트만 허용 (프로덕션)
setsebool -P httpd_can_network_connect 1
setsebool -P httpd_can_network_connect_db 1

# ==============================================
# 방화벽 설정
# ==============================================

echo "방화벽 설정..."

systemctl enable firewalld
systemctl start firewalld

# 포트 오픈
firewall-cmd --permanent --add-port=22/tcp
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --permanent --add-port=3000/tcp
firewall-cmd --permanent --add-port=3306/tcp
firewall-cmd --permanent --add-port=6379/tcp
firewall-cmd --permanent --add-port=9200/tcp
firewall-cmd --permanent --add-port=9300/tcp

firewall-cmd --reload

# ==============================================
# 시스템 제한 설정
# ==============================================

echo "시스템 제한 설정..."

cat >> /etc/security/limits.conf << EOF
# MCP System Limits
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
elasticsearch soft memlock unlimited
elasticsearch hard memlock unlimited
EOF

# ==============================================
# Sysctl 튜닝
# ==============================================

echo "Sysctl 튜닝..."

cat > /etc/sysctl.d/99-mcp.conf << EOF
# Network
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65535

# Memory
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# Elasticsearch
vm.max_map_count = 262144
EOF

sysctl -p /etc/sysctl.d/99-mcp.conf

# ==============================================
# 타임존 설정
# ==============================================

echo "타임존 설정..."
timedatectl set-timezone Asia/Seoul

# ==============================================
# NTP 동기화
# ==============================================

echo "NTP 동기화..."
dnf install -y chrony
systemctl enable chronyd
systemctl start chronyd

# ==============================================
# 필수 패키지 설치
# ==============================================

echo "필수 패키지 설치..."

dnf install -y \
    vim \
    git \
    curl \
    wget \
    net-tools \
    bind-utils \
    telnet \
    nc \
    htop \
    iotop \
    sysstat \
    lsof \
    strace \
    tcpdump

echo "RHEL 8 기본 설정 완료!"
```

### 3.2 사용자 및 그룹 설정

```bash
#!/bin/bash
# 사용자 및 그룹 설정

# ==============================================
# mcps 사용자 생성
# ==============================================

groupadd -g 3000 mcps
useradd -u 3000 -g mcps -m -s /bin/bash mcps

# 비밀번호 설정
echo "mcps:CHANGE_ME_PASSWORD" | chpasswd

# sudo 권한 부여 (필요시)
echo "mcps ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/mcps
chmod 440 /etc/sudoers.d/mcps

# ==============================================
# 디렉토리 생성 및 권한 설정
# ==============================================

mkdir -p /app/poc/mcps
chown -R mcps:mcps /app/poc/mcps

# 로그 디렉토리
mkdir -p /var/log/mcps
chown -R mcps:mcps /var/log/mcps

# 데이터 디렉토리
mkdir -p /data/mcps
chown -R mcps:mcps /data/mcps

echo "사용자 설정 완료!"
```

### 3.3 디스크 설정

```bash
#!/bin/bash
# 디스크 파티션 및 마운트 설정

# ==============================================
# LVM 설정 (선택)
# ==============================================

# 물리 볼륨 생성
# pvcreate /dev/sdb

# 볼륨 그룹 생성
# vgcreate vg_data /dev/sdb

# 논리 볼륨 생성
# lvcreate -L 200G -n lv_database vg_data
# lvcreate -L 100G -n lv_elasticsearch vg_data
# lvcreate -L 50G -n lv_logs vg_data

# ==============================================
# 파일시스템 생성
# ==============================================

# XFS (권장)
# mkfs.xfs /dev/vg_data/lv_database
# mkfs.xfs /dev/vg_data/lv_elasticsearch
# mkfs.xfs /dev/vg_data/lv_logs

# ==============================================
# 마운트 포인트 생성
# ==============================================

mkdir -p /data/mariadb
mkdir -p /data/elasticsearch
mkdir -p /data/logs

# ==============================================
# fstab 설정
# ==============================================

cat >> /etc/fstab << EOF
# MCP Data Volumes
/dev/vg_data/lv_database    /data/mariadb        xfs    defaults,noatime    0 2
/dev/vg_data/lv_elasticsearch /data/elasticsearch xfs    defaults,noatime    0 2
/dev/vg_data/lv_logs        /data/logs           xfs    defaults,noatime    0 2
EOF

# 마운트
mount -a

# 권한 설정
chown -R mysql:mysql /data/mariadb
chown -R elasticsearch:elasticsearch /data/elasticsearch
chown -R mcps:mcps /data/logs

echo "디스크 설정 완료!"
```

***

## 4. MariaDB 클러스터 설정

### 4.1 Galera Cluster 설치

```bash
#!/bin/bash
# MariaDB Galera Cluster 설치

# ==============================================
# 노드 정보
# ==============================================

NODE1_IP="192.168.1.101"
NODE2_IP="192.168.1.102"
NODE3_IP="192.168.1.103"

CLUSTER_NAME="mcps_cluster"

# ==============================================
# MariaDB 저장소 추가
# ==============================================

cat > /etc/yum.repos.d/mariadb.repo << EOF
[mariadb]
name = MariaDB
baseurl = https://rpm.mariadb.org/10.11/rhel/8/x86_64/
module_hotfixes = 1
gpgkey = https://rpm.mariadb.org/RPM-GPG-KEY-MariaDB
gpgcheck = 1
enabled = 1
EOF

# ==============================================
# Galera 설치
# ==============================================

dnf install -y \
    MariaDB-server \
    MariaDB-client \
    galera-4 \
    MariaDB-backup

# ==============================================
# Galera 설정 (Node 1)
# ==============================================

cat > /etc/my.cnf.d/galera.cnf << EOF
[galera]
# Cluster Configuration
wsrep_on=ON
wsrep_provider=/usr/lib64/galera-4/libgalera_smm.so
wsrep_cluster_name="${CLUSTER_NAME}"
wsrep_cluster_address="gcomm://${NODE1_IP},${NODE2_IP},${NODE3_IP}"

# Node Configuration
wsrep_node_address="${NODE1_IP}"
wsrep_node_name="node1"

# Replication Configuration
wsrep_slave_threads=4
wsrep_replicate_myisam=ON

# SST Configuration
wsrep_sst_method=rsync

# InnoDB Configuration
binlog_format=ROW
default_storage_engine=InnoDB
innodb_autoinc_lock_mode=2

# Network
bind-address=0.0.0.0
EOF

# ==============================================
# 방화벽 설정
# ==============================================

firewall-cmd --permanent --add-port=3306/tcp  # MySQL
firewall-cmd --permanent --add-port=4444/tcp  # SST
firewall-cmd --permanent --add-port=4567/tcp  # Galera
firewall-cmd --permanent --add-port=4568/tcp  # IST
firewall-cmd --reload

# ==============================================
# 첫 번째 노드 시작
# ==============================================

galera_new_cluster

# 상태 확인
mysql -u root -e "SHOW STATUS LIKE 'wsrep_cluster_size';"

echo "Node 1 설정 완료!"
echo "다른 노드에서 systemctl start mariadb 실행"
```

### 4.2 MariaDB 최적화 설정

```bash
#!/bin/bash
# MariaDB 성능 튜닝 설정

cat > /etc/my.cnf.d/server.cnf << EOF
[mysqld]
# ==============================================
# General
# ==============================================
datadir=/data/mariadb
socket=/var/lib/mysql/mysql.sock
pid-file=/var/run/mariadb/mariadb.pid

user=mysql

# Character Set
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci

# ==============================================
# Connection
# ==============================================
max_connections=1000
max_connect_errors=1000000
thread_cache_size=100
table_open_cache=4000
table_definition_cache=2000

# ==============================================
# Query Cache (Disabled in MariaDB 10.11)
# ==============================================
query_cache_type=0
query_cache_size=0

# ==============================================
# InnoDB
# ==============================================
# Buffer Pool (전체 메모리의 70-80%)
innodb_buffer_pool_size=32G
innodb_buffer_pool_instances=8

# Log Files
innodb_log_file_size=1G
innodb_log_buffer_size=64M
innodb_flush_log_at_trx_commit=2

# I/O
innodb_io_capacity=2000
innodb_io_capacity_max=4000
innodb_read_io_threads=8
innodb_write_io_threads=8
innodb_flush_method=O_DIRECT

# File Per Table
innodb_file_per_table=1

# ==============================================
# Logging
# ==============================================
# General Log (비활성화 - 성능)
general_log=0

# Slow Query Log
slow_query_log=1
slow_query_log_file=/var/log/mariadb/slow.log
long_query_time=2
log_slow_verbosity=query_plan,explain

# Binary Log
log_bin=/data/mariadb/binlog/mysql-bin
expire_logs_days=7
max_binlog_size=100M
binlog_format=ROW

# ==============================================
# Replication
# ==============================================
server-id=1
sync_binlog=1
relay_log=/data/mariadb/relay/mysql-relay
relay_log_recovery=1

# ==============================================
# Temp Tables
# ==============================================
tmp_table_size=256M
max_heap_table_size=256M

# ==============================================
# Sort and Join
# ==============================================
sort_buffer_size=4M
read_buffer_size=2M
read_rnd_buffer_size=8M
join_buffer_size=8M

# ==============================================
# Security
# ==============================================
local_infile=0
skip_name_resolve=1

[client]
default-character-set=utf8mb4
socket=/var/lib/mysql/mysql.sock
EOF

# 디렉토리 생성
mkdir -p /data/mariadb/binlog
mkdir -p /data/mariadb/relay
chown -R mysql:mysql /data/mariadb

# 재시작
systemctl restart mariadb

echo "MariaDB 최적화 완료!"
```

### 4.3 MaxScale (로드 밸런서) 설정

```bash
#!/bin/bash
# MaxScale 설치 및 설정

# ==============================================
# MaxScale 설치
# ==============================================

dnf install -y maxscale

# ==============================================
# 설정
# ==============================================

cat > /etc/maxscale.cnf << EOF
[maxscale]
threads=auto
admin_host=0.0.0.0
admin_port=8989
admin_secure_gui=false

# ==============================================
# Servers
# ==============================================

[server1]
type=server
address=192.168.1.101
port=3306
protocol=MariaDBBackend

[server2]
type=server
address=192.168.1.102
port=3306
protocol=MariaDBBackend

[server3]
type=server
address=192.168.1.103
port=3306
protocol=MariaDBBackend

# ==============================================
# Monitor
# ==============================================

[Galera-Monitor]
type=monitor
module=galeramon
servers=server1,server2,server3
user=maxscale
password=CHANGE_ME_PASSWORD
monitor_interval=2000ms
use_priority=true
available_when_donor=true

# ==============================================
# Service
# ==============================================

[Read-Write-Service]
type=service
router=readwritesplit
servers=server1,server2,server3
user=maxscale
password=CHANGE_ME_PASSWORD
master_reconnection=true
master_failure_mode=fail_on_write
transaction_replay=true

# ==============================================
# Listener
# ==============================================

[Read-Write-Listener]
type=listener
service=Read-Write-Service
protocol=MariaDBClient
port=3307
EOF

# ==============================================
# MaxScale 사용자 생성 (각 MariaDB 노드에서)
# ==============================================

mysql -u root -p << EOF
CREATE USER 'maxscale'@'%' IDENTIFIED BY 'CHANGE_ME_PASSWORD';
GRANT SELECT ON mysql.user TO 'maxscale'@'%';
GRANT SELECT ON mysql.db TO 'maxscale'@'%';
GRANT SELECT ON mysql.tables_priv TO 'maxscale'@'%';
GRANT SELECT ON mysql.roles_mapping TO 'maxscale'@'%';
GRANT SHOW DATABASES ON *.* TO 'maxscale'@'%';
FLUSH PRIVILEGES;
EOF

# ==============================================
# 시작
# ==============================================

systemctl enable maxscale
systemctl start maxscale

# 상태 확인
maxctrl list servers

echo "MaxScale 설정 완료!"
```

***

## 5. Elasticsearch 클러스터

### 5.1 Elasticsearch 클러스터 설치

```bash
#!/bin/bash
# Elasticsearch 클러스터 설치

# ==============================================
# 노드 정보
# ==============================================

NODE1_IP="192.168.1.201"
NODE2_IP="192.168.1.202"
NODE3_IP="192.168.1.203"

NODE_NAME=$(hostname)
CLUSTER_NAME="mcps-es-cluster"

# ==============================================
# Elasticsearch 설치
# ==============================================

rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch

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

dnf install -y elasticsearch

# ==============================================
# 설정
# ==============================================

cat > /etc/elasticsearch/elasticsearch.yml << EOF
# ==============================================
# Cluster
# ==============================================
cluster.name: ${CLUSTER_NAME}
node.name: ${NODE_NAME}

# Roles
node.roles: [master, data, ingest]

# ==============================================
# Network
# ==============================================
network.host: 0.0.0.0
http.port: 9200
transport.port: 9300

# ==============================================
# Discovery
# ==============================================
discovery.seed_hosts:
  - ${NODE1_IP}
  - ${NODE2_IP}
  - ${NODE3_IP}

cluster.initial_master_nodes:
  - node1
  - node2
  - node3

# ==============================================
# Paths
# ==============================================
path.data: /data/elasticsearch/data
path.logs: /data/elasticsearch/logs

# ==============================================
# Memory
# ==============================================
bootstrap.memory_lock: true

# ==============================================
# Security (개발 환경 - 비활성화)
# ==============================================
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false

# ==============================================
# Performance
# ==============================================
indices.memory.index_buffer_size: 20%
indices.queries.cache.size: 10%
EOF

# ==============================================
# JVM 설정
# ==============================================

# 전체 메모리의 50% (최대 31GB)
cat > /etc/elasticsearch/jvm.options.d/heap.options << EOF
-Xms16g
-Xmx16g
EOF

# ==============================================
# Systemd 설정
# ==============================================

mkdir -p /etc/systemd/system/elasticsearch.service.d

cat > /etc/systemd/system/elasticsearch.service.d/override.conf << EOF
[Service]
LimitNOFILE=65535
LimitNPROC=4096
LimitMEMLOCK=infinity
EOF

# ==============================================
# 디렉토리 생성
# ==============================================

mkdir -p /data/elasticsearch/data
mkdir -p /data/elasticsearch/logs
chown -R elasticsearch:elasticsearch /data/elasticsearch

# ==============================================
# 방화벽
# ==============================================

firewall-cmd --permanent --add-port=9200/tcp
firewall-cmd --permanent --add-port=9300/tcp
firewall-cmd --reload

# ==============================================
# 시작
# ==============================================

systemctl daemon-reload
systemctl enable elasticsearch
systemctl start elasticsearch

# 대기
sleep 30

# 상태 확인
curl -X GET "http://localhost:9200/_cluster/health?pretty"

echo "Elasticsearch 클러스터 설정 완료!"
```

### 5.2 Elasticsearch 최적화

```bash
#!/bin/bash
# Elasticsearch 인덱스 템플릿 및 최적화

# ==============================================
# 인덱스 템플릿 생성
# ==============================================

curl -X PUT "http://localhost:9200/_index_template/mcps_template" \
-H 'Content-Type: application/json' \
-d '{
  "index_patterns": ["documents-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "refresh_interval": "30s",
      "index.codec": "best_compression",
      "index.max_result_window": 50000,
      "analysis": {
        "analyzer": {
          "korean": {
            "type": "custom",
            "tokenizer": "nori_tokenizer",
            "filter": ["lowercase", "nori_part_of_speech"]
          }
        },
        "filter": {
          "nori_part_of_speech": {
            "type": "nori_part_of_speech",
            "stoptags": ["E", "IC", "J", "MAG", "MAJ", "MM", "SP", "SSC", "SSO", "SC", "SE", "XPN", "XSA", "XSN", "XSV", "UNA", "NA", "VSV"]
          }
        }
      }
    },
    "mappings": {
      "dynamic": "strict",
      "properties": {
        "doc_id": {"type": "keyword"},
        "title": {
          "type": "text",
          "analyzer": "korean",
          "fields": {
            "keyword": {"type": "keyword"},
            "ngram": {
              "type": "text",
              "analyzer": "standard"
            }
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
  },
  "priority": 100
}'

# ==============================================
# ILM 정책 (Index Lifecycle Management)
# ==============================================

curl -X PUT "http://localhost:9200/_ilm/policy/mcps_policy" \
-H 'Content-Type: application/json' \
-d '{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "50gb",
            "max_age": "30d"
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": {
            "number_of_shards": 1
          },
          "forcemerge": {
            "max_num_segments": 1
          }
        }
      },
      "cold": {
        "min_age": "90d",
        "actions": {
          "freeze": {}
        }
      },
      "delete": {
        "min_age": "365d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}'

echo "Elasticsearch 최적화 완료!"
```

***

## 6. Redis 고가용성

### 6.1 Redis Sentinel 설정

```bash
#!/bin/bash
# Redis Sentinel 설치 및 설정

# ==============================================
# 노드 정보
# ==============================================

MASTER_IP="192.168.1.301"
SLAVE1_IP="192.168.1.302"
SLAVE2_IP="192.168.1.303"

# ==============================================
# Redis 설치
# ==============================================

dnf install -y redis

# ==============================================
# Master 설정
# ==============================================

cat > /etc/redis/redis.conf << EOF
# Network
bind 0.0.0.0
port 6379
protected-mode yes
requirepass CHANGE_ME_PASSWORD

# General
daemonize no
supervised systemd
pidfile /var/run/redis/redis.pid
loglevel notice
logfile /var/log/redis/redis.log

# Persistence
save 900 1
save 300 10
save 60 10000
dir /data/redis

# Replication
masterauth CHANGE_ME_PASSWORD

# Memory
maxmemory 8gb
maxmemory-policy allkeys-lru

# AOF
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Performance
tcp-backlog 511
timeout 0
tcp-keepalive 300
EOF

# ==============================================
# Slave 설정 (Slave 노드에서)
# ==============================================

# 위 설정에 추가:
# replicaof ${MASTER_IP} 6379

# ==============================================
# Sentinel 설정 (모든 노드)
# ==============================================

cat > /etc/redis/sentinel.conf << EOF
# Sentinel Configuration
port 26379
bind 0.0.0.0
protected-mode no
daemonize no
supervised systemd
pidfile /var/run/redis/redis-sentinel.pid
logfile /var/log/redis/sentinel.log
dir /tmp

# Monitor
sentinel monitor mymaster ${MASTER_IP} 6379 2
sentinel auth-pass mymaster CHANGE_ME_PASSWORD
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 10000
EOF

# ==============================================
# Systemd 서비스
# ==============================================

cp /usr/lib/systemd/system/redis-sentinel.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable redis
systemctl enable redis-sentinel
systemctl start redis
systemctl start redis-sentinel

# ==============================================
# 방화벽
# ==============================================

firewall-cmd --permanent --add-port=6379/tcp
firewall-cmd --permanent --add-port=26379/tcp
firewall-cmd --reload

echo "Redis Sentinel 설정 완료!"
```

***

## 7. 보안 설정

### 7.1 SSL/TLS 설정

```bash
#!/bin/bash
# SSL/TLS 인증서 생성 및 설정

# ==============================================
# 인증서 디렉토리
# ==============================================

CERT_DIR="/etc/pki/mcps"
mkdir -p ${CERT_DIR}
cd ${CERT_DIR}

# ==============================================
# 자체 서명 인증서 생성 (개발/테스트)
# ==============================================

# CA 생성
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
    -subj "/C=KR/ST=Seoul/L=Seoul/O=MCP/CN=MCP-CA"

# 서버 인증서 생성
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr \
    -subj "/C=KR/ST=Seoul/L=Seoul/O=MCP/CN=*.mcps.local"

# 서버 인증서 서명
openssl x509 -req -days 365 -in server.csr \
    -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out server.crt

# 권한 설정
chmod 600 *.key
chmod 644 *.crt

# ==============================================
# Nginx SSL 설정 (선택)
# ==============================================

dnf install -y nginx

cat > /etc/nginx/conf.d/mcps.conf << EOF
upstream api_backend {
    least_conn;
    server 127.0.0.1:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name mcps.local;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mcps.local;

    ssl_certificate ${CERT_DIR}/server.crt;
    ssl_certificate_key ${CERT_DIR}/server.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

systemctl enable nginx
systemctl start nginx

echo "SSL/TLS 설정 완료!"
```

### 7.2 방화벽 및 네트워크 보안

```bash
#!/bin/bash
# 방화벽 및 네트워크 보안 강화

# ==============================================
# Fail2ban 설치
# ==============================================

dnf install -y epel-release
dnf install -y fail2ban fail2ban-systemd

# ==============================================
# Fail2ban 설정
# ==============================================

cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
banaction = firewallcmd-ipset
backend = systemd

[sshd]
enabled = true
port = 22
logpath = /var/log/secure

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
EOF

systemctl enable fail2ban
systemctl start fail2ban

# ==============================================
# 포트 스캔 방지
# ==============================================

cat >> /etc/sysctl.d/99-security.conf << EOF
# Port Scan Protection
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
EOF

sysctl -p /etc/sysctl.d/99-security.conf

echo "보안 설정 완료!"
```

### 7.3 Database 보안

```bash
#!/bin/bash
# MariaDB 보안 강화

mysql -u root -p << EOF
-- 불필요한 사용자 삭제
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');

-- 테스트 데이터베이스 삭제
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';

-- 권한 제한된 사용자 생성
CREATE USER 'mcps_app'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE ON mcps_db.* TO 'mcps_app'@'localhost';

-- 읽기 전용 사용자
CREATE USER 'mcps_readonly'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD';
GRANT SELECT ON mcps_db.* TO 'mcps_readonly'@'localhost';

-- 백업 사용자
CREATE USER 'mcps_backup'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD';
GRANT SELECT, LOCK TABLES, RELOAD, REPLICATION CLIENT ON *.* TO 'mcps_backup'@'localhost';

FLUSH PRIVILEGES;
EOF

# ==============================================
# SSL 연결 강제 (선택)
# ==============================================

cat >> /etc/my.cnf.d/server.cnf << EOF
[mysqld]
require_secure_transport=ON
ssl_ca=/etc/pki/mcps/ca.crt
ssl_cert=/etc/pki/mcps/server.crt
ssl_key=/etc/pki/mcps/server.key
EOF

systemctl restart mariadb

echo "Database 보안 강화 완료!"
```





## 8. 성능 튜닝

### 8.1 Python 애플리케이션 튜닝

```bash
#!/bin/bash
# Python 애플리케이션 성능 튜닝

# ==============================================
# Gunicorn 설정 (API Gateway)
# ==============================================

cat > /app/poc/mcps/api-gateway/gunicorn_config.py << 'EOF'
"""Gunicorn 설정"""

import multiprocessing
import os

# Server Socket
bind = "0.0.0.0:8080"
backlog = 2048

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 100
timeout = 120
keepalive = 5

# Logging
accesslog = "/data/logs/api-gateway/access.log"
errorlog = "/data/logs/api-gateway/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process Naming
proc_name = "mcp-api-gateway"

# Server Mechanics
daemon = False
pidfile = "/var/run/mcps/api-gateway.pid"
user = "mcps"
group = "mcps"
tmp_upload_dir = None

# SSL (선택)
# keyfile = "/etc/pki/mcps/server.key"
# certfile = "/etc/pki/mcps/server.crt"
EOF

# ==============================================
# Systemd 서비스 업데이트
# ==============================================

cat > /etc/systemd/system/mcp-api-gateway.service << EOF
[Unit]
Description=MCP API Gateway (Gunicorn)
After=network.target mariadb.service redis.service elasticsearch.service mcp-host.service

[Service]
Type=notify
User=mcps
Group=mcps
WorkingDirectory=/app/poc/mcps/api-gateway

Environment="PATH=/app/poc/mcps/venv/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="WORKERS=8"

ExecStart=/app/poc/mcps/venv/bin/gunicorn \
    -c gunicorn_config.py \
    main:app

ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=30
PrivateTmp=true

# Performance
LimitNOFILE=65536
LimitNPROC=32768

# Security
NoNewPrivileges=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/data/logs/api-gateway /tmp

Restart=always
RestartSec=10

StandardOutput=append:/data/logs/api-gateway/service.log
StandardError=append:/data/logs/api-gateway/error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo "Python 애플리케이션 튜닝 완료!"
```

### 8.2 연결 풀 최적화

```python
#!/usr/bin/env python3
# /app/poc/mcps/config/database_pool.py
"""Database 연결 풀 최적화 설정"""

from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
import redis
from elasticsearch import Elasticsearch
import os

# ==============================================
# MariaDB 연결 풀
# ==============================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://mcps_user:password@localhost:3306/mcps_db"
)

# SQLAlchemy Engine with Pool
engine = create_engine(
    DATABASE_URL,
    # Connection Pool Settings
    poolclass=pool.QueuePool,
    pool_size=20,                    # 기본 연결 수
    max_overflow=40,                 # 추가 연결 수
    pool_timeout=30,                 # 연결 대기 시간
    pool_recycle=3600,               # 연결 재활용 시간 (1시간)
    pool_pre_ping=True,              # 연결 유효성 확인
    
    # Connection Settings
    connect_args={
        "connect_timeout": 10,
        "read_timeout": 30,
        "write_timeout": 30,
        "charset": "utf8mb4",
        "autocommit": False,
        
        # Performance
        "max_allowed_packet": 64 * 1024 * 1024,  # 64MB
    },
    
    # Echo SQL (개발 환경에서만)
    echo=False,
    
    # Execution Options
    execution_options={
        "isolation_level": "READ COMMITTED"
    }
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ==============================================
# Redis 연결 풀
# ==============================================

redis_pool = redis.ConnectionPool(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", None),
    db=0,
    
    # Pool Settings
    max_connections=50,
    socket_connect_timeout=5,
    socket_timeout=5,
    socket_keepalive=True,
    socket_keepalive_options={
        1: 1,  # TCP_KEEPIDLE
        2: 1,  # TCP_KEEPINTVL
        3: 3,  # TCP_KEEPCNT
    },
    
    # Retry
    retry_on_timeout=True,
    
    # Health Check
    health_check_interval=30,
)

redis_client = redis.Redis(connection_pool=redis_pool)

# ==============================================
# Elasticsearch 클라이언트
# ==============================================

es_client = Elasticsearch(
    hosts=[
        {"host": "localhost", "port": 9200, "scheme": "http"}
    ],
    
    # Connection Settings
    max_retries=3,
    retry_on_timeout=True,
    timeout=30,
    
    # Connection Pool
    maxsize=25,
    
    # Performance
    sniff_on_start=True,
    sniff_on_connection_fail=True,
    sniffer_timeout=60,
)

# ==============================================
# Helper Functions
# ==============================================

def get_db():
    """Database 세션 가져오기"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    """Redis 클라이언트 가져오기"""
    return redis_client

def get_elasticsearch():
    """Elasticsearch 클라이언트 가져오기"""
    return es_client

# ==============================================
# Health Check
# ==============================================

def check_database():
    """Database 연결 확인"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False

def check_redis():
    """Redis 연결 확인"""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"Redis health check failed: {e}")
        return False

def check_elasticsearch():
    """Elasticsearch 연결 확인"""
    try:
        es_client.ping()
        return True
    except Exception as e:
        print(f"Elasticsearch health check failed: {e}")
        return False

if __name__ == "__main__":
    print("Database:", "OK" if check_database() else "FAIL")
    print("Redis:", "OK" if check_redis() else "FAIL")
    print("Elasticsearch:", "OK" if check_elasticsearch() else "FAIL")
```

### 8.3 캐싱 전략

```python
#!/usr/bin/env python3
# /app/poc/mcps/api-gateway/cache_manager.py
"""캐싱 관리자"""

import redis
import pickle
import hashlib
import functools
from typing import Any, Callable, Optional
from datetime import timedelta

class CacheManager:
    """캐싱 관리자"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """캐시 키 생성"""
        key_data = f"{prefix}:{args}:{kwargs}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"cache:{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """캐시 조회"""
        try:
            data = self.redis.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """캐시 저장"""
        try:
            data = pickle.dumps(value)
            self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """캐시 삭제"""
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """패턴으로 캐시 삭제"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
        return 0
    
    def cached(
        self,
        prefix: str,
        ttl: int = 3600,
        key_builder: Optional[Callable] = None
    ):
        """캐싱 데코레이터"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 캐시 키 생성
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = self.generate_key(prefix, *args, **kwargs)
                
                # 캐시 조회
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 함수 실행
                result = func(*args, **kwargs)
                
                # 캐시 저장
                self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator

# ==============================================
# 사용 예시
# ==============================================

# cache_manager = CacheManager(redis_client)

# @cache_manager.cached(prefix="user", ttl=1800)
# def get_user_by_id(user_id: str):
#     """사용자 조회 (캐싱)"""
#     # DB 조회
#     return db.query(User).filter(User.id == user_id).first()

# @cache_manager.cached(prefix="document", ttl=3600)
# def search_documents(query: str, limit: int = 10):
#     """문서 검색 (캐싱)"""
#     # Elasticsearch 검색
#     return es.search(index="documents", body={"query": {"match": {"content": query}}})
```

### 8.4 비동기 처리

```python
#!/usr/bin/env python3
# /app/poc/mcps/api-gateway/async_tasks.py
"""비동기 작업 처리"""

from celery import Celery
import os

# ==============================================
# Celery 설정
# ==============================================

celery_app = Celery(
    "mcps_tasks",
    broker=os.getenv("CELERY_BROKER", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_BACKEND", "redis://localhost:6379/2")
)

celery_app.conf.update(
    # Task Settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    
    # Performance
    task_acks_late=True,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Result Backend
    result_expires=3600,
    result_backend_transport_options={
        "master_name": "mymaster",
    },
    
    # Broker Settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
)

# ==============================================
# 비동기 작업 정의
# ==============================================

@celery_app.task(name="index_document", bind=True, max_retries=3)
def index_document_task(self, doc_id: str):
    """문서 인덱싱 비동기 작업"""
    try:
        # DB에서 문서 조회
        # Elasticsearch에 인덱싱
        print(f"Indexing document: {doc_id}")
        return {"status": "success", "doc_id": doc_id}
    except Exception as exc:
        # 재시도
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="generate_report")
def generate_report_task(report_type: str, params: dict):
    """보고서 생성 비동기 작업"""
    try:
        print(f"Generating report: {report_type}")
        # 보고서 생성 로직
        return {"status": "success", "report_type": report_type}
    except Exception as e:
        print(f"Report generation failed: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task(name="cleanup_old_data")
def cleanup_old_data_task():
    """오래된 데이터 정리 (스케줄러)"""
    try:
        print("Cleaning up old data...")
        # 정리 로직
        return {"status": "success"}
    except Exception as e:
        print(f"Cleanup failed: {e}")
        return {"status": "error", "message": str(e)}

# ==============================================
# 스케줄러 설정 (Celery Beat)
# ==============================================

celery_app.conf.beat_schedule = {
    "cleanup-every-day": {
        "task": "cleanup_old_data",
        "schedule": 86400.0,  # 매일
    },
}
```

```bash
#!/bin/bash
# Celery Worker 및 Beat Systemd 서비스

# ==============================================
# Celery Worker 서비스
# ==============================================

cat > /etc/systemd/system/mcp-celery-worker.service << EOF
[Unit]
Description=MCP Celery Worker
After=network.target redis.service mariadb.service

[Service]
Type=forking
User=mcps
Group=mcps
WorkingDirectory=/app/poc/mcps/api-gateway

Environment="PATH=/app/poc/mcps/venv/bin:/usr/local/bin:/usr/bin"

ExecStart=/app/poc/mcps/venv/bin/celery -A async_tasks worker \
    --loglevel=info \
    --concurrency=8 \
    --logfile=/data/logs/celery/worker.log \
    --pidfile=/var/run/mcps/celery-worker.pid

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# ==============================================
# Celery Beat 서비스
# ==============================================

cat > /etc/systemd/system/mcp-celery-beat.service << EOF
[Unit]
Description=MCP Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=mcps
Group=mcps
WorkingDirectory=/app/poc/mcps/api-gateway

Environment="PATH=/app/poc/mcps/venv/bin:/usr/local/bin:/usr/bin"

ExecStart=/app/poc/mcps/venv/bin/celery -A async_tasks beat \
    --loglevel=info \
    --logfile=/data/logs/celery/beat.log \
    --pidfile=/var/run/mcps/celery-beat.pid

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# ==============================================
# 디렉토리 생성
# ==============================================

mkdir -p /data/logs/celery
chown -R mcps:mcps /data/logs/celery

mkdir -p /var/run/mcps
chown -R mcps:mcps /var/run/mcps

# ==============================================
# 서비스 시작
# ==============================================

systemctl daemon-reload
systemctl enable mcp-celery-worker
systemctl enable mcp-celery-beat
systemctl start mcp-celery-worker
systemctl start mcp-celery-beat

echo "Celery 서비스 설정 완료!"
```

***

## 9. 모니터링 설정

### 9.1 Prometheus 설치

```bash
#!/bin/bash
# Prometheus 설치 및 설정

# ==============================================
# Prometheus 다운로드
# ==============================================

cd /tmp
PROMETHEUS_VERSION="2.45.0"
wget https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz

tar xzf prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz
mv prometheus-${PROMETHEUS_VERSION}.linux-amd64 /opt/prometheus

# ==============================================
# 사용자 생성
# ==============================================

useradd -r -s /bin/false prometheus

# ==============================================
# 디렉토리 생성
# ==============================================

mkdir -p /data/prometheus
mkdir -p /etc/prometheus
chown -R prometheus:prometheus /data/prometheus
chown -R prometheus:prometheus /opt/prometheus

# ==============================================
# 설정 파일
# ==============================================

cat > /etc/prometheus/prometheus.yml << EOF
# Prometheus Configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'mcps-production'

# Alertmanager Configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

# Scrape Configurations
scrape_configs:
  # Prometheus 자체 모니터링
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node Exporter
  - job_name: 'node'
    static_configs:
      - targets:
          - '192.168.1.101:9100'
          - '192.168.1.102:9100'
          - '192.168.1.103:9100'
        labels:
          group: 'app-servers'

  # MariaDB Exporter
  - job_name: 'mariadb'
    static_configs:
      - targets:
          - '192.168.1.101:9104'
          - '192.168.1.102:9104'
          - '192.168.1.103:9104'

  # Redis Exporter
  - job_name: 'redis'
    static_configs:
      - targets:
          - '192.168.1.301:9121'
          - '192.168.1.302:9121'
          - '192.168.1.303:9121'

  # Elasticsearch Exporter
  - job_name: 'elasticsearch'
    static_configs:
      - targets:
          - '192.168.1.201:9114'
          - '192.168.1.202:9114'
          - '192.168.1.203:9114'

  # MCP Application
  - job_name: 'mcp-app'
    static_configs:
      - targets:
          - '192.168.1.101:8000'
          - '192.168.1.102:8000'
          - '192.168.1.103:8000'
    metrics_path: '/metrics'
EOF

# ==============================================
# Systemd 서비스
# ==============================================

cat > /etc/systemd/system/prometheus.service << EOF
[Unit]
Description=Prometheus Time Series Database
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus

ExecStart=/opt/prometheus/prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/data/prometheus \
    --storage.tsdb.retention.time=30d \
    --web.console.templates=/opt/prometheus/consoles \
    --web.console.libraries=/opt/prometheus/console_libraries \
    --web.listen-address=0.0.0.0:9090

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# ==============================================
# 방화벽
# ==============================================

firewall-cmd --permanent --add-port=9090/tcp
firewall-cmd --reload

# ==============================================
# 시작
# ==============================================

systemctl daemon-reload
systemctl enable prometheus
systemctl start prometheus

echo "Prometheus 설치 완료!"
echo "접속: http://localhost:9090"
```

### 9.2 Grafana 설치

```bash
#!/bin/bash
# Grafana 설치 및 설정

# ==============================================
# Grafana 저장소 추가
# ==============================================

cat > /etc/yum.repos.d/grafana.repo << EOF
[grafana]
name=grafana
baseurl=https://rpm.grafana.com
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://rpm.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF

# ==============================================
# Grafana 설치
# ==============================================

dnf install -y grafana

# ==============================================
# 설정
# ==============================================

cat > /etc/grafana/grafana.ini << EOF
[server]
protocol = http
http_addr = 0.0.0.0
http_port = 3001
domain = localhost

[database]
type = mysql
host = localhost:3306
name = grafana
user = grafana
password = CHANGE_ME_PASSWORD

[security]
admin_user = admin
admin_password = CHANGE_ME_PASSWORD
secret_key = CHANGE_ME_SECRET

[auth.anonymous]
enabled = false

[analytics]
reporting_enabled = false
check_for_updates = false

[log]
mode = file
level = info
EOF

# ==============================================
# Database 생성
# ==============================================

mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS grafana CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'grafana'@'localhost' IDENTIFIED BY 'CHANGE_ME_PASSWORD';
GRANT ALL PRIVILEGES ON grafana.* TO 'grafana'@'localhost';
FLUSH PRIVILEGES;
EOF

# ==============================================
# 방화벽
# ==============================================

firewall-cmd --permanent --add-port=3001/tcp
firewall-cmd --reload

# ==============================================
# 시작
# ==============================================

systemctl enable grafana-server
systemctl start grafana-server

echo "Grafana 설치 완료!"
echo "접속: http://localhost:3001"
echo "ID: admin / PW: CHANGE_ME_PASSWORD"
```

### 9.3 Node Exporter 설치

```bash
#!/bin/bash
# Node Exporter 설치

# ==============================================
# 다운로드
# ==============================================

cd /tmp
NODE_EXPORTER_VERSION="1.6.1"
wget https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz

tar xzf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
mv node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/

# ==============================================
# 사용자 생성
# ==============================================

useradd -r -s /bin/false node_exporter

# ==============================================
# Systemd 서비스
# ==============================================

cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
User=node_exporter
Group=node_exporter

ExecStart=/usr/local/bin/node_exporter \
    --web.listen-address=:9100

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# ==============================================
# 방화벽
# ==============================================

firewall-cmd --permanent --add-port=9100/tcp
firewall-cmd --reload

# ==============================================
# 시작
# ==============================================

systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

echo "Node Exporter 설치 완료!"
```

### 9.4 애플리케이션 메트릭

```python
#!/usr/bin/env python3
# /app/poc/mcps/api-gateway/metrics.py
"""Prometheus 메트릭"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from fastapi import Response
import time

# ==============================================
# 메트릭 정의
# ==============================================

# Request Counter
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Request Duration
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Active Requests
active_requests = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)

# Database Connections
db_connections = Gauge(
    'database_connections_active',
    'Active database connections'
)

# Cache Hit Rate
cache_hits = Counter('cache_hits_total', 'Cache hits')
cache_misses = Counter('cache_misses_total', 'Cache misses')

# Document Count
document_count = Gauge('documents_total', 'Total documents')

# Search Performance
search_duration = Histogram(
    'search_duration_seconds',
    'Search duration'
)

# ==============================================
# 미들웨어
# ==============================================

class PrometheusMiddleware:
    """Prometheus 메트릭 미들웨어"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        method = scope["method"]
        path = scope["path"]
        
        active_requests.inc()
        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status = message["status"]
                duration = time.time() - start_time
                
                request_count.labels(
                    method=method,
                    endpoint=path,
                    status=status
                ).inc()
                
                request_duration.labels(
                    method=method,
                    endpoint=path
                ).observe(duration)
                
                active_requests.dec()
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

# ==============================================
# 메트릭 엔드포인트
# ==============================================

async def metrics_endpoint():
    """메트릭 엔드포인트"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# ==============================================
# 사용 예시
# ==============================================

# from fastapi import FastAPI
# from metrics import PrometheusMiddleware, metrics_endpoint

# app = FastAPI()
# app.add_middleware(PrometheusMiddleware)
# app.add_route("/metrics", metrics_endpoint)
```

### 9.5 로그 수집 (ELK 스택)

```bash
#!/bin/bash
# Logstash 및 Filebeat 설치

# ==============================================
# Filebeat 설치
# ==============================================

dnf install -y filebeat

# ==============================================
# Filebeat 설정
# ==============================================

cat > /etc/filebeat/filebeat.yml << EOF
# Filebeat Configuration

filebeat.inputs:
  # MCP Host Logs
  - type: log
    enabled: true
    paths:
      - /data/logs/mcp-host/*.log
    fields:
      service: mcp-host
      environment: production
    multiline.pattern: '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
    multiline.negate: true
    multiline.match: after

  # API Gateway Logs
  - type: log
    enabled: true
    paths:
      - /data/logs/api-gateway/*.log
    fields:
      service: api-gateway
      environment: production

  # MariaDB Slow Query
  - type: log
    enabled: true
    paths:
      - /var/log/mariadb/slow.log
    fields:
      service: mariadb
      log_type: slow_query

  # System Logs
  - type: log
    enabled: true
    paths:
      - /var/log/messages
      - /var/log/secure
    fields:
      service: system

# Output to Elasticsearch
output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "filebeat-mcps-%{+yyyy.MM.dd}"

# Kibana Configuration
setup.kibana:
  host: "localhost:5601"

# Processors
processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
  - add_cloud_metadata: ~
  - add_docker_metadata: ~
EOF

# ==============================================
# Filebeat 시작
# ==============================================

systemctl enable filebeat
systemctl start filebeat

echo "Filebeat 설치 완료!"
```

***

## 10. 트러블슈팅

### 10.1 일반적인 문제 해결

```bash
#!/bin/bash
# 트러블슈팅 스크립트

# ==============================================
# 시스템 정보 수집
# ==============================================

collect_system_info() {
    echo "=========================================="
    echo "시스템 정보 수집"
    echo "=========================================="
    
    OUTPUT_DIR="/tmp/mcps-diagnostic-$(date +%Y%m%d_%H%M%S)"
    mkdir -p ${OUTPUT_DIR}
    
    # 기본 정보
    echo "# Hostname" > ${OUTPUT_DIR}/system_info.txt
    hostname >> ${OUTPUT_DIR}/system_info.txt
    
    echo -e "\n# OS Version" >> ${OUTPUT_DIR}/system_info.txt
    cat /etc/redhat-release >> ${OUTPUT_DIR}/system_info.txt
    
    echo -e "\n# Kernel Version" >> ${OUTPUT_DIR}/system_info.txt
    uname -a >> ${OUTPUT_DIR}/system_info.txt
    
    echo -e "\n# Uptime" >> ${OUTPUT_DIR}/system_info.txt
    uptime >> ${OUTPUT_DIR}/system_info.txt
    
    # 리소스
    echo -e "\n# CPU Info" >> ${OUTPUT_DIR}/system_info.txt
    lscpu >> ${OUTPUT_DIR}/system_info.txt
    
    echo -e "\n# Memory Info" >> ${OUTPUT_DIR}/system_info.txt
    free -h >> ${OUTPUT_DIR}/system_info.txt
    
    echo -e "\n# Disk Info" >> ${OUTPUT_DIR}/system_info.txt
    df -h >> ${OUTPUT_DIR}/system_info.txt
    
    # 서비스 상태
    systemctl status mariadb > ${OUTPUT_DIR}/mariadb_status.txt 2>&1
    systemctl status redis > ${OUTPUT_DIR}/redis_status.txt 2>&1
    systemctl status elasticsearch > ${OUTPUT_DIR}/elasticsearch_status.txt 2>&1
    systemctl status mcp-host > ${OUTPUT_DIR}/mcp_host_status.txt 2>&1
    systemctl status mcp-api-gateway > ${OUTPUT_DIR}/api_gateway_status.txt 2>&1
    
    # 로그
    tail -1000 /data/logs/mcp-host/error.log > ${OUTPUT_DIR}/mcp_host_error.log 2>&1
    tail -1000 /data/logs/api-gateway/error.log > ${OUTPUT_DIR}/api_gateway_error.log 2>&1
    tail -1000 /var/log/mariadb/mariadb.log > ${OUTPUT_DIR}/mariadb.log 2>&1
    
    # 네트워크
    netstat -tuln > ${OUTPUT_DIR}/network_ports.txt
    
    # 압축
    tar czf ${OUTPUT_DIR}.tar.gz ${OUTPUT_DIR}
    rm -rf ${OUTPUT_DIR}
    
    echo "진단 정보 저장 완료: ${OUTPUT_DIR}.tar.gz"
}

# ==============================================
# Database 연결 문제
# ==============================================

check_database_connection() {
    echo "=========================================="
    echo "Database 연결 확인"
    echo "=========================================="
    
    # MariaDB 프로세스 확인
    if ! pgrep -x mysqld > /dev/null; then
        echo "ERROR: MariaDB가 실행 중이 아닙니다"
        systemctl status mariadb
        return 1
    fi
    
    # 포트 확인
    if ! netstat -tuln | grep -q ":3306 "; then
        echo "ERROR: MariaDB 포트 3306이 열려 있지 않습니다"
        return 1
    fi
    
    # 연결 테스트
    if mysql -u root -e "SELECT 1" > /dev/null 2>&1; then
        echo "OK: Database 연결 성공"
    else
        echo "ERROR: Database 연결 실패"
        echo "확인사항:"
        echo "  1. MariaDB 서비스 상태: systemctl status mariadb"
        echo "  2. 로그 확인: tail -f /var/log/mariadb/mariadb.log"
        echo "  3. 연결 수 확인: mysql -e 'SHOW PROCESSLIST'"
        return 1
    fi
}

# ==============================================
# 메모리 부족 문제
# ==============================================

check_memory() {
    echo "=========================================="
    echo "메모리 확인"
    echo "=========================================="
    
    AVAILABLE_MEM=$(free -m | awk '/^Mem:/{print $7}')
    SWAP_USED=$(free -m | awk '/^Swap:/{print $3}')
    
    echo "가용 메모리: ${AVAILABLE_MEM}MB"
    echo "Swap 사용: ${SWAP_USED}MB"
    
    if [ ${AVAILABLE_MEM} -lt 1024 ]; then
        echo "WARNING: 가용 메모리 부족 (< 1GB)"
        echo "메모리를 많이 사용하는 프로세스:"
        ps aux --sort=-%mem | head -10
    fi
    
    if [ ${SWAP_USED} -gt 1024 ]; then
        echo "WARNING: Swap 메모리 과다 사용 (> 1GB)"
    fi
}

# ==============================================
# 디스크 공간 문제
# ==============================================

check_disk_space() {
    echo "=========================================="
    echo "디스크 공간 확인"
    echo "=========================================="
    
    df -h | awk 'NR==1 || /\/$|\/data|\/var/ {print $0}'
    
    # 80% 이상 사용 시 경고
    df -h | awk 'NR>1 {gsub("%","",$5); if($5>80) print "WARNING: "$6" 파티션이 "$5"% 사용 중"}'
    
    echo -e "\n대용량 파일:"
    find /data/logs -type f -size +100M -exec ls -lh {} \; 2>/dev/null | head -10
}

# ==============================================
# 포트 충돌 문제
# ==============================================

check_port_conflicts() {
    echo "=========================================="
    echo "포트 충돌 확인"
    echo "=========================================="
    
    PORTS=(8000 8080 3000 3306 6379 9200)
    
    for PORT in "${PORTS[@]}"; do
        if netstat -tuln | grep -q ":${PORT} "; then
            PROCESS=$(lsof -ti:${PORT} 2>/dev/null)
            if [ -n "${PROCESS}" ]; then
                PROCESS_NAME=$(ps -p ${PROCESS} -o comm=)
                echo "포트 ${PORT}: 사용 중 (PID: ${PROCESS}, Name: ${PROCESS_NAME})"
            else
                echo "포트 ${PORT}: 사용 중 (프로세스 정보 없음)"
            fi
        else
            echo "포트 ${PORT}: 사용 가능"
        fi
    done
}

# ==============================================
# 실행
# ==============================================

case "${1}" in
    all)
        collect_system_info
        check_database_connection
        check_memory
        check_disk_space
        check_port_conflicts
        ;;
    db)
        check_database_connection
        ;;
    memory)
        check_memory
        ;;
    disk)
        check_disk_space
        ;;
    port)
        check_port_conflicts
        ;;
    collect)
        collect_system_info
        ;;
    *)
        echo "Usage: $0 {all|db|memory|disk|port|collect}"
        echo ""
        echo "  all     - 모든 항목 확인"
        echo "  db      - Database 연결 확인"
        echo "  memory  - 메모리 확인"
        echo "  disk    - 디스크 공간 확인"
        echo "  port    - 포트 충돌 확인"
        echo "  collect - 진단 정보 수집"
        exit 1
        ;;
esac
```

### 10.2 성능 문제 진단

```bash
#!/bin/bash
# 성능 문제 진단 스크립트

# ==============================================
# CPU 병목 확인
# ==============================================

check_cpu_bottleneck() {
    echo "=========================================="
    echo "CPU 사용률 확인"
    echo "=========================================="
    
    echo "전체 CPU 사용률:"
    mpstat 1 5
    
    echo -e "\nCPU를 많이 사용하는 프로세스:"
    ps aux --sort=-%cpu | head -10
    
    echo -e "\n시스템 Load Average:"
    uptime
}

# ==============================================
# I/O 병목 확인
# ==============================================

check_io_bottleneck() {
    echo "=========================================="
    echo "I/O 사용률 확인"
    echo "=========================================="
    
    echo "디스크 I/O 통계:"
    iostat -x 1 5
    
    echo -e "\nI/O를 많이 사용하는 프로세스:"
    iotop -b -n 1 | head -20
}

# ==============================================
# 네트워크 확인
# ==============================================

check_network() {
    echo "=========================================="
    echo "네트워크 확인"
    echo "=========================================="
    
    echo "네트워크 인터페이스 통계:"
    sar -n DEV 1 5
    
    echo -e "\n연결 상태:"
    netstat -an | awk '{print $6}' | sort | uniq -c | sort -rn
    
    echo -e "\nTCP 재전송:"
    netstat -s | grep -i retrans
}

# ==============================================
# Database 성능
# ==============================================

check_database_performance() {
    echo "=========================================="
    echo "Database 성능 확인"
    echo "=========================================="
    
    mysql -u root -e "
        SELECT 
            COUNT(*) as total_connections,
            SUM(IF(command='Sleep', 1, 0)) as sleeping_connections,
            SUM(IF(command!='Sleep', 1, 0)) as active_connections
        FROM information_schema.processlist;
    "
    
    echo -e "\n슬로우 쿼리:"
    mysql -u root -e "
        SELECT 
            query_time,
            lock_time,
            rows_examined,
            sql_text
        FROM mysql.slow_log
        ORDER BY query_time DESC
        LIMIT 10;
    "
}

# 실행
case "${1}" in
    cpu)
        check_cpu_bottleneck
        ;;
    io)
        check_io_bottleneck
        ;;
    network)
        check_network
        ;;
    db)
        check_database_performance
        ;;
    all)
        check_cpu_bottleneck
        check_io_bottleneck
        check_network
        check_database_performance
        ;;
    *)
        echo "Usage: $0 {cpu|io|network|db|all}"
        exit 1
        ;;
esac
```

### 10.3 FAQ

```markdown
# 자주 묻는 질문 (FAQ)

## Q1: 서비스가 시작되지 않습니다

A: 다음 순서로 확인하세요:

1. 서비스 상태 확인
   ```bash
   systemctl status mcp-host
   journalctl -u mcp-host -n 50
   ```

2. 로그 확인
   ```bash
   tail -f /data/logs/mcp-host/error.log
   ```

3. 포트 충돌 확인
   ```bash
   netstat -tuln | grep :8000
   ```

4. 의존 서비스 확인
   ```bash
   systemctl status mariadb redis elasticsearch
   ```

## Q2: Database 연결이 느립니다

A: 다음을 확인하세요:

1. 연결 풀 설정 확인
2. 슬로우 쿼리 로그 분석
3. 인덱스 최적화
4. 통계 정보 업데이트
   ```sql
   ANALYZE TABLE documents;
   ```

## Q3: Elasticsearch 인덱싱이 느립니다

A: 다음을 시도하세요:

1. Refresh interval 증가
   ```bash
   curl -X PUT "localhost:9200/documents/_settings" \
   -H 'Content-Type: application/json' \
   -d '{"index": {"refresh_interval": "30s"}}'
   ```

2. Bulk 크기 조정
3. 샤드 수 최적화

## Q4: 메모리 부족 에러가 발생합니다

A: 다음을 확인하세요:

1. JVM 힙 크기 조정 (Elasticsearch)
2. InnoDB 버퍼 풀 크기 조정 (MariaDB)
3. Python 애플리케이션 메모리 사용 프로파일링
4. Swap 메모리 확인

## Q5: 로그 파일이 너무 큽니다

A: 로그 로테이션 설정:

```bash
sudo bash /app/poc/mcps/scripts/manage/cleanup.sh
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
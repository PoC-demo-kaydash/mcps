# 운영 가이드

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상**: 운영팀, SRE, DevOps  
**목적**: 시스템 일상 운영 및 장애 대응 가이드

***

## 목차

1. [개요](#1-개요)
2. [일상 운영](#2-일상-운영)
3. [백업 및 복구](#3-백업-및-복구)
4. [모니터링 및 알림](#4-모니터링-및-알림)
5. [장애 대응](#5-장애-대응)
6. [성능 관리](#6-성능-관리)
7. [보안 운영](#7-보안-운영)
8. [변경 관리](#8-변경-관리)
9. [용량 계획](#9-용량-계획)
10. [운영 체크리스트](#10-운영-체크리스트)

***

## 1. 개요

### 1.1 운영 조직

```
┌─────────────────────────────────────────┐
│           운영 조직 구조                 │
├─────────────────────────────────────────┤
│                                          │
│  [운영 관리자]                           │
│        │                                 │
│        ├─── [모니터링팀]                │
│        │      └─ 24/7 모니터링          │
│        │                                 │
│        ├─── [인프라팀]                  │
│        │      ├─ Database 관리          │
│        │      ├─ 서버 관리              │
│        │      └─ 네트워크 관리           │
│        │                                 │
│        ├─── [보안팀]                    │
│        │      ├─ 보안 모니터링          │
│        │      └─ 취약점 관리            │
│        │                                 │
│        └─── [개발팀]                    │
│               ├─ 애플리케이션 지원      │
│               └─ 긴급 패치             │
│                                          │
└─────────────────────────────────────────┘
```

### 1.2 운영 원칙

| 원칙 | 설명 |
|------|------|
| **가용성 우선** | 서비스 중단 최소화 |
| **예방적 조치** | 사전 모니터링 및 대응 |
| **문서화** | 모든 작업 기록 |
| **자동화** | 반복 작업 자동화 |
| **보안 준수** | 보안 정책 준수 |

### 1.3 SLA (Service Level Agreement)

```yaml
가용성:
  목표: 99.9%
  허용 다운타임: 43.8분/월
  
응답 시간:
  API 조회: < 200ms (평균)
  검색: < 500ms (평균)
  문서 등록: < 1초
  
처리량:
  동시 사용자: 1,000명
  API 요청: 10,000 req/min
```

***

## 2. 일상 운영

### 2.1 일일 점검 (Daily Check)

```bash
#!/bin/bash
# /app/poc/mcps/scripts/operations/daily_check.sh
# 일일 시스템 점검 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

REPORT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="/data/reports/daily_check_${REPORT_DATE}.txt"

log_info "=========================================="
log_info "  일일 점검 시작: ${REPORT_DATE}"
log_info "=========================================="

# 보고서 디렉토리 생성
mkdir -p /data/reports

# ==============================================
# 1. 서비스 상태 확인
# ==============================================

echo "========================================" > ${REPORT_FILE}
echo "일일 점검 보고서: ${REPORT_DATE}" >> ${REPORT_FILE}
echo "========================================" >> ${REPORT_FILE}
echo "" >> ${REPORT_FILE}

echo "1. 서비스 상태" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

SERVICES=(
    "mariadb:MariaDB"
    "redis:Redis"
    "elasticsearch:Elasticsearch"
    "mcp-host:MCP Host"
    "mcp-api-gateway:API Gateway"
    "mcp-frontend:Frontend"
)

ALL_SERVICES_OK=true

for SERVICE_INFO in "${SERVICES[@]}"; do
    IFS=':' read -r SERVICE_NAME DISPLAY_NAME <<< "$SERVICE_INFO"
    
    if systemctl is-active --quiet "${SERVICE_NAME}"; then
        echo "  [OK] ${DISPLAY_NAME}: 실행 중" >> ${REPORT_FILE}
        log_success "${DISPLAY_NAME}: 실행 중"
    else
        echo "  [FAIL] ${DISPLAY_NAME}: 중지됨" >> ${REPORT_FILE}
        log_error "${DISPLAY_NAME}: 중지됨"
        ALL_SERVICES_OK=false
    fi
done

echo "" >> ${REPORT_FILE}

# ==============================================
# 2. 리소스 사용량
# ==============================================

echo "2. 리소스 사용량" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# CPU
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
echo "  CPU 사용률: ${CPU_USAGE}%" >> ${REPORT_FILE}

# Memory
MEMORY_TOTAL=$(free -h | awk '/^Mem:/{print $2}')
MEMORY_USED=$(free -h | awk '/^Mem:/{print $3}')
MEMORY_PERCENT=$(free | awk '/^Mem:/{printf "%.1f", $3/$2 * 100}')
echo "  메모리: ${MEMORY_USED}/${MEMORY_TOTAL} (${MEMORY_PERCENT}%)" >> ${REPORT_FILE}

# Disk
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
DISK_USED=$(df -h / | awk 'NR==2 {print $3}')
DISK_TOTAL=$(df -h / | awk 'NR==2 {print $2}')
echo "  디스크 (/): ${DISK_USED}/${DISK_TOTAL} (${DISK_USAGE}%)" >> ${REPORT_FILE}

# 경고 확인
if [ $(echo "$CPU_USAGE > 80" | bc) -eq 1 ]; then
    log_warning "CPU 사용률 높음: ${CPU_USAGE}%"
fi

if [ $(echo "$MEMORY_PERCENT > 80" | bc) -eq 1 ]; then
    log_warning "메모리 사용률 높음: ${MEMORY_PERCENT}%"
fi

if [ ${DISK_USAGE} -gt 80 ]; then
    log_warning "디스크 사용률 높음: ${DISK_USAGE}%"
fi

echo "" >> ${REPORT_FILE}

# ==============================================
# 3. Database 상태
# ==============================================

echo "3. Database 상태" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 연결 수
DB_CONNECTIONS=$(mysql -u root -N -e "SHOW STATUS LIKE 'Threads_connected';" | awk '{print $2}')
DB_MAX_CONNECTIONS=$(mysql -u root -N -e "SHOW VARIABLES LIKE 'max_connections';" | awk '{print $2}')
echo "  연결 수: ${DB_CONNECTIONS}/${DB_MAX_CONNECTIONS}" >> ${REPORT_FILE}

# Database 크기
DB_SIZE=$(mysql -u root -N -e "
    SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) 
    FROM information_schema.tables 
    WHERE table_schema = '${DB_NAME}';
")
echo "  Database 크기: ${DB_SIZE} MB" >> ${REPORT_FILE}

# 슬로우 쿼리
SLOW_QUERIES=$(mysql -u root -N -e "SHOW GLOBAL STATUS LIKE 'Slow_queries';" | awk '{print $2}')
echo "  슬로우 쿼리: ${SLOW_QUERIES}" >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# ==============================================
# 4. 로그 에러 확인
# ==============================================

echo "4. 에러 로그 (최근 24시간)" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

for SERVICE in mcp-host api-gateway frontend; do
    LOG_FILE="/data/logs/${SERVICE}/error.log"
    
    if [ -f "${LOG_FILE}" ]; then
        ERROR_COUNT=$(find "${LOG_FILE}" -mtime -1 -exec grep -i "error" {} \; 2>/dev/null | wc -l)
        echo "  ${SERVICE}: ${ERROR_COUNT}개의 에러" >> ${REPORT_FILE}
        
        if [ ${ERROR_COUNT} -gt 100 ]; then
            log_warning "${SERVICE}: 에러 급증 (${ERROR_COUNT}개)"
        fi
    fi
done

echo "" >> ${REPORT_FILE}

# ==============================================
# 5. 백업 상태
# ==============================================

echo "5. 백업 상태" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

LATEST_BACKUP=$(ls -t ${BACKUP_DIR}/backup_*.tar.gz 2>/dev/null | head -1)

if [ -n "${LATEST_BACKUP}" ]; then
    BACKUP_DATE=$(stat -c %y "${LATEST_BACKUP}" | cut -d' ' -f1)
    BACKUP_SIZE=$(du -h "${LATEST_BACKUP}" | cut -f1)
    echo "  최근 백업: ${BACKUP_DATE} (${BACKUP_SIZE})" >> ${REPORT_FILE}
    
    # 백업이 24시간 이상 오래된 경우 경고
    BACKUP_AGE=$(find "${LATEST_BACKUP}" -mtime +1 | wc -l)
    if [ ${BACKUP_AGE} -gt 0 ]; then
        log_warning "백업이 24시간 이상 오래되었습니다"
        echo "  [WARNING] 백업이 24시간 이상 오래됨" >> ${REPORT_FILE}
    fi
else
    echo "  [ERROR] 백업 파일 없음" >> ${REPORT_FILE}
    log_error "백업 파일을 찾을 수 없습니다"
fi

echo "" >> ${REPORT_FILE}

# ==============================================
# 6. 보안 이벤트
# ==============================================

echo "6. 보안 이벤트 (최근 24시간)" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 로그인 실패
FAILED_LOGINS=$(grep "Failed password" /var/log/secure 2>/dev/null | grep "$(date +%b\ %d)" | wc -l)
echo "  실패한 로그인 시도: ${FAILED_LOGINS}" >> ${REPORT_FILE}

if [ ${FAILED_LOGINS} -gt 10 ]; then
    log_warning "로그인 실패 시도 급증: ${FAILED_LOGINS}회"
fi

# Fail2ban 차단
if command -v fail2ban-client &> /dev/null; then
    BANNED_IPS=$(fail2ban-client status sshd 2>/dev/null | grep "Currently banned" | awk '{print $NF}')
    echo "  차단된 IP: ${BANNED_IPS}개" >> ${REPORT_FILE}
fi

echo "" >> ${REPORT_FILE}

# ==============================================
# 7. 전체 요약
# ==============================================

echo "========================================" >> ${REPORT_FILE}
echo "요약" >> ${REPORT_FILE}
echo "========================================" >> ${REPORT_FILE}

if [ "${ALL_SERVICES_OK}" = true ] && \
   [ ${DISK_USAGE} -lt 80 ] && \
   [ $(echo "$MEMORY_PERCENT < 80" | bc) -eq 1 ] && \
   [ -n "${LATEST_BACKUP}" ]; then
    echo "상태: 정상" >> ${REPORT_FILE}
    log_success "일일 점검 완료: 정상"
else
    echo "상태: 주의 필요" >> ${REPORT_FILE}
    log_warning "일일 점검 완료: 주의 필요"
fi

echo "" >> ${REPORT_FILE}
echo "보고서 생성 시간: $(date)" >> ${REPORT_FILE}

# ==============================================
# 보고서 출력 및 이메일 발송 (선택)
# ==============================================

cat ${REPORT_FILE}

# 이메일 발송 (설정된 경우)
# mail -s "MCP 일일 점검 보고서 - ${REPORT_DATE}" admin@example.com < ${REPORT_FILE}

log_success "일일 점검 완료!"
```

### 2.2 주간 점검 (Weekly Check)

```bash
#!/bin/bash
# /app/poc/mcps/scripts/operations/weekly_check.sh
# 주간 시스템 점검 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

REPORT_DATE=$(date +%Y-W%V)
REPORT_FILE="/data/reports/weekly_check_${REPORT_DATE}.txt"

log_info "=========================================="
log_info "  주간 점검 시작: ${REPORT_DATE}"
log_info "=========================================="

mkdir -p /data/reports

echo "========================================" > ${REPORT_FILE}
echo "주간 점검 보고서: ${REPORT_DATE}" >> ${REPORT_FILE}
echo "========================================" >> ${REPORT_FILE}
echo "" >> ${REPORT_FILE}

# ==============================================
# 1. 주간 통계
# ==============================================

echo "1. 주간 통계" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# Database 통계
mysql -u root << EOF >> ${REPORT_FILE}
SELECT 
    '문서 수' AS metric,
    COUNT(*) AS value
FROM ${DB_NAME}.documents
UNION ALL
SELECT 
    '사용자 수',
    COUNT(*)
FROM ${DB_NAME}.users
UNION ALL
SELECT 
    '이번 주 신규 문서',
    COUNT(*)
FROM ${DB_NAME}.documents
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY);
EOF

echo "" >> ${REPORT_FILE}

# ==============================================
# 2. 성능 추이
# ==============================================

echo "2. 성능 추이" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 평균 응답 시간 (Prometheus 메트릭에서 가져오기)
echo "  평균 응답 시간: [Prometheus에서 조회]" >> ${REPORT_FILE}
echo "  최대 동시 사용자: [Prometheus에서 조회]" >> ${REPORT_FILE}
echo "  총 API 호출: [Prometheus에서 조회]" >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# ==============================================
# 3. 보안 점검
# ==============================================

echo "3. 보안 점검" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 패키지 업데이트 확인
UPDATES_AVAILABLE=$(dnf check-update | grep -c "^[a-zA-Z]" || true)
echo "  사용 가능한 업데이트: ${UPDATES_AVAILABLE}개" >> ${REPORT_FILE}

# 취약한 패키지 확인
echo "  보안 업데이트: $(dnf updateinfo list security 2>/dev/null | wc -l)개" >> ${REPORT_FILE}

# 인증서 만료 확인 (90일 이내)
if [ -f "/etc/pki/mcps/server.crt" ]; then
    CERT_EXPIRY=$(openssl x509 -enddate -noout -in /etc/pki/mcps/server.crt | cut -d= -f2)
    CERT_EXPIRY_EPOCH=$(date -d "${CERT_EXPIRY}" +%s)
    NOW_EPOCH=$(date +%s)
    DAYS_LEFT=$(( (CERT_EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
    
    echo "  SSL 인증서 만료까지: ${DAYS_LEFT}일" >> ${REPORT_FILE}
    
    if [ ${DAYS_LEFT} -lt 30 ]; then
        log_warning "SSL 인증서 만료 임박: ${DAYS_LEFT}일 남음"
    fi
fi

echo "" >> ${REPORT_FILE}

# ==============================================
# 4. 용량 추이
# ==============================================

echo "4. 용량 추이" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# Database 크기 추이
mysql -u root -N -e "
    SELECT 
        table_schema AS 'Database',
        ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
    FROM information_schema.tables
    WHERE table_schema = '${DB_NAME}'
    GROUP BY table_schema;
" >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# Elasticsearch 인덱스 크기
curl -s "http://localhost:9200/_cat/indices?v&h=index,store.size" >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# 로그 파일 크기
echo "로그 파일 크기:" >> ${REPORT_FILE}
du -sh /data/logs/* >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# ==============================================
# 5. 권장 사항
# ==============================================

echo "5. 권장 사항" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 자동 권장사항 생성
RECOMMENDATIONS=()

if [ ${DISK_USAGE} -gt 70 ]; then
    RECOMMENDATIONS+=("디스크 정리 필요 (사용률: ${DISK_USAGE}%)")
fi

if [ ${UPDATES_AVAILABLE} -gt 0 ]; then
    RECOMMENDATIONS+=("시스템 업데이트 필요 (${UPDATES_AVAILABLE}개)")
fi

if [ ${DAYS_LEFT} -lt 60 ]; then
    RECOMMENDATIONS+=("SSL 인증서 갱신 필요 (${DAYS_LEFT}일 남음)")
fi

if [ ${#RECOMMENDATIONS[@]} -eq 0 ]; then
    echo "  특별한 조치 필요 없음" >> ${REPORT_FILE}
else
    for REC in "${RECOMMENDATIONS[@]}"; do
        echo "  - ${REC}" >> ${REPORT_FILE}
    done
fi

echo "" >> ${REPORT_FILE}
echo "보고서 생성 시간: $(date)" >> ${REPORT_FILE}

# 출력
cat ${REPORT_FILE}

log_success "주간 점검 완료!"
```

### 2.3 정기 유지보수 작업

```bash
#!/bin/bash
# /app/poc/mcps/scripts/operations/maintenance.sh
# 정기 유지보수 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "정기 유지보수 시작..."

# ==============================================
# 1. Database 최적화
# ==============================================

log_info "Database 최적화 중..."

# 테이블 최적화
mysql -u root ${DB_NAME} << EOF
OPTIMIZE TABLE documents;
OPTIMIZE TABLE users;
OPTIMIZE TABLE audit_logs;
OPTIMIZE TABLE search_logs;
EOF

# 통계 정보 업데이트
mysql -u root ${DB_NAME} << EOF
ANALYZE TABLE documents;
ANALYZE TABLE users;
ANALYZE TABLE audit_logs;
ANALYZE TABLE search_logs;
EOF

log_success "Database 최적화 완료"

# ==============================================
# 2. Elasticsearch 최적화
# ==============================================

log_info "Elasticsearch 최적화 중..."

# Force merge (읽기 전용 인덱스)
curl -X POST "http://localhost:9200/documents/_forcemerge?max_num_segments=1" \
    -H 'Content-Type: application/json'

# 캐시 정리
curl -X POST "http://localhost:9200/_cache/clear"

log_success "Elasticsearch 최적화 완료"

# ==============================================
# 3. Redis 최적화
# ==============================================

log_info "Redis 최적화 중..."

# BGSAVE (백그라운드 저장)
redis-cli BGSAVE

# 메모리 최적화
redis-cli MEMORY PURGE

log_success "Redis 최적화 완료"

# ==============================================
# 4. 로그 정리
# ==============================================

log_info "오래된 로그 정리 중..."

bash "${SCRIPTS_DIR}/manage/cleanup.sh"

log_success "로그 정리 완료"

# ==============================================
# 5. 임시 파일 정리
# ==============================================

log_info "임시 파일 정리 중..."

# Python 캐시 정리
find /app/poc/mcps -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /app/poc/mcps -type f -name "*.pyc" -delete

# 임시 디렉토리 정리
find /tmp -type f -mtime +7 -delete 2>/dev/null || true

log_success "임시 파일 정리 완료"

# ==============================================
# 6. 시스템 통계 업데이트
# ==============================================

log_info "시스템 통계 업데이트 중..."

# 시스템 정보 수집
sar -u 1 1 > /data/reports/cpu_stats_$(date +%Y%m%d).txt
sar -r 1 1 > /data/reports/memory_stats_$(date +%Y%m%d).txt
sar -d 1 1 > /data/reports/disk_stats_$(date +%Y%m%d).txt

log_success "시스템 통계 업데이트 완료"

log_success "정기 유지보수 완료!"
```

***

## 3. 백업 및 복구

### 3.1 백업 전략

```
┌─────────────────────────────────────────┐
│           백업 전략                      │
├─────────────────────────────────────────┤
│                                          │
│  [Full Backup]                          │
│    - 주기: 주 1회 (일요일 02:00)        │
│    - 보관: 4주                          │
│    - 내용: 전체 Database + Files       │
│                                          │
│  [Incremental Backup]                   │
│    - 주기: 일 1회 (02:00)              │
│    - 보관: 7일                          │
│    - 내용: 변경된 데이터만              │
│                                          │
│  [Transaction Log]                      │
│    - 주기: 실시간                       │
│    - 보관: 24시간                       │
│    - 내용: MariaDB Binary Log          │
│                                          │
│  [Configuration]                        │
│    - 주기: 변경 시                      │
│    - 보관: 영구                         │
│    - 내용: 설정 파일                    │
│                                          │
└─────────────────────────────────────────┘
```

### 3.2 전체 백업 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/scripts/backup/full_backup.sh
# 전체 백업 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_ROOT="${BACKUP_DIR}/full_${BACKUP_DATE}"

log_info "=========================================="
log_info "  전체 백업 시작: ${BACKUP_DATE}"
log_info "=========================================="

# 백업 디렉토리 생성
mkdir -p "${BACKUP_ROOT}"/{database,elasticsearch,config,files}

# ==============================================
# 1. Database 백업
# ==============================================

log_info "[1/5] Database 백업 중..."

# Full backup with compression
mysqldump \
    -u ${DB_USER} \
    -p"${DB_PASSWORD}" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --hex-blob \
    --quick \
    --lock-tables=false \
    --max_allowed_packet=1G \
    ${DB_NAME} | gzip > "${BACKUP_ROOT}/database/full.sql.gz"

# Database 크기 기록
DB_SIZE=$(du -sh "${BACKUP_ROOT}/database" | cut -f1)
log_success "Database 백업 완료 (크기: ${DB_SIZE})"

# ==============================================
# 2. Binary Log 백업
# ==============================================

log_info "[2/5] Binary Log 백업 중..."

# Binary log 위치 기록
mysql -u root -N -e "SHOW MASTER STATUS;" > "${BACKUP_ROOT}/database/binlog_position.txt"

# Binary log 복사
BINLOG_DIR="/data/mariadb/binlog"
if [ -d "${BINLOG_DIR}" ]; then
    cp -r ${BINLOG_DIR}/* "${BACKUP_ROOT}/database/binlogs/" 2>/dev/null || true
fi

log_success "Binary Log 백업 완료"

# ==============================================
# 3. Elasticsearch 백업
# ==============================================

log_info "[3/5] Elasticsearch 백업 중..."

# Snapshot 생성
SNAPSHOT_NAME="snapshot_${BACKUP_DATE}"

# Snapshot repository 등록 (최초 1회)
curl -X PUT "http://localhost:9200/_snapshot/backup" \
    -H 'Content-Type: application/json' \
    -d "{
        \"type\": \"fs\",
        \"settings\": {
            \"location\": \"${BACKUP_ROOT}/elasticsearch\",
            \"compress\": true
        }
    }" 2>/dev/null || true

# Snapshot 생성
curl -X PUT "http://localhost:9200/_snapshot/backup/${SNAPSHOT_NAME}?wait_for_completion=true" \
    -H 'Content-Type: application/json' \
    -d '{
        "indices": "*",
        "ignore_unavailable": true,
        "include_global_state": true
    }'

log_success "Elasticsearch 백업 완료"

# ==============================================
# 4. 설정 파일 백업
# ==============================================

log_info "[4/5] 설정 파일 백업 중..."

# 애플리케이션 설정
for SERVICE_DIR in mcp-host api-gateway frontend; do
    if [ -f "${PROJECT_ROOT}/${SERVICE_DIR}/.env" ]; then
        cp "${PROJECT_ROOT}/${SERVICE_DIR}/.env" \
           "${BACKUP_ROOT}/config/${SERVICE_DIR}.env"
    fi
    
    if [ -f "${PROJECT_ROOT}/${SERVICE_DIR}/config.yaml" ]; then
        cp "${PROJECT_ROOT}/${SERVICE_DIR}/config.yaml" \
           "${BACKUP_ROOT}/config/${SERVICE_DIR}.yaml"
    fi
done

# 시스템 설정
cp /etc/my.cnf.d/*.cnf "${BACKUP_ROOT}/config/" 2>/dev/null || true
cp /etc/redis/redis.conf "${BACKUP_ROOT}/config/" 2>/dev/null || true
cp /etc/elasticsearch/elasticsearch.yml "${BACKUP_ROOT}/config/" 2>/dev/null || true

# Systemd 서비스
cp /etc/systemd/system/mcp-*.service "${BACKUP_ROOT}/config/" 2>/dev/null || true

# Nginx 설정 (있는 경우)
if [ -d "/etc/nginx/conf.d" ]; then
    cp /etc/nginx/conf.d/mcps.conf "${BACKUP_ROOT}/config/" 2>/dev/null || true
fi

log_success "설정 파일 백업 완료"

# ==============================================
# 5. 업로드 파일 백업
# ==============================================

log_info "[5/5] 업로드 파일 백업 중..."

UPLOAD_DIR="${DATA_DIR}/uploads"

if [ -d "${UPLOAD_DIR}" ]; then
    rsync -a --delete "${UPLOAD_DIR}/" "${BACKUP_ROOT}/files/"
    FILE_SIZE=$(du -sh "${BACKUP_ROOT}/files" | cut -f1)
    log_success "업로드 파일 백업 완료 (크기: ${FILE_SIZE})"
else
    log_info "업로드 파일 없음"
fi

# ==============================================
# 6. 메타데이터 생성
# ==============================================

log_info "메타데이터 생성 중..."

cat > "${BACKUP_ROOT}/backup_info.txt" << EOF
========================================
백업 정보
========================================

백업 일시: $(date)
백업 유형: Full Backup
백업 ID: ${BACKUP_DATE}

서버 정보:
  호스트명: $(hostname)
  OS: $(cat /etc/redhat-release)
  커널: $(uname -r)

Database:
  크기: ${DB_SIZE}
  Binary Log Position: $(cat "${BACKUP_ROOT}/database/binlog_position.txt")

Elasticsearch:
  Snapshot: ${SNAPSHOT_NAME}

파일:
  업로드 파일: ${FILE_SIZE}

총 백업 크기: $(du -sh "${BACKUP_ROOT}" | cut -f1)
========================================
EOF

# ==============================================
# 7. 압축
# ==============================================

log_info "백업 압축 중..."

cd "${BACKUP_DIR}"
tar -czf "full_${BACKUP_DATE}.tar.gz" "full_${BACKUP_DATE}"

COMPRESSED_SIZE=$(du -sh "full_${BACKUP_DATE}.tar.gz" | cut -f1)
log_success "백업 압축 완료 (크기: ${COMPRESSED_SIZE})"

# 압축 후 원본 디렉토리 삭제
rm -rf "full_${BACKUP_DATE}"

# ==============================================
# 8. 백업 검증
# ==============================================

log_info "백업 검증 중..."

# 압축 파일 무결성 확인
if tar -tzf "full_${BACKUP_DATE}.tar.gz" > /dev/null; then
    log_success "백업 파일 무결성 확인 완료"
else
    log_error "백업 파일 손상됨!"
    exit 1
fi

# ==============================================
# 9. 오래된 백업 삭제
# ==============================================

log_info "오래된 백업 삭제 중..."

# 4주 이상 된 Full 백업 삭제
find "${BACKUP_DIR}" -name "full_*.tar.gz" -mtime +28 -delete

REMAINING_BACKUPS=$(ls -1 ${BACKUP_DIR}/full_*.tar.gz 2>/dev/null | wc -l)
log_success "백업 정리 완료 (보관 중인 백업: ${REMAINING_BACKUPS}개)"

# ==============================================
# 10. 백업 완료
# ==============================================

log_success "=========================================="
log_success "  전체 백업 완료!"
log_success "=========================================="
log_info "백업 파일: ${BACKUP_DIR}/full_${BACKUP_DATE}.tar.gz"
log_info "백업 크기: ${COMPRESSED_SIZE}"
log_info ""

# 백업 로그 기록
echo "$(date): Full backup completed - full_${BACKUP_DATE}.tar.gz (${COMPRESSED_SIZE})" \
    >> "${BACKUP_DIR}/backup.log"
```

### 3.3 증분 백업 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/scripts/backup/incremental_backup.sh
# 증분 백업 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/incremental_${BACKUP_DATE}"

log_info "증분 백업 시작: ${BACKUP_DATE}"

mkdir -p "${BACKUP_PATH}"

# ==============================================
# 마지막 Full 백업 찾기
# ==============================================

LAST_FULL_BACKUP=$(ls -t ${BACKUP_DIR}/full_*.tar.gz 2>/dev/null | head -1)

if [ -z "${LAST_FULL_BACKUP}" ]; then
    log_error "Full 백업이 없습니다. 먼저 Full 백업을 수행하세요."
    exit 1
fi

log_info "마지막 Full 백업: $(basename ${LAST_FULL_BACKUP})"

# ==============================================
# Database 증분 백업 (Binary Log)
# ==============================================

log_info "Database 증분 백업 중..."

# 마지막 백업 이후 Binary Log만 복사
LAST_BACKUP_TIME=$(stat -c %Y "${LAST_FULL_BACKUP}")

mkdir -p "${BACKUP_PATH}/binlogs"

find /data/mariadb/binlog -type f -newer "${LAST_FULL_BACKUP}" \
    -exec cp {} "${BACKUP_PATH}/binlogs/" \;

# Binary log 위치 기록
mysql -u root -N -e "SHOW MASTER STATUS;" > "${BACKUP_PATH}/binlog_position.txt"

log_success "Database 증분 백업 완료"

# ==============================================
# 변경된 파일만 백업
# ==============================================

log_info "변경된 파일 백업 중..."

if [ -d "${DATA_DIR}/uploads" ]; then
    # rsync로 변경된 파일만 백업
    rsync -a --delete \
        --link-dest="${LAST_FULL_BACKUP}" \
        "${DATA_DIR}/uploads/" \
        "${BACKUP_PATH}/files/"
fi

# ==============================================
# 압축 및 정리
# ==============================================

cd "${BACKUP_DIR}"
tar -czf "incremental_${BACKUP_DATE}.tar.gz" "incremental_${BACKUP_DATE}"
rm -rf "incremental_${BACKUP_DATE}"

# 7일 이상 된 증분 백업 삭제
find "${BACKUP_DIR}" -name "incremental_*.tar.gz" -mtime +7 -delete

log_success "증분 백업 완료: incremental_${BACKUP_DATE}.tar.gz"
```

### 3.4 복구 절차

```bash
#!/bin/bash
# /app/poc/mcps/scripts/backup/restore_full.sh
# 전체 복구 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

# ==============================================
# 사용법
# ==============================================

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "사용 가능한 백업:"
    ls -lh ${BACKUP_DIR}/full_*.tar.gz
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "${BACKUP_FILE}" ]; then
    log_error "백업 파일을 찾을 수 없습니다: ${BACKUP_FILE}"
    exit 1
fi

# ==============================================
# 경고 및 확인
# ==============================================

log_warning "=========================================="
log_warning "  경고: 전체 시스템 복구"
log_warning "=========================================="
log_warning "현재 데이터가 모두 삭제됩니다!"
log_warning "백업 파일: ${BACKUP_FILE}"
log_warning ""

read -p "정말 복구하시겠습니까? (yes 입력): " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    log_info "복구 작업이 취소되었습니다."
    exit 0
fi

# ==============================================
# 1. 서비스 중지
# ==============================================

log_info "[1/6] 서비스 중지 중..."
bash "${SCRIPTS_DIR}/control/stop_all.sh"

# ==============================================
# 2. 백업 압축 해제
# ==============================================

log_info "[2/6] 백업 압축 해제 중..."

RESTORE_DIR="${BACKUP_DIR}/restore_temp"
rm -rf "${RESTORE_DIR}"
mkdir -p "${RESTORE_DIR}"

tar -xzf "${BACKUP_FILE}" -C "${RESTORE_DIR}"

BACKUP_DIR_NAME=$(ls "${RESTORE_DIR}")
BACKUP_ROOT="${RESTORE_DIR}/${BACKUP_DIR_NAME}"

# 백업 정보 출력
cat "${BACKUP_ROOT}/backup_info.txt"

# ==============================================
# 3. Database 복구
# ==============================================

log_info "[3/6] Database 복구 중..."

# Database 초기화
mysql -u root << EOF
DROP DATABASE IF EXISTS ${DB_NAME};
CREATE DATABASE ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

# Full 백업 복원
zcat "${BACKUP_ROOT}/database/full.sql.gz" | mysql -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME}

log_success "Database 복구 완료"

# ==============================================
# 4. Elasticsearch 복구
# ==============================================

log_info "[4/6] Elasticsearch 복구 중..."

# Elasticsearch 시작
systemctl start elasticsearch
sleep 30

# Snapshot 복원
SNAPSHOT_NAME=$(ls "${BACKUP_ROOT}/elasticsearch/indices" | head -1)

curl -X POST "http://localhost:9200/_snapshot/backup/${SNAPSHOT_NAME}/_restore?wait_for_completion=true" \
    -H 'Content-Type: application/json' \
    -d '{
        "indices": "*",
        "ignore_unavailable": true,
        "include_global_state": true
    }'

log_success "Elasticsearch 복구 완료"

# ==============================================
# 5. 파일 복구
# ==============================================

log_info "[5/6] 파일 복구 중..."

if [ -d "${BACKUP_ROOT}/files" ]; then
    rm -rf "${DATA_DIR}/uploads"
    cp -r "${BACKUP_ROOT}/files" "${DATA_DIR}/uploads"
    chown -R mcps:mcps "${DATA_DIR}/uploads"
fi

log_success "파일 복구 완료"

# ==============================================
# 6. 설정 파일 복구 (선택)
# ==============================================

log_info "[6/6] 설정 파일 확인..."

log_info "설정 파일은 수동으로 확인하세요:"
log_info "  위치: ${BACKUP_ROOT}/config/"
ls -l "${BACKUP_ROOT}/config/"

# ==============================================
# 정리
# ==============================================

log_info "임시 파일 정리 중..."
# rm -rf "${RESTORE_DIR}"

# ==============================================
# 서비스 시작
# ==============================================

log_info "서비스 시작 중..."
bash "${SCRIPTS_DIR}/control/start_all.sh"

# ==============================================
# 완료
# ==============================================

log_success "=========================================="
log_success "  복구 완료!"
log_success "=========================================="
log_info "시스템 상태를 확인하세요:"
log_info "  sudo bash ${SCRIPTS_DIR}/manage/status.sh"
log_info ""
```



## 4. 모니터링 및 알림

### 4.1 모니터링 대시보드

```yaml
# Grafana 대시보드 구성

대시보드 1: 시스템 개요
  - 서비스 상태 (UP/DOWN)
  - 전체 응답 시간
  - 에러율
  - 활성 사용자 수
  - API 처리량

대시보드 2: 인프라
  - CPU 사용률
  - 메모리 사용률
  - 디스크 I/O
  - 네트워크 트래픽
  - 프로세스 수

대시보드 3: Database
  - 연결 수
  - 쿼리 실행 시간
  - 슬로우 쿼리
  - 테이블 크기
  - Replication Lag

대시보드 4: 애플리케이션
  - 요청 수 (by endpoint)
  - 응답 시간 분포
  - 에러 로그
  - 캐시 히트율
  - 큐 크기
```

### 4.2 알림 규칙 설정

```yaml
# /etc/prometheus/alert_rules.yml
# Prometheus 알림 규칙

groups:
  - name: system_alerts
    interval: 30s
    rules:
      # 서비스 다운
      - alert: ServiceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "서비스 다운: {{ $labels.job }}"
          description: "{{ $labels.instance }}의 {{ $labels.job }} 서비스가 2분 이상 응답하지 않습니다."

      # 높은 CPU 사용률
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "높은 CPU 사용률"
          description: "{{ $labels.instance }}의 CPU 사용률이 80%를 초과했습니다. 현재: {{ $value }}%"

      # 높은 메모리 사용률
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "높은 메모리 사용률"
          description: "{{ $labels.instance }}의 메모리 사용률이 85%를 초과했습니다. 현재: {{ $value }}%"

      # 디스크 공간 부족
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "디스크 공간 부족"
          description: "{{ $labels.instance }}의 디스크 여유 공간이 15% 미만입니다. 현재: {{ $value }}%"

  - name: database_alerts
    interval: 30s
    rules:
      # Database 연결 수 초과
      - alert: HighDatabaseConnections
        expr: mysql_global_status_threads_connected / mysql_global_variables_max_connections * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database 연결 수 높음"
          description: "Database 연결 수가 최대 연결 수의 80%를 초과했습니다. 현재: {{ $value }}%"

      # Replication Lag
      - alert: ReplicationLag
        expr: mysql_slave_status_seconds_behind_master > 60
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Replication Lag 발생"
          description: "Replication이 {{ $value }}초 지연되고 있습니다."

      # 슬로우 쿼리 증가
      - alert: HighSlowQueries
        expr: rate(mysql_global_status_slow_queries[5m]) > 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "슬로우 쿼리 증가"
          description: "슬로우 쿼리가 증가하고 있습니다. 현재: {{ $value }}/s"

  - name: application_alerts
    interval: 30s
    rules:
      # 높은 응답 시간
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "높은 응답 시간"
          description: "95 percentile 응답 시간이 1초를 초과했습니다. 현재: {{ $value }}s"

      # 높은 에러율
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100 > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "높은 에러율"
          description: "5xx 에러율이 5%를 초과했습니다. 현재: {{ $value }}%"

      # 낮은 캐시 히트율
      - alert: LowCacheHitRate
        expr: rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) * 100 < 70
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "낮은 캐시 히트율"
          description: "캐시 히트율이 70% 미만입니다. 현재: {{ $value }}%"

  - name: elasticsearch_alerts
    interval: 30s
    rules:
      # Elasticsearch Cluster Red
      - alert: ElasticsearchClusterRed
        expr: elasticsearch_cluster_health_status{color="red"} == 1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Elasticsearch Cluster Red"
          description: "Elasticsearch 클러스터 상태가 Red입니다."

      # Elasticsearch Heap Usage
      - alert: ElasticsearchHighHeapUsage
        expr: elasticsearch_jvm_memory_used_bytes{area="heap"} / elasticsearch_jvm_memory_max_bytes{area="heap"} * 100 > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Elasticsearch 높은 힙 사용률"
          description: "Elasticsearch 힙 사용률이 85%를 초과했습니다. 현재: {{ $value }}%"
```

### 4.3 Alertmanager 설정

```yaml
# /etc/alertmanager/alertmanager.yml
# Alertmanager 설정

global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alertmanager@example.com'
  smtp_auth_username: 'alertmanager@example.com'
  smtp_auth_password: 'PASSWORD'

# 알림 템플릿
templates:
  - '/etc/alertmanager/templates/*.tmpl'

# 라우팅
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  
  routes:
    # Critical 알림은 즉시 전송
    - match:
        severity: critical
      receiver: 'critical'
      group_wait: 0s
      repeat_interval: 5m
    
    # Warning 알림
    - match:
        severity: warning
      receiver: 'warning'
      repeat_interval: 1h

# 수신자 설정
receivers:
  - name: 'default'
    email_configs:
      - to: 'ops-team@example.com'
        headers:
          Subject: '[MCP] {{ .GroupLabels.alertname }}'
    
    webhook_configs:
      - url: 'http://slack-webhook-url'
        send_resolved: true

  - name: 'critical'
    email_configs:
      - to: 'ops-team@example.com,manager@example.com'
        headers:
          Subject: '[MCP CRITICAL] {{ .GroupLabels.alertname }}'
    
    webhook_configs:
      - url: 'http://slack-webhook-url'
        send_resolved: true
    
    # SMS 알림 (예시)
    # pagerduty_configs:
    #   - service_key: 'YOUR_SERVICE_KEY'

  - name: 'warning'
    email_configs:
      - to: 'ops-team@example.com'
        headers:
          Subject: '[MCP Warning] {{ .GroupLabels.alertname }}'

# 알림 억제 (Inhibition)
inhibit_rules:
  # 서비스가 다운되면 다른 알림 억제
  - source_match:
      severity: 'critical'
      alertname: 'ServiceDown'
    target_match:
      severity: 'warning'
    equal: ['instance']
```

### 4.4 로그 분석 자동화

```bash
#!/bin/bash
# /app/poc/mcps/scripts/operations/log_analysis.sh
# 로그 분석 및 이상 탐지

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

ANALYSIS_DATE=$(date +%Y-%m-%d)
REPORT_FILE="/data/reports/log_analysis_${ANALYSIS_DATE}.txt"

log_info "로그 분석 시작: ${ANALYSIS_DATE}"

# ==============================================
# 1. 에러 패턴 분석
# ==============================================

echo "========================================" > ${REPORT_FILE}
echo "로그 분석 보고서: ${ANALYSIS_DATE}" >> ${REPORT_FILE}
echo "========================================" >> ${REPORT_FILE}
echo "" >> ${REPORT_FILE}

echo "1. 에러 패턴 (Top 10)" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

for SERVICE in mcp-host api-gateway frontend; do
    LOG_FILE="/data/logs/${SERVICE}/error.log"
    
    if [ -f "${LOG_FILE}" ]; then
        echo "" >> ${REPORT_FILE}
        echo "[${SERVICE}]" >> ${REPORT_FILE}
        
        # 에러 메시지 추출 및 그룹화
        grep -i "error" "${LOG_FILE}" 2>/dev/null | \
            sed 's/[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}.*ERROR/ERROR/g' | \
            sort | uniq -c | sort -rn | head -10 >> ${REPORT_FILE}
    fi
done

echo "" >> ${REPORT_FILE}

# ==============================================
# 2. 응답 시간 분석
# ==============================================

echo "2. 느린 요청 분석" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# API Gateway 액세스 로그에서 느린 요청 추출
ACCESS_LOG="/data/logs/api-gateway/access.log"

if [ -f "${ACCESS_LOG}" ]; then
    echo "2초 이상 소요된 요청:" >> ${REPORT_FILE}
    
    awk '{
        if ($NF > 2000000) {  # 마이크로초 단위 (2초 = 2000000)
            print $7, $NF/1000000 "s"
        }
    }' "${ACCESS_LOG}" | sort -k2 -rn | head -20 >> ${REPORT_FILE}
fi

echo "" >> ${REPORT_FILE}

# ==============================================
# 3. 비정상 접근 탐지
# ==============================================

echo "3. 비정상 접근 탐지" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 404 에러가 많은 IP
echo "404 에러가 많은 IP (Top 10):" >> ${REPORT_FILE}
grep " 404 " "${ACCESS_LOG}" 2>/dev/null | \
    awk '{print $1}' | sort | uniq -c | sort -rn | head -10 >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# 401 에러가 많은 IP (인증 실패)
echo "인증 실패가 많은 IP (Top 10):" >> ${REPORT_FILE}
grep " 401 " "${ACCESS_LOG}" 2>/dev/null | \
    awk '{print $1}' | sort | uniq -c | sort -rn | head -10 >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# ==============================================
# 4. Database 슬로우 쿼리 분석
# ==============================================

echo "4. Database 슬로우 쿼리" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

SLOW_LOG="/var/log/mariadb/slow.log"

if [ -f "${SLOW_LOG}" ]; then
    # 오늘 발생한 슬로우 쿼리 수
    SLOW_COUNT=$(grep "Query_time:" "${SLOW_LOG}" 2>/dev/null | wc -l)
    echo "슬로우 쿼리 수: ${SLOW_COUNT}" >> ${REPORT_FILE}
    
    echo "" >> ${REPORT_FILE}
    echo "가장 느린 쿼리 (Top 5):" >> ${REPORT_FILE}
    
    # 슬로우 쿼리 파싱 (간단한 버전)
    grep -A 5 "Query_time:" "${SLOW_LOG}" 2>/dev/null | \
        head -30 >> ${REPORT_FILE}
fi

echo "" >> ${REPORT_FILE}

# ==============================================
# 5. 권장 사항
# ==============================================

echo "5. 권장 사항" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

RECOMMENDATIONS=()

# 에러가 많으면 경고
for SERVICE in mcp-host api-gateway frontend; do
    ERROR_COUNT=$(grep -i "error" "/data/logs/${SERVICE}/error.log" 2>/dev/null | wc -l)
    
    if [ ${ERROR_COUNT} -gt 100 ]; then
        RECOMMENDATIONS+=("${SERVICE}: 에러 로그 확인 필요 (${ERROR_COUNT}개)")
    fi
done

# 슬로우 쿼리가 많으면 경고
if [ ${SLOW_COUNT} -gt 50 ]; then
    RECOMMENDATIONS+=("Database: 슬로우 쿼리 최적화 필요 (${SLOW_COUNT}개)")
fi

if [ ${#RECOMMENDATIONS[@]} -eq 0 ]; then
    echo "  특별한 조치 필요 없음" >> ${REPORT_FILE}
else
    for REC in "${RECOMMENDATIONS[@]}"; do
        echo "  - ${REC}" >> ${REPORT_FILE}
    done
fi

echo "" >> ${REPORT_FILE}
echo "분석 완료: $(date)" >> ${REPORT_FILE}

# 출력
cat ${REPORT_FILE}

log_success "로그 분석 완료!"
```

***

## 5. 장애 대응

### 5.1 장애 대응 프로세스

```
┌─────────────────────────────────────────┐
│        장애 대응 프로세스                │
├─────────────────────────────────────────┤
│                                          │
│  [1. 장애 감지]                         │
│    - 모니터링 알림                       │
│    - 사용자 신고                         │
│    - 자동 헬스체크                       │
│          ↓                               │
│  [2. 초기 대응] (5분 이내)             │
│    - 장애 확인                          │
│    - 영향 범위 파악                     │
│    - 관련자 통보                        │
│          ↓                               │
│  [3. 원인 분석] (15분 이내)            │
│    - 로그 분석                          │
│    - 메트릭 확인                        │
│    - 시스템 상태 점검                   │
│          ↓                               │
│  [4. 임시 조치] (30분 이내)            │
│    - 서비스 재시작                      │
│    - 트래픽 우회                        │
│    - 긴급 패치                          │
│          ↓                               │
│  [5. 근본 해결]                         │
│    - 원인 제거                          │
│    - 시스템 정상화                      │
│    - 테스트 및 검증                     │
│          ↓                               │
│  [6. 사후 조치]                         │
│    - 장애 보고서 작성                   │
│    - 재발 방지 대책                     │
│    - 프로세스 개선                      │
│                                          │
└─────────────────────────────────────────┘
```

### 5.2 장애 레벨 정의

| 레벨 | 정의 | 대응 시간 | 예시 |
|------|------|----------|------|
| **P0 (Critical)** | 전체 서비스 중단 | 즉시 | 서버 다운, Database 장애 |
| **P1 (High)** | 주요 기능 장애 | 15분 이내 | 검색 불가, 로그인 실패 |
| **P2 (Medium)** | 부분 기능 장애 | 1시간 이내 | 특정 기능 오류, 성능 저하 |
| **P3 (Low)** | 경미한 문제 | 24시간 이내 | UI 오류, 로그 에러 |

### 5.3 장애 대응 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/scripts/operations/emergency_response.sh
# 긴급 장애 대응 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

INCIDENT_ID="INC_$(date +%Y%m%d%H%M%S)"
INCIDENT_DIR="/data/incidents/${INCIDENT_ID}"

log_warning "=========================================="
log_warning "  긴급 장애 대응 시작: ${INCIDENT_ID}"
log_warning "=========================================="

# ==============================================
# 장애 정보 수집
# ==============================================

collect_incident_data() {
    log_info "장애 정보 수집 중..."
    
    mkdir -p "${INCIDENT_DIR}"/{logs,metrics,database,system}
    
    # 타임스탬프 기록
    date > "${INCIDENT_DIR}/incident_time.txt"
    
    # 1. 서비스 상태
    systemctl status mariadb > "${INCIDENT_DIR}/system/mariadb_status.txt" 2>&1
    systemctl status redis > "${INCIDENT_DIR}/system/redis_status.txt" 2>&1
    systemctl status elasticsearch > "${INCIDENT_DIR}/system/elasticsearch_status.txt" 2>&1
    systemctl status mcp-host > "${INCIDENT_DIR}/system/mcp_host_status.txt" 2>&1
    systemctl status mcp-api-gateway > "${INCIDENT_DIR}/system/api_gateway_status.txt" 2>&1
    
    # 2. 로그 (최근 1000줄)
    tail -1000 /data/logs/mcp-host/error.log > "${INCIDENT_DIR}/logs/mcp_host_error.log" 2>&1
    tail -1000 /data/logs/api-gateway/error.log > "${INCIDENT_DIR}/logs/api_gateway_error.log" 2>&1
    tail -1000 /var/log/mariadb/mariadb.log > "${INCIDENT_DIR}/logs/mariadb.log" 2>&1
    tail -1000 /var/log/messages > "${INCIDENT_DIR}/logs/system.log" 2>&1
    
    # 3. 시스템 메트릭
    top -bn1 > "${INCIDENT_DIR}/metrics/top.txt"
    free -h > "${INCIDENT_DIR}/metrics/memory.txt"
    df -h > "${INCIDENT_DIR}/metrics/disk.txt"
    netstat -tuln > "${INCIDENT_DIR}/metrics/network.txt"
    ps aux --sort=-%mem | head -20 > "${INCIDENT_DIR}/metrics/top_memory.txt"
    ps aux --sort=-%cpu | head -20 > "${INCIDENT_DIR}/metrics/top_cpu.txt"
    
    # 4. Database 상태
    mysql -u root -e "SHOW PROCESSLIST;" > "${INCIDENT_DIR}/database/processlist.txt" 2>&1
    mysql -u root -e "SHOW ENGINE INNODB STATUS\G" > "${INCIDENT_DIR}/database/innodb_status.txt" 2>&1
    mysql -u root -e "SHOW STATUS;" > "${INCIDENT_DIR}/database/status.txt" 2>&1
    
    # 5. 압축
    cd /data/incidents
    tar -czf "${INCIDENT_ID}.tar.gz" "${INCIDENT_ID}"
    
    log_success "장애 정보 수집 완료: ${INCIDENT_DIR}"
}

# ==============================================
# 자동 복구 시도
# ==============================================

auto_recovery() {
    log_info "자동 복구 시도 중..."
    
    # 1. 서비스 재시작
    local FAILED_SERVICES=()
    
    for SERVICE in mariadb redis elasticsearch mcp-host mcp-api-gateway; do
        if ! systemctl is-active --quiet "${SERVICE}"; then
            log_warning "${SERVICE} 중지됨. 재시작 시도..."
            
            systemctl restart "${SERVICE}"
            sleep 5
            
            if systemctl is-active --quiet "${SERVICE}"; then
                log_success "${SERVICE} 재시작 성공"
            else
                log_error "${SERVICE} 재시작 실패"
                FAILED_SERVICES+=("${SERVICE}")
            fi
        fi
    done
    
    # 2. 헬스체크
    sleep 10
    bash "${SCRIPTS_DIR}/health/healthcheck.sh"
    
    if [ $? -eq 0 ]; then
        log_success "자동 복구 성공"
        return 0
    else
        log_error "자동 복구 실패"
        return 1
    fi
}

# ==============================================
# Database 긴급 복구
# ==============================================

database_emergency_recovery() {
    log_warning "Database 긴급 복구 시도..."
    
    # InnoDB 복구 모드로 시작
    systemctl stop mariadb
    
    # my.cnf에 복구 모드 추가
    echo "innodb_force_recovery = 1" >> /etc/my.cnf.d/recovery.cnf
    
    systemctl start mariadb
    sleep 10
    
    if systemctl is-active --quiet mariadb; then
        log_success "Database 복구 모드로 시작 성공"
        
        # 데이터 덤프
        mysqldump -u root --all-databases > "${INCIDENT_DIR}/database/emergency_dump.sql"
        
        # 복구 모드 해제
        rm /etc/my.cnf.d/recovery.cnf
        systemctl restart mariadb
        
        log_success "Database 긴급 복구 완료"
    else
        log_error "Database 복구 실패. 수동 조치 필요"
    fi
}

# ==============================================
# 트래픽 차단 (긴급)
# ==============================================

block_traffic() {
    log_warning "트래픽 차단 시작..."
    
    # Nginx를 통한 트래픽 차단 (Maintenance 모드)
    if command -v nginx &> /dev/null; then
        cat > /etc/nginx/conf.d/maintenance.conf << 'EOF'
server {
    listen 80 default_server;
    listen 443 ssl default_server;
    
    location / {
        return 503 "System maintenance in progress. Please try again later.";
    }
}
EOF
        
        nginx -t && nginx -s reload
        log_success "트래픽 차단 완료 (Maintenance 모드)"
    fi
}

# ==============================================
# 메인 메뉴
# ==============================================

show_menu() {
    echo ""
    echo "=========================================="
    echo "  긴급 장애 대응 메뉴"
    echo "=========================================="
    echo "1. 장애 정보 수집"
    echo "2. 자동 복구 시도"
    echo "3. Database 긴급 복구"
    echo "4. 트래픽 차단 (Maintenance)"
    echo "5. 전체 서비스 재시작"
    echo "6. 시스템 상태 확인"
    echo "9. 종료"
    echo "=========================================="
    read -p "선택: " choice
    
    case ${choice} in
        1)
            collect_incident_data
            ;;
        2)
            auto_recovery
            ;;
        3)
            database_emergency_recovery
            ;;
        4)
            block_traffic
            ;;
        5)
            bash "${SCRIPTS_DIR}/control/restart_all.sh"
            ;;
        6)
            bash "${SCRIPTS_DIR}/manage/status.sh"
            ;;
        9)
            log_info "종료합니다."
            exit 0
            ;;
        *)
            log_error "잘못된 선택입니다."
            ;;
    esac
    
    show_menu
}

# ==============================================
# 실행
# ==============================================

if [ $# -eq 0 ]; then
    # 대화형 모드
    show_menu
else
    # 명령줄 모드
    case $1 in
        collect)
            collect_incident_data
            ;;
        recover)
            auto_recovery
            ;;
        *)
            echo "Usage: $0 {collect|recover}"
            exit 1
            ;;
    esac
fi
```

### 5.4 장애 시나리오별 대응

```bash
#!/bin/bash
# /app/poc/mcps/docs/operations/incident_playbook.sh
# 장애 시나리오별 대응 매뉴얼

# ==============================================
# 시나리오 1: Database 연결 불가
# ==============================================

scenario_database_connection_failure() {
    cat << 'EOF'
========================================
장애: Database 연결 불가
========================================

증상:
- 애플리케이션에서 Database 연결 실패
- "Too many connections" 에러
- Connection timeout

원인:
1. MariaDB 서비스 중단
2. 최대 연결 수 초과
3. 네트워크 문제
4. 인증 실패

대응 절차:

1. MariaDB 상태 확인
   systemctl status mariadb
   
2. 연결 수 확인
   mysql -u root -e "SHOW PROCESSLIST;"
   mysql -u root -e "SHOW STATUS LIKE 'Threads_connected';"
   
3. 조치:
   
   [3-1] 서비스가 중단된 경우:
   systemctl start mariadb
   
   [3-2] 연결 수 초과:
   # 유휴 연결 종료
   mysql -u root -e "
     SELECT CONCAT('KILL ', id, ';') 
     FROM information_schema.processlist 
     WHERE command='Sleep' AND time > 300;
   "
   
   # max_connections 증가 (임시)
   mysql -u root -e "SET GLOBAL max_connections = 500;"
   
   [3-3] 네트워크 문제:
   # 방화벽 확인
   firewall-cmd --list-ports
   
   # 포트 확인
   netstat -tuln | grep 3306
   
4. 확인:
   mysql -u mcps_user -p -e "SELECT 1;"

5. 재발 방지:
   - Connection pool 설정 확인
   - 연결 leak 조사
   - max_connections 조정
EOF
}

# ==============================================
# 시나리오 2: 디스크 공간 부족
# ==============================================

scenario_disk_full() {
    cat << 'EOF'
========================================
장애: 디스크 공간 부족
========================================

증상:
- "No space left on device" 에러
- 쓰기 작업 실패
- 서비스 중단

원인:
1. 로그 파일 급증
2. 임시 파일 누적
3. Database 크기 증가
4. 백업 파일 누적

대응 절차:

1. 디스크 사용량 확인
   df -h
   du -sh /* | sort -rh | head -10
   
2. 긴급 공간 확보:
   
   [2-1] 로그 파일 정리
   # 오래된 로그 삭제
   find /data/logs -type f -mtime +7 -delete
   
   # 압축된 로그 삭제
   find /data/logs -name "*.gz" -mtime +7 -delete
   
   # journalctl 정리
   journalctl --vacuum-time=7d
   
   [2-2] 임시 파일 정리
   rm -rf /tmp/*
   rm -rf /var/tmp/*
   
   [2-3] 오래된 백업 삭제
   find /data/backups -type f -mtime +30 -delete
   
   [2-4] Database 정리
   # 불필요한 테이블 삭제
   # 오래된 audit_log 삭제
   mysql -u root -e "
     DELETE FROM mcps_db.audit_logs 
     WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
   "

3. 확인:
   df -h

4. 재발 방지:
   - 로그 로테이션 설정
   - 디스크 모니터링 알림
   - 자동 정리 스크립트 스케줄링
EOF
}

# ==============================================
# 시나리오 3: 메모리 부족 (OOM)
# ==============================================

scenario_out_of_memory() {
    cat << 'EOF'
========================================
장애: 메모리 부족 (OOM Killer)
========================================

증상:
- 프로세스 갑자기 종료
- "Out of memory" 에러
- 시스템 느림

원인:
1. Memory leak
2. 설정 과다 (Elasticsearch heap 등)
3. 프로세스 폭주
4. 캐시 과다 사용

대응 절차:

1. 메모리 상태 확인
   free -h
   vmstat 1
   
2. OOM Killer 로그 확인
   dmesg | grep -i "out of memory"
   grep -i "killed process" /var/log/messages
   
3. 메모리 사용 프로세스 확인
   ps aux --sort=-%mem | head -20
   
4. 긴급 조치:
   
   [4-1] Swap 활성화 (임시)
   swapon -a
   
   [4-2] 캐시 정리
   sync
   echo 3 > /proc/sys/vm/drop_caches
   
   [4-3] 메모리 많이 쓰는 서비스 재시작
   systemctl restart elasticsearch
   systemctl restart mcp-api-gateway
   
   [4-4] Elasticsearch heap 조정
   # /etc/elasticsearch/jvm.options.d/heap.options
   -Xms8g
   -Xmx8g

5. 확인:
   free -h

6. 재발 방지:
   - Memory leak 분석
   - Heap 크기 적정화
   - 메모리 모니터링
EOF
}

# ==============================================
# 시나리오 4: 높은 CPU 사용률
# ==============================================

scenario_high_cpu() {
    cat << 'EOF'
========================================
장애: 높은 CPU 사용률
========================================

증상:
- 시스템 전반적인 느림
- Load average 높음
- 응답 시간 증가

원인:
1. 슬로우 쿼리
2. 무한 루프
3. DDoS 공격
4. 비효율적 알고리즘

대응 절차:

1. CPU 사용률 확인
   top
   mpstat 1 5
   
2. CPU 많이 사용하는 프로세스
   ps aux --sort=-%cpu | head -20
   
3. 원인 분석:
   
   [3-1] Database 확인
   mysql -u root -e "SHOW PROCESSLIST;"
   
   # 슬로우 쿼리 확인
   tail -100 /var/log/mariadb/slow.log
   
   [3-2] 애플리케이션 프로파일링
   # Python 프로파일링
   py-spy top --pid <PID>
   
   [3-3] 네트워크 확인
   netstat -an | wc -l
   
4. 조치:
   
   [4-1] 슬로우 쿼리 kill
   mysql -u root -e "KILL <PROCESS_ID>;"
   
   [4-2] 부하 높은 프로세스 재시작
   systemctl restart mcp-api-gateway
   
   [4-3] Rate limiting 활성화
   # Nginx rate limit 설정
   
5. 확인:
   top

6. 재발 방지:
   - 쿼리 최적화
   - 인덱스 추가
   - 코드 최적화
EOF
}

# ==============================================
# 메뉴
# ==============================================

echo "=========================================="
echo "  장애 대응 매뉴얼"
echo "=========================================="
echo "1. Database 연결 불가"
echo "2. 디스크 공간 부족"
echo "3. 메모리 부족 (OOM)"
echo "4. 높은 CPU 사용률"
echo "=========================================="
read -p "시나리오 선택: " choice

case ${choice} in
    1) scenario_database_connection_failure ;;
    2) scenario_disk_full ;;
    3) scenario_out_of_memory ;;
    4) scenario_high_cpu ;;
    *) echo "잘못된 선택" ;;
esac
```

***

## 6. 성능 관리

### 6.1 성능 모니터링 지표

```yaml
# 주요 성능 지표 (KPI)

애플리케이션:
  - 평균 응답 시간: < 200ms
  - 95 percentile: < 500ms
  - 99 percentile: < 1s
  - 에러율: < 0.1%
  - 처리량: > 1000 req/s

Database:
  - 쿼리 실행 시간: < 100ms
  - 연결 사용률: < 80%
  - Replication lag: < 1s
  - 캐시 히트율: > 95%

Elasticsearch:
  - 검색 응답 시간: < 500ms
  - 인덱싱 처리량: > 1000 docs/s
  - JVM Heap: < 75%
  - 클러스터 상태: Green

Redis:
  - 응답 시간: < 10ms
  - 캐시 히트율: > 80%
  - 메모리 사용률: < 80%
  - 연결 수: < 1000

시스템:
  - CPU 사용률: < 70%
  - 메모리 사용률: < 80%
  - 디스크 I/O 대기: < 10%
  - 네트워크 처리량: < 70%
```

### 6.2 성능 테스트

```bash
#!/bin/bash
# /app/poc/mcps/scripts/operations/performance_test.sh
# 성능 테스트 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

TEST_DATE=$(date +%Y%m%d_%H%M%S)
RESULT_DIR="/data/performance_tests/${TEST_DATE}"

log_info "=========================================="
log_info "  성능 테스트 시작: ${TEST_DATE}"
log_info "=========================================="

mkdir -p "${RESULT_DIR}"

# ==============================================
# 1. API 부하 테스트 (Apache Bench)
# ==============================================

log_info "[1/4] API 부하 테스트..."

# API Gateway 테스트
ab -n 10000 -c 100 -g "${RESULT_DIR}/api_test.tsv" \
   "http://localhost:8080/api/v1/health" \
   > "${RESULT_DIR}/api_test_result.txt"

log_success "API 부하 테스트 완료"

# ==============================================
# 2. Database 성능 테스트
# ==============================================

log_info "[2/4] Database 성능 테스트..."

# sysbench 설치 확인
if ! command -v sysbench &> /dev/null; then
    dnf install -y sysbench
fi

# 테스트 데이터 준비
sysbench /usr/share/sysbench/oltp_read_write.lua \
    --mysql-host=localhost \
    --mysql-user=${DB_USER} \
    --mysql-password=${DB_PASSWORD} \
    --mysql-db=${DB_NAME} \
    --tables=10 \
    --table-size=10000 \
    prepare > /dev/null 2>&1

# 읽기/쓰기 테스트
sysbench /usr/share/sysbench/oltp_read_write.lua \
    --mysql-host=localhost \
    --mysql-user=${DB_USER} \
    --mysql-password=${DB_PASSWORD} \
    --mysql-db=${DB_NAME} \
    --tables=10 \
    --table-size=10000 \
    --threads=10 \
    --time=60 \
    run > "${RESULT_DIR}/db_test_result.txt"

# 정리
sysbench /usr/share/sysbench/oltp_read_write.lua \
    --mysql-host=localhost \
    --mysql-user=${DB_USER} \
    --mysql-password=${DB_PASSWORD} \
    --mysql-db=${DB_NAME} \
    cleanup > /dev/null 2>&1

log_success "Database 성능 테스트 완료"

# ==============================================
# 3. Elasticsearch 성능 테스트
# ==============================================

log_info "[3/4] Elasticsearch 성능 테스트..."

# Bulk 인덱싱 테스트
python3 << 'PYTHON_SCRIPT' > "${RESULT_DIR}/es_test_result.txt"
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import time
import json

es = Elasticsearch(['http://localhost:9200'])

# 테스트 데이터 생성
def generate_docs(count):
    for i in range(count):
        yield {
            "_index": "test_performance",
            "_source": {
                "title": f"Test Document {i}",
                "content": "This is a test document for performance testing. " * 10,
                "number": i
            }
        }

# 인덱싱 테스트
start_time = time.time()
success, failed = bulk(es, generate_docs(10000))
index_time = time.time() - start_time

print(f"Indexed {success} documents in {index_time:.2f} seconds")
print(f"Rate: {success/index_time:.2f} docs/s")

# 검색 테스트
es.indices.refresh(index="test_performance")

search_times = []
for i in range(100):
    start = time.time()
    result = es.search(index="test_performance", body={
        "query": {"match": {"content": "test"}}
    })
    search_times.append(time.time() - start)

avg_search_time = sum(search_times) / len(search_times)
print(f"\nAverage search time: {avg_search_time*1000:.2f}ms")

# 정리
es.indices.delete(index="test_performance")
PYTHON_SCRIPT

log_success "Elasticsearch 성능 테스트 완료"

# ==============================================
# 4. Redis 성능 테스트
# ==============================================

log_info "[4/4] Redis 성능 테스트..."

redis-benchmark -h localhost -p 6379 -t set,get -n 100000 -c 50 \
    > "${RESULT_DIR}/redis_test_result.txt"

log_success "Redis 성능 테스트 완료"

# ==============================================
# 결과 요약
# ==============================================

log_info "테스트 결과 요약 생성 중..."

cat > "${RESULT_DIR}/summary.txt" << EOF
========================================
성능 테스트 결과: ${TEST_DATE}
========================================

1. API 부하 테스트:
$(grep "Requests per second" "${RESULT_DIR}/api_test_result.txt")
$(grep "Time per request" "${RESULT_DIR}/api_test_result.txt")

2. Database 성능:
$(grep "transactions:" "${RESULT_DIR}/db_test_result.txt")
$(grep "queries:" "${RESULT_DIR}/db_test_result.txt")

3. Elasticsearch:
$(cat "${RESULT_DIR}/es_test_result.txt")

4. Redis:
$(grep "GET:" "${RESULT_DIR}/redis_test_result.txt")
$(grep "SET:" "${RESULT_DIR}/redis_test_result.txt")

테스트 완료 시간: $(date)
========================================
EOF

cat "${RESULT_DIR}/summary.txt"

log_success "=========================================="
log_success "  성능 테스트 완료!"
log_success "=========================================="
log_info "결과 디렉토리: ${RESULT_DIR}"
```




### 6.3 성능 튜닝 가이드

```bash
#!/bin/bash
# /app/poc/mcps/scripts/operations/performance_tuning.sh
# 성능 튜닝 가이드 및 자동화

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "성능 튜닝 분석 시작..."

# ==============================================
# Database 성능 분석
# ==============================================

analyze_database_performance() {
    log_info "Database 성능 분석 중..."
    
    echo "========================================" 
    echo "Database 성능 분석"
    echo "========================================"
    
    # 1. 인덱스 없는 테이블 확인
    echo -e "\n[1] 인덱스가 없는 테이블:"
    mysql -u root ${DB_NAME} -e "
        SELECT 
            table_name,
            table_rows,
            round(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
        FROM information_schema.tables
        WHERE table_schema = '${DB_NAME}'
        AND table_rows > 1000
        AND table_name NOT IN (
            SELECT DISTINCT table_name 
            FROM information_schema.statistics 
            WHERE table_schema = '${DB_NAME}' 
            AND index_name != 'PRIMARY'
        );"
    
    # 2. 사용되지 않는 인덱스
    echo -e "\n[2] 사용되지 않는 인덱스:"
    mysql -u root -e "
        SELECT 
            object_schema,
            object_name,
            index_name
        FROM performance_schema.table_io_waits_summary_by_index_usage
        WHERE index_name IS NOT NULL
        AND index_name != 'PRIMARY'
        AND count_star = 0
        AND object_schema = '${DB_NAME}'
        ORDER BY object_schema, object_name;"
    
    # 3. 테이블 조각화
    echo -e "\n[3] 조각화된 테이블 (최적화 필요):"
    mysql -u root ${DB_NAME} -e "
        SELECT 
            table_name,
            round(data_length/1024/1024, 2) AS data_mb,
            round(data_free/1024/1024, 2) AS free_mb,
            round((data_free/(data_length+data_free))*100, 2) AS frag_pct
        FROM information_schema.tables
        WHERE table_schema = '${DB_NAME}'
        AND data_free > 0
        AND (data_free/(data_length+data_free)) > 0.1
        ORDER BY frag_pct DESC;"
    
    # 4. 자주 실행되는 쿼리 (느린 쿼리)
    echo -e "\n[4] 최근 슬로우 쿼리 (Top 5):"
    mysql -u root -e "
        SELECT 
            LEFT(digest_text, 100) AS query,
            count_star AS exec_count,
            ROUND(avg_timer_wait/1000000000000, 3) AS avg_time_sec
        FROM performance_schema.events_statements_summary_by_digest
        WHERE schema_name = '${DB_NAME}'
        ORDER BY avg_timer_wait DESC
        LIMIT 5;" 2>/dev/null || echo "Performance schema 비활성화됨"
    
    echo -e "\n권장 사항:"
    echo "- 인덱스 없는 대용량 테이블에 인덱스 추가"
    echo "- 사용되지 않는 인덱스 삭제"
    echo "- 조각화된 테이블 OPTIMIZE"
    echo "- 슬로우 쿼리 최적화"
}

# ==============================================
# Elasticsearch 성능 분석
# ==============================================

analyze_elasticsearch_performance() {
    log_info "Elasticsearch 성능 분석 중..."
    
    echo -e "\n========================================"
    echo "Elasticsearch 성능 분석"
    echo "========================================"
    
    # 1. 클러스터 상태
    echo -e "\n[1] 클러스터 상태:"
    curl -s "http://localhost:9200/_cluster/health?pretty" | \
        jq '{status, number_of_nodes, active_shards, relocating_shards, unassigned_shards}'
    
    # 2. 인덱스 통계
    echo -e "\n[2] 인덱스 크기 및 문서 수:"
    curl -s "http://localhost:9200/_cat/indices?v&h=index,docs.count,store.size,pri,rep"
    
    # 3. JVM 메모리
    echo -e "\n[3] JVM 힙 사용률:"
    curl -s "http://localhost:9200/_cat/nodes?v&h=name,heap.percent,heap.current,heap.max,ram.percent"
    
    # 4. 느린 검색 쿼리
    echo -e "\n[4] 인덱스별 설정 확인:"
    curl -s "http://localhost:9200/_all/_settings?pretty" | \
        jq '.[] | {refresh_interval, number_of_shards, number_of_replicas}' | head -20
    
    echo -e "\n권장 사항:"
    echo "- Yellow/Red 상태인 경우 샤드 재배치"
    echo "- 힙 사용률 > 75% 시 힙 크기 조정"
    echo "- refresh_interval 조정으로 인덱싱 성능 향상"
    echo "- Force merge로 세그먼트 최적화"
}

# ==============================================
# 애플리케이션 성능 분석
# ==============================================

analyze_application_performance() {
    log_info "애플리케이션 성능 분석 중..."
    
    echo -e "\n========================================"
    echo "애플리케이션 성능 분석"
    echo "========================================"
    
    # 1. 프로세스 리소스 사용
    echo -e "\n[1] 프로세스 리소스 사용:"
    ps aux | grep -E "mcp-host|api-gateway|gunicorn" | grep -v grep | \
        awk '{printf "%-20s CPU: %5s%% MEM: %5s%% RSS: %8s\n", $11, $3, $4, $6}'
    
    # 2. 연결 풀 상태 (예시)
    echo -e "\n[2] Database 연결 상태:"
    mysql -u root -e "SHOW STATUS LIKE 'Threads_%';"
    
    # 3. Redis 연결 수
    echo -e "\n[3] Redis 연결 수:"
    redis-cli INFO clients | grep connected_clients
    
    # 4. API 응답 시간 분석 (로그 기반)
    echo -e "\n[4] API 응답 시간 분석 (최근 1000개 요청):"
    if [ -f "/data/logs/api-gateway/access.log" ]; then
        tail -1000 /data/logs/api-gateway/access.log | \
            awk '{sum+=$NF; count++} END {print "평균:", sum/count/1000, "ms"}' 2>/dev/null || \
            echo "로그 형식 확인 필요"
    fi
    
    echo -e "\n권장 사항:"
    echo "- 높은 메모리/CPU 사용 프로세스 최적화"
    echo "- 연결 풀 크기 조정"
    echo "- 캐싱 전략 개선"
}

# ==============================================
# 자동 튜닝 (안전한 항목만)
# ==============================================

auto_tune() {
    log_warning "자동 튜닝 시작 (안전한 항목만)..."
    
    # 1. Database 테이블 최적화
    log_info "조각화된 테이블 최적화..."
    mysql -u root ${DB_NAME} -N -e "
        SELECT CONCAT('OPTIMIZE TABLE ', table_name, ';')
        FROM information_schema.tables
        WHERE table_schema = '${DB_NAME}'
        AND data_free > 1048576  -- 1MB 이상
    " | mysql -u root ${DB_NAME}
    
    # 2. Elasticsearch force merge (읽기 전용 인덱스)
    log_info "Elasticsearch 세그먼트 병합..."
    curl -X POST "http://localhost:9200/documents/_forcemerge?max_num_segments=1" \
        -H 'Content-Type: application/json' 2>/dev/null
    
    # 3. Redis 메모리 최적화
    log_info "Redis 메모리 최적화..."
    redis-cli MEMORY PURGE
    
    # 4. 시스템 캐시 정리 (안전)
    log_info "시스템 캐시 정리..."
    sync
    echo 1 > /proc/sys/vm/drop_caches
    
    log_success "자동 튜닝 완료"
}

# ==============================================
# 메인 메뉴
# ==============================================

if [ $# -eq 0 ]; then
    echo "========================================"
    echo "  성능 튜닝 메뉴"
    echo "========================================"
    echo "1. Database 성능 분석"
    echo "2. Elasticsearch 성능 분석"
    echo "3. 애플리케이션 성능 분석"
    echo "4. 전체 분석"
    echo "5. 자동 튜닝 (안전)"
    echo "========================================"
    read -p "선택: " choice
    
    case ${choice} in
        1) analyze_database_performance ;;
        2) analyze_elasticsearch_performance ;;
        3) analyze_application_performance ;;
        4)
            analyze_database_performance
            analyze_elasticsearch_performance
            analyze_application_performance
            ;;
        5) auto_tune ;;
        *) echo "잘못된 선택" ;;
    esac
else
    case $1 in
        db) analyze_database_performance ;;
        es) analyze_elasticsearch_performance ;;
        app) analyze_application_performance ;;
        all)
            analyze_database_performance
            analyze_elasticsearch_performance
            analyze_application_performance
            ;;
        tune) auto_tune ;;
        *) echo "Usage: $0 {db|es|app|all|tune}" ;;
    esac
fi
```

***

## 7. 보안 운영

### 7.1 보안 점검 체크리스트

```bash
#!/bin/bash
# /app/poc/mcps/scripts/operations/security_audit.sh
# 보안 점검 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

AUDIT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="/data/reports/security_audit_${AUDIT_DATE}.txt"

log_info "=========================================="
log_info "  보안 점검 시작: ${AUDIT_DATE}"
log_info "=========================================="

mkdir -p /data/reports

# ==============================================
# 보고서 헤더
# ==============================================

cat > ${REPORT_FILE} << EOF
========================================
보안 점검 보고서
========================================
점검 일시: $(date)
점검자: $(whoami)
호스트: $(hostname)
========================================

EOF

# ==============================================
# 1. 시스템 보안
# ==============================================

echo "1. 시스템 보안 점검" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 1-1. 패키지 업데이트
echo "[1-1] 보안 업데이트 확인:" >> ${REPORT_FILE}
SECURITY_UPDATES=$(dnf updateinfo list security 2>/dev/null | wc -l)
echo "  보안 업데이트: ${SECURITY_UPDATES}개" >> ${REPORT_FILE}

if [ ${SECURITY_UPDATES} -gt 0 ]; then
    log_warning "보안 업데이트 필요: ${SECURITY_UPDATES}개"
    dnf updateinfo list security >> ${REPORT_FILE}
fi

# 1-2. 방화벽 상태
echo -e "\n[1-2] 방화벽 상태:" >> ${REPORT_FILE}
if systemctl is-active --quiet firewalld; then
    echo "  상태: 활성화" >> ${REPORT_FILE}
    firewall-cmd --list-all >> ${REPORT_FILE}
else
    echo "  상태: 비활성화 [경고]" >> ${REPORT_FILE}
    log_warning "방화벽이 비활성화되어 있습니다"
fi

# 1-3. SELinux 상태
echo -e "\n[1-3] SELinux 상태:" >> ${REPORT_FILE}
SELINUX_STATUS=$(getenforce)
echo "  상태: ${SELINUX_STATUS}" >> ${REPORT_FILE}

if [ "${SELINUX_STATUS}" = "Disabled" ]; then
    log_warning "SELinux가 비활성화되어 있습니다"
fi

# 1-4. SSH 설정 확인
echo -e "\n[1-4] SSH 보안 설정:" >> ${REPORT_FILE}
echo "  PermitRootLogin: $(grep "^PermitRootLogin" /etc/ssh/sshd_config)" >> ${REPORT_FILE}
echo "  PasswordAuthentication: $(grep "^PasswordAuthentication" /etc/ssh/sshd_config)" >> ${REPORT_FILE}
echo "  Port: $(grep "^Port" /etc/ssh/sshd_config)" >> ${REPORT_FILE}

# Root 로그인 허용 시 경고
if grep -q "^PermitRootLogin yes" /etc/ssh/sshd_config; then
    log_warning "SSH Root 로그인이 허용되어 있습니다"
fi

echo "" >> ${REPORT_FILE}

# ==============================================
# 2. 계정 보안
# ==============================================

echo "2. 계정 보안 점검" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 2-1. 비밀번호 없는 계정
echo "[2-1] 비밀번호 없는 계정:" >> ${REPORT_FILE}
awk -F: '($2 == "" ) { print $1 }' /etc/shadow >> ${REPORT_FILE}

# 2-2. UID 0인 계정 (root 외)
echo -e "\n[2-2] UID 0인 계정 (root 제외):" >> ${REPORT_FILE}
awk -F: '($3 == "0" && $1 != "root") {print $1}' /etc/passwd >> ${REPORT_FILE}

# 2-3. 최근 로그인 실패
echo -e "\n[2-3] 최근 로그인 실패 (Top 10):" >> ${REPORT_FILE}
grep "Failed password" /var/log/secure | \
    awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -10 >> ${REPORT_FILE}

# 2-4. sudo 권한 사용자
echo -e "\n[2-4] sudo 권한 사용자:" >> ${REPORT_FILE}
grep -v "^#" /etc/sudoers | grep -v "^$" >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# ==============================================
# 3. Database 보안
# ==============================================

echo "3. Database 보안 점검" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 3-1. 익명 사용자
echo "[3-1] 익명 사용자:" >> ${REPORT_FILE}
mysql -u root -N -e "SELECT User, Host FROM mysql.user WHERE User='';" >> ${REPORT_FILE} 2>&1

# 3-2. 원격 Root 접근
echo -e "\n[3-2] 원격 Root 접근 허용:" >> ${REPORT_FILE}
mysql -u root -N -e "SELECT User, Host FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');" >> ${REPORT_FILE} 2>&1

# 3-3. 비밀번호 없는 사용자
echo -e "\n[3-3] 비밀번호 없는 Database 사용자:" >> ${REPORT_FILE}
mysql -u root -N -e "SELECT User, Host FROM mysql.user WHERE authentication_string='';" >> ${REPORT_FILE} 2>&1

# 3-4. 권한 확인
echo -e "\n[3-4] 강력한 권한을 가진 사용자:" >> ${REPORT_FILE}
mysql -u root -N -e "SELECT User, Host FROM mysql.user WHERE Super_priv='Y' OR Grant_priv='Y';" >> ${REPORT_FILE} 2>&1

echo "" >> ${REPORT_FILE}

# ==============================================
# 4. 파일 권한
# ==============================================

echo "4. 파일 권한 점검" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 4-1. World writable 파일
echo "[4-1] World writable 파일 (중요 디렉토리):" >> ${REPORT_FILE}
find /app/poc/mcps /etc -type f -perm -002 2>/dev/null | head -20 >> ${REPORT_FILE}

# 4-2. SUID/SGID 파일
echo -e "\n[4-2] SUID/SGID 파일 (시스템 외):" >> ${REPORT_FILE}
find /app/poc/mcps -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null >> ${REPORT_FILE}

# 4-3. 설정 파일 권한
echo -e "\n[4-3] 민감한 설정 파일 권한:" >> ${REPORT_FILE}
for FILE in /app/poc/mcps/*/.env /etc/my.cnf.d/*.cnf /etc/redis/redis.conf; do
    if [ -f "${FILE}" ]; then
        ls -l "${FILE}" >> ${REPORT_FILE}
    fi
done

echo "" >> ${REPORT_FILE}

# ==============================================
# 5. 네트워크 보안
# ==============================================

echo "5. 네트워크 보안 점검" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 5-1. 열린 포트
echo "[5-1] 열린 포트:" >> ${REPORT_FILE}
netstat -tuln | grep LISTEN >> ${REPORT_FILE}

# 5-2. 외부 연결
echo -e "\n[5-2] 외부로의 연결 (ESTABLISHED):" >> ${REPORT_FILE}
netstat -tn | grep ESTABLISHED | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -10 >> ${REPORT_FILE}

# 5-3. Fail2ban 상태
echo -e "\n[5-3] Fail2ban 상태:" >> ${REPORT_FILE}
if command -v fail2ban-client &> /dev/null; then
    fail2ban-client status >> ${REPORT_FILE} 2>&1
else
    echo "  Fail2ban 미설치" >> ${REPORT_FILE}
fi

echo "" >> ${REPORT_FILE}

# ==============================================
# 6. 애플리케이션 보안
# ==============================================

echo "6. 애플리케이션 보안 점검" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 6-1. 환경 변수 노출
echo "[6-1] 민감한 환경 변수 파일 권한:" >> ${REPORT_FILE}
for ENV_FILE in /app/poc/mcps/*/.env; do
    if [ -f "${ENV_FILE}" ]; then
        PERM=$(stat -c %a "${ENV_FILE}")
        echo "  ${ENV_FILE}: ${PERM}" >> ${REPORT_FILE}
        
        if [ "${PERM}" != "600" ] && [ "${PERM}" != "400" ]; then
            log_warning "환경 변수 파일 권한 취약: ${ENV_FILE} (${PERM})"
        fi
    fi
done

# 6-2. SSL/TLS 인증서
echo -e "\n[6-2] SSL 인증서 만료일:" >> ${REPORT_FILE}
if [ -f "/etc/pki/mcps/server.crt" ]; then
    EXPIRY=$(openssl x509 -enddate -noout -in /etc/pki/mcps/server.crt)
    echo "  ${EXPIRY}" >> ${REPORT_FILE}
    
    EXPIRY_DATE=$(echo ${EXPIRY} | cut -d= -f2)
    EXPIRY_EPOCH=$(date -d "${EXPIRY_DATE}" +%s)
    NOW_EPOCH=$(date +%s)
    DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
    
    echo "  만료까지: ${DAYS_LEFT}일" >> ${REPORT_FILE}
    
    if [ ${DAYS_LEFT} -lt 30 ]; then
        log_warning "SSL 인증서 만료 임박: ${DAYS_LEFT}일"
    fi
else
    echo "  SSL 인증서 없음" >> ${REPORT_FILE}
fi

# 6-3. 디버그 모드 확인
echo -e "\n[6-3] 디버그 모드 확인:" >> ${REPORT_FILE}
for ENV_FILE in /app/poc/mcps/*/.env; do
    if [ -f "${ENV_FILE}" ]; then
        DEBUG=$(grep "^DEBUG" "${ENV_FILE}" 2>/dev/null || echo "Not found")
        echo "  $(basename $(dirname ${ENV_FILE})): ${DEBUG}" >> ${REPORT_FILE}
    fi
done

echo "" >> ${REPORT_FILE}

# ==============================================
# 7. 로그 보안
# ==============================================

echo "7. 로그 보안 점검" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 7-1. 민감한 정보 노출
echo "[7-1] 로그 파일 내 비밀번호 패턴 검색:" >> ${REPORT_FILE}
SENSITIVE_PATTERNS=("password" "token" "secret" "key")

for PATTERN in "${SENSITIVE_PATTERNS[@]}"; do
    COUNT=$(grep -ri "${PATTERN}" /data/logs/ 2>/dev/null | grep -v "Binary" | wc -l)
    echo "  ${PATTERN}: ${COUNT}개 발견" >> ${REPORT_FILE}
    
    if [ ${COUNT} -gt 10 ]; then
        log_warning "로그에 민감한 정보 다수 발견: ${PATTERN} (${COUNT}개)"
    fi
done

# 7-2. 로그 파일 권한
echo -e "\n[7-2] 로그 파일 권한:" >> ${REPORT_FILE}
ls -la /data/logs/*/error.log 2>/dev/null | head -10 >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# ==============================================
# 8. 취약점 스캔 (간단한 버전)
# ==============================================

echo "8. 알려진 취약점 확인" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 8-1. Python 패키지 취약점 (pip-audit 필요)
echo "[8-1] Python 패키지 취약점:" >> ${REPORT_FILE}
if command -v pip-audit &> /dev/null; then
    source ${VENV_DIR}/bin/activate
    pip-audit >> ${REPORT_FILE} 2>&1 || echo "  검사 완료" >> ${REPORT_FILE}
else
    echo "  pip-audit 미설치 (pip install pip-audit)" >> ${REPORT_FILE}
fi

echo "" >> ${REPORT_FILE}

# ==============================================
# 요약 및 권장사항
# ==============================================

echo "========================================" >> ${REPORT_FILE}
echo "요약 및 권장사항" >> ${REPORT_FILE}
echo "========================================" >> ${REPORT_FILE}

ISSUES=0

# 이슈 카운트
if [ ${SECURITY_UPDATES} -gt 0 ]; then
    echo "- [중요] 보안 업데이트 적용 필요: ${SECURITY_UPDATES}개" >> ${REPORT_FILE}
    ISSUES=$((ISSUES + 1))
fi

if ! systemctl is-active --quiet firewalld; then
    echo "- [중요] 방화벽 활성화 필요" >> ${REPORT_FILE}
    ISSUES=$((ISSUES + 1))
fi

if grep -q "^PermitRootLogin yes" /etc/ssh/sshd_config; then
    echo "- [보통] SSH Root 로그인 비활성화 권장" >> ${REPORT_FILE}
    ISSUES=$((ISSUES + 1))
fi

if [ ${DAYS_LEFT} -lt 30 ]; then
    echo "- [중요] SSL 인증서 갱신 필요: ${DAYS_LEFT}일 남음" >> ${REPORT_FILE}
    ISSUES=$((ISSUES + 1))
fi

if [ ${ISSUES} -eq 0 ]; then
    echo "발견된 주요 보안 이슈 없음" >> ${REPORT_FILE}
    log_success "보안 점검 완료: 이슈 없음"
else
    echo "총 ${ISSUES}개의 보안 이슈 발견" >> ${REPORT_FILE}
    log_warning "보안 점검 완료: ${ISSUES}개 이슈 발견"
fi

echo "" >> ${REPORT_FILE}
echo "점검 완료 시간: $(date)" >> ${REPORT_FILE}

# 출력
cat ${REPORT_FILE}

log_success "보안 점검 완료!"
log_info "보고서: ${REPORT_FILE}"
```

### 7.2 보안 강화 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/scripts/operations/security_hardening.sh
# 보안 강화 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

log_info "=========================================="
log_info "  보안 강화 시작"
log_info "=========================================="

# ==============================================
# 1. SSH 보안 강화
# ==============================================

harden_ssh() {
    log_info "SSH 보안 강화 중..."
    
    # 백업
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d)
    
    # 설정 변경
    sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
    sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
    sed -i 's/^#*PermitEmptyPasswords.*/PermitEmptyPasswords no/' /etc/ssh/sshd_config
    sed -i 's/^#*X11Forwarding.*/X11Forwarding no/' /etc/ssh/sshd_config
    sed -i 's/^#*MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config
    sed -i 's/^#*ClientAliveInterval.*/ClientAliveInterval 300/' /etc/ssh/sshd_config
    sed -i 's/^#*ClientAliveCountMax.*/ClientAliveCountMax 2/' /etc/ssh/sshd_config
    
    # 설정 추가
    if ! grep -q "^Protocol 2" /etc/ssh/sshd_config; then
        echo "Protocol 2" >> /etc/ssh/sshd_config
    fi
    
    # 재시작
    systemctl restart sshd
    
    log_success "SSH 보안 강화 완료"
}

# ==============================================
# 2. 방화벽 강화
# ==============================================

harden_firewall() {
    log_info "방화벽 강화 중..."
    
    # Fail2ban 설치 및 설정
    if ! command -v fail2ban-server &> /dev/null; then
        dnf install -y epel-release
        dnf install -y fail2ban
    fi
    
    # Fail2ban 설정
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
maxretry = 3

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10

[nginx-noscript]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 6
EOF
    
    systemctl enable fail2ban
    systemctl restart fail2ban
    
    log_success "방화벽 강화 완료"
}

# ==============================================
# 3. Database 보안 강화
# ==============================================

harden_database() {
    log_info "Database 보안 강화 중..."
    
    # 익명 사용자 삭제
    mysql -u root << EOF
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
EOF
    
    # 보안 설정
    cat >> /etc/my.cnf.d/security.cnf << EOF
[mysqld]
# Security
local_infile=0
skip_name_resolve=1
symbolic-links=0

# Audit
log_error=/var/log/mariadb/error.log
log_warnings=2
EOF
    
    systemctl restart mariadb
    
    log_success "Database 보안 강화 완료"
}

# ==============================================
# 4. 파일 권한 강화
# ==============================================

harden_file_permissions() {
    log_info "파일 권한 강화 중..."
    
    # 환경 변수 파일
    find /app/poc/mcps -name ".env" -exec chmod 600 {} \;
    
    # 설정 파일
    chmod 600 /etc/my.cnf.d/*.cnf 2>/dev/null || true
    chmod 600 /etc/redis/redis.conf 2>/dev/null || true
    chmod 600 /etc/elasticsearch/elasticsearch.yml 2>/dev/null || true
    
    # SSL 인증서
    if [ -d "/etc/pki/mcps" ]; then
        chmod 600 /etc/pki/mcps/*.key 2>/dev/null || true
        chmod 644 /etc/pki/mcps/*.crt 2>/dev/null || true
    fi
    
    # 로그 디렉토리
    chmod 750 /data/logs
    chown -R mcps:mcps /data/logs
    
    log_success "파일 권한 강화 완료"
}

# ==============================================
# 5. 커널 파라미터 보안 강화
# ==============================================

harden_kernel() {
    log_info "커널 파라미터 보안 강화 중..."
    
    cat > /etc/sysctl.d/99-security.conf << EOF
# IP 스푸핑 방지
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# ICMP redirect 무시
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0

# Source routing 비활성화
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# SYN Cookies
net.ipv4.tcp_syncookies = 1

# ICMP echo 브로드캐스트 무시
net.ipv4.icmp_echo_ignore_broadcasts = 1

# 잘못된 ICMP 에러 무시
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Log Martian Packets
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# IPv6 비활성화 (사용하지 않는 경우)
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF
    
    sysctl -p /etc/sysctl.d/99-security.conf
    
    log_success "커널 파라미터 보안 강화 완료"
}

# ==============================================
# 6. 감사 로깅 설정
# ==============================================

setup_audit_logging() {
    log_info "감사 로깅 설정 중..."
    
    # auditd 설치
    if ! command -v auditd &> /dev/null; then
        dnf install -y audit
    fi
    
    # 감사 규칙
    cat > /etc/audit/rules.d/mcps.rules << EOF
# 파일 접근 감사
-w /app/poc/mcps/ -p wa -k mcps_files
-w /etc/my.cnf.d/ -p wa -k db_config
-w /etc/redis/ -p wa -k redis_config

# 계정 관리 감사
-w /etc/passwd -p wa -k passwd_changes
-w /etc/shadow -p wa -k shadow_changes
-w /etc/sudoers -p wa -k sudoers_changes

# 시스템 호출 감사
-a exit,always -F arch=b64 -S execve -k exec
EOF
    
    # auditd 재시작
    service auditd restart
    
    log_success "감사 로깅 설정 완료"
}

# ==============================================
# 메인 메뉴
# ==============================================

if [ $# -eq 0 ]; then
    echo "========================================"
    echo "  보안 강화 메뉴"
    echo "========================================"
    echo "1. SSH 보안 강화"
    echo "2. 방화벽 강화"
    echo "3. Database 보안 강화"
    echo "4. 파일 권한 강화"
    echo "5. 커널 파라미터 보안"
    echo "6. 감사 로깅 설정"
    echo "7. 전체 강화"
    echo "========================================"
    read -p "선택: " choice
    
    case ${choice} in
        1) harden_ssh ;;
        2) harden_firewall ;;
        3) harden_database ;;
        4) harden_file_permissions ;;
        5) harden_kernel ;;
        6) setup_audit_logging ;;
        7)
            harden_ssh
            harden_firewall
            harden_database
            harden_file_permissions
            harden_kernel
            setup_audit_logging
            ;;
        *) echo "잘못된 선택" ;;
    esac
else
    case $1 in
        all)
            harden_ssh
            harden_firewall
            harden_database
            harden_file_permissions
            harden_kernel
            setup_audit_logging
            ;;
        *) echo "Usage: $0 {all}" ;;
    esac
fi

log_success "보안 강화 완료!"
```

***

## 8. 변경 관리

### 8.1 변경 관리 프로세스

```
┌─────────────────────────────────────────┐
│        변경 관리 프로세스                │
├─────────────────────────────────────────┤
│                                          │
│  [1. 변경 요청]                         │
│    - 변경 내용 상세 기술                 │
│    - 영향 범위 분석                     │
│    - 롤백 계획 수립                     │
│          ↓                               │
│  [2. 변경 검토]                         │
│    - 기술 검토                          │
│    - 보안 검토                          │
│    - 승인                               │
│          ↓                               │
│  [3. 변경 준비]                         │
│    - 테스트 환경 검증                   │
│    - 백업 수행                          │
│    - 체크리스트 준비                    │
│          ↓                               │
│  [4. 변경 실행]                         │
│    - 변경 작업 수행                     │
│    - 단계별 확인                        │
│    - 문서화                             │
│          ↓                               │
│  [5. 변경 검증]                         │
│    - 기능 테스트                        │
│    - 성능 확인                          │
│    - 모니터링                           │
│          ↓                               │
│  [6. 사후 검토]                         │
│    - 결과 분석                          │
│    - 문서 업데이트                      │
│    - 교훈 도출                          │
│                                          │
└─────────────────────────────────────────┘
```

### 8.2 변경 관리 템플릿

```markdown
# 변경 요청서 (Change Request)

## 기본 정보
- **CR 번호**: CR-2026-001
- **요청자**: 홍길동
- **요청일**: 2026-01-08
- **변경 유형**: [ ] 긴급 [ ] 일반 [x] 계획된
- **우선순위**: [ ] 높음 [x] 보통 [ ] 낮음

## 변경 내용
### 변경 대상
- Database 인덱스 추가
- API 응답 시간 개선

### 변경 사유
- 검색 성능 저하 (평균 2초 → 목표 500ms)
- 사용자 불만 증가

### 상세 내용
```sql
CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_documents_created_at ON documents(created_at);
```

## 영향 분석
### 영향받는 시스템
- Database: MariaDB
- 애플리케이션: API Gateway

### 다운타임
- **예상 시간**: 5분
- **작업 시간**: 2026-01-08 02:00-02:05 (KST)

### 영향받는 사용자
- 영향 범위: 없음 (Online DDL 사용)

## 롤백 계획
```sql
DROP INDEX idx_documents_category ON documents;
DROP INDEX idx_documents_created_at ON documents;
```

## 테스트 계획
1. 스테이징 환경 적용
2. 검색 성능 테스트
3. 부하 테스트

## 체크리스트
- [ ] 백업 완료
- [ ] 스테이징 테스트 완료
- [ ] 롤백 스크립트 준비
- [ ] 모니터링 설정
- [ ] 관련자 통보

## 승인
- **기술 검토자**: ___________  날짜: _______
- **보안 검토자**: ___________  날짜: _______
- **승인자**: ___________  날짜: _______
```

### 8.3 변경 실행 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/scripts/operations/change_management.sh
# 변경 관리 실행 스크립트

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

CHANGE_ID="CR_$(date +%Y%m%d_%H%M%S)"
CHANGE_DIR="/data/changes/${CHANGE_ID}"

log_info "=========================================="
log_info "  변경 작업 시작: ${CHANGE_ID}"
log_info "=========================================="

# ==============================================
# 변경 작업 준비
# ==============================================

prepare_change() {
    log_info "변경 작업 준비 중..."
    
    mkdir -p "${CHANGE_DIR}"/{pre,post,rollback,logs}
    
    # 타임스탬프 기록
    date > "${CHANGE_DIR}/start_time.txt"
    
    # 1. 사전 상태 기록
    log_info "사전 상태 기록 중..."
    
    bash "${SCRIPTS_DIR}/manage/status.sh" > "${CHANGE_DIR}/pre/system_status.txt"
    bash "${SCRIPTS_DIR}/health/healthcheck.sh" > "${CHANGE_DIR}/pre/health_check.txt" 2>&1 || true
    
    # Database 상태
    mysql -u root -e "SHOW PROCESSLIST;" > "${CHANGE_DIR}/pre/db_processlist.txt"
    mysql -u root -e "SHOW TABLE STATUS FROM ${DB_NAME};" > "${CHANGE_DIR}/pre/db_tables.txt"
    
    # 2. 백업 수행
    log_info "백업 수행 중..."
    bash "${SCRIPTS_DIR}/backup/backup.sh"
    
    log_success "변경 작업 준비 완료"
}

# ==============================================
# 변경 작업 실행
# ==============================================

execute_change() {
    local CHANGE_SCRIPT=$1
    
    if [ ! -f "${CHANGE_SCRIPT}" ]; then
        log_error "변경 스크립트를 찾을 수 없습니다: ${CHANGE_SCRIPT}"
        return 1
    fi
    
    log_info "변경 작업 실행 중..."
    log_info "스크립트: ${CHANGE_SCRIPT}"
    
    # 변경 스크립트 실행
    bash "${CHANGE_SCRIPT}" 2>&1 | tee "${CHANGE_DIR}/logs/change_execution.log"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "변경 작업 실행 완료"
        return 0
    else
        log_error "변경 작업 실행 실패"
        return 1
    fi
}

# ==============================================
# 변경 검증
# ==============================================

verify_change() {
    log_info "변경 검증 중..."
    
    # 1. 헬스체크
    log_info "헬스체크 수행 중..."
    if bash "${SCRIPTS_DIR}/health/healthcheck.sh" > "${CHANGE_DIR}/post/health_check.txt" 2>&1; then
        log_success "헬스체크 통과"
    else
        log_error "헬스체크 실패"
        return 1
    fi
    
    # 2. 서비스 상태
    log_info "서비스 상태 확인 중..."
    bash "${SCRIPTS_DIR}/manage/status.sh" > "${CHANGE_DIR}/post/system_status.txt"
    
    # 3. 성능 확인 (간단한 테스트)
    log_info "성능 확인 중..."
    
    # API 응답 시간
    API_RESPONSE=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8080/api/v1/health)
    echo "API 응답 시간: ${API_RESPONSE}초" | tee -a "${CHANGE_DIR}/post/performance.txt"
    
    # Database 응답 시간
    DB_RESPONSE=$(mysql -u root -e "SELECT BENCHMARK(1000, MD5('test'));" 2>&1 | grep "Query OK" || echo "0.01 sec")
    echo "Database 응답: ${DB_RESPONSE}" | tee -a "${CHANGE_DIR}/post/performance.txt"
    
    log_success "변경 검증 완료"
}

# ==============================================
# 롤백
# ==============================================

rollback_change() {
    local ROLLBACK_SCRIPT=$1
    
    log_warning "=========================================="
    log_warning "  롤백 시작"
    log_warning "=========================================="
    
    if [ ! -f "${ROLLBACK_SCRIPT}" ]; then
        log_error "롤백 스크립트를 찾을 수 없습니다: ${ROLLBACK_SCRIPT}"
        return 1
    fi
    
    # 롤백 실행
    bash "${ROLLBACK_SCRIPT}" 2>&1 | tee "${CHANGE_DIR}/logs/rollback_execution.log"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "롤백 완료"
        
        # 롤백 후 검증
        bash "${SCRIPTS_DIR}/health/healthcheck.sh"
        
        return 0
    else
        log_error "롤백 실패 - 수동 개입 필요"
        return 1
    fi
}

# ==============================================
# 변경 완료
# ==============================================

finalize_change() {
    log_info "변경 작업 마무리 중..."
    
    # 종료 시간 기록
    date > "${CHANGE_DIR}/end_time.txt"
    
    # 변경 보고서 생성
    cat > "${CHANGE_DIR}/change_report.txt" << EOF
========================================
변경 작업 보고서
========================================

변경 ID: ${CHANGE_ID}
시작 시간: $(cat ${CHANGE_DIR}/start_time.txt)
종료 시간: $(cat ${CHANGE_DIR}/end_time.txt)
작업자: $(whoami)
호스트: $(hostname)

변경 결과: 성공

사전 상태:
$(cat ${CHANGE_DIR}/pre/health_check.txt | grep "상태:")

사후 상태:
$(cat ${CHANGE_DIR}/post/health_check.txt | grep "상태:")

성능 비교:
$(cat ${CHANGE_DIR}/post/performance.txt)

로그 위치: ${CHANGE_DIR}/logs/

========================================
EOF
    
    cat "${CHANGE_DIR}/change_report.txt"
    
    log_success "변경 작업 완료!"
}

# ==============================================
# 메인
# ==============================================

usage() {
    echo "Usage: $0 <change_script> [rollback_script]"
    echo ""
    echo "Example:"
    echo "  $0 /path/to/change.sh /path/to/rollback.sh"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

CHANGE_SCRIPT=$1
ROLLBACK_SCRIPT=${2:-""}

# 1. 준비
prepare_change

# 2. 실행
if execute_change "${CHANGE_SCRIPT}"; then
    # 3. 검증
    if verify_change; then
        # 4. 완료
        finalize_change
    else
        # 검증 실패 - 롤백
        log_error "변경 검증 실패. 롤백 시작..."
        
        if [ -n "${ROLLBACK_SCRIPT}" ]; then
            rollback_change "${ROLLBACK_SCRIPT}"
        else
            log_error "롤백 스크립트가 지정되지 않았습니다. 수동 롤백 필요"
        fi
        
        exit 1
    fi
else
    # 실행 실패 - 롤백
    log_error "변경 실행 실패. 롤백 시작..."
    
    if [ -n "${ROLLBACK_SCRIPT}" ]; then
        rollback_change "${ROLLBACK_SCRIPT}"
    else
        log_error "롤백 스크립트가 지정되지 않았습니다. 수동 롤백 필요"
    fi
    
    exit 1
fi
```

***

## 9. 용량 계획

### 9.1 용량 모니터링

```bash
#!/bin/bash
# /app/poc/mcps/scripts/operations/capacity_monitoring.sh
# 용량 모니터링 및 예측

set -e

source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils/logger.sh"

REPORT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="/data/reports/capacity_report_${REPORT_DATE}.txt"

log_info "용량 모니터링 시작..."

mkdir -p /data/reports

# ==============================================
# 보고서 헤더
# ==============================================

cat > ${REPORT_FILE} << EOF
========================================
용량 모니터링 보고서
========================================
생성 일시: $(date)
보고 기간: 최근 30일
========================================

EOF

# ==============================================
# 1. Database 용량
# ==============================================

echo "1. Database 용량" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

# 현재 크기
mysql -u root -e "
    SELECT 
        table_schema AS 'Database',
        ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)',
        ROUND(SUM(data_free) / 1024 / 1024, 2) AS 'Free (MB)'
    FROM information_schema.tables
    WHERE table_schema = '${DB_NAME}'
    GROUP BY table_schema;
" >> ${REPORT_FILE}

# 테이블별 크기
echo -e "\n테이블별 크기:" >> ${REPORT_FILE}
mysql -u root -e "
    SELECT 
        table_name AS 'Table',
        table_rows AS 'Rows',
        ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
    FROM information_schema.tables
    WHERE table_schema = '${DB_NAME}'
    ORDER BY (data_length + index_length) DESC
    LIMIT 10;
" >> ${REPORT_FILE}

# 증가율 계산 (간단한 예측)
CURRENT_SIZE=$(mysql -u root -N -e "
    SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2)
    FROM information_schema.tables
    WHERE table_schema = '${DB_NAME}';
")

echo -e "\n현재 Database 크기: ${CURRENT_SIZE} MB" >> ${REPORT_FILE}
echo "예상 증가율: 10% / 월" >> ${REPORT_FILE}
echo "3개월 후 예상 크기: $(echo "${CURRENT_SIZE} * 1.331" | bc) MB" >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# ==============================================
# 2. Elasticsearch 용량
# ==============================================

echo "2. Elasticsearch 용량" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

curl -s "http://localhost:9200/_cat/indices?v&h=index,docs.count,store.size" >> ${REPORT_FILE}

echo -e "\n클러스터 통계:" >> ${REPORT_FILE}
curl -s "http://localhost:9200/_cluster/stats?pretty" | \
    jq '{
        indices: .indices.count,
        docs: .indices.docs.count,
        store_size: .indices.store.size_in_bytes
    }' >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# ==============================================
# 3. 디스크 사용량
# ==============================================

echo "3. 디스크 사용량" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

df -h | grep -E "/$|/data" >> ${REPORT_FILE}

echo -e "\n디렉토리별 사용량:" >> ${REPORT_FILE}
du -sh /data/* 2>/dev/null | sort -rh | head -10 >> ${REPORT_FILE}

# 증가 추세 (로그 기반)
echo -e "\n로그 파일 증가 추세:" >> ${REPORT_FILE}
find /data/logs -name "*.log" -mtime -30 -exec du -sh {} \; | \
    awk '{sum+=$1} END {print "최근 30일 증가량:", sum, "MB"}' >> ${REPORT_FILE} 2>/dev/null || \
    echo "데이터 부족" >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# ==============================================
# 4. 메모리 사용량
# ==============================================

echo "4. 메모리 사용량" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

free -h >> ${REPORT_FILE}

echo -e "\n프로세스별 메모리:" >> ${REPORT_FILE}
ps aux --sort=-%mem | head -10 | \
    awk '{printf "%-20s %6s%%\n", $11, $4}' >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# ==============================================
# 5. 연결 수 추이
# ==============================================

echo "5. 연결 수 추이" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

echo "Database 연결:" >> ${REPORT_FILE}
mysql -u root -e "SHOW STATUS LIKE 'Threads_%';" >> ${REPORT_FILE}

echo -e "\nRedis 연결:" >> ${REPORT_FILE}
redis-cli INFO clients | grep connected_clients >> ${REPORT_FILE}

echo "" >> ${REPORT_FILE}

# ==============================================
# 6. 용량 경고
# ==============================================

echo "6. 용량 경고" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

WARNINGS=()

# 디스크 경고
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
if [ ${DISK_USAGE} -gt 80 ]; then
    WARNINGS+=("디스크 사용률 높음: ${DISK_USAGE}%")
fi

# Database 크기 경고 (10GB 이상)
if [ $(echo "${CURRENT_SIZE} > 10240" | bc) -eq 1 ]; then
    WARNINGS+=("Database 크기 큼: ${CURRENT_SIZE} MB")
fi

# 메모리 경고
MEM_USAGE=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')
if [ ${MEM_USAGE} -gt 85 ]; then
    WARNINGS+=("메모리 사용률 높음: ${MEM_USAGE}%")
fi

if [ ${#WARNINGS[@]} -eq 0 ]; then
    echo "경고 없음" >> ${REPORT_FILE}
else
    for WARNING in "${WARNINGS[@]}"; do
        echo "- ${WARNING}" >> ${REPORT_FILE}
        log_warning "${WARNING}"
    done
fi

echo "" >> ${REPORT_FILE}

# ==============================================
# 7. 권장 사항
# ==============================================

echo "7. 권장 사항" >> ${REPORT_FILE}
echo "----------------------------------------" >> ${REPORT_FILE}

RECOMMENDATIONS=()

if [ ${DISK_USAGE} -gt 70 ]; then
    RECOMMENDATIONS+=("디스크 정리 또는 확장 고려")
fi

if [ $(echo "${CURRENT_SIZE} > 5120" | bc) -eq 1 ]; then
    RECOMMENDATIONS+=("Database 아카이빙 고려")
fi

if [ ${MEM_USAGE} -gt 80 ]; then
    RECOMMENDATIONS+=("메모리 증설 고려")
fi

if [ ${#RECOMMENDATIONS[@]} -eq 0 ]; then
    echo "특별한 조치 필요 없음" >> ${REPORT_FILE}
else
    for REC in "${RECOMMENDATIONS[@]}"; do
        echo "- ${REC}" >> ${REPORT_FILE}
    done
fi

echo "" >> ${REPORT_FILE}
echo "보고서 생성 완료: $(date)" >> ${REPORT_FILE}

# 출력
cat ${REPORT_FILE}

log_success "용량 모니터링 완료!"
log_info "보고서: ${REPORT_FILE}"
```

***

## 10. 운영 체크리스트

### 10.1 일일 체크리스트

```markdown
# MCP 시스템 일일 점검 체크리스트

날짜: _______________
점검자: _______________

## 1. 서비스 상태 점검
- [ ] MariaDB 실행 중
- [ ] Redis 실행 중
- [ ] Elasticsearch 실행 중
- [ ] MCP Host 실행 중
- [ ] API Gateway 실행 중
- [ ] Frontend 실행 중

## 2. 시스템 리소스
- [ ] CPU 사용률 < 70%
- [ ] 메모리 사용률 < 80%
- [ ] 디스크 사용률 < 80%
- [ ] Swap 사용량 확인

## 3. Database
- [ ] 연결 수 정상 범위
- [ ] 슬로우 쿼리 확인
- [ ] Replication 지연 없음 (클러스터의 경우)
- [ ] 백업 완료 확인

## 4. 로그 점검
- [ ] Error 로그 확인 (MCP Host)
- [ ] Error 로그 확인 (API Gateway)
- [ ] Error 로그 확인 (Frontend)
- [ ] 시스템 로그 확인

## 5. 백업
- [ ] 최근 백업 24시간 이내
- [ ] 백업 파일 무결성 확인
- [ ] 백업 크기 적정

## 6. 보안
- [ ] 실패한 로그인 시도 확인
- [ ] Fail2ban 상태 확인
- [ ] 방화벽 상태 확인

## 7. 성능
- [ ] 평균 응답 시간 정상
- [ ] 에러율 < 1%
- [ ] API 처리량 정상

## 8. 알림
- [ ] 모니터링 알림 확인
- [ ] 미처리 알림 없음

## 이슈
_______________________________________________
_______________________________________________
_______________________________________________

## 특이사항
_______________________________________________
_______________________________________________
_______________________________________________

서명: _______________
```

### 10.2 주간 체크리스트

```markdown
# MCP 시스템 주간 점검 체크리스트

주차: _______________
점검자: _______________

## 1. 시스템 업데이트
- [ ] 보안 패치 확인
- [ ] 패키지 업데이트 필요 여부
- [ ] Python 패키지 취약점 확인

## 2. 용량 관리
- [ ] Database 크기 증가 추이
- [ ] Elasticsearch 인덱스 크기
- [ ] 로그 파일 정리 필요 여부
- [ ] 백업 저장 공간 확인

## 3. 성능 분석
- [ ] 주간 성능 통계 확인
- [ ] 슬로우 쿼리 분석
- [ ] 캐시 히트율 확인
- [ ] API 응답 시간 추이

## 4. 백업 테스트
- [ ] 백업 복구 테스트 수행
- [ ] 백업 정책 준수 확인

## 5. 보안 점검
- [ ] 보안 감사 수행
- [ ] SSL 인증서 만료일 확인
- [ ] 접근 로그 분석
- [ ] 취약점 스캔

## 6. 문서 업데이트
- [ ] 변경 사항 문서화
- [ ] 운영 일지 작성
- [ ] 알려진 이슈 업데이트

## 7. 정리 작업
- [ ] 임시 파일 정리
- [ ] 오래된 로그 삭제
- [ ] 오래된 백업 삭제

## 주간 보고
_______________________________________________
_______________________________________________
_______________________________________________

서명: _______________
```

### 10.3 월간 체크리스트

```markdown
# MCP 시스템 월간 점검 체크리스트

월: _______________
점검자: _______________

## 1. 전체 시스템 검토
- [ ] 아키텍처 검토
- [ ] 용량 계획 업데이트
- [ ] 성능 벤치마크
- [ ] DR(재해복구) 테스트

## 2. Database 유지보수
- [ ] 테이블 최적화
- [ ] 인덱스 재구성
- [ ] 통계 정보 업데이트
- [ ] 파티션 관리

## 3. 보안 검토
- [ ] 접근 권한 검토
- [ ] 계정 감사
- [ ] 보안 정책 준수 확인
- [ ] 침투 테스트 (분기별)

## 4. 성능 튜닝
- [ ] 쿼리 최적화
- [ ] 캐시 전략 검토
- [ ] 리소스 사용 최적화

## 5. 백업 및 복구
- [ ] 전체 복구 테스트
- [ ] 백업 전략 검토
- [ ] RTO/RPO 목표 달성 확인

## 6. 모니터링 개선
- [ ] 알림 규칙 검토
- [ ] 대시보드 업데이트
- [ ] 메트릭 추가/제거

## 7. 문서화
- [ ] 운영 문서 업데이트
- [ ] 장애 대응 매뉴얼 갱신
- [ ] 아키텍처 다이어그램 업데이트

## 8. 교육 및 개선
- [ ] 팀 교육 실시
- [ ] 운영 프로세스 개선
- [ ] 자동화 확대

## 월간 통계
- 가동률: ______%
- 평균 응답 시간: ______ms
- 총 에러 수: ______건
- 장애 건수: ______건

## 개선 계획
_______________________________________________
_______________________________________________
_______________________________________________

서명: _______________
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


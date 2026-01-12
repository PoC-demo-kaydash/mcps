# MCP 시스템 관리 가이드

## 목차
- [설치](#설치)
- [실행](#실행)
- [상태 확인](#상태-확인)
- [로그 조회](#로그-조회)
- [백업/복구](#백업복구)
- [문제 해결](#문제-해결)

---

## 설치

### 1. 전체 설치 (권장)
```bash
cd /app/poc/mcps/scripts
./install/setup.sh
```

이 스크립트는 다음을 자동으로 수행합니다:
1. 환경 확인 (OS, 디스크, 메모리, 네트워크)
2. Python 3.11 설치 및 venv 생성
3. MariaDB 10.11 설치 및 설정
4. Redis 설치 및 설정
5. Elasticsearch 8.x 설치 및 설정
6. MCP 서비스 설치 및 등록
7. 데이터베이스 초기화

### 2. 개별 설치
```bash
# 환경 확인
./env/check_env.sh

# Python 설치
./install/install_python.sh

# MariaDB 설치
./install/install_database.sh

# Redis 설치
./install/install_redis.sh

# Elasticsearch 설치
./install/install_elasticsearch.sh

# MCP 서비스 설치
./install/install_services.sh
```

---

## 실행

### 전체 시작
```bash
./control/start_all.sh
```

### 전체 중지
```bash
./control/stop_all.sh
```

### 전체 재시작
```bash
./control/restart_all.sh
```

### 개별 서비스 제어
```bash
# 시작
./control/start_service.sh mcp-host
./control/start_service.sh mcp-api-gateway
./control/start_service.sh mcp-frontend

# 중지
./control/stop_service.sh mcp-host
./control/stop_service.sh mcp-api-gateway
./control/stop_service.sh mcp-frontend
```

---

## 상태 확인

### 시스템 상태
```bash
./manage/status.sh
```

표시 내용:
- 서비스 실행 상태
- 포트 사용 상태
- 디스크 사용량
- 메모리 사용량

### 헬스체크
```bash
# 전체 헬스체크
./health/healthcheck.sh

# 개별 확인
./health/check_database.sh      # 데이터베이스
./health/check_services.sh      # 서비스
./health/check_connectivity.sh  # 네트워크
```

---

## 로그 조회

### 기본 사용법
```bash
./manage/logs.sh <service> [options]
```

### 예제
```bash
# 최근 50줄 (기본)
./manage/logs.sh mcp-host

# 최근 100줄
./manage/logs.sh mcp-host -n 100

# 실시간 추적
./manage/logs.sh mcp-host -f

# 에러 로그만
./manage/logs.sh mcp-host -e

# 실시간 에러 로그
./manage/logs.sh mcp-host -f -e
```

### 지원 서비스
- `mcp-host` - MCP Host
- `api-gateway` - API Gateway
- `frontend` - Frontend
- `mariadb` - MariaDB
- `redis` - Redis
- `elasticsearch` - Elasticsearch

---

## 백업/복구

### 백업
```bash
./backup/backup.sh
```

백업 내용:
- 데이터베이스 (mysqldump)
- 설정 파일 (config/)

백업 위치: `/app/poc/mcps/backups/`

### 복구
```bash
# 백업 파일 목록 확인
./backup/restore.sh

# 복구 실행
./backup/restore.sh /app/poc/mcps/backups/20240101_120000.tar.gz
```

⚠️ **주의**: 복구 시 기존 데이터가 삭제됩니다!

---

## 문제 해결

### 서비스가 시작되지 않을 때
1. 상태 확인
```bash
./manage/status.sh
```

2. 로그 확인
```bash
./manage/logs.sh <service> -e
```

3. 헬스체크
```bash
./health/healthcheck.sh
```

### 포트 충돌
```bash
# 포트 사용 확인
netstat -tuln | grep <port>

# 프로세스 확인
lsof -i :<port>
```

### 디스크 부족
```bash
# 오래된 로그/백업 삭제
./manage/cleanup.sh

# 디스크 사용량 확인
df -h
```

### 데이터베이스 연결 오류
```bash
# MariaDB 상태 확인
systemctl status mariadb

# 연결 테스트
mysql -h localhost -u mcps_user -p
```

### Elasticsearch 메모리 부족
```bash
# ES 힙 메모리 확인 (config: -Xms2g -Xmx2g)
grep "Xm" /etc/elasticsearch/jvm.options

# ES 상태 확인
curl http://localhost:9200/_cluster/health?pretty
```

---

## 시스템 관리

### 정기 점검
```bash
# 시스템 정리 (cron 등록 권장)
./manage/cleanup.sh

# 일일 헬스체크
./health/healthcheck.sh

# 주간 백업
./backup/backup.sh
```

### 업데이트
```bash
./manage/update.sh
```

수행 내용:
1. 서비스 중지
2. 백업 생성
3. Python 패키지 업데이트
4. 서비스 시작

---

## 참고 사항

### 디렉토리 구조
```
/app/poc/mcps/
├── scripts/          # 관리 스크립트
│   ├── utils/       # 공통 유틸리티
│   ├── install/     # 설치 스크립트
│   ├── init/        # 초기화 스크립트
│   ├── control/     # 실행 제어
│   ├── manage/      # 관리 스크립트
│   ├── health/      # 헬스체크
│   └── backup/      # 백업/복구
├── logs/            # 로그 파일
├── backups/         # 백업 파일
└── config/          # 설정 파일
```

### 주요 설정
- 프로젝트 루트: `/app/poc/mcps`
- Python 버전: 3.11
- MariaDB 포트: 3306
- Redis 포트: 6379
- Elasticsearch 포트: 9200
- MCP Host 포트: 8001
- API Gateway 포트: 8000
- Frontend 포트: 3000

### 로그 보관 기간
- 로그: 30일
- 백업: 7일

---

## 지원

문제가 지속될 경우:
1. 로그 확인: `./manage/logs.sh <service> -e`
2. 헬스체크: `./health/healthcheck.sh`
3. 시스템 상태: `./manage/status.sh`

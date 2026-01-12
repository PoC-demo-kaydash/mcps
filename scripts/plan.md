# Scripts 구현 계획서

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/scripts/`  
**기준 문서**: [SR.md](SR.md)

---

## 1. 개요

### 1.1 목적

MCP 문서 관리 시스템의 설치, 실행, 관리를 위한 쉘 스크립트 구현

### 1.2 범위

| 구분 | 스크립트 수 | 설명 |
|------|-------------|------|
| 환경 설정 | 2 | config.sh, check_env.sh |
| 설치 | 6 | setup.sh, install_*.sh |
| 초기화 | 4 | init_*.sh |
| 실행 제어 | 5 | start/stop/restart |
| 관리 | 4 | status, logs, cleanup, update |
| 헬스체크 | 4 | healthcheck, check_*.sh |
| 백업/복구 | 2 | backup.sh, restore.sh |
| 유틸리티 | 3 | logger.sh, common.sh, colors.sh |
| **합계** | **30** | |

### 1.3 설계 원칙

#### 1.3.1 Python vs Shell 역할 분담 (권장방안)

```
┌─────────────────────────────────────────────────────────────┐
│                      역할 분담 구조                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Shell Scripts - 오케스트레이션]                           │
│    ├─ 환경 확인 (OS, 권한, 디스크, 포트)                    │
│    ├─ 서비스 관리 (systemctl start/stop)                   │
│    ├─ 의존성 체크 (서비스 순서 보장)                        │
│    └─ Python 스크립트 호출                                  │
│         │                                                   │
│         ▼                                                   │
│  [Python Scripts - 실제 로직]                               │
│    ├─ init_database.py (DB 스키마, 인덱스, 트리거)         │
│    ├─ init_elasticsearch.py (ES 인덱스, 매핑)              │
│    ├─ generate_sample_*.py (샘플 데이터)                   │
│    └─ sync_*_to_es.py (ES 동기화)                          │
│                                                             │
│  [장점]                                                     │
│    ✓ 기존 Python 스크립트 재사용 (shared/ 모듈 활용)        │
│    ✓ 복잡한 데이터 처리는 Python이 적합                     │
│    ✓ Shell은 시스템 레벨 작업에 집중                        │
│    ✓ 코드 중복 방지                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 1.3.2 기존 스크립트 통합 (권장방안)

| 기존 위치 | 통합 위치 | 처리 방법 |
|-----------|-----------|-----------|
| `data/database/backup/backup_database.sh` | `scripts/backup/backup.sh` | 로직 통합 후 심볼릭 링크 |
| `data/database/cron/daily_cleanup.sh` | `scripts/manage/cleanup.sh` | 로직 통합 후 심볼릭 링크 |

**이유**:
- 운영 스크립트는 `scripts/` 하위에서 일원화 관리
- 기존 cron 작업 호환성을 위해 심볼릭 링크 유지
- 중복 코드 제거 및 유지보수 편의성

---

## 2. 폴더 구조

```
scripts/
├── config.sh                    # 공통 설정 ★
├── README.md                    # 사용 가이드
│
├── env/                         # 환경 설정
│   └── check_env.sh            # 환경 확인 ★
│
├── install/                     # 설치
│   ├── setup.sh                # 마스터 설치 ★
│   ├── install_python.sh       # Python 설치
│   ├── install_database.sh     # MariaDB 설치
│   ├── install_redis.sh        # Redis 설치
│   ├── install_elasticsearch.sh # Elasticsearch 설치
│   └── install_services.sh     # MCP 서비스 설치
│
├── init/                        # 초기화
│   ├── init_all.sh             # 전체 초기화 ★
│   ├── init_database.sh        # DB 초기화 (→ Python 호출)
│   ├── init_elasticsearch.sh   # ES 초기화 (→ Python 호출)
│   └── init_data.sh            # 초기 데이터 (→ Python 호출)
│
├── control/                     # 실행 제어
│   ├── start_all.sh            # 전체 시작 ★
│   ├── stop_all.sh             # 전체 중지 ★
│   ├── restart_all.sh          # 전체 재시작
│   ├── start_service.sh        # 개별 서비스 시작
│   └── stop_service.sh         # 개별 서비스 중지
│
├── manage/                      # 관리
│   ├── status.sh               # 상태 확인 ★
│   ├── logs.sh                 # 로그 조회
│   ├── cleanup.sh              # 정리 (기존 cron 통합)
│   └── update.sh               # 업데이트
│
├── health/                      # 헬스체크
│   ├── healthcheck.sh          # 전체 헬스체크 ★
│   ├── check_database.sh       # DB 체크
│   ├── check_services.sh       # 서비스 체크
│   └── check_connectivity.sh   # 연결 체크
│
├── backup/                      # 백업/복구
│   ├── backup.sh               # 백업 (기존 backup_database.sh 통합)
│   └── restore.sh              # 복구
│
└── utils/                       # 유틸리티
    ├── logger.sh               # 로깅 함수 ★
    ├── colors.sh               # 색상 출력
    └── common.sh               # 공통 함수

★ = 핵심 스크립트 (우선 구현)
```

---

## 3. 진행 상태

| Phase | 구분 | 파일 수 | 상태 | 진행률 |
|-------|------|---------|------|--------|
| **Phase 1** | 유틸리티 & 설정 | 4 | ⏳ 대기 | 0% |
| **Phase 2** | 환경 & 설치 | 7 | ⏳ 대기 | 0% |
| **Phase 3** | 초기화 | 4 | ⏳ 대기 | 0% |
| **Phase 4** | 실행 제어 | 5 | ⏳ 대기 | 0% |
| **Phase 5** | 관리 | 4 | ⏳ 대기 | 0% |
| **Phase 6** | 헬스체크 | 4 | ⏳ 대기 | 0% |
| **Phase 7** | 백업/복구 & 문서 | 3 | ⏳ 대기 | 0% |
| **전체** | - | **31** | ⏳ 대기 | **0%** |

---

## 4. Phase 1: 유틸리티 & 설정 (4개)

### 4.1 체크리스트

- [ ] **utils/logger.sh** - 로깅 함수
  - [ ] `log_info()` - 정보 메시지 (파란색)
  - [ ] `log_success()` - 성공 메시지 (녹색)
  - [ ] `log_warning()` - 경고 메시지 (노란색)
  - [ ] `log_error()` - 에러 메시지 (빨간색)

- [ ] **utils/colors.sh** - 색상 정의
  - [ ] COLOR_RED, GREEN, YELLOW, BLUE, NC 정의

- [ ] **utils/common.sh** - 공통 함수
  - [ ] `is_service_running()` - 서비스 실행 확인
  - [ ] `is_port_in_use()` - 포트 사용 확인
  - [ ] `command_exists()` - 명령어 존재 확인
  - [ ] `wait_for_service()` - 서비스 대기 (타임아웃)
  - [ ] `wait_for_url()` - URL 응답 대기

- [ ] **config.sh** - 공통 설정
  - [ ] 프로젝트 경로 (PROJECT_ROOT, SCRIPTS_DIR, DATA_DIR, LOGS_DIR)
  - [ ] Python 설정 (PYTHON_VERSION, VENV_DIR)
  - [ ] DB 설정 (DB_HOST, PORT, NAME, USER, PASSWORD)
  - [ ] Redis 설정 (REDIS_HOST, PORT)
  - [ ] ES 설정 (ES_HOST, PORT, CLUSTER_NAME)
  - [ ] 서비스 포트 (MCP_HOST, API_GATEWAY, FRONTEND)
  - [ ] 로그/백업 설정 (LOG_LEVEL, RETENTION_DAYS)

### 4.2 의존성

```
없음 (기반 스크립트)
```

---

## 5. Phase 2: 환경 & 설치 (7개)

### 5.1 체크리스트

- [ ] **env/check_env.sh** - 환경 확인
  - [ ] `check_os()` - OS 확인 (RHEL 8.x)
  - [ ] `check_permissions()` - root 권한 확인
  - [ ] `check_disk_space()` - 디스크 공간 (최소 20GB)
  - [ ] `check_memory()` - 메모리 (권장 8GB)
  - [ ] `check_network()` - 네트워크, 포트 확인
  - [ ] `check_packages()` - 필수 패키지 확인

- [ ] **install/install_python.sh** - Python 설치
  - [ ] Python 3.11 설치 확인/설치
  - [ ] pip 업그레이드
  - [ ] 가상환경 생성 (${VENV_DIR})

- [ ] **install/install_database.sh** - MariaDB 설치
  - [ ] MariaDB 10.11 저장소 추가
  - [ ] 설치 및 서비스 활성화
  - [ ] 보안 설정 (root 비밀번호, 불필요 계정 삭제)
  - [ ] 성능 튜닝 (mcps.cnf)

- [ ] **install/install_redis.sh** - Redis 설치
  - [ ] EPEL 저장소 활성화
  - [ ] Redis 설치 및 서비스 활성화
  - [ ] 설정 (bind, maxmemory, appendonly)

- [ ] **install/install_elasticsearch.sh** - Elasticsearch 설치
  - [ ] ES 8.x 저장소 추가
  - [ ] 설치 및 서비스 활성화
  - [ ] 설정 (single-node, security disabled for dev)
  - [ ] JVM 힙 설정 (2GB)

- [ ] **install/install_services.sh** - MCP 서비스 설치
  - [ ] 디렉토리 생성 (logs, uploads, backups)
  - [ ] 가상환경 활성화
  - [ ] 각 서비스 requirements.txt 설치 (9개 위치)
  - [ ] Systemd 서비스 파일 생성 (mcp-host, mcp-api-gateway, mcp-frontend)

- [ ] **install/setup.sh** - 마스터 설치
  - [ ] 환경 확인 호출
  - [ ] Python 설치 호출
  - [ ] Database 설치 호출
  - [ ] Redis 설치 호출
  - [ ] Elasticsearch 설치 호출
  - [ ] 서비스 설치 호출
  - [ ] 초기화 호출

### 5.2 의존성

```
Phase 1 완료 필요 (config.sh, utils/*.sh)
```

---

## 6. Phase 3: 초기화 (4개)

### 6.1 체크리스트

- [ ] **init/init_database.sh** - DB 초기화
  - [ ] MariaDB 실행 확인
  - [ ] Database 및 사용자 생성
  - [ ] **Python 스크립트 호출**: `init_database.py`
    - [ ] schema.sql 실행
    - [ ] indexes.sql 실행
    - [ ] triggers.sql 실행
    - [ ] procedures.sql 실행
    - [ ] views.sql 실행

- [ ] **init/init_elasticsearch.sh** - ES 초기화
  - [ ] Elasticsearch 실행 대기 (30초 타임아웃)
  - [ ] **Python 스크립트 호출**: `init_elasticsearch.py`
    - [ ] documents 인덱스 생성
    - [ ] audit_logs 인덱스 생성

- [ ] **init/init_data.sh** - 초기 데이터
  - [ ] seed_data.sql 실행 (기본 사용자)
  - [ ] **Python 스크립트 호출** (선택):
    - [ ] `generate_sample_documents.py`
    - [ ] `generate_sample_audit_logs.py`
    - [ ] `sync_documents_to_es.py`
    - [ ] `sync_audit_logs_to_es.py`

- [ ] **init/init_all.sh** - 전체 초기화
  - [ ] init_database.sh 호출
  - [ ] init_elasticsearch.sh 호출
  - [ ] init_data.sh 호출

### 6.2 Python 호출 패턴

```bash
# init_database.sh 예시
log_info "Python 스크립트로 스키마 초기화..."
source "${VENV_DIR}/bin/activate"
python "${SCRIPTS_DIR}/init_database.py" || {
    log_error "init_database.py 실행 실패"
    exit 1
}
log_success "스키마 초기화 완료"
```

### 6.3 의존성

```
Phase 2 완료 필요 (인프라 설치)
기존 Python 스크립트 활용:
  - scripts/init_database.py
  - scripts/init_elasticsearch.py
  - scripts/generate_sample_*.py
  - scripts/sync_*_to_es.py
```

---

## 7. Phase 4: 실행 제어 (5개)

### 7.1 체크리스트

- [ ] **control/start_all.sh** - 전체 시작
  - [ ] 인프라 시작 순서: MariaDB → Redis → Elasticsearch
  - [ ] 서비스 시작 순서: mcp-host → mcp-api-gateway → mcp-frontend
  - [ ] 각 서비스 시작 후 대기 (sleep)
  - [ ] 헬스체크 호출

- [ ] **control/stop_all.sh** - 전체 중지
  - [ ] 서비스 중지 순서: mcp-frontend → mcp-api-gateway → mcp-host
  - [ ] 인프라 중지 (선택, 사용자 확인)

- [ ] **control/restart_all.sh** - 전체 재시작
  - [ ] stop_all.sh 호출
  - [ ] 5초 대기
  - [ ] start_all.sh 호출

- [ ] **control/start_service.sh** - 개별 서비스 시작
  - [ ] 서비스명 인수 처리
  - [ ] 사용 가능한 서비스 목록 표시
  - [ ] systemctl start 실행
  - [ ] 상태 확인

- [ ] **control/stop_service.sh** - 개별 서비스 중지
  - [ ] 서비스명 인수 처리
  - [ ] systemctl stop 실행

### 7.2 서비스 시작 순서

```
┌─────────────────────────────────────────┐
│            시작 순서                     │
├─────────────────────────────────────────┤
│  1. MariaDB      (3306)                 │
│       ↓                                 │
│  2. Redis        (6379)                 │
│       ↓                                 │
│  3. Elasticsearch (9200)                │
│       ↓ (30초 대기)                     │
│  4. MCP Host     (8000)                 │
│       ↓ (5초 대기)                      │
│  5. API Gateway  (8080)                 │
│       ↓ (3초 대기)                      │
│  6. Frontend     (3000)                 │
└─────────────────────────────────────────┘
```

### 7.3 의존성

```
Phase 1 완료 필요 (config.sh, utils/*.sh)
Phase 2의 install_services.sh 완료 필요 (systemd 서비스 등록)
```

---

## 8. Phase 5: 관리 (4개)

### 8.1 체크리스트

- [ ] **manage/status.sh** - 상태 확인
  - [ ] 서비스 상태 표시 (● 실행 중 / ● 중지됨)
  - [ ] 포트 상태 표시 (LISTEN / CLOSED)
  - [ ] 디스크 사용량 표시
  - [ ] 메모리 사용량 표시
  - [ ] 최근 에러 수 표시

- [ ] **manage/logs.sh** - 로그 조회
  - [ ] 서비스별 로그 파일 결정
  - [ ] `-f, --follow` 실시간 추적
  - [ ] `-n NUM` 최근 N줄
  - [ ] `-e, --error` 에러 로그만

- [ ] **manage/cleanup.sh** - 정리 (기존 daily_cleanup.sh 통합)
  - [ ] 오래된 로그 삭제 (LOG_RETENTION_DAYS)
  - [ ] 오래된 백업 삭제 (BACKUP_RETENTION_DAYS)
  - [ ] 임시 파일 삭제 (*.pyc, __pycache__, .pytest_cache)
  - [ ] 만료된 세션 정리 (DB)
  - [ ] 오래된 감사 로그 아카이빙

- [ ] **manage/update.sh** - 업데이트
  - [ ] 서비스 중지
  - [ ] 백업 생성
  - [ ] git pull (선택)
  - [ ] Python 패키지 업데이트
  - [ ] DB 마이그레이션 (선택)
  - [ ] 서비스 시작

### 8.2 기존 스크립트 통합

```bash
# cleanup.sh에서 기존 daily_cleanup.sh 로직 통합
# 기존 위치에 심볼릭 링크 생성:
# ln -sf ${SCRIPTS_DIR}/manage/cleanup.sh ${DATA_DIR}/database/cron/daily_cleanup.sh
```

### 8.3 의존성

```
Phase 1 완료 필요 (config.sh, utils/*.sh)
Phase 4 완료 필요 (start/stop 스크립트)
```

---

## 9. Phase 6: 헬스체크 (4개)

### 9.1 체크리스트

- [ ] **health/check_database.sh** - DB 체크
  - [ ] MariaDB 연결 테스트 (SELECT 1)
  - [ ] 종료 코드 반환 (0=OK, 1=FAIL)

- [ ] **health/check_services.sh** - 서비스 체크
  - [ ] mcp-host 실행 확인
  - [ ] mcp-api-gateway 실행 확인
  - [ ] mcp-frontend 실행 확인

- [ ] **health/check_connectivity.sh** - 연결 체크
  - [ ] MCP Host /health 엔드포인트 확인
  - [ ] API Gateway /health 엔드포인트 확인
  - [ ] Frontend 응답 확인 (선택)

- [ ] **health/healthcheck.sh** - 전체 헬스체크
  - [ ] check_database.sh 호출
  - [ ] Redis ping 테스트
  - [ ] Elasticsearch 연결 테스트
  - [ ] check_services.sh 호출
  - [ ] check_connectivity.sh 호출
  - [ ] 전체 결과 요약 출력

### 9.2 의존성

```
Phase 1 완료 필요 (config.sh, utils/*.sh)
```

---

## 10. Phase 7: 백업/복구 & 문서 (3개)

### 10.1 체크리스트

- [ ] **backup/backup.sh** - 백업 (기존 backup_database.sh 통합)
  - [ ] Database 백업 (mysqldump)
    - [ ] --single-transaction
    - [ ] --routines, --triggers
  - [ ] Elasticsearch 스냅샷 (선택)
  - [ ] 설정 파일 백업 (.env, systemd 서비스)
  - [ ] 압축 (BACKUP_COMPRESS=true 시)
  - [ ] 오래된 백업 삭제

- [ ] **backup/restore.sh** - 복구
  - [ ] 백업 파일/디렉토리 확인
  - [ ] 압축 해제 (.tar.gz)
  - [ ] 사용자 확인 (경고 메시지)
  - [ ] 서비스 중지
  - [ ] Database 복구
  - [ ] 설정 파일 복구
  - [ ] 서비스 시작

- [ ] **README.md** - 사용 가이드
  - [ ] 설치 방법
  - [ ] 실행/중지/재시작
  - [ ] 상태 확인
  - [ ] 로그 확인
  - [ ] 백업/복구
  - [ ] 문제 해결

### 10.2 기존 스크립트 통합

```bash
# backup.sh에서 기존 backup_database.sh 로직 통합
# 기존 위치에 심볼릭 링크 생성:
# ln -sf ${SCRIPTS_DIR}/backup/backup.sh ${DATA_DIR}/database/backup/backup_database.sh
```

### 10.3 의존성

```
Phase 1 완료 필요 (config.sh, utils/*.sh)
Phase 4 완료 필요 (start/stop 스크립트)
```

---

## 11. 파일 목록 (전체 31개)

### 11.1 Phase별 파일 목록

| # | Phase | 경로 | 설명 | 상태 |
|---|-------|------|------|------|
| 1 | 1 | `utils/logger.sh` | 로깅 함수 | ⬜ |
| 2 | 1 | `utils/colors.sh` | 색상 정의 | ⬜ |
| 3 | 1 | `utils/common.sh` | 공통 함수 | ⬜ |
| 4 | 1 | `config.sh` | 공통 설정 | ⬜ |
| 5 | 2 | `env/check_env.sh` | 환경 확인 | ⬜ |
| 6 | 2 | `install/install_python.sh` | Python 설치 | ⬜ |
| 7 | 2 | `install/install_database.sh` | MariaDB 설치 | ⬜ |
| 8 | 2 | `install/install_redis.sh` | Redis 설치 | ⬜ |
| 9 | 2 | `install/install_elasticsearch.sh` | ES 설치 | ⬜ |
| 10 | 2 | `install/install_services.sh` | 서비스 설치 | ⬜ |
| 11 | 2 | `install/setup.sh` | 마스터 설치 | ⬜ |
| 12 | 3 | `init/init_database.sh` | DB 초기화 | ⬜ |
| 13 | 3 | `init/init_elasticsearch.sh` | ES 초기화 | ⬜ |
| 14 | 3 | `init/init_data.sh` | 초기 데이터 | ⬜ |
| 15 | 3 | `init/init_all.sh` | 전체 초기화 | ⬜ |
| 16 | 4 | `control/start_all.sh` | 전체 시작 | ⬜ |
| 17 | 4 | `control/stop_all.sh` | 전체 중지 | ⬜ |
| 18 | 4 | `control/restart_all.sh` | 전체 재시작 | ⬜ |
| 19 | 4 | `control/start_service.sh` | 개별 시작 | ⬜ |
| 20 | 4 | `control/stop_service.sh` | 개별 중지 | ⬜ |
| 21 | 5 | `manage/status.sh` | 상태 확인 | ⬜ |
| 22 | 5 | `manage/logs.sh` | 로그 조회 | ⬜ |
| 23 | 5 | `manage/cleanup.sh` | 정리 | ⬜ |
| 24 | 5 | `manage/update.sh` | 업데이트 | ⬜ |
| 25 | 6 | `health/check_database.sh` | DB 체크 | ⬜ |
| 26 | 6 | `health/check_services.sh` | 서비스 체크 | ⬜ |
| 27 | 6 | `health/check_connectivity.sh` | 연결 체크 | ⬜ |
| 28 | 6 | `health/healthcheck.sh` | 전체 헬스체크 | ⬜ |
| 29 | 7 | `backup/backup.sh` | 백업 | ⬜ |
| 30 | 7 | `backup/restore.sh` | 복구 | ⬜ |
| 31 | 7 | `README.md` | 사용 가이드 | ⬜ |

### 11.2 기존 Python 스크립트 (재사용)

| 파일 | 호출 위치 | 설명 |
|------|-----------|------|
| `init_database.py` | init/init_database.sh | DB 스키마 초기화 |
| `init_elasticsearch.py` | init/init_elasticsearch.sh | ES 인덱스 생성 |
| `generate_sample_documents.py` | init/init_data.sh | 샘플 문서 생성 |
| `generate_sample_audit_logs.py` | init/init_data.sh | 샘플 감사 로그 생성 |
| `sync_documents_to_es.py` | init/init_data.sh | 문서 ES 동기화 |
| `sync_audit_logs_to_es.py` | init/init_data.sh | 감사 로그 ES 동기화 |

---

## 12. 마일스톤

| 마일스톤 | 목표 | 완료 조건 | 상태 |
|----------|------|-----------|------|
| **M1** | Phase 1-2 완료 | 환경 확인 및 설치 가능 | ⬜ |
| **M2** | Phase 3-4 완료 | 초기화 및 서비스 실행 가능 | ⬜ |
| **M3** | Phase 5-6 완료 | 관리 및 헬스체크 가능 | ⬜ |
| **M4** | Phase 7 완료 | 백업/복구 및 문서화 완료 | ⬜ |

---

## 13. 구현 순서 요약

```
┌─────────────────────────────────────────────────────────────┐
│                      구현 순서                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 1: 유틸리티 & 설정 (4개)                             │
│    └─ utils/logger.sh, colors.sh, common.sh, config.sh     │
│         ↓                                                   │
│  Phase 2: 환경 & 설치 (7개)                                 │
│    └─ env/check_env.sh                                     │
│    └─ install/*.sh (6개)                                   │
│         ↓                                                   │
│  Phase 3: 초기화 (4개)                                      │
│    └─ init/*.sh (Python 스크립트 호출)                     │
│         ↓                                                   │
│  Phase 4: 실행 제어 (5개)                                   │
│    └─ control/start_all.sh, stop_all.sh 등                 │
│         ↓                                                   │
│  Phase 5: 관리 (4개)                                        │
│    └─ manage/status.sh, logs.sh, cleanup.sh, update.sh     │
│         ↓                                                   │
│  Phase 6: 헬스체크 (4개)                                    │
│    └─ health/*.sh                                          │
│         ↓                                                   │
│  Phase 7: 백업/복구 & 문서 (3개)                            │
│    └─ backup/*.sh, README.md                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 14. 문서 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2026-01-08 | 초안 작성 |

---

## 15. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| 작성자 | AI Assistant | | 2026-01-08 |
| 검토자 | | | |
| 승인자 | | | |

# config 및 data 구현 계획서

**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/config/`, `/app/poc/mcps/data/`  
**상태**: ✅ 완료 (2026-01-08)

---

## 1. 환경 정보 (확정)

| 항목 | 값 |
|------|-----|
| **Python 버전** | 3.10.19 |
| **Conda 환경명** | `mcp_env` |
| **Python 경로** | `/app/miniconda3/envs/mcp_env/bin/python` |
| **OS** | Rocky Linux 8.10 |

### 1.1 MariaDB 접속 정보

| 항목 | 값 |
|------|-----|
| **Host** | L4 |
| **Port** | 2503 |
| **User** | aia |
| **Password** | aia123! |
| **Database** | mcps_db |
| **Charset** | utf8mb4 |
| **CLI** | `/usr/local/bin/mysql -uaia -paia123! -P2503 -hL4 --ssl=0 -Dmcps_db` |

### 1.2 Elasticsearch 접속 정보

| 항목 | 값 |
|------|-----|
| **Host** | http://shbank.kro.kr:39200 |
| **User** | ciq_admin |
| **Password** | shinhan@2 |

---

## 2. 구현 파일 목록 (16개)

### 2.1 config 설정 파일 (4개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 1 | `config/registry.json` | Tool 레지스트리 (10개 Tool 정의) | ✅ |
| 2 | `config/permissions.json` | RBAC 권한 설정 (5개 역할, 3개 등급) | ✅ |
| 3 | `config/users.json` | PoC 사용자 목록 (7명 + 3개 팀) | ✅ |
| 4 | `config/services.json` | MCP Server 실행 설정 (5개 서버) | ✅ |

### 2.2 data/database SQL 파일 (4개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 5 | `data/database/schema.sql` | 테이블 DDL (9개 테이블) | ✅ |
| 6 | `data/database/indexes.sql` | 추가 인덱스 (성능 최적화) | ✅ |
| 7 | `data/database/triggers.sql` | 트리거 (버전 자동 생성, 감사 로그) | ✅ |
| 8 | `data/database/seed_data.sql` | 초기 데이터 (사용자, 문서, Tool, Server) | ✅ |

### 2.3 data/elasticsearch 매핑 파일 (2개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 9 | `data/elasticsearch/mappings/documents.json` | 문서 인덱스 매핑 (Nori 분석기) | ✅ |
| 10 | `data/elasticsearch/mappings/audit_logs.json` | 감사 로그 인덱스 매핑 | ✅ |

### 2.4 scripts 스크립트 (6개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 11 | `scripts/init_database.py` | DB 스키마 초기화 | ✅ |
| 12 | `scripts/init_elasticsearch.py` | ES 인덱스 생성 | ✅ |
| 13 | `scripts/sync_documents_to_es.py` | 문서 동기화 (MariaDB → ES) | ✅ |
| 14 | `scripts/sync_audit_logs_to_es.py` | 감사 로그 동기화 (MariaDB → ES) | ✅ |
| 15 | `scripts/generate_sample_documents.py` | 샘플 문서 생성 (40개) | ✅ |
| 16 | `scripts/generate_sample_audit_logs.py` | 샘플 감사 로그 생성 | ✅ |

---

## 3. 구현 순서

```
Phase 1: config 설정 파일 (4개)
   ├── registry.json (Tool 레지스트리)
   ├── permissions.json (권한 설정)
   ├── users.json (사용자 목록)
   └── services.json (MCP Server 설정)
   ↓
Phase 2: data/database SQL (4개)
   ├── schema.sql (테이블 DDL)
   ├── indexes.sql (추가 인덱스)
   ├── triggers.sql (트리거)
   └── seed_data.sql (초기 데이터)
   ↓
Phase 3: data/elasticsearch 매핑 (2개)
   ├── documents.json (문서 인덱스)
   └── audit_logs.json (감사 로그 인덱스)
   ↓
Phase 4: scripts 스크립트 (6개)
   ├── init_database.py (DB 초기화)
   ├── init_elasticsearch.py (ES 초기화)
   ├── sync_documents_to_es.py (문서 동기화)
   ├── sync_audit_logs_to_es.py (감사 로그 동기화)
   ├── generate_sample_documents.py (샘플 문서)
   └── generate_sample_audit_logs.py (샘플 감사 로그)
   ↓
Phase 5: 검증 및 테스트
   └── 전체 파일 검증 및 기능 테스트
```

---

## 4. 상세 구현 내용

### 4.1 config/registry.json (Tool 레지스트리)

**10개 Tool 정의:**
| # | Tool 이름 | 설명 | Server |
|---|-----------|------|--------|
| 1 | search_documents | 문서 전문 검색 | search_server |
| 2 | get_document | 문서 상세 조회 | document_server |
| 3 | create_document | 문서 생성 | document_server |
| 4 | update_document | 문서 수정 | document_server |
| 5 | delete_document | 문서 삭제 | document_server |
| 6 | list_documents | 문서 목록 조회 | document_server |
| 7 | get_document_versions | 문서 버전 히스토리 | version_server |
| 8 | authenticate | 사용자 인증 | auth_server |
| 9 | request_access | 접근 권한 요청 | auth_server |
| 10 | get_audit_logs | 감사 로그 조회 | audit_server |

### 4.2 config/permissions.json (권한 설정)

**5개 역할:**
| 역할 | Level | 설명 | 문서 권한 |
|------|-------|------|----------|
| junior | 1 | 신입 사원 | public(R) |
| staff | 2 | 일반 사원 | public(RCU), team(RCU) |
| manager | 3 | 팀 관리자 | public(RCUD), team(RCUD) |
| executive | 4 | 임원 | public(R), team(R), confidential(R) |
| admin | 5 | 시스템 관리자 | all(RCUD) |

**3개 문서 등급:**
| 등급 | 설명 | 최소 역할 Level |
|------|------|----------------|
| public | 공개 문서 | 1 |
| team | 팀 문서 | 2 (팀 제한) |
| confidential | 기밀 문서 | 4 |

### 4.3 config/users.json (사용자 목록)

**7명 사용자:**
| ID | 이름 | 역할 | 팀 |
|----|------|------|-----|
| U000 | 관리자 | admin | - |
| U001 | 김신입 | junior | dev_team |
| U002 | 이사원 | staff | dev_team |
| U003 | 박매니저 | manager | dev_team |
| U004 | 최임원 | executive | - |
| U005 | 정사원 | staff | hr_team |
| U006 | 강대리 | staff | finance_team |

**3개 팀:**
| ID | 이름 | 관리자 |
|----|------|--------|
| dev_team | 개발팀 | U003 |
| hr_team | 인사팀 | - |
| finance_team | 재무팀 | - |

### 4.4 config/services.json (MCP Server 설정)

**5개 MCP Server:**
| Server | 설명 | 자동 시작 |
|--------|------|----------|
| auth_server | 인증 및 권한 관리 | ✓ |
| search_server | 문서 검색 | ✓ |
| document_server | 문서 CRUD | ✓ |
| version_server | 문서 버전 관리 | ✓ |
| audit_server | 감사 로그 | ✓ |

### 4.5 data/database (9개 테이블)

| # | 테이블 | 설명 | 주요 컬럼 |
|---|--------|------|----------|
| 1 | users | 사용자 | id, name, email, role, team |
| 2 | documents | 문서 | id, title, content, classification, author_id |
| 3 | document_versions | 문서 버전 | document_id, version, title, content |
| 4 | permissions | 권한 | user_id, role, resource_type, actions |
| 5 | tools | Tool 레지스트리 | name, server_name, metadata |
| 6 | servers | MCP Server | name, status, pid |
| 7 | audit_logs | 감사 로그 | user_id, action, resource_type, result |
| 8 | access_requests | 접근 요청 | user_id, resource_id, status |
| 9 | system_settings | 시스템 설정 | key_name, value_text, value_json |

### 4.6 data/elasticsearch (2개 인덱스)

| 인덱스 | 설명 | 주요 필드 |
|--------|------|----------|
| documents | 문서 검색 | doc_id, title, content, classification |
| audit_logs | 감사 로그 | user_id, action, result, timestamp |

---

## 5. 디렉토리 구조 (최종)

```
/app/poc/mcps/
├── config/
│   ├── SR.md                    # 설계서 (기존)
│   ├── plan.md                  # 구현 계획서 (신규)
│   ├── registry.json            # Tool 레지스트리
│   ├── permissions.json         # 권한 설정
│   ├── users.json               # 사용자 목록
│   └── services.json            # MCP Server 설정
│
├── data/
│   ├── database/
│   │   ├── schema.sql           # 테이블 DDL
│   │   ├── indexes.sql          # 추가 인덱스
│   │   ├── triggers.sql         # 트리거
│   │   └── seed_data.sql        # 초기 데이터
│   │
│   └── elasticsearch/
│       └── mappings/
│           ├── documents.json   # 문서 인덱스 매핑
│           └── audit_logs.json  # 감사 로그 매핑
│
└── scripts/
    ├── init_database.py         # DB 초기화
    ├── init_elasticsearch.py    # ES 초기화
    ├── sync_documents_to_es.py  # 문서 동기화
    ├── sync_audit_logs_to_es.py # 감사 로그 동기화
    ├── generate_sample_documents.py    # 샘플 문서
    └── generate_sample_audit_logs.py   # 샘플 감사 로그
```

---

## 6. 진행 상황

- [x] 설계서 분석 (SR.md)
- [x] 구현 계획서 작성 (plan.md)
- [x] Phase 1: config 설정 파일 (4개) ✅
- [x] Phase 2: data/database SQL (4개) ✅
- [x] Phase 3: data/elasticsearch 매핑 (2개) ✅
- [x] Phase 4: scripts 스크립트 (6개) ✅
- [x] Phase 5: 검증 완료 ✅

**🎉 전체 16개 파일 구현 완료!**

---

## 7. 참고 사항

### 7.1 shared 모듈 연동

이 구현에서는 `shared/` 모듈의 다음 기능을 활용합니다:
- `shared.database.DatabaseManager` - DB 연결 관리
- `shared.elasticsearch.ElasticsearchManager` - ES 연결 관리
- `shared.utils.generate_id()` - ID 생성
- `shared.logging_config.setup_logging()` - 로깅

### 7.2 기존 shared 파일과의 중복

- `shared/schema.sql` → `data/database/schema.sql`로 이동/확장
- `shared/es_mappings/` → `data/elasticsearch/mappings/`로 이동/확장

기존 shared에 있는 파일은 참조용으로 유지하고, data/ 경로에 확장된 버전을 생성합니다.

---

**참조 문서**: [SR.md](SR.md) (config 및 데이터 스키마 설계서)

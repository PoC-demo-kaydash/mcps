# shared 공유모듈 구현 계획서

**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/shared/`  
**상태**: 🚧 진행 중

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
| **SSL** | 0 (미사용) |
| **CLI** | `/usr/local/bin/mysql -uaia -paia123! -P2503 -hL4 --ssl=0 -Dmcps_db` |

### 1.2 Elasticsearch 접속 정보

| 항목 | 값 |
|------|-----|
| **Host** | http://shbank.kro.kr:39200 |
| **User** | ciq_admin |
| **Password** | shinhan@2 |
| **SSL Enable** | N |
| **SSL Verify Skip** | Y |

---

## 2. 구현 파일 목록 (14개)

### 2.1 환경 설정 파일

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 1 | `.env.example` | 환경 설정 예제 | ✅ |
| 2 | `shared/requirements.txt` | 의존성 패키지 | ✅ |

### 2.2 shared 모듈 (9개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 3 | `shared/__init__.py` | CONFIG 로드, 초기화 | ✅ |
| 4 | `shared/logging_config.py` | 로거 설정 | ✅ |
| 5 | `shared/utils.py` | 유틸리티 함수 | ✅ |
| 6 | `shared/cache.py` | 캐시 시스템 | ✅ |
| 7 | `shared/database.py` | DB 연결 관리 | ✅ |
| 8 | `shared/queries.py` | SQL 쿼리 모음 | ✅ |
| 9 | `shared/elasticsearch.py` | ES 클라이언트 | ✅ |
| 10 | `shared/permissions.py` | RBAC 권한 시스템 | ✅ |
| 11 | `shared/mcp_protocol.py` | MCP 프로토콜 | ✅ |

### 2.3 데이터 스키마 파일

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 12 | `shared/schema.sql` | 테이블 생성 스크립트 | ✅ |
| 13 | `shared/es_mappings/documents.json` | 문서 인덱스 매핑 | ✅ |
| 14 | `shared/es_mappings/audit_logs.json` | 감사로그 인덱스 매핑 | ✅ |

---

## 3. 구현 순서

```
1. .env.example, requirements.txt (환경 설정)
   ↓
2. __init__.py, logging_config.py (기반 모듈)
   ↓
3. utils.py, cache.py (유틸리티)
   ↓
4. database.py, queries.py (데이터베이스)
   ↓
5. elasticsearch.py (검색 엔진)
   ↓
6. permissions.py (권한 시스템)
   ↓
7. mcp_protocol.py (MCP 프로토콜)
   ↓
8. schema.sql, ES mappings (스키마)
   ↓
9. 테스트 및 검증
```

---

## 4. 의존성 패키지

```txt
# Database
pymysql==1.1.0
DBUtils==3.0.3

# Search
elasticsearch==8.11.1

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0

# Configuration
python-dotenv==1.0.0

# Parsing
PyYAML==6.0.1
python-frontmatter==1.1.0

# Utilities
python-dateutil==2.8.2
```

---

## 5. 테이블 구조 (7개)

1. **users** - 사용자
2. **documents** - 문서
3. **permissions** - 권한
4. **tools** - Tool 레지스트리
5. **servers** - MCP Server
6. **audit_logs** - 감사 로그
7. **document_versions** - 문서 버전
8. **access_requests** - 접근 요청

---

## 6. 진행 상황

- [x] 환경 정보 확정
- [x] 데이터베이스 생성 (mcps_db)
- [x] 계획서 작성
- [x] 구현 완료 (14개 파일 모두 완료)
- [x] 테스트 및 검증 완료

**구현 완료 일자**: 2026-01-08

---

**참조 문서**: [SR.md](SR.md) (shared 공유모듈 설계서)

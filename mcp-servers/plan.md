# mcp-servers 구현 계획서

**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/mcp-servers/`  
**상태**: 🔄 Phase 5 완료, Phase 6-7 진행 예정

---

## 1. 환경 정보

| 항목 | 값 |
|------|-----|
| **Python 버전** | 3.10.19 |
| **Conda 환경명** | `mcp_env` |
| **Python 경로** | `/app/miniconda3/envs/mcp_env/bin/python` |
| **OS** | Rocky Linux 8.10 |

### 1.1 의존 모듈

| 모듈 | 주요 클래스/함수 |
|------|------------------|
| `shared.database` | `DatabaseManager` |
| `shared.elasticsearch` | `ElasticsearchManager` |
| `shared.mcp_protocol` | `MCPProtocol` |
| `shared.logging_config` | `setup_logging()`, `get_logger()` |
| `mcp_tools.core.*` | Tool 클래스들 (AuthenticateTool, GetDocumentTool 등) |

---

## 2. SR.md 대비 구조 변경 사항

### 2.1 설계 vs 구현 비교

| 항목 | SR.md (원본 설계) | 실제 구현 | 변경 사유 |
|------|------------------|----------|----------|
| **서버 구조** | 3개 서버 (`core/`, `search/`, `analytics/`) | 5개 서버 (`core/` 하위) | 기능별 명확한 분리, 독립적 재시작 가능 |
| **Tool 위치** | 각 서버 내 `tools/` 폴더 | `mcp-tools/core/` 중앙화 | Tool 재사용성 극대화, 중복 방지 |
| **공통 모듈** | `common/` 신규 생성 | `shared/` 기존 모듈 활용 | 이미 구현된 DatabaseManager, ElasticsearchManager 재사용 |
| **Resources** | `document://`, `template://` 구현 | 미구현 | PoC 범위 외, 추후 확장 |
| **Prompts** | `summarize`, `format` 구현 | 미구현 | PoC 범위 외, 추후 확장 |

### 2.2 5-서버 분리 상세 사유

```
SR.md 설계 (3-서버)              실제 구현 (5-서버)
=====================           ====================
core/                           core/
├── server.py                   ├── auth_server/      ← 인증/권한 분리
│   └── 인증 + 문서 CRUD        ├── document_server/  ← 문서 CRUD 전담
│                               ├── search_server/    ← 검색 전담
search/                         ├── version_server/   ← 버전 관리 (신규)
└── server.py                   └── audit_server/     ← 감사 로그 (신규)

analytics/
└── server.py ─────────────────→ audit_server로 통합 (통계 기능)
```

**분리 이유:**
1. **auth_server**: 보안 관련 기능 격리, 인증 실패 시 다른 서버 영향 없음
2. **document_server**: 핵심 CRUD 기능 집중, 가장 빈번한 호출 대상
3. **search_server**: Elasticsearch 의존성 분리, ES 장애 시 다른 기능 유지
4. **version_server**: 버전 관리 로직 독립, 문서 서버 부하 분산
5. **audit_server**: 감사/통계 기능 통합, Analytics 서버 역할 흡수

### 2.3 Tool 중앙화 (`mcp-tools/`) 선택 근거

```
SR.md 설계                      실제 구현
===========                     ==========
mcp-servers/                    mcp-tools/
├── core/tools/                 └── core/
│   └── document_tools.py           ├── auth_tools.py
├── search/tools/                   ├── document_tools.py
│   └── search_tools.py             ├── search_tools.py
└── analytics/tools/                ├── version_tools.py
    └── stats_tools.py              └── audit_tools.py
```

**중앙화 이유:**
1. **재사용성**: 여러 서버에서 동일 Tool 참조 가능
2. **일관성**: Tool 스키마, 검증 로직 통일
3. **유지보수**: Tool 수정 시 한 곳만 변경
4. **테스트**: Tool 단위 테스트 용이

---

## 3. 구현 파일 목록

### 3.1 Core Servers (5개 Server, 각 2개 파일) - ✅ 완료

| # | Server | 파일 | Tool 수 | 상태 |
|---|--------|------|---------|------|
| 1 | auth_server | main.py | 4 | ✅ |
| 2 | auth_server | requirements.txt | - | ✅ |
| 3 | document_server | main.py | 5 | ✅ |
| 4 | document_server | requirements.txt | - | ✅ |
| 5 | search_server | main.py | 2 | ✅ |
| 6 | search_server | requirements.txt | - | ✅ |
| 7 | version_server | main.py | 3 | ✅ |
| 8 | version_server | requirements.txt | - | ✅ |
| 9 | audit_server | main.py | 3 | ✅ |
| 10 | audit_server | requirements.txt | - | ✅ |

### 3.2 운영 스크립트 (SR.md 제안) - ⏳ 대기

| # | 파일 | 기능 | 상태 |
|---|------|------|------|
| 11 | scripts/start_servers.sh | 전체 MCP 서버 시작 | ⏳ |
| 12 | scripts/stop_servers.sh | 전체 MCP 서버 중지 | ⏳ |
| 13 | scripts/status.sh | 서버 상태 확인 | ⏳ |

---

## 4. Server별 상세 정보

### 4.1 auth_server (인증/권한)

**Tool 목록 (4개):**
| Tool | 기능 |
|------|------|
| `authenticate` | 사용자 인증 |
| `request_access` | 접근 권한 요청 |
| `approve_access` | 권한 승인 |
| `get_my_permissions` | 내 권한 조회 |

**의존 모듈:** `mcp_tools.core.auth_tools`  
**리소스:** DatabaseManager

---

### 4.2 document_server (문서 CRUD)

**Tool 목록 (5개):**
| Tool | 기능 |
|------|------|
| `get_document` | 문서 조회 |
| `create_document` | 문서 생성 |
| `update_document` | 문서 수정 |
| `delete_document` | 문서 삭제 |
| `list_documents` | 문서 목록 |

**의존 모듈:** `mcp_tools.core.document_tools`  
**리소스:** DatabaseManager, ElasticsearchManager (동기화용)

---

### 4.3 search_server (검색)

**Tool 목록 (2개):**
| Tool | 기능 |
|------|------|
| `search_documents` | 문서 전문 검색 |
| `suggest_documents` | 자동완성 |

**의존 모듈:** `mcp_tools.core.search_tools`  
**리소스:** DatabaseManager, ElasticsearchManager

---

### 4.4 version_server (버전 관리)

**Tool 목록 (3개):**
| Tool | 기능 |
|------|------|
| `get_document_versions` | 문서 버전 목록 |
| `get_document_version` | 특정 버전 조회 |
| `compare_versions` | 버전 비교 |

**의존 모듈:** `mcp_tools.core.version_tools`  
**리소스:** DatabaseManager

---

### 4.5 audit_server (감사 로그)

**Tool 목록 (3개):**
| Tool | 기능 |
|------|------|
| `get_audit_logs` | 감사 로그 조회 |
| `get_my_activity` | 내 활동 조회 |
| `get_statistics` | 통계 조회 |

**의존 모듈:** `mcp_tools.core.audit_tools`  
**리소스:** DatabaseManager, ElasticsearchManager

---

## 5. 디렉토리 구조 (현재)

```
/app/poc/mcps/mcp-servers/
├── SR.md                           # 원본 설계서 (참조용)
├── plan.md                         # 구현 계획서 (본 문서)
├── fix_plan.md                     # 구조 수정 계획서
│
├── auth_server/                    # Auth Server (4 Tools)
│   ├── main.py
│   └── requirements.txt
│
├── document_server/                # Document Server (5 Tools)
│   ├── main.py
│   └── requirements.txt
│
├── search_server/                  # Search Server (2 Tools)
│   ├── main.py
│   └── requirements.txt
│
├── version_server/                 # Version Server (3 Tools)
│   ├── main.py
│   └── requirements.txt
│
├── audit_server/                   # Audit Server (3 Tools)
│   ├── main.py
│   └── requirements.txt
│
└── scripts/                        # 운영 스크립트
    ├── start_servers.sh
    ├── stop_servers.sh
    ├── status.sh
    └── integration_test.py
```

---

## 6. 구현 순서

```
Phase 1-5: 서버 구현 ✅ 완료
   ├── Phase 1: auth_server (2개 파일) ✅
   ├── Phase 2: document_server (2개 파일) ✅
   ├── Phase 3: search_server (2개 파일) ✅
   ├── Phase 4: version_server (2개 파일) ✅
   └── Phase 5: audit_server (2개 파일) ✅
   ↓
Phase 6: 운영 스크립트 ⏳ 진행 예정
   ├── scripts/start_servers.sh
   ├── scripts/stop_servers.sh
   └── scripts/status.sh
   ↓
Phase 7: 통합 테스트 ⏳ 진행 예정
   ├── mcp-host 연동 테스트
   ├── 서버 간 통신 검증
   └── 에러 처리 검증
```

---

## 7. Phase 6: 운영 스크립트 (SR.md 제안 반영)

### 7.1 start_servers.sh

**기능:**
- 모든 MCP 서버 순차 시작
- 의존성 순서: auth → document → search → version → audit
- PID 파일 생성 (`/tmp/mcp_*.pid`)
- 시작 확인 (포트 체크)

**실행:**
```bash
./scripts/start_servers.sh
```

### 7.2 stop_servers.sh

**기능:**
- 모든 MCP 서버 중지
- PID 파일 기반 프로세스 종료
- Graceful shutdown (SIGTERM → SIGKILL)

**실행:**
```bash
./scripts/stop_servers.sh
```

### 7.3 status.sh

**기능:**
- 각 서버 실행 상태 표시
- PID, 포트, 메모리 사용량
- 최근 로그 에러 확인

**실행:**
```bash
./scripts/status.sh
```

---

## 8. Phase 7: 통합 테스트

### 8.1 테스트 시나리오

| # | 시나리오 | 검증 항목 |
|---|----------|----------|
| 1 | 인증 플로우 | authenticate → get_my_permissions |
| 2 | 문서 CRUD | create → get → update → delete |
| 3 | 검색 연동 | create_document → search_documents |
| 4 | 버전 관리 | update_document → get_document_versions |
| 5 | 감사 로그 | 각 작업 후 get_audit_logs 확인 |

### 8.2 mcp-host 연동 검증

- [ ] ServerManager가 5개 서버 모두 시작
- [ ] Router가 Tool별 서버 라우팅 정상
- [ ] 세션 컨텍스트 전달 확인
- [ ] 서버 장애 시 자동 재시작

### 8.3 에러 처리 검증

- [ ] 권한 없는 사용자 접근 차단
- [ ] 존재하지 않는 문서 조회 에러
- [ ] Elasticsearch 연결 실패 시 Fallback
- [ ] 잘못된 Tool 파라미터 검증

---

## 9. 추후 확장 가능 항목

SR.md에서 제안되었으나 현재 PoC 범위 외로 미구현된 항목:

### 9.1 MCP Resources

| Resource URI | 설명 | 우선순위 |
|--------------|------|----------|
| `document://{id}` | 문서 컨텐츠 직접 접근 | 중 |
| `template://{name}` | 문서 템플릿 | 하 |
| `search://{query}` | 검색 결과 캐시 | 하 |

### 9.2 MCP Prompts

| Prompt | 설명 | 우선순위 |
|--------|------|----------|
| `summarize` | 문서 요약 프롬프트 | 중 (LLM 연동 시) |
| `format` | 문서 포맷 변환 | 하 |
| `translate` | 다국어 번역 | 하 |

### 9.3 Analytics 고급 기능

| 기능 | 설명 | 우선순위 |
|------|------|----------|
| `analyze_trends` | 트렌드 분석 | 중 |
| `generate_report` | 리포트 생성 | 중 |
| `user_activity` | 사용자 활동 분석 | 하 |

---

## 10. 진행 상황 요약

| Phase | 내용 | 파일 수 | 상태 |
|-------|------|---------|------|
| Phase 1 | auth_server | 2 | ✅ 완료 |
| Phase 2 | document_server | 2 | ✅ 완료 |
| Phase 3 | search_server | 2 | ✅ 완료 |
| Phase 4 | version_server | 2 | ✅ 완료 |
| Phase 5 | audit_server | 2 | ✅ 완료 |
| Phase 6 | 운영 스크립트 | 3 | ⏳ 대기 |
| Phase 7 | 통합 테스트 | - | ⏳ 대기 |

**총 진행률**: Phase 5/7 완료 (서버 구현 100%, 전체 71%)

---

## 11. 참조 문서

- [SR.md](SR.md) - 원본 설계서 (3-서버 아키텍처)
- [mcp-tools/plan.md](../mcp-tools/plan.md) - Tool 구현 계획
- [mcp-host/plan.md](../mcp-host/plan.md) - Host 구현 계획
- [shared/plan.md](../shared/plan.md) - 공유 모듈 계획

---

**Note**: 본 문서는 SR.md의 원본 설계를 기반으로 하되, PoC 목적에 맞게 구조를 최적화한 구현 계획입니다. SR.md는 참조용 원본 설계로 유지됩니다.

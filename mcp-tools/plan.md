# mcp-tools 구현 계획서

**작성일**: 2026-01-08  
**완료일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/mcp-tools/`  
**상태**: ✅ 완료

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
| `shared.permissions` | `PermissionEngine`, `User`, `Document` |
| `shared.queries` | `UserQueries`, `DocumentQueries`, `AuditLogQueries` 등 |
| `shared.utils` | `generate_id()`, `now_iso()`, `validate_*()` |
| `shared.logging_config` | `setup_logging()`, `get_logger()` |

---

## 2. 구현 파일 목록 (19개)

### 2.1 기본 모듈 (4개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 1 | `__init__.py` | 패키지 초기화, Tool 자동 등록 | ✅ |
| 2 | `base.py` | BaseTool, AsyncBaseTool, ToolMetadata | ✅ |
| 3 | `validator.py` | ToolValidator (JSON Schema, 입력 검증) | ✅ |
| 4 | `registry.py` | ToolRegistry (전역 레지스트리) | ✅ |

### 2.2 core/ 핵심 Tool (6개)

| # | 파일 | 설명 | Tool 수 | 상태 |
|---|------|------|---------|------|
| 5 | `core/__init__.py` | core 패키지 초기화 | - | ✅ |
| 6 | `core/auth_tools.py` | 인증/권한 Tool | 4개 | ✅ |
| 7 | `core/document_tools.py` | 문서 CRUD Tool | 5개 | ✅ |
| 8 | `core/search_tools.py` | 검색 Tool | 2개 | ✅ |
| 9 | `core/version_tools.py` | 버전 관리 Tool | 3개 | ✅ |
| 10 | `core/audit_tools.py` | 감사/통계 Tool | 3개 | ✅ |

### 2.3 utils/ 유틸리티 Tool (4개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 11 | `utils/__init__.py` | utils 패키지 초기화 | ✅ |
| 12 | `utils/text_tools.py` | 텍스트 처리 (요약, 추출) | ✅ |
| 13 | `utils/file_tools.py` | 파일 처리 (업로드, 변환) | ✅ |
| 14 | `utils/format_tools.py` | 포맷 변환 (JSON, CSV, MD) | ✅ |

### 2.4 templates/ 템플릿 (2개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 15 | `templates/tool_template.py` | 동기 Tool 템플릿 | ✅ |
| 16 | `templates/async_tool_template.py` | 비동기 Tool 템플릿 | ✅ |

### 2.5 tests/ 테스트 (3개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 17 | `tests/test_auth_tools.py` | 인증 Tool 테스트 | ✅ |
| 18 | `tests/test_document_tools.py` | 문서 Tool 테스트 | ✅ |
| 19 | `tests/test_search_tools.py` | 검색 Tool 테스트 | ✅ |

---

## 3. 구현 순서

```
Phase 1: 기본 모듈 (4개)
   ├── base.py (BaseTool, ToolMetadata)
   ├── validator.py (입력 검증)
   ├── registry.py (Tool 레지스트리)
   └── __init__.py (패키지 초기화)
   ↓
Phase 2: core/ 핵심 Tool (6개)
   ├── core/__init__.py
   ├── core/auth_tools.py (4 Tool)
   ├── core/document_tools.py (5 Tool)
   ├── core/search_tools.py (2 Tool)
   ├── core/version_tools.py (3 Tool)
   └── core/audit_tools.py (3 Tool)
   ↓
Phase 3: utils/ 유틸리티 Tool (4개)
   ├── utils/__init__.py
   ├── utils/text_tools.py
   ├── utils/file_tools.py
   └── utils/format_tools.py
   ↓
Phase 4: templates/ 템플릿 (2개)
   ├── templates/tool_template.py
   └── templates/async_tool_template.py
   ↓
Phase 5: tests/ 테스트 (3개)
   ├── tests/test_auth_tools.py
   ├── tests/test_document_tools.py
   └── tests/test_search_tools.py
   ↓
Phase 6: 통합 검증
   └── 전체 Tool import 및 기능 테스트
```

---

## 4. 상세 구현 내용

### 4.1 base.py - 기본 클래스

**클래스:**
| 클래스 | 설명 |
|--------|------|
| `ToolMetadata` | Tool 메타데이터 (dataclass) |
| `BaseTool` | 동기 Tool 기본 클래스 (ABC) |
| `AsyncBaseTool` | 비동기 Tool 기본 클래스 |

**BaseTool 메서드:**
| 메서드 | 설명 |
|--------|------|
| `_define_metadata()` | 메타데이터 정의 (추상) |
| `execute()` | Tool 실행 (추상) |
| `validate_arguments()` | 입력 검증 |
| `check_permission()` | 권한 확인 |
| `create_success_response()` | 성공 응답 생성 |
| `create_error_response()` | 에러 응답 생성 |
| `log_execution()` | 실행 로그 기록 |

### 4.2 validator.py - 입력 검증

**클래스:**
| 클래스 | 설명 |
|--------|------|
| `ValidationError` | 검증 에러 예외 |
| `ToolValidator` | 검증 유틸리티 |

**ToolValidator 메서드:**
| 메서드 | 설명 |
|--------|------|
| `validate()` | JSON Schema 검증 |
| `validate_doc_id()` | 문서 ID 형식 검증 |
| `validate_user_id()` | 사용자 ID 형식 검증 |
| `validate_classification()` | 문서 등급 검증 |
| `validate_pagination()` | 페이지네이션 검증 |
| `sanitize_string()` | 문자열 정제 |
| `validate_date_range()` | 날짜 범위 검증 |

### 4.3 registry.py - Tool 레지스트리

**클래스:**
| 클래스 | 설명 |
|--------|------|
| `ToolRegistry` | Tool 레지스트리 |

**ToolRegistry 메서드:**
| 메서드 | 설명 |
|--------|------|
| `register()` | Tool 등록 |
| `get_tool()` | Tool 가져오기 |
| `get_metadata()` | 메타데이터 조회 |
| `list_tools()` | Tool 목록 (필터 지원) |
| `exists()` | Tool 존재 여부 |
| `get_categories()` | 카테고리 목록 |
| `search_tools()` | Tool 검색 |
| `get_stats()` | 레지스트리 통계 |

**전역 함수:**
| 함수 | 설명 |
|------|------|
| `get_registry()` | 전역 레지스트리 반환 |
| `register_tool()` | Tool 등록 (편의 함수) |

### 4.4 core/auth_tools.py - 인증/권한 Tool (4개)

| Tool | 설명 | 권한 |
|------|------|------|
| `AuthenticateTool` | 사용자 인증 (PoC) | 없음 |
| `RequestAccessTool` | 접근 권한 요청 | 없음 |
| `ApproveAccessTool` | 권한 승인/거부 | admin:approve |
| `GetMyPermissionsTool` | 내 권한 조회 | 없음 |

### 4.5 core/document_tools.py - 문서 CRUD Tool (5개)

| Tool | 설명 | 권한 |
|------|------|------|
| `GetDocumentTool` | 문서 상세 조회 | document:read |
| `CreateDocumentTool` | 문서 생성 | document:create |
| `UpdateDocumentTool` | 문서 수정 | document:update |
| `DeleteDocumentTool` | 문서 삭제 | document:delete |
| `ListDocumentsTool` | 문서 목록 조회 | document:read |

### 4.6 core/search_tools.py - 검색 Tool (2개)

| Tool | 설명 | 권한 |
|------|------|------|
| `SearchDocumentsTool` | 전문 검색 (ES) | document:read |
| `SuggestDocumentsTool` | 자동완성 | document:read |

### 4.7 core/version_tools.py - 버전 관리 Tool (3개)

| Tool | 설명 | 권한 |
|------|------|------|
| `GetDocumentVersionsTool` | 버전 히스토리 | document:read |
| `GetDocumentVersionTool` | 특정 버전 조회 | document:read |
| `CompareVersionsTool` | 버전 비교 (diff) | document:read |

### 4.8 core/audit_tools.py - 감사/통계 Tool (3개)

| Tool | 설명 | 권한 |
|------|------|------|
| `GetAuditLogsTool` | 감사 로그 조회 | admin:audit |
| `GetMyActivityTool` | 내 활동 조회 | 없음 |
| `GetStatisticsTool` | 통계 조회 | admin:audit |

### 4.9 utils/ 유틸리티 Tool

**text_tools.py:**
| Tool | 설명 |
|------|------|
| `SummarizeTextTool` | 텍스트 요약 |
| `ExtractKeywordsTool` | 키워드 추출 |

**file_tools.py:**
| Tool | 설명 |
|------|------|
| `ValidateFileTool` | 파일 검증 |
| `GetFileInfoTool` | 파일 정보 조회 |

**format_tools.py:**
| Tool | 설명 |
|------|------|
| `ConvertToJsonTool` | JSON 변환 |
| `ConvertToCsvTool` | CSV 변환 |
| `ConvertToMarkdownTool` | Markdown 변환 |

---

## 5. 디렉토리 구조 (최종)

```
/app/poc/mcps/mcp-tools/
├── SR.md                       # 설계서 (기존)
├── plan.md                     # 구현 계획서 (신규)
├── __init__.py                 # 패키지 초기화
├── base.py                     # 기본 Tool 클래스
├── validator.py                # 입력 검증
├── registry.py                 # Tool 레지스트리
│
├── core/                       # 핵심 Tool (17개)
│   ├── __init__.py
│   ├── auth_tools.py          # 4개 Tool
│   ├── document_tools.py      # 5개 Tool
│   ├── search_tools.py        # 2개 Tool
│   ├── version_tools.py       # 3개 Tool
│   └── audit_tools.py         # 3개 Tool
│
├── utils/                      # 유틸리티 Tool (7개)
│   ├── __init__.py
│   ├── text_tools.py          # 2개 Tool
│   ├── file_tools.py          # 2개 Tool
│   └── format_tools.py        # 3개 Tool
│
├── templates/                  # Tool 템플릿
│   ├── tool_template.py
│   └── async_tool_template.py
│
└── tests/                      # 테스트
    ├── test_auth_tools.py
    ├── test_document_tools.py
    └── test_search_tools.py
```

---

## 6. 진행 상황

- [x] 설계서 분석 (SR.md)
- [x] 구현 계획서 작성 (plan.md)
- [x] Phase 1: 기본 모듈 (4/4 완료)
- [x] Phase 2: core/ 핵심 Tool (6/6 완료, 17 Tool 클래스)
- [x] Phase 3: utils/ 유틸리티 Tool (4/4 완료, 7 Tool 클래스)
- [x] Phase 4: templates/ 템플릿 (2/2 완료)
- [x] Phase 5: tests/ 테스트 (3/3 완료)
- [x] Phase 6: 통합 검증 (완료)

**최종 결과**: 19/19 파일, 24/24 Tool 클래스 구현 완료

---

## 7. Tool 구현 원칙

### 7.1 응답 형식

**성공 응답:**
```python
{
    "status": "success",
    "data": { ... }
}
```

**에러 응답:**
```python
{
    "status": "error",
    "error": {
        "code": "ERROR_CODE",
        "message": "에러 메시지",
        "details": { ... }  # 선택
    }
}
```

### 7.2 에러 코드

| 코드 | 설명 |
|------|------|
| `INVALID_INPUT` | 입력 검증 실패 |
| `NOT_FOUND` | 리소스 없음 |
| `PERMISSION_DENIED` | 권한 없음 |
| `ALREADY_EXISTS` | 중복 |
| `DATABASE_ERROR` | DB 오류 |
| `SEARCH_ERROR` | 검색 오류 |
| `AUTH_ERROR` | 인증 오류 |
| `EXECUTION_ERROR` | 실행 오류 |

### 7.3 실행 컨텍스트

```python
context = {
    "user_id": "U001",
    "user_role": "staff",
    "user_team": "dev_team",
    "request_id": "req_xxx"
}
```

---

## 8. config/registry.json 동기화

SR.md 기준 전체 Tool 목록 (17개 core + 7개 utils = 24개):

### core Tool (17개)
| # | Tool 이름 | 카테고리 | 서버 |
|---|-----------|----------|------|
| 1 | `authenticate` | auth | auth_server |
| 2 | `request_access` | auth | auth_server |
| 3 | `approve_access` | auth | auth_server |
| 4 | `get_my_permissions` | auth | auth_server |
| 5 | `get_document` | document | document_server |
| 6 | `create_document` | document | document_server |
| 7 | `update_document` | document | document_server |
| 8 | `delete_document` | document | document_server |
| 9 | `list_documents` | document | document_server |
| 10 | `search_documents` | search | search_server |
| 11 | `suggest_documents` | search | search_server |
| 12 | `get_document_versions` | version | version_server |
| 13 | `get_document_version` | version | version_server |
| 14 | `compare_versions` | version | version_server |
| 15 | `get_audit_logs` | audit | audit_server |
| 16 | `get_my_activity` | audit | audit_server |
| 17 | `get_statistics` | audit | audit_server |

### utils Tool (7개)
| # | Tool 이름 | 카테고리 |
|---|-----------|----------|
| 18 | `summarize_text` | text |
| 19 | `extract_keywords` | text |
| 20 | `validate_file` | file |
| 21 | `get_file_info` | file |
| 22 | `convert_to_json` | format |
| 23 | `convert_to_csv` | format |
| 24 | `convert_to_markdown` | format |

---

**참조 문서**: [SR.md](SR.md) (mcp-tools 개발가이드 설계서)

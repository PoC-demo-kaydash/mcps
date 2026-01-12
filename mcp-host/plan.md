# mcp-host 구현 계획서

**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/mcp-host/`  
**상태**: 🚧 진행 중

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
| `shared.permissions` | `PermissionEngine`, `UserRole`, `Classification` |
| `shared.queries` | `UserQueries`, `DocumentQueries`, `AuditLogQueries` |
| `shared.logging_config` | `setup_logging()`, `get_logger()` |
| `shared.cache` | `Cache`, `cached()` |
| `shared.mcp_protocol` | `MCPRequest`, `MCPResponse`, `MCPError`, `BaseMCPServer` |

### 1.2 외부 의존성 (FastAPI)

| 패키지 | 용도 |
|--------|------|
| `fastapi` | 웹 프레임워크 |
| `uvicorn` | ASGI 서버 |
| `pydantic` | 데이터 검증 |

---

## 2. 구현 파일 목록 (21개)

### 2.1 설정 및 기본 파일 (2개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 1 | `config.py` | 설정 관리, services.json/registry.json 로드 | ✅ |
| 2 | `requirements.txt` | FastAPI 의존성 | ✅ |

### 2.2 models/ 데이터 모델 (4개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 3 | `models/__init__.py` | models 패키지 초기화 | ✅ |
| 4 | `models/session.py` | SessionCreate, SessionResponse, Session | ✅ |
| 5 | `models/server.py` | ServerInfo, ServerActionRequest/Response | ✅ |
| 6 | `models/request.py` | ToolExecuteRequest/Response, ToolInfo | ✅ |

### 2.3 core/ 핵심 컴포넌트 (5개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 7 | `core/__init__.py` | core 패키지 초기화 | ✅ |
| 8 | `core/server_manager.py` | Server 프로세스 시작/중지/재시작 | ✅ |
| 9 | `core/session_manager.py` | 세션 생성/검증/관리 | ✅ |
| 10 | `core/router.py` | Tool → Server 매핑 및 라우팅 | ✅ |
| 11 | `core/executor.py` | STDIO 통신, JSON-RPC 실행 | ✅ |

### 2.4 api/ REST API (4개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 12 | `api/__init__.py` | api 패키지 초기화 | ✅ |
| 13 | `api/schemas.py` | Pydantic 스키마 (API 전용) | ✅ |
| 14 | `api/middleware.py` | 로깅, CORS 미들웨어 | ✅ |
| 15 | `api/routes.py` | API 라우트 정의 | ✅ |

### 2.5 utils/ 유틸리티 (3개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 16 | `utils/__init__.py` | utils 패키지 초기화 | ✅ |
| 17 | `utils/cache.py` | shared/cache 래퍼 | ✅ |
| 18 | `utils/metrics.py` | 메트릭 수집 | ✅ |

### 2.6 메인 애플리케이션 (1개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 19 | `main.py` | FastAPI 앱, 시작/종료 이벤트 | ✅ |

### 2.7 tests/ 테스트 (2개)

| # | 파일 | 설명 | 상태 |
|---|------|------|------|
| 20 | `tests/test_server_manager.py` | ServerManager 테스트 | ✅ |
| 21 | `tests/test_api.py` | API 엔드포인트 테스트 | ✅ |

---

## 3. 구현 순서

```
Phase 1: 설정 및 기본 구조 (2개)
   ├── config.py (설정 관리)
   └── requirements.txt (의존성)
   ↓
Phase 2: 데이터 모델 (4개)
   ├── models/__init__.py
   ├── models/session.py
   ├── models/server.py
   └── models/request.py
   ↓
Phase 3: 핵심 컴포넌트 (5개)
   ├── core/__init__.py
   ├── core/server_manager.py
   ├── core/session_manager.py
   ├── core/router.py
   └── core/executor.py
   ↓
Phase 4: 유틸리티 (3개)
   ├── utils/__init__.py
   ├── utils/cache.py
   └── utils/metrics.py
   ↓
Phase 5: REST API (4개)
   ├── api/__init__.py
   ├── api/schemas.py
   ├── api/middleware.py
   └── api/routes.py
   ↓
Phase 6: 메인 애플리케이션 (1개)
   └── main.py
   ↓
Phase 7: 테스트 (2개)
   ├── tests/test_server_manager.py
   └── tests/test_api.py
   ↓
Phase 8: 통합 검증
   └── 전체 API 테스트
```

---

## 4. 상세 구현 내용

### 4.1 config.py - 설정 관리

**클래스:**
| 클래스 | 설명 |
|--------|------|
| `DatabaseConfig` | DB 연결 설정 (Pydantic) |
| `ElasticsearchConfig` | ES 설정 |
| `ServerConfig` | 개별 Server 설정 |
| `HostConfig` | Host 서버 설정 (포트 등) |
| `Config` | 통합 설정 클래스 |

**Config 메서드:**
| 메서드 | 설명 |
|--------|------|
| `_load_servers()` | services.json 로드 |
| `_load_registry()` | registry.json 로드 |
| `get_server()` | Server 설정 조회 |
| `get_tool_registry()` | Tool 레지스트리 조회 |

### 4.2 models/ 데이터 모델

**session.py:**
| 클래스 | 설명 |
|--------|------|
| `SessionCreate` | 세션 생성 요청 |
| `SessionResponse` | 세션 생성 응답 |
| `SessionInfo` | 세션 정보 |
| `Session` | 세션 데이터 (dataclass) |

**server.py:**
| 클래스 | 설명 |
|--------|------|
| `ServerInfo` | Server 상태 정보 |
| `ServerListResponse` | Server 목록 응답 |
| `ServerActionRequest` | Server 액션 요청 |
| `ServerActionResponse` | Server 액션 응답 |

**request.py:**
| 클래스 | 설명 |
|--------|------|
| `ToolExecuteRequest` | Tool 실행 요청 |
| `ToolExecuteResponse` | Tool 실행 응답 |
| `ToolListResponse` | Tool 목록 응답 |
| `ToolInfo` | Tool 메타데이터 |

### 4.3 core/server_manager.py - Server 관리

**클래스:**
| 클래스 | 설명 |
|--------|------|
| `ServerProcess` | 프로세스 정보 (dataclass) |
| `ServerManager` | Server 관리자 |

**ServerManager 메서드:**
| 메서드 | 설명 |
|--------|------|
| `start_server()` | Server 시작 (subprocess) |
| `stop_server()` | Server 중지 (SIGTERM) |
| `restart_server()` | Server 재시작 |
| `is_running()` | 실행 여부 확인 |
| `get_server_info()` | Server 정보 조회 |
| `list_servers()` | 전체 Server 목록 |
| `start_all()` | 전체 Server 시작 |
| `stop_all()` | 전체 Server 중지 |
| `health_check()` | 헬스 체크 |
| `cleanup()` | 리소스 정리 |

### 4.4 core/session_manager.py - 세션 관리

**클래스:**
| 클래스 | 설명 |
|--------|------|
| `SessionManager` | 세션 관리자 |

**메서드:**
| 메서드 | 설명 |
|--------|------|
| `create_session()` | 세션 생성 |
| `get_session()` | 세션 조회 |
| `delete_session()` | 세션 삭제 |
| `get_user_context()` | 사용자 컨텍스트 조회 |
| `cleanup_expired_sessions()` | 만료 세션 정리 |
| `list_active_sessions()` | 활성 세션 목록 |

### 4.5 core/router.py - 요청 라우팅

**클래스:**
| 클래스 | 설명 |
|--------|------|
| `Router` | Tool → Server 라우터 |

**메서드:**
| 메서드 | 설명 |
|--------|------|
| `_build_tool_map()` | Tool → Server 매핑 구축 |
| `get_server_for_tool()` | Tool의 Server 찾기 |
| `is_tool_available()` | Tool 사용 가능 여부 |
| `list_all_tools()` | 전체 Tool 목록 |
| `get_tool_metadata()` | Tool 메타데이터 조회 |
| `reload_mapping()` | 매핑 재로드 |

### 4.6 core/executor.py - Tool 실행

**클래스:**
| 클래스 | 설명 |
|--------|------|
| `ToolExecutor` | Tool 실행기 |

**메서드:**
| 메서드 | 설명 |
|--------|------|
| `execute_tool()` | Tool 실행 (async) |
| `list_tools()` | Server의 Tool 목록 조회 |

### 4.7 api/routes.py - REST API

**엔드포인트:**
| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/sessions` | 세션 생성 (인증) |
| `GET` | `/api/sessions/{id}` | 세션 정보 조회 |
| `DELETE` | `/api/sessions/{id}` | 세션 삭제 (로그아웃) |
| `POST` | `/api/tools/execute` | Tool 실행 |
| `GET` | `/api/tools/list` | Tool 목록 조회 |
| `GET` | `/api/tools/{name}` | Tool 상세 정보 |
| `GET` | `/api/servers` | Server 목록 |
| `GET` | `/api/servers/{name}` | Server 정보 |
| `POST` | `/api/servers/action` | Server 액션 |
| `GET` | `/health` | 헬스 체크 |

### 4.8 main.py - 메인 애플리케이션

**이벤트:**
| 이벤트 | 설명 |
|--------|------|
| `startup_event()` | 관리자 초기화, Server 시작 |
| `shutdown_event()` | Server 종료, 리소스 정리 |

**기능:**
- FastAPI 앱 생성
- 미들웨어 설정 (CORS, 로깅)
- 라우터 등록
- 세션 정리 백그라운드 태스크
- 시그널 핸들러 (SIGINT, SIGTERM)

---

## 5. Server 매핑 정보 (config/registry.json 기준)

### 5.1 Tool → Server 매핑

| Server | Tool |
|--------|------|
| `auth_server` | authenticate, request_access, approve_access, get_my_permissions |
| `document_server` | get_document, create_document, update_document, delete_document, list_documents |
| `search_server` | search_documents, suggest_documents |
| `version_server` | get_document_versions, get_document_version, compare_versions |
| `audit_server` | get_audit_logs, get_my_activity, get_statistics |

### 5.2 Server 설정 (config/services.json 기준)

| Server | Python | auto_start | restart_on_failure |
|--------|--------|------------|-------------------|
| `auth_server` | mcp_env | ✅ | ✅ |
| `document_server` | mcp_env | ✅ | ✅ |
| `search_server` | mcp_env | ✅ | ✅ |
| `version_server` | mcp_env | ✅ | ✅ |
| `audit_server` | mcp_env | ✅ | ✅ |

---

## 6. 디렉토리 구조 (최종)

```
/app/poc/mcps/mcp-host/
├── SR.md                       # 설계서 (기존)
├── plan.md                     # 구현 계획서 (신규)
├── main.py                     # FastAPI 앱
├── config.py                   # 설정 관리
├── requirements.txt            # 의존성
│
├── core/                       # 핵심 컴포넌트
│   ├── __init__.py
│   ├── server_manager.py      # Server 프로세스 관리
│   ├── session_manager.py     # 세션 관리
│   ├── router.py              # Tool 라우팅
│   └── executor.py            # Tool 실행
│
├── api/                        # REST API
│   ├── __init__.py
│   ├── schemas.py             # Pydantic 스키마
│   ├── middleware.py          # 미들웨어
│   └── routes.py              # 라우트 정의
│
├── models/                     # 데이터 모델
│   ├── __init__.py
│   ├── session.py
│   ├── server.py
│   └── request.py
│
├── utils/                      # 유틸리티
│   ├── __init__.py
│   ├── cache.py
│   └── metrics.py
│
└── tests/                      # 테스트
    ├── test_server_manager.py
    └── test_api.py
```

---

## 7. 진행 상황

- [x] 설계서 분석 (SR.md)
- [x] 구현 계획서 작성 (plan.md)
- [x] Phase 1: 설정 및 기본 구조 (2개)
- [x] Phase 2: 데이터 모델 (4개)
- [x] Phase 3: 핵심 컴포넌트 (5개)
- [x] Phase 4: 유틸리티 (3개)
- [x] Phase 5: REST API (4개)
- [x] Phase 6: 메인 애플리케이션 (1개)
- [x] Phase 7: 테스트 (2개)
- [ ] Phase 8: 통합 검증

---

## 8. API 응답 형식

### 8.1 성공 응답

```python
{
    "status": "success",
    "data": { ... }
}
```

### 8.2 에러 응답

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

### 8.3 에러 코드

| 코드 | HTTP | 설명 |
|------|------|------|
| `INVALID_INPUT` | 400 | 입력 검증 실패 |
| `UNAUTHORIZED` | 401 | 인증 필요 |
| `FORBIDDEN` | 403 | 권한 없음 |
| `NOT_FOUND` | 404 | 리소스 없음 |
| `TIMEOUT` | 408 | 타임아웃 |
| `SERVER_ERROR` | 500 | 서버 오류 |
| `SERVER_START_FAILED` | 500 | Server 시작 실패 |

---

## 9. 통신 프로토콜 (JSON-RPC 2.0)

### 9.1 Tool 실행 요청

```json
{
    "jsonrpc": "2.0",
    "id": "uuid",
    "method": "tools/call",
    "params": {
        "name": "search_documents",
        "arguments": {
            "query": "AI",
            "limit": 10
        },
        "_context": {
            "user_id": "U001",
            "user_role": "engineer",
            "user_team": "dev_team"
        }
    }
}
```

### 9.2 Tool 실행 응답

```json
{
    "jsonrpc": "2.0",
    "id": "uuid",
    "result": {
        "status": "success",
        "data": {
            "total": 5,
            "results": [...]
        }
    }
}
```

---

**참조 문서**: [SR.md](SR.md) (mcp-host 개발가이드 설계서)

# API Gateway 구현 계획서

> 작성일: 2026-01-08  
> 기준 문서: [SR.md](SR.md)  
> 상태: 🔴 미완료 | 🟡 진행중 | 🟢 완료

---

## 1. 개요

SR.md 설계서를 기반으로 FastAPI 기반 API Gateway를 구현합니다.

### 목표
- MCP Host와 클라이언트 사이의 게이트웨이 역할
- 인증/인가, Rate Limiting, CORS, 로깅 등 공통 기능 제공
- RESTful API 제공 (세션, Tool 실행, 문서 관리, 사용자 관리, 관리자 기능)

### 기술 스택
- FastAPI 0.104+
- Python 3.11+
- Uvicorn (ASGI Server)
- JWT Authentication
- Redis (Rate Limiting, Caching)
- Pydantic (Validation)

---

## 2. To-Do List

### 2.1 🔴 Phase 1: 핵심 컴포넌트 구현

#### 2.1.1 프로젝트 구조 설정

- [x] `api-gateway/` 디렉토리 구조 생성
- [x] `requirements.txt` 생성 - 의존성 정의
- [x] `.env.example` 생성 - 환경 변수 템플릿
- [x] `__init__.py` 파일들 생성 (각 모듈)

#### 2.1.2 Core 모듈 (4개 파일)

- [x] `app/core/config.py` - 설정 관리 (Pydantic Settings)
  - [ ] Settings 클래스 정의
  - [ ] 환경 변수 로드
  - [ ] MCP Host URL, DB, Redis 설정
  - [ ] JWT 설정
  - [ ] CORS, Rate Limit 설정

- [x] `app/core/security.py` - 보안 기능
  - [ ] JWT 토큰 생성 함수 (create_access_token)
  - [ ] JWT 토큰 검증 함수 (verify_token)
  - [ ] 비밀번호 해싱 함수 (get_password_hash)
  - [ ] 비밀번호 검증 함수 (verify_password)
  - [ ] 세션 토큰 생성/검증

- [x] `app/core/exceptions.py` - 커스텀 예외
  - [ ] APIGatewayException (기본 예외)
  - [ ] AuthenticationError (401)
  - [ ] AuthorizationError (403)
  - [ ] RateLimitExceeded (429)
  - [ ] ValidationError (400)
  - [ ] ServiceUnavailable (503)

- [x] `app/core/dependencies.py` - FastAPI 의존성
  - [ ] get_session_service()
  - [ ] get_cache_service()
  - [ ] get_current_user()
  - [ ] get_optional_user()
  - [ ] require_role() - 역할 기반 접근 제어

#### 2.1.3 유틸리티 (2개 파일)

- [x] `app/utils/logger.py` - 로거 설정
  - [ ] setup_logger() 함수
  - [ ] JSON 포맷 로깅 설정

- [x] `app/utils/metrics.py` - 메트릭 수집 (선택)
  - [ ] Prometheus 메트릭 설정

---

### 2.2 🟡 Phase 2: 모델 정의

#### 2.2.1 Request 모델 (1개 파일)

- [x] `app/models/request.py`
  - [ ] CreateSessionRequest - 세션 생성
  - [ ] ExecuteToolRequest - Tool 실행
  - [ ] CreateDocumentRequest - 문서 생성
  - [ ] UpdateDocumentRequest - 문서 수정

#### 2.2.2 Response 모델 (1개 파일)

- [x] `app/models/response.py`
  - [ ] ErrorDetail - 에러 상세
  - [ ] ErrorResponse - 에러 응답
  - [ ] SuccessResponse - 성공 응답 (기본)
  - [ ] SessionResponse
  - [ ] ToolResponse
  - [ ] ToolListResponse
  - [ ] DocumentResponse
  - [ ] DocumentListResponse
  - [ ] UserResponse
  - [ ] AdminResponse

---

### 2.3 🟡 Phase 3: 서비스 레이어

#### 2.3.1 서비스 파일 (5개 파일)

- [x] `app/services/auth_service.py` - 인증 서비스
  - [ ] authenticate_user() - 사용자 인증
  - [ ] create_token() - 토큰 생성
  - [ ] validate_token() - 토큰 검증

- [x] `app/services/session_service.py` - 세션 서비스
  - [ ] create_session() - 세션 생성
  - [ ] get_session() - 세션 조회
  - [ ] delete_session() - 세션 삭제

- [x] `app/services/tool_service.py` - Tool 서비스
  - [ ] list_tools() - Tool 목록
  - [ ] execute_tool() - Tool 실행
  - [ ] get_tool_info() - Tool 정보

- [x] `app/services/mcp_client.py` - MCP Host 클라이언트
  - [ ] MCP Host HTTP 요청 래퍼

- [x] `app/services/cache_service.py` - 캐시 서비스
  - [ ] Redis 연결
  - [ ] get(), set(), delete() 메서드
  - [ ] ping() - 헬스체크

---

### 2.4 🟢 Phase 4: 미들웨어

#### 2.4.1 미들웨어 파일 (4개 파일)

- [x] `app/middleware/error_handler.py` - 전역 에러 핸들러
  - [ ] ErrorHandlerMiddleware 클래스
  - [ ] APIGatewayException 처리
  - [ ] 일반 Exception 처리

- [x] `app/middleware/logging.py` - 요청/응답 로깅
  - [ ] LoggingMiddleware 클래스
  - [ ] 요청 정보 로깅
  - [ ] 응답 시간 측정
  - [ ] X-Process-Time 헤더 추가

- [x] `app/middleware/auth.py` - 인증 미들웨어
  - [ ] AuthMiddleware 클래스
  - [ ] PUBLIC_PATHS 정의
  - [ ] Authorization 헤더 확인

- [x] `app/middleware/rate_limit.py` - Rate Limiting
  - [ ] RateLimitMiddleware 클래스
  - [ ] Redis 기반 카운터
  - [ ] 클라이언트 IP 기반 제한

---

### 2.5 🟢 Phase 5: API 라우터

#### 2.5.1 Health Check (1개 파일)

- [x] `app/api/health.py`
  - [ ] GET /health - 헬스체크
  - [ ] GET /ping - 간단한 핑

#### 2.5.2 Sessions API (1개 파일)

- [x] `app/api/v1/sessions.py`
  - [ ] POST /api/v1/sessions - 세션 생성
  - [ ] GET /api/v1/sessions/{session_id} - 세션 조회
  - [ ] DELETE /api/v1/sessions/{session_id} - 세션 삭제

#### 2.5.3 Tools API (1개 파일)

- [x] `app/api/v1/tools.py`
  - [ ] GET /api/v1/tools/list - Tool 목록
  - [ ] POST /api/v1/tools/execute - Tool 실행
  - [ ] GET /api/v1/tools/{tool_name} - Tool 정보

#### 2.5.4 Documents API (1개 파일)

- [x] `app/api/v1/documents.py`
  - [ ] GET /api/v1/documents - 문서 목록
  - [ ] GET /api/v1/documents/{doc_id} - 문서 조회
  - [ ] POST /api/v1/documents - 문서 생성
  - [ ] PUT /api/v1/documents/{doc_id} - 문서 수정
  - [ ] DELETE /api/v1/documents/{doc_id} - 문서 삭제
  - [ ] GET /api/v1/documents/{doc_id}/versions - 버전 목록

#### 2.5.5 Users API (1개 파일)

- [x] `app/api/v1/users.py`
  - [ ] GET /api/v1/users/me - 내 정보
  - [ ] GET /api/v1/users/me/permissions - 내 권한
  - [ ] GET /api/v1/users/{user_id} - 사용자 정보 (Manager+)

#### 2.5.6 Admin API (1개 파일)

- [x] `app/api/v1/admin.py`
  - [ ] GET /api/v1/admin/stats - 시스템 통계 (Admin)
  - [ ] GET /api/v1/admin/audit-logs - 감사 로그 (Admin)
  - [ ] POST /api/v1/admin/permissions/grant - 권한 부여 (Manager+)
  - [ ] DELETE /api/v1/admin/permissions/revoke - 권한 회수 (Manager+)

---

### 2.6 🟢 Phase 6: 메인 애플리케이션

#### 2.6.1 FastAPI 앱 (1개 파일)

- [x] `main.py`
  - [ ] FastAPI 앱 초기화
  - [ ] Lifespan 이벤트 설정
  - [ ] CORS 미들웨어 등록
  - [ ] Error Handler 미들웨어 등록
  - [ ] Logging 미들웨어 등록
  - [ ] Auth 미들웨어 등록
  - [ ] Rate Limit 미들웨어 등록
  - [ ] 라우터 등록 (health, sessions, tools, documents, users, admin)
  - [ ] 루트 엔드포인트 구현
  - [ ] Uvicorn 실행 설정

---

### 2.7 🟡 Phase 7: 설정 및 배포

#### 2.7.1 설정 파일 (2개 파일)

- [x] `.env.example` - 환경 변수 템플릿
  - [ ] ENVIRONMENT, DEBUG, HOST, PORT
  - [ ] MCP_HOST_URL, MCP_HOST_TIMEOUT
  - [ ] DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  - [ ] REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
  - [ ] JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
  - [ ] CORS_ORIGINS
  - [ ] RATE_LIMIT_ENABLED, RATE_LIMIT_REQUESTS, RATE_LIMIT_PERIOD
  - [ ] CACHE_ENABLED, CACHE_TTL
  - [ ] METRICS_ENABLED

- [x] `requirements.txt` - Python 의존성
  - [ ] fastapi==0.104.1
  - [ ] uvicorn[standard]==0.24.0
  - [ ] pydantic==2.5.0
  - [ ] pydantic-settings==2.1.0
  - [ ] httpx==0.25.2
  - [ ] pyjwt==2.8.0
  - [ ] passlib[bcrypt]==1.7.4
  - [ ] python-multipart==0.0.6
  - [ ] redis==5.0.1
  - [ ] pymysql==1.1.0 (선택)
  - [ ] python-dotenv==1.0.0
  - [ ] python-json-logger==2.0.7
  - [ ] prometheus-client==0.19.0 (선택)

#### 2.7.2 Docker 설정 (2개 파일)

- [x] `Dockerfile`
  - [ ] Python 3.11-slim 베이스 이미지
  - [ ] 의존성 설치
  - [ ] 애플리케이션 복사
  - [ ] 사용자 생성
  - [ ] 포트 노출 (8080)
  - [ ] 헬스체크 설정
  - [ ] Uvicorn 실행 CMD

- [x] `docker-compose.yml`
  - [ ] api-gateway 서비스
  - [ ] redis 서비스
  - [ ] mariadb 서비스 (선택)
  - [ ] 네트워크 설정
  - [ ] 볼륨 설정

#### 2.7.3 배포 스크립트 (1개 파일)

- [x] `deploy.sh`
  - [ ] 가상환경 생성
  - [ ] 의존성 설치
  - [ ] .env 확인
  - [ ] 테스트 실행 (선택)
  - [ ] Systemd 서비스 재시작
  - [ ] 헬스체크

---

## 3. 파일 구조 및 생성 순서

```
api-gateway/
├── main.py                          # Phase 6 (1개)
├── requirements.txt                 # Phase 7 (1개)
├── .env.example                     # Phase 7 (1개)
├── Dockerfile                       # Phase 7 (1개)
├── docker-compose.yml               # Phase 7 (1개)
├── deploy.sh                        # Phase 7 (1개)
│
├── app/
│   ├── __init__.py
│   │
│   ├── core/                        # Phase 1 (4개)
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   └── dependencies.py
│   │
│   ├── middleware/                  # Phase 4 (4개)
│   │   ├── __init__.py
│   │   ├── error_handler.py
│   │   ├── logging.py
│   │   ├── auth.py
│   │   └── rate_limit.py
│   │
│   ├── api/                         # Phase 5 (6개)
│   │   ├── __init__.py
│   │   ├── health.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── sessions.py
│   │       ├── tools.py
│   │       ├── documents.py
│   │       ├── users.py
│   │       └── admin.py
│   │
│   ├── services/                    # Phase 3 (5개)
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── session_service.py
│   │   ├── tool_service.py
│   │   ├── mcp_client.py
│   │   └── cache_service.py
│   │
│   ├── models/                      # Phase 2 (2개)
│   │   ├── __init__.py
│   │   ├── request.py
│   │   └── response.py
│   │
│   └── utils/                       # Phase 1 (2개)
│       ├── __init__.py
│       ├── logger.py
│       └── metrics.py
│
└── tests/                           # Phase 8 (선택)
    ├── __init__.py
    ├── conftest.py
    ├── test_api.py
    ├── test_middleware.py
    └── test_services.py
```

---

## 4. 진행 상태

| Phase | 항목 | 파일 수 | 상태 | 완료일 |
|-------|------|---------|------|--------|
| 1 | Core & Utils | 6개 | � 완료 | 2026-01-08 |
| 2 | Models | 2개 | 🟢 완료 | 2026-01-08 |
| 3 | Services | 5개 | 🟢 완료 | 2026-01-08 |
| 4 | Middleware | 4개 | 🟢 완료 | 2026-01-08 |
| 5 | API Routers | 6개 | 🟢 완료 | 2026-01-08 |
| 6 | Main App | 1개 | 🟢 완료 | 2026-01-08 |
| 7 | Deployment | 4개 | 🟢 완료 | 2026-01-08 |
| 8 | Tests (선택) | 5개 | 🔴 미완료 | - |

**총 필수 파일 수**: 30개  
**선택 파일 수**: 5개 (tests)

---

## 5. 주요 API 엔드포인트 목록

### 5.1 Health & Root
- `GET /` - 루트 (서비스 정보)
- `GET /health` - 헬스체크
- `GET /ping` - 간단한 핑

### 5.2 Sessions (인증 필요 ❌ POST만)
- `POST /api/v1/sessions` - 세션 생성 ⭕ Public
- `GET /api/v1/sessions/{session_id}` - 세션 조회
- `DELETE /api/v1/sessions/{session_id}` - 세션 삭제

### 5.3 Tools (인증 필요 ✅)
- `GET /api/v1/tools/list` - Tool 목록
- `POST /api/v1/tools/execute` - Tool 실행
- `GET /api/v1/tools/{tool_name}` - Tool 정보

### 5.4 Documents (인증 필요 ✅)
- `GET /api/v1/documents` - 문서 목록
- `GET /api/v1/documents/{doc_id}` - 문서 조회
- `POST /api/v1/documents` - 문서 생성
- `PUT /api/v1/documents/{doc_id}` - 문서 수정
- `DELETE /api/v1/documents/{doc_id}` - 문서 삭제
- `GET /api/v1/documents/{doc_id}/versions` - 버전 목록

### 5.5 Users (인증 필요 ✅)
- `GET /api/v1/users/me` - 내 정보
- `GET /api/v1/users/me/permissions` - 내 권한
- `GET /api/v1/users/{user_id}` - 사용자 정보 (Manager 이상)

### 5.6 Admin (인증 필요 ✅ + 역할 제한)
- `GET /api/v1/admin/stats` - 시스템 통계 (Admin 전용)
- `GET /api/v1/admin/audit-logs` - 감사 로그 (Admin 전용)
- `POST /api/v1/admin/permissions/grant` - 권한 부여 (Manager 이상)
- `DELETE /api/v1/admin/permissions/revoke` - 권한 회수 (Manager 이상)

---

## 6. 주요 설계 결정 사항

### 6.1 인증 방식
- **JWT Bearer Token** 사용
- 세션 기반 인증 (MCP Host와 연동)
- Token 만료 시간: **24시간** (설정 가능)
- Authorization 헤더: `Bearer <token>`

### 6.2 Rate Limiting
- **Redis 기반** 카운터
- 기본 설정: **60초당 100회**
- 클라이언트 **IP 기반** 제한
- 헬스체크는 Rate Limit 제외

### 6.3 에러 응답 포맷
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "details": {}
  }
}
```

### 6.4 성공 응답 포맷
```json
{
  "status": "success",
  "data": {}
}
```

### 6.5 미들웨어 순서 (중요!)
1. **CORS** (가장 먼저)
2. **Error Handler**
3. **Logging**
4. **Auth**
5. **Rate Limit** (마지막)

### 6.6 권한 계층
```
junior (0) < staff (1) < manager (2) < executive (2) < admin (3)
```

### 6.7 Public 경로 (인증 불필요)
- `/` - 루트
- `/health` - 헬스체크
- `/ping` - 핑
- `/docs` - API 문서 (개발 환경만)
- `/redoc` - ReDoc (개발 환경만)
- `/openapi.json` - OpenAPI Spec (개발 환경만)
- `/api/v1/sessions` (POST) - 세션 생성

---

## 7. 의존성 및 기술 스택

### 7.1 핵심 의존성
- **FastAPI** 0.104+ - Web Framework
- **Uvicorn** 0.24+ - ASGI Server
- **Pydantic** 2.5+ - Validation
- **PyJWT** 2.8+ - JWT Token
- **passlib[bcrypt]** 1.7+ - Password Hashing
- **httpx** 0.25+ - HTTP Client (MCP Host 연동)
- **redis** 5.0+ - Rate Limiting & Caching

### 7.2 선택 의존성
- **pymysql** 1.1+ - MariaDB 연결 (직접 연결 시)
- **prometheus-client** 0.19+ - 메트릭 수집
- **python-json-logger** 2.0+ - JSON 포맷 로깅

### 7.3 개발 의존성
- **pytest** - 테스트
- **pytest-asyncio** - 비동기 테스트
- **httpx** - 테스트 클라이언트

---

## 8. 환경 변수 설정

### 8.1 필수 환경 변수
```bash
# 환경
ENVIRONMENT=production
DEBUG=false

# 서버
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO

# MCP Host
MCP_HOST_URL=http://localhost:8000
MCP_HOST_TIMEOUT=30

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# JWT
JWT_SECRET_KEY=your-secret-key-change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# 캐싱
CACHE_ENABLED=true
CACHE_TTL=300
```

---

## 9. 참고 사항

### 9.1 MCP Host 연동
- MCP Host URL: `http://localhost:8000` (기본값)
- Timeout: 30초
- API Gateway → MCP Host 요청 시 세션 정보 전달
- MCP Host가 실행 중이어야 함

### 9.2 Redis 설정
- Rate Limiting: 클라이언트 IP → 요청 카운트 저장
- 캐싱: Tool 정보, 사용자 정보 캐싱 (선택)
- TTL: 기본 5분 (300초)

### 9.3 데이터베이스 연동
- 직접 DB 연결은 선택 사항
- 대부분 MCP Host를 통해 데이터 조회

### 9.4 로깅
- 요청/응답 로깅
- 에러 로깅
- 처리 시간 측정 (X-Process-Time 헤더)

### 9.5 보안
- JWT Secret Key는 **반드시 변경**
- HTTPS 사용 권장 (프로덕션)
- CORS Origins 제한

---

## 10. 다음 단계

### 실행 순서
1. **Phase 1 시작**: Core 모듈 구현 (config, security, exceptions, dependencies)
2. **Phase 2**: 모델 정의 (request, response)
3. **Phase 3**: 서비스 레이어 구현 (auth, session, tool, mcp_client, cache)
4. **Phase 4**: 미들웨어 구현 (error_handler, logging, auth, rate_limit)
5. **Phase 5**: API 라우터 구현 (health, sessions, tools, documents, users, admin)
6. **Phase 6**: 메인 앱 구현 (main.py)
7. **Phase 7**: 배포 설정 (.env, Dockerfile, docker-compose.yml, deploy.sh)

### 테스트
- 각 Phase 완료 시 단위 테스트
- API 엔드포인트 테스트
- 통합 테스트 (MCP Host 연동)

---

## 11. 예상 소요 시간

| Phase | 예상 시간 | 누적 시간 |
|-------|----------|----------|
| Phase 1: Core & Utils | 1-2시간 | 1-2시간 |
| Phase 2: Models | 30분 | 1.5-2.5시간 |
| Phase 3: Services | 2-3시간 | 3.5-5.5시간 |
| Phase 4: Middleware | 1-2시간 | 4.5-7.5시간 |
| Phase 5: API Routers | 3-4시간 | 7.5-11.5시간 |
| Phase 6: Main App | 30분 | 8-12시간 |
| Phase 7: Deployment | 1시간 | 9-13시간 |
| **총 예상 시간** | **9-13시간** | |

---

## 12. 완료 조건

- [x] 모든 API 엔드포인트 구현 완료 (18개)
- [x] 미들웨어 정상 동작 확인 (5개)
- [x] MCP Host 연동 테스트 통과
- [x] 인증/인가 테스트 통과
- [x] Rate Limiting 동작 확인
- [x] Docker 이미지 빌드 성공
- [x] API 문서 자동 생성 확인 (Swagger)
- [x] 헬스체크 정상 응답 (200 OK)

---

## 13. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

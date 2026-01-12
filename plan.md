# MCP Ecosystem 검증 계획

**작성일**: 2026-01-12  
**버전**: 1.0.0  
**목적**: SR.md 설계서 대비 구현 검증 및 시스템 동작 확인

---

## 1. 개요

### 1.1 검증 목표
- SR.md 설계서와 현재 구현 상태의 일치성 확인
- 각 구성요소의 논리적 동작 검증
- 전체 시스템 통합 동작 검증

### 1.2 검증 범위
- 12개 핵심 폴더 (config, shared, mcp-tools, mcp-servers, mcp-host, api-gateway, frontend, data, scripts, tests, docs, pids)
- 5개 MCP Server (auth, document, search, version, audit)
- 17개 Tool
- 8개 shared 모듈

### 1.3 검증 방식
- Phase 1: 설계서 불일치 항목 수정 (즉시 조치)
- Phase 2: 단위 테스트 (모듈별 검증)
- Phase 3: 통합 테스트 (컴포넌트 간 연동)
- Phase 4: E2E 테스트 (시나리오 기반)
- Phase 5: 성능 및 안정성 테스트

---

## 2. 현재 구현 상태 요약

### 2.1 SR.md 핵심 요구사항 체크리스트

| 요구사항 | 섹션 | 구현 파일 | 상태 | 비고 |
|----------|------|-----------|------|------|
| 망분리 환경 독립 실행 | 1.1 | 전체 시스템 | ✅ | 모든 의존성 로컬 설치 가능 |
| 역할별 문서 접근 제어 (5단계) | 1.2 | shared/permissions.py | ✅ | junior, staff, manager, executive, admin |
| 동적 Tool/Server 등록 | 1.2 | mcp-tools/registry.py | ✅ | ToolRegistry 클래스 |
| 전문 검색 (Elasticsearch) | 1.2 | shared/elasticsearch.py | ✅ | Nori 분석기 |
| 감사 로그 | 1.2 | audit_server/main.py | ✅ | 3개 Tool |
| 외부 AI Agent 연동 API | 1.2 | api-gateway/ | ✅ | REST API + JWT |

### 2.2 3-Tier 아키텍처 구현 상태

| 계층 | 구성요소 | 구현 상태 |
|------|----------|-----------|
| Presentation | Reflex Frontend | ✅ |
| Presentation | API Gateway (FastAPI) | ✅ |
| Business Logic | MCP Host | ✅ |
| Business Logic | MCP Servers (5개) | ✅ |
| Data | MariaDB | ✅ |
| Data | Elasticsearch | ✅ |
| Data | File System | ✅ |

### 2.3 기술 스택 구현 상태

| 기술 | 요구 버전 | 구현 상태 |
|------|-----------|-----------|
| Python | 3.10+ | ✅ |
| FastAPI | 0.109+ | ✅ |
| Reflex | 0.4+ | ✅ |
| MariaDB | 10.11+ | ✅ |
| Elasticsearch | 8.x | ✅ |
| ORM 미사용 | - | ✅ Parameterized Query |

---

## 3. Phase 1: 설계서 불일치 항목 수정

### 3.1 역할명 통일 (SR.md 기준)

**SR.md 정의 (섹션 6.2.1)**:
```
junior (level 1) - 신입
staff (level 2) - 일반 사원
manager (level 3) - 팀 관리자
executive (level 4) - 임원
admin (level 5) - 시스템 관리자
```

**수정 대상 파일**:

| 파일 | 수정 내용 | 상태 |
|------|-----------|------|
| shared/permissions.py | Role enum: VIEWER→JUNIOR, EDITOR→STAFF, SUPER_ADMIN→ADMIN 삭제 | ✅ |
| shared/permissions.py | ROLE_MAP: viewer→junior, editor→staff, super_admin 삭제 | ✅ |
| shared/queries.py | 기본값: "viewer" → "junior" | ✅ |
| tests/unit/test_shared.py | 테스트 코드 역할명 수정 | ✅ |
| config/permissions.json | (유지 - 이미 SR.md 기준) | ✅ |
| config/users.json | (유지 - 이미 SR.md 기준) | ✅ |

### 3.2 services.json 경로 수정

**현재 경로**: `mcp-servers/core/auth_server/`  
**수정 경로**: `mcp-servers/auth_server/`  
**상태**: ✅ 완료

### 3.3 보안 등급 정의

**SR.md 정의**: public, team, confidential (3단계)  
**현재 구현**: PUBLIC, INTERNAL, CONFIDENTIAL, SECRET, TOP_SECRET (5단계)  
**조치**: 확장된 구현 유지, patch.md에 문서화  
**상태**: ✅ 완료 (patch.md 작성됨)

---

## 4. Phase 2: 단위 테스트

### 4.1 테스트 대상 모듈

| 순서 | 대상 모듈 | 테스트 파일 | 검증 항목 | 우선순위 |
|------|-----------|-------------|-----------|----------|
| 2.1 | shared/database.py | tests/unit/test_database.py | Connection Pool, Parameterized Query, 트랜잭션 | 🔴 높음 |
| 2.2 | shared/elasticsearch.py | tests/unit/test_elasticsearch.py | ES 클라이언트, 인덱스, 검색, Nori | 🔴 높음 |
| 2.3 | shared/permissions.py | tests/unit/test_permissions.py | RBAC 5단계, 권한 매트릭스 | 🔴 높음 |
| 2.4 | shared/mcp_protocol.py | tests/unit/test_mcp_protocol.py | JSON-RPC 2.0, STDIO | 🟡 중간 |
| 2.5 | shared/cache.py | tests/unit/test_cache.py | TTL, LRU | 🟡 중간 |
| 2.6 | mcp-tools/core/*.py | tests/unit/test_tools.py | execute(), validate_params() | 🔴 높음 |

### 4.2 테스트 시나리오

#### 4.2.1 DatabaseManager 테스트
```
- test_connection_pool_creation
- test_execute_query_with_params
- test_execute_query_without_params
- test_transaction_commit
- test_transaction_rollback
- test_connection_reuse
```

#### 4.2.2 PermissionEngine 테스트
```
- test_check_permission_junior_public
- test_check_permission_junior_confidential_denied
- test_check_permission_manager_team
- test_check_permission_admin_all
- test_get_accessible_documents
```

#### 4.2.3 Tool 테스트
```
- test_tool_execute_success
- test_tool_execute_invalid_params
- test_tool_execute_permission_denied
```

---

## 5. Phase 3: 통합 테스트

### 5.1 테스트 시나리오

| 순서 | 시나리오 | 관련 컴포넌트 | 검증 항목 |
|------|----------|---------------|-----------|
| 3.1 | MCP Host ↔ Server STDIO 통신 | server_manager.py, 각 서버 main.py | JSON-RPC 요청/응답 |
| 3.2 | API Gateway ↔ MCP Host | mcp_client.py | HTTP 프록시, 오류 전파 |
| 3.3 | JWT 인증 플로우 | auth.py, session_service.py | 토큰 발급/검증 |
| 3.4 | 권한 체크 체인 | permissions.py → Tool.execute() | 역할별 접근 제어 |
| 3.5 | 문서 CRUD + ES 동기화 | document_tools → DB + ES | 색인 동기화 |

### 5.2 통합 테스트 절차

```bash
# 1. 서비스 시작
./scripts/control/start_all.sh

# 2. 상태 확인
./scripts/manage/status.sh

# 3. 통합 테스트 실행
python mcp-servers/scripts/integration_test.py

# 4. 로그 확인
tail -f data/logs/mcp-host/app.log
```

---

## 6. Phase 4: E2E 테스트

### 6.1 시나리오별 테스트

| 순서 | 시나리오 | 검증 항목 | 예상 결과 |
|------|----------|-----------|-----------|
| 4.1 | 로그인 → 검색 → 문서 조회 | 전체 사용자 플로우 | 200 OK, 문서 데이터 반환 |
| 4.2 | 문서 생성 → 수정 → 버전 히스토리 | 버전 관리, 트리거 | 버전 자동 증가 |
| 4.3 | junior가 confidential 접근 시도 | RBAC | 403 Forbidden |
| 4.4 | 외부 AI Agent API 호출 | REST API | Tool 실행 결과 |
| 4.5 | 감사 로그 기록 확인 | 감사 추적 | audit_logs 기록 존재 |

### 6.2 E2E 테스트 절차

```bash
# 1. 전체 시스템 시작
./scripts/control/start_all.sh

# 2. E2E 테스트 실행
pytest tests/e2e/ -v

# 3. 결과 확인 및 로그 분석
```

---

## 7. Phase 5: 성능 및 안정성 테스트

### 7.1 성능 목표 (SR.md 섹션 7)

| 지표 | 목표 | 테스트 방법 |
|------|------|-------------|
| 동시 접속 | 50명 | Apache Bench |
| 검색 응답 시간 | < 500ms (95p) | wrk |
| 문서 조회 응답 | < 200ms (95p) | wrk |
| DB Connection Pool | 5-20개 | 모니터링 |
| 메모리 사용 | < 8GB | top/htop |

### 7.2 안정성 테스트

| 테스트 | 방법 | 기대 결과 |
|--------|------|-----------|
| MCP Server 재시작 | kill -9 후 자동 복구 | 3회 내 재시작 |
| DB 연결 끊김 | 네트워크 차단 후 복구 | 자동 재연결 |
| 메모리 누수 | 장시간 운영 | 메모리 안정 |

---

## 8. 검증 체크리스트

### 8.1 Phase 1 체크리스트

- [x] permissions.py 역할명 수정 (VIEWER → JUNIOR 등)
- [x] queries.py 기본값 수정 (viewer → junior)
- [x] test_shared.py 역할명 수정
- [x] services.json 경로 수정
- [x] patch.md 작성 (확장된 구현 문서화)

**✅ Phase 1 완료일**: 2026-01-12

### 8.2 Phase 2 체크리스트

- [ ] test_database.py 작성 및 통과
- [ ] test_elasticsearch.py 작성 및 통과
- [ ] test_permissions.py 작성 및 통과
- [ ] test_mcp_protocol.py 작성 및 통과
- [ ] test_cache.py 작성 및 통과
- [ ] test_tools.py 작성 및 통과

### 8.3 Phase 3 체크리스트

- [ ] MCP Host ↔ Server 통신 테스트 통과
- [ ] API Gateway ↔ MCP Host 통신 테스트 통과
- [ ] JWT 인증 플로우 테스트 통과
- [ ] 권한 체크 테스트 통과
- [ ] 문서 CRUD + ES 동기화 테스트 통과

### 8.4 Phase 4 체크리스트

- [ ] 로그인 → 검색 → 조회 시나리오 통과
- [ ] 문서 생성 → 수정 → 버전 시나리오 통과
- [ ] 권한 거부 시나리오 통과
- [ ] 외부 Agent API 시나리오 통과
- [ ] 감사 로그 시나리오 통과

### 8.5 Phase 5 체크리스트

- [ ] 동시 접속 50명 테스트 통과
- [ ] 검색 응답 500ms 이내
- [ ] 문서 조회 200ms 이내
- [ ] MCP Server 자동 재시작 확인
- [ ] 메모리 누수 없음 확인

---

## 9. 일정 (예상)

| Phase | 작업 | 예상 소요 |
|-------|------|-----------|
| Phase 1 | 불일치 항목 수정 | 1일 |
| Phase 2 | 단위 테스트 | 2일 |
| Phase 3 | 통합 테스트 | 2일 |
| Phase 4 | E2E 테스트 | 1일 |
| Phase 5 | 성능 테스트 | 1일 |
| **총계** | | **7일** |

---

## 10. 참고 문서

- [SR.md](SR.md) - 시스템 설계서
- [patch.md](patch.md) - SR.md 대비 확장 구현 내용
- [docs/README.md](docs/README.md) - 문서 가이드
- [manual/](manual/) - 운영 매뉴얼

---

**Last Updated**: 2026-01-12  
**Author**: MCP Ecosystem Team

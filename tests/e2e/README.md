# End-to-End Tests

## 개요

이 디렉토리는 전체 시스템의 E2E(End-to-End) 테스트를 포함합니다.
사용자 시나리오 기반으로 전체 플로우를 검증합니다.

## 테스트 원칙

- **사용자 관점**: 실제 사용자 시나리오 기반
- **전체 플로우**: API Gateway → MCP Host → MCP Server → DB/ES
- **실제 환경**: 모든 컴포넌트가 실제로 실행 중이어야 함
- **데이터 검증**: 최종 결과뿐 아니라 중간 상태도 검증

## 테스트 시나리오

### 1. 사용자 인증 및 문서 조회
```
[사용자] 로그인 → JWT 발급 → 문서 목록 조회 → 문서 상세 조회
```

### 2. 문서 생성 및 검색
```
[사용자] 로그인 → 문서 생성 → ES 색인 → 검색 → 결과 확인
```

### 3. 권한 기반 접근 제어
```
[Junior 사용자] 로그인 → Confidential 문서 조회 시도 → 403 에러
[Manager 사용자] 로그인 → Confidential 문서 조회 → 성공
```

### 4. 외부 AI Agent 연동
```
[AI Agent] JWT 발급 → Tool 목록 조회 → Tool 실행 → 결과 반환
```

### 5. 감사 로그 기록
```
[사용자] 문서 생성 → 감사 로그 기록 → 로그 조회 → 검증
```

## 테스트 구조

```
e2e/
├── test_user_document_flow.py      # 사용자 문서 관리 플로우
├── test_search_flow.py             # 검색 플로우
├── test_permission_flow.py         # 권한 검증 플로우
├── test_external_agent_flow.py     # 외부 Agent 연동 플로우
├── test_audit_flow.py              # 감사 로그 플로우
└── conftest.py                     # Pytest 설정 및 공통 fixture
```

## 실행 방법

### 1. 전체 시스템 시작

```bash
# 모든 서비스 시작
cd /app/poc/mcps
./scripts/control/start_all.sh

# 서비스 상태 확인
./scripts/manage/status.sh
```

### 2. E2E 테스트 실행

```bash
# 전체 E2E 테스트
pytest tests/e2e/

# 특정 시나리오 테스트
pytest tests/e2e/test_user_document_flow.py

# 상세 로그 포함
pytest tests/e2e/ -v -s --tb=short

# 실패 시 즉시 중단
pytest tests/e2e/ -x
```

### 3. 테스트 후 정리

```bash
# 테스트 데이터 삭제
python scripts/cleanup_test_data.py

# 서비스 종료 (선택)
./scripts/control/stop_all.sh
```

## 작성 가이드

### 테스트 파일명
- `test_<시나리오>_flow.py` 형식
- 예: `test_user_document_flow.py`

### 공통 Fixture (conftest.py)

```python
import pytest
import httpx

@pytest.fixture(scope="session")
def api_base_url():
    """API Gateway URL"""
    return "http://localhost:8000"

@pytest.fixture(scope="session")
def test_user_credentials():
    """테스트 사용자 인증 정보"""
    return {
        "junior": {"user_id": "TEST_J001", "password": "test123"},
        "staff": {"user_id": "TEST_S001", "password": "test123"},
        "manager": {"user_id": "TEST_M001", "password": "test123"},
    }

@pytest.fixture
async def auth_client(api_base_url, test_user_credentials):
    """인증된 HTTP 클라이언트"""
    async with httpx.AsyncClient(base_url=api_base_url) as client:
        # 로그인하여 JWT 획득
        response = await client.post("/api/auth/login", json=test_user_credentials["staff"])
        token = response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        yield client
```

### E2E 테스트 예제

```python
import pytest

@pytest.mark.asyncio
async def test_document_create_and_search_flow(auth_client):
    """문서 생성 후 검색 플로우 E2E 테스트"""
    
    # Step 1: 문서 생성
    doc_data = {
        "title": "E2E 테스트 문서",
        "content": "이것은 E2E 테스트를 위한 문서입니다.",
        "classification": "public",
        "tags": ["test", "e2e"]
    }
    response = await auth_client.post("/api/documents", json=doc_data)
    assert response.status_code == 201
    doc_id = response.json()["doc_id"]
    
    # Step 2: Elasticsearch 색인 대기 (refresh_interval)
    import asyncio
    await asyncio.sleep(2)
    
    # Step 3: 문서 검색
    response = await auth_client.get(
        "/api/search/documents",
        params={"query": "E2E 테스트", "classification": "public"}
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) > 0
    assert any(r["doc_id"] == doc_id for r in results)
    
    # Step 4: 문서 조회
    response = await auth_client.get(f"/api/documents/{doc_id}")
    assert response.status_code == 200
    doc = response.json()
    assert doc["title"] == "E2E 테스트 문서"
    
    # Step 5: 감사 로그 확인
    response = await auth_client.get("/api/audit/my-activity")
    assert response.status_code == 200
    logs = response.json()["logs"]
    # 문서 생성, 검색, 조회 액션 확인
    actions = [log["action"] for log in logs]
    assert "create_document" in actions
    assert "search_documents" in actions
    assert "get_document" in actions
    
    # Cleanup: 문서 삭제
    response = await auth_client.delete(f"/api/documents/{doc_id}")
    assert response.status_code == 200
```

## 주의사항

1. **서비스 실행 필수**: 모든 서비스가 실행 중이어야 함
2. **네트워크 타임아웃**: 실제 네트워크 요청이므로 타임아웃 설정
3. **ES 색인 지연**: `refresh_interval` 고려 (기본 1초)
4. **테스트 데이터 정리**: 각 테스트 후 생성한 데이터 삭제
5. **실행 시간**: 가장 느린 테스트 (수십 초 ~ 수 분)
6. **포트 충돌**: 8000, 8080, 8501 포트 사용 가능 확인

## 필요한 패키지

```txt
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.26.0
selenium==4.15.2  # 선택: 브라우저 UI 테스트
playwright==1.40.0  # 선택: 브라우저 UI 테스트
```

## CI/CD 연동

```yaml
# .github/workflows/e2e-test.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up services
        run: |
          docker-compose up -d
          ./scripts/control/start_all.sh
      - name: Run E2E tests
        run: pytest tests/e2e/ -v
      - name: Cleanup
        run: ./scripts/control/stop_all.sh
```

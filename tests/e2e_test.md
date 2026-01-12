# E2E 테스트 및 CI/CD

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/tests/`  
**목적**: 테스트 전략 및 CI/CD 파이프라인 가이드

***

## 목차

1. [개요](#1-개요)
2. [테스트 전략](#2-테스트-전략)
3. [단위 테스트](#3-단위-테스트)
4. [통합 테스트](#4-통합-테스트)
5. [E2E 테스트](#5-e2e-테스트)
6. [성능 테스트](#6-성능-테스트)
7. [CI/CD 파이프라인](#7-cicd-파이프라인)
8. [배포 자동화](#8-배포-자동화)
9. [모니터링 및 알림](#9-모니터링-및-알림)
10. [테스트 데이터 관리](#10-테스트-데이터-관리)

***

## 1. 개요

### 1.1 테스트 피라미드

```
┌─────────────────────────────────────────┐
│           테스트 피라미드                │
├─────────────────────────────────────────┤
│                                          │
│              ┌─────────┐                │
│              │  E2E    │                │
│              │ Tests   │  10%           │
│              └─────────┘                │
│          ┌───────────────┐              │
│          │ Integration   │              │
│          │    Tests      │  30%         │
│          └───────────────┘              │
│      ┌───────────────────────┐          │
│      │    Unit Tests         │          │
│      │                       │  60%     │
│      └───────────────────────┘          │
│                                          │
│  속도: 빠름 ←────────────→ 느림         │
│  비용: 낮음 ←────────────→ 높음         │
│  안정성: 높음 ←──────────→ 낮음         │
│                                          │
└─────────────────────────────────────────┘
```

### 1.2 테스트 디렉토리 구조

```
/app/poc/mcps/tests/
├── README.md                     # 테스트 가이드
├── pytest.ini                    # Pytest 설정
├── conftest.py                   # 공통 fixture
├── requirements-test.txt         # 테스트 의존성
│
├── unit/                        # 단위 테스트
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_utils.py
│   ├── mcp_host/
│   │   ├── test_client.py
│   │   └── test_connection.py
│   ├── api_gateway/
│   │   ├── test_routes.py
│   │   ├── test_middleware.py
│   │   └── test_auth.py
│   └── mcp_servers/
│       ├── test_core_tools.py
│       ├── test_search_tools.py
│       └── test_analytics_tools.py
│
├── integration/                 # 통합 테스트
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_elasticsearch.py
│   ├── test_redis.py
│   ├── test_api_flow.py
│   └── test_mcp_integration.py
│
├── e2e/                        # E2E 테스트
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_user_workflows.py
│   ├── test_document_lifecycle.py
│   ├── test_search_flow.py
│   └── test_admin_operations.py
│
├── performance/                # 성능 테스트
│   ├── __init__.py
│   ├── locustfile.py
│   ├── test_load.py
│   ├── test_stress.py
│   └── test_spike.py
│
├── fixtures/                   # 테스트 데이터
│   ├── __init__.py
│   ├── users.json
│   ├── documents.json
│   └── search_queries.json
│
├── helpers/                    # 테스트 헬퍼
│   ├── __init__.py
│   ├── api_client.py
│   ├── database_helper.py
│   ├── mock_data.py
│   └── assertions.py
│
└── reports/                    # 테스트 리포트
    ├── coverage/
    ├── pytest/
    └── performance/
```

### 1.3 테스트 도구

| 도구 | 용도 | 설치 |
|-----|------|------|
| **pytest** | 테스트 프레임워크 | `pip install pytest` |
| **pytest-asyncio** | 비동기 테스트 | `pip install pytest-asyncio` |
| **pytest-cov** | 코드 커버리지 | `pip install pytest-cov` |
| **pytest-mock** | 모킹 | `pip install pytest-mock` |
| **httpx** | HTTP 클라이언트 | `pip install httpx` |
| **faker** | 가짜 데이터 생성 | `pip install faker` |
| **locust** | 부하 테스트 | `pip install locust` |
| **selenium** | 브라우저 자동화 | `pip install selenium` |

***

## 2. 테스트 전략

### 2.1 테스트 원칙

```python
"""
테스트 작성 원칙

1. FIRST 원칙
   - Fast: 빠르게 실행
   - Independent: 독립적으로 실행
   - Repeatable: 반복 가능
   - Self-Validating: 자체 검증
   - Timely: 적시에 작성

2. AAA 패턴
   - Arrange: 준비
   - Act: 실행
   - Assert: 검증

3. Given-When-Then
   - Given: 주어진 상황
   - When: 특정 동작
   - Then: 예상 결과
"""
```

### 2.2 테스트 커버리지 목표

```yaml
# 테스트 커버리지 목표

전체 커버리지: > 80%

모듈별 목표:
  models: > 90%
  services: > 85%
  utils: > 80%
  routes: > 75%
  
중요 영역:
  인증/권한: 100%
  보안 관련: 100%
  결제/중요 비즈니스 로직: 95%
```

### 2.3 테스트 환경

```python
# /app/poc/mcps/tests/conftest.py
"""Pytest 전역 설정 및 Fixture"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.config import settings

# ==============================================
# 테스트 Database 설정
# ==============================================

TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    """테스트용 Database 엔진"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db(test_engine):
    """테스트용 Database 세션"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================================
# API 클라이언트
# ==============================================

@pytest.fixture(scope="module")
def test_client():
    """테스트용 API 클라이언트"""
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
async def async_client():
    """비동기 테스트 클라이언트"""
    import httpx
    async with httpx.AsyncClient(
        app=app,
        base_url="http://test"
    ) as client:
        yield client

# ==============================================
# 테스트 데이터
# ==============================================

@pytest.fixture
def test_user():
    """테스트 사용자"""
    return {
        "id": "test-user-001",
        "username": "testuser",
        "email": "test@example.com",
        "role": "user"
    }

@pytest.fixture
def test_admin():
    """테스트 관리자"""
    return {
        "id": "test-admin-001",
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin"
    }

@pytest.fixture
def test_document():
    """테스트 문서"""
    return {
        "title": "테스트 문서",
        "content": "테스트 내용입니다.",
        "classification": "internal",
        "category": "테스트",
        "tags": ["test", "sample"]
    }

# ==============================================
# Mock 설정
# ==============================================

@pytest.fixture
def mock_elasticsearch(mocker):
    """Elasticsearch Mock"""
    mock_es = mocker.Mock()
    mock_es.search.return_value = {
        "hits": {
            "total": {"value": 0},
            "hits": []
        }
    }
    return mock_es

@pytest.fixture
def mock_redis(mocker):
    """Redis Mock"""
    mock_redis = mocker.Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    return mock_redis

# ==============================================
# 이벤트 루프
# ==============================================

@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

***

## 3. 단위 테스트

### 3.1 모델 테스트

```python
# /app/poc/mcps/tests/unit/test_models.py
"""모델 단위 테스트"""

import pytest
from datetime import datetime
from app.models.document import Document, DocumentCreate
from app.models.user import User

def test_document_creation():
    """문서 모델 생성 테스트"""
    # Given
    doc_data = DocumentCreate(
        title="테스트 문서",
        content="테스트 내용",
        classification="internal",
        author_id="user-001"
    )
    
    # When
    document = Document(**doc_data.dict(), id="DOC-001")
    
    # Then
    assert document.title == "테스트 문서"
    assert document.classification == "internal"
    assert document.author_id == "user-001"

def test_document_validation_invalid_classification():
    """잘못된 보안 등급 검증 테스트"""
    # Given
    invalid_data = {
        "title": "테스트",
        "content": "내용",
        "classification": "invalid",  # 잘못된 값
        "author_id": "user-001"
    }
    
    # When & Then
    with pytest.raises(ValueError):
        DocumentCreate(**invalid_data)

def test_document_dict_method():
    """문서 dict 변환 테스트"""
    # Given
    document = Document(
        id="DOC-001",
        title="테스트",
        content="내용",
        classification="internal",
        author_id="user-001"
    )
    
    # When
    doc_dict = document.dict()
    
    # Then
    assert "id" in doc_dict
    assert doc_dict["title"] == "테스트"
    assert isinstance(doc_dict, dict)

def test_user_password_hashing():
    """사용자 비밀번호 해싱 테스트"""
    # Given
    user = User(
        username="testuser",
        email="test@example.com"
    )
    plain_password = "password123"
    
    # When
    user.set_password(plain_password)
    
    # Then
    assert user.password_hash != plain_password
    assert user.verify_password(plain_password) is True
    assert user.verify_password("wrongpassword") is False
```

### 3.2 서비스 테스트

```python
# /app/poc/mcps/tests/unit/test_services.py
"""서비스 레이어 단위 테스트"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.document_service import DocumentService
from app.models.document import DocumentCreate

@pytest.mark.asyncio
async def test_create_document_success():
    """문서 생성 성공 테스트"""
    # Given
    service = DocumentService()
    doc_data = DocumentCreate(
        title="테스트 문서",
        content="내용",
        classification="internal",
        author_id="user-001"
    )
    
    # When
    with patch.object(service, 'repository') as mock_repo:
        mock_repo.create.return_value = {
            "id": "DOC-001",
            **doc_data.dict()
        }
        
        result = await service.create_document(doc_data)
    
    # Then
    assert result["id"] == "DOC-001"
    assert result["title"] == "테스트 문서"
    mock_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_get_document_not_found():
    """존재하지 않는 문서 조회 테스트"""
    # Given
    service = DocumentService()
    doc_id = "NON-EXISTENT"
    
    # When
    with patch.object(service, 'repository') as mock_repo:
        mock_repo.get.return_value = None
        
        result = await service.get_document(doc_id)
    
    # Then
    assert result is None

@pytest.mark.asyncio
async def test_update_document_permission_check():
    """문서 수정 권한 확인 테스트"""
    # Given
    service = DocumentService()
    doc_id = "DOC-001"
    user_id = "unauthorized-user"
    
    # When
    with patch.object(service, 'check_write_permission') as mock_perm:
        mock_perm.return_value = False
        
        with pytest.raises(PermissionError):
            await service.update_document(doc_id, {}, user_id)
    
    # Then
    mock_perm.assert_called_once_with(doc_id, user_id)

@pytest.mark.asyncio
async def test_search_with_cache():
    """캐시를 사용한 검색 테스트"""
    # Given
    service = DocumentService()
    query = "테스트"
    cached_result = [{"id": "DOC-001", "title": "캐시된 결과"}]
    
    # When
    with patch.object(service, 'cache') as mock_cache, \
         patch.object(service, 'repository') as mock_repo:
        
        mock_cache.get.return_value = cached_result
        
        result = await service.search(query)
    
    # Then
    assert result == cached_result
    mock_cache.get.assert_called_once()
    mock_repo.search.assert_not_called()  # DB 조회 안함
```

### 3.3 유틸리티 테스트

```python
# /app/poc/mcps/tests/unit/test_utils.py
"""유틸리티 함수 단위 테스트"""

import pytest
from app.utils.text import sanitize_input, truncate_text
from app.utils.validation import validate_email, validate_phone
from app.utils.encryption import encrypt, decrypt

def test_sanitize_input_removes_html():
    """HTML 태그 제거 테스트"""
    # Given
    text = "<script>alert('xss')</script>안전한 텍스트"
    
    # When
    result = sanitize_input(text)
    
    # Then
    assert "<script>" not in result
    assert "안전한 텍스트" in result

def test_truncate_text_long_text():
    """긴 텍스트 자르기 테스트"""
    # Given
    text = "a" * 500
    max_length = 100
    
    # When
    result = truncate_text(text, max_length)
    
    # Then
    assert len(result) <= max_length + 3  # "..." 포함
    assert result.endswith("...")

def test_truncate_text_short_text():
    """짧은 텍스트는 그대로 반환"""
    # Given
    text = "짧은 텍스트"
    
    # When
    result = truncate_text(text, 100)
    
    # Then
    assert result == text

@pytest.mark.parametrize("email,expected", [
    ("test@example.com", True),
    ("user.name@domain.co.kr", True),
    ("invalid.email", False),
    ("@nodomain.com", False),
    ("no@domain", False),
])
def test_validate_email(email, expected):
    """이메일 검증 파라미터 테스트"""
    assert validate_email(email) == expected

def test_encrypt_decrypt_round_trip():
    """암호화/복호화 왕복 테스트"""
    # Given
    plaintext = "비밀 메시지"
    key = "encryption-key-123"
    
    # When
    encrypted = encrypt(plaintext, key)
    decrypted = decrypt(encrypted, key)
    
    # Then
    assert encrypted != plaintext
    assert decrypted == plaintext
```

### 3.4 API 라우트 테스트

```python
# /app/poc/mcps/tests/unit/api_gateway/test_routes.py
"""API 라우트 단위 테스트"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

def test_health_check(test_client):
    """헬스체크 엔드포인트 테스트"""
    # When
    response = test_client.get("/health")
    
    # Then
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_document_success(test_client, test_user):
    """문서 생성 API 성공 테스트"""
    # Given
    doc_data = {
        "title": "API 테스트 문서",
        "content": "내용",
        "classification": "internal"
    }
    
    # When
    with patch('app.services.document_service.DocumentService.create_document') as mock_create:
        mock_create.return_value = {"id": "DOC-001", **doc_data}
        
        response = test_client.post(
            "/api/v1/documents",
            json=doc_data,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
    
    # Then
    assert response.status_code == 201
    assert response.json()["id"] == "DOC-001"

def test_create_document_unauthorized(test_client):
    """인증 없이 문서 생성 시도"""
    # Given
    doc_data = {
        "title": "테스트",
        "content": "내용",
        "classification": "internal"
    }
    
    # When
    response = test_client.post("/api/v1/documents", json=doc_data)
    
    # Then
    assert response.status_code == 401

def test_get_document_not_found(test_client, test_user):
    """존재하지 않는 문서 조회"""
    # When
    with patch('app.services.document_service.DocumentService.get_document') as mock_get:
        mock_get.return_value = None
        
        response = test_client.get(
            "/api/v1/documents/NON-EXISTENT",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
    
    # Then
    assert response.status_code == 404

@pytest.mark.parametrize("invalid_data", [
    {"title": "", "content": "내용", "classification": "internal"},  # 빈 제목
    {"title": "제목", "content": "", "classification": "internal"},  # 빈 내용
    {"title": "제목", "content": "내용", "classification": "invalid"},  # 잘못된 등급
])
def test_create_document_validation_error(test_client, test_user, invalid_data):
    """문서 생성 검증 오류 테스트"""
    # When
    response = test_client.post(
        "/api/v1/documents",
        json=invalid_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Then
    assert response.status_code == 422  # Validation Error
```

***

## 4. 통합 테스트

### 4.1 Database 통합 테스트

```python
# /app/poc/mcps/tests/integration/test_database.py
"""Database 통합 테스트"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository

@pytest.fixture(scope="module")
def db_session():
    """테스트용 DB 세션"""
    engine = create_engine("sqlite:///./test_integration.db")
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_document_crud_operations(db_session):
    """문서 CRUD 전체 흐름 테스트"""
    repo = DocumentRepository(db_session)
    
    # Create
    doc_data = {
        "title": "통합 테스트 문서",
        "content": "내용",
        "classification": "internal",
        "author_id": "user-001"
    }
    created_doc = await repo.create(doc_data)
    assert created_doc.id is not None
    
    # Read
    retrieved_doc = await repo.get(created_doc.id)
    assert retrieved_doc.title == "통합 테스트 문서"
    
    # Update
    updated_doc = await repo.update(
        created_doc.id,
        {"title": "수정된 제목"}
    )
    assert updated_doc.title == "수정된 제목"
    
    # Delete
    await repo.delete(created_doc.id)
    deleted_doc = await repo.get(created_doc.id)
    assert deleted_doc is None

@pytest.mark.asyncio
async def test_transaction_rollback(db_session):
    """트랜잭션 롤백 테스트"""
    repo = DocumentRepository(db_session)
    
    try:
        # 정상 문서 생성
        doc1 = await repo.create({
            "title": "문서 1",
            "content": "내용",
            "classification": "internal",
            "author_id": "user-001"
        })
        
        # 에러 발생 (잘못된 데이터)
        await repo.create({
            "title": "",  # 빈 제목
            "content": "내용",
            "classification": "internal",
            "author_id": "user-001"
        })
        
        db_session.commit()
    except Exception:
        db_session.rollback()
    
    # 롤백 후 확인
    docs = await repo.list()
    assert len(docs) == 0  # 모두 롤백됨
```

### 4.2 Elasticsearch 통합 테스트

```python
# /app/poc/mcps/tests/integration/test_elasticsearch.py
"""Elasticsearch 통합 테스트"""

import pytest
from elasticsearch import Elasticsearch
from app.services.search_service import SearchService

@pytest.fixture(scope="module")
def es_client():
    """테스트용 ES 클라이언트"""
    client = Elasticsearch(["http://localhost:9200"])
    
    # 테스트 인덱스 생성
    index_name = "test_documents"
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
    
    client.indices.create(
        index=index_name,
        body={
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "category": {"type": "keyword"}
                }
            }
        }
    )
    
    yield client
    
    # 정리
    client.indices.delete(index=index_name)

@pytest.mark.asyncio
async def test_index_and_search(es_client):
    """인덱싱 및 검색 테스트"""
    service = SearchService(es_client, index="test_documents")
    
    # 문서 인덱싱
    doc = {
        "id": "DOC-001",
        "title": "Elasticsearch 테스트",
        "content": "검색 기능 테스트 문서입니다.",
        "category": "테스트"
    }
    
    await service.index_document(doc)
    
    # 인덱스 새로고침
    es_client.indices.refresh(index="test_documents")
    
    # 검색
    results = await service.search("Elasticsearch")
    
    assert len(results) > 0
    assert results[0]["title"] == "Elasticsearch 테스트"

@pytest.mark.asyncio
async def test_bulk_indexing(es_client):
    """대량 인덱싱 테스트"""
    service = SearchService(es_client, index="test_documents")
    
    # 여러 문서 생성
    docs = [
        {
            "id": f"DOC-{i:03d}",
            "title": f"문서 {i}",
            "content": f"내용 {i}",
            "category": "bulk"
        }
        for i in range(100)
    ]
    
    # 대량 인덱싱
    await service.bulk_index(docs)
    
    # 확인
    es_client.indices.refresh(index="test_documents")
    results = await service.search("bulk", limit=100)
    
    assert len(results) == 100
```

### 4.3 API 플로우 통합 테스트

```python
# /app/poc/mcps/tests/integration/test_api_flow.py
"""API 전체 플로우 통합 테스트"""

import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_complete_document_workflow(test_client):
    """완전한 문서 워크플로우 테스트"""
    
    # 1. 사용자 로그인
    login_response = test_client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 문서 생성
    create_response = test_client.post(
        "/api/v1/documents",
        json={
            "title": "통합 테스트 문서",
            "content": "전체 플로우 테스트",
            "classification": "internal",
            "category": "테스트"
        },
        headers=headers
    )
    assert create_response.status_code == 201
    doc_id = create_response.json()["id"]
    
    # 3. 문서 조회
    get_response = test_client.get(
        f"/api/v1/documents/{doc_id}",
        headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "통합 테스트 문서"
    
    # 4. 문서 검색
    search_response = test_client.get(
        "/api/v1/search?q=통합테스트",
        headers=headers
    )
    assert search_response.status_code == 200
    results = search_response.json()["results"]
    assert any(r["id"] == doc_id for r in results)
    
    # 5. 문서 수정
    update_response = test_client.put(
        f"/api/v1/documents/{doc_id}",
        json={"title": "수정된 제목"},
        headers=headers
    )
    assert update_response.status_code == 200
    
    # 6. 수정 확인
    updated_doc = test_client.get(
        f"/api/v1/documents/{doc_id}",
        headers=headers
    )
    assert updated_doc.json()["title"] == "수정된 제목"
    
    # 7. 문서 삭제
    delete_response = test_client.delete(
        f"/api/v1/documents/{doc_id}",
        headers=headers
    )
    assert delete_response.status_code == 204
    
    # 8. 삭제 확인
    not_found_response = test_client.get(
        f"/api/v1/documents/{doc_id}",
        headers=headers
    )
    assert not_found_response.status_code == 404
```

***

## 5. E2E 테스트

### 5.1 E2E 테스트 설정

```python
# /app/poc/mcps/tests/e2e/conftest.py
"""E2E 테스트 설정"""

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

@pytest.fixture(scope="module")
def browser():
    """Selenium 브라우저"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    
    yield driver
    
    driver.quit()

@pytest.fixture
def wait(browser):
    """WebDriverWait"""
    return WebDriverWait(browser, 10)

@pytest.fixture
def base_url():
    """기본 URL"""
    return "http://localhost:3000"
```

### 5.2 사용자 워크플로우 E2E 테스트

```python
# /app/poc/mcps/tests/e2e/test_user_workflows.py
"""사용자 워크플로우 E2E 테스트"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def test_user_login_and_logout(browser, wait, base_url):
    """사용자 로그인/로그아웃 E2E"""
    
    # 1. 로그인 페이지 접속
    browser.get(f"{base_url}/login")
    assert "로그인" in browser.title
    
    # 2. 로그인 폼 입력
    username_input = browser.find_element(By.ID, "username")
    password_input = browser.find_element(By.ID, "password")
    
    username_input.send_keys("testuser")
    password_input.send_keys("password123")
    
    # 3. 로그인 버튼 클릭
    login_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()
    
    # 4. 대시보드로 리다이렉트 확인
    wait.until(EC.url_contains("/dashboard"))
    assert "/dashboard" in browser.current_url
    
    # 5. 환영 메시지 확인
    welcome_msg = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".welcome-message"))
    )
    assert "testuser" in welcome_msg.text
    
    # 6. 로그아웃
    logout_button = browser.find_element(By.ID, "logout-button")
    logout_button.click()
    
    # 7. 로그인 페이지로 리다이렉트 확인
    wait.until(EC.url_contains("/login"))
    assert "/login" in browser.current_url

def test_create_document_flow(browser, wait, base_url):
    """문서 생성 전체 플로우 E2E"""
    
    # 1. 로그인 (재사용 가능한 헬퍼 함수로 만들어도 좋음)
    browser.get(f"{base_url}/login")
    browser.find_element(By.ID, "username").send_keys("testuser")
    browser.find_element(By.ID, "password").send_keys("password123")
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    wait.until(EC.url_contains("/dashboard"))
    
    # 2. 새 문서 버튼 클릭
    new_doc_button = wait.until(
        EC.element_to_be_clickable((By.ID, "new-document-button"))
    )
    new_doc_button.click()
    
    # 3. 문서 작성 폼 작성
    wait.until(EC.url_contains("/documents/new"))
    
    browser.find_element(By.ID, "title").send_keys("E2E 테스트 문서")
    browser.find_element(By.ID, "content").send_keys("E2E 테스트 내용입니다.")
    
    # 보안 등급 선택
    from selenium.webdriver.support.select import Select
    classification_select = Select(browser.find_element(By.ID, "classification"))
    classification_select.select_by_value("internal")
    
    # 4. 저장 버튼 클릭
    save_button = browser.find_element(By.ID, "save-button")
    save_button.click()
    
    # 5. 성공 메시지 확인
    success_msg = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message"))
    )
    assert "생성되었습니다" in success_msg.text
    
    # 6. 문서 상세 페이지로 이동 확인
    wait.until(EC.url_contains("/documents/"))
    
    # 7. 문서 내용 확인
    title_element = browser.find_element(By.CSS_SELECTOR, "h1.document-title")
    assert title_element.text == "E2E 테스트 문서"

def test_search_flow(browser, wait, base_url):
    """검색 플로우 E2E"""
    
    # 로그인
    browser.get(f"{base_url}/login")
    browser.find_element(By.ID, "username").send_keys("testuser")
    browser.find_element(By.ID, "password").send_keys("password123")
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    wait.until(EC.url_contains("/dashboard"))
    
    # 1. 검색창에 검색어 입력
    search_input = browser.find_element(By.ID, "search-input")
    search_input.send_keys("테스트")
    search_input.submit()
    
    # 2. 검색 결과 페이지 확인
    wait.until(EC.url_contains("/search"))
    
    # 3. 검색 결과 확인
    results = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".search-result-item"))
    )
    assert len(results) > 0
    
    # 4. 첫 번째 결과 클릭
    results[0].click()
    
    # 5. 문서 상세 페이지로 이동 확인
    wait.until(EC.url_contains("/documents/"))
```

### 5.3 관리자 기능 E2E 테스트

```python
# /app/poc/mcps/tests/e2e/test_admin_operations.py
"""관리자 기능 E2E 테스트"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def test_admin_dashboard_access(browser, wait, base_url):
    """관리자 대시보드 접근 E2E"""
    
    # 1. 관리자 로그인
    browser.get(f"{base_url}/login")
    browser.find_element(By.ID, "username").send_keys("admin")
    browser.find_element(By.ID, "password").send_keys("admin123")
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    wait.until(EC.url_contains("/dashboard"))
    
    # 2. 관리자 메뉴 클릭
    admin_menu = wait.until(
        EC.element_to_be_clickable((By.ID, "admin-menu"))
    )
    admin_menu.click()
    
    # 3. 관리자 페이지로 이동
    admin_link = wait.until(
        EC.element_to_be_clickable((By.LINK_TEXT, "시스템 관리"))
    )
    admin_link.click()
    
    # 4. 관리자 대시보드 확인
    wait.until(EC.url_contains("/admin"))
    
    # 통계 위젯 확인
    stats_widgets = browser.find_elements(By.CSS_SELECTOR, ".stat-widget")
    assert len(stats_widgets) >= 3  # 최소 3개의 통계 위젯

def test_user_management(browser, wait, base_url):
    """사용자 관리 E2E"""
    
    # 관리자 로그인 및 사용자 관리 페이지 이동
    browser.get(f"{base_url}/login")
    browser.find_element(By.ID, "username").send_keys("admin")
    browser.find_element(By.ID, "password").send_keys("admin123")
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    wait.until(EC.url_contains("/dashboard"))
    browser.get(f"{base_url}/admin/users")
    
    # 1. 사용자 목록 확인
    users_table = wait.until(
        EC.presence_of_element_located((By.ID, "users-table"))
    )
    
    # 2. 새 사용자 추가 버튼 클릭
    add_user_button = browser.find_element(By.ID, "add-user-button")
    add_user_button.click()
    
    # 3. 사용자 정보 입력
    wait.until(EC.presence_of_element_located((By.ID, "user-form")))
    
    browser.find_element(By.ID, "new-username").send_keys("newuser")
    browser.find_element(By.ID, "new-email").send_keys("newuser@example.com")
    browser.find_element(By.ID, "new-password").send_keys("password123")
    
    # 4. 저장
    save_button = browser.find_element(By.ID, "save-user-button")
    save_button.click()
    
    # 5. 성공 메시지 확인
    success_msg = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message"))
    )
    assert "추가되었습니다" in success_msg.text
```


## 6. 성능 테스트

### 6.1 Locust 부하 테스트

```python
# /app/poc/mcps/tests/performance/locustfile.py
"""Locust 부하 테스트"""

from locust import HttpUser, task, between, events
import json
import random

class MCPUser(HttpUser):
    """MCP 시스템 사용자 시뮬레이션"""
    
    wait_time = between(1, 3)  # 1-3초 대기
    
    def on_start(self):
        """테스트 시작 시 실행 (로그인)"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "password123"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(5)
    def view_dashboard(self):
        """대시보드 조회 (가중치 5)"""
        self.client.get("/api/v1/dashboard", headers=self.headers)
    
    @task(3)
    def search_documents(self):
        """문서 검색 (가중치 3)"""
        queries = ["테스트", "보안", "정책", "가이드", "매뉴얼"]
        query = random.choice(queries)
        
        self.client.get(
            f"/api/v1/search?q={query}",
            headers=self.headers,
            name="/api/v1/search"
        )
    
    @task(2)
    def get_document(self):
        """문서 조회 (가중치 2)"""
        doc_id = f"DOC-{random.randint(1, 1000):04d}"
        
        self.client.get(
            f"/api/v1/documents/{doc_id}",
            headers=self.headers,
            name="/api/v1/documents/[id]"
        )
    
    @task(1)
    def create_document(self):
        """문서 생성 (가중치 1)"""
        doc_data = {
            "title": f"부하 테스트 문서 {random.randint(1, 10000)}",
            "content": "성능 테스트를 위한 문서입니다.",
            "classification": random.choice(["public", "internal", "confidential"]),
            "category": "테스트"
        }
        
        self.client.post(
            "/api/v1/documents",
            json=doc_data,
            headers=self.headers
        )
    
    @task(1)
    def update_document(self):
        """문서 수정 (가중치 1)"""
        doc_id = f"DOC-{random.randint(1, 1000):04d}"
        
        self.client.put(
            f"/api/v1/documents/{doc_id}",
            json={"title": f"수정된 문서 {random.randint(1, 10000)}"},
            headers=self.headers,
            name="/api/v1/documents/[id]"
        )
    
    @task(1)
    def list_documents(self):
        """문서 목록 조회 (가중치 1)"""
        self.client.get(
            "/api/v1/documents?limit=20",
            headers=self.headers
        )

class AdminUser(HttpUser):
    """관리자 사용자 시뮬레이션"""
    
    wait_time = between(2, 5)
    weight = 1  # 일반 사용자 대비 10%
    
    def on_start(self):
        """관리자 로그인"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def view_analytics(self):
        """분석 데이터 조회"""
        self.client.get("/api/v1/analytics/statistics", headers=self.headers)
    
    @task(2)
    def generate_report(self):
        """리포트 생성"""
        self.client.post(
            "/api/v1/analytics/reports",
            json={"report_type": "usage", "period": "week"},
            headers=self.headers
        )
    
    @task(1)
    def manage_users(self):
        """사용자 관리"""
        self.client.get("/api/v1/admin/users", headers=self.headers)

# 이벤트 핸들러
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """테스트 시작 시"""
    print("=" * 50)
    print("  부하 테스트 시작")
    print("=" * 50)

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """테스트 종료 시"""
    print("=" * 50)
    print("  부하 테스트 종료")
    print("=" * 50)

# 실행 방법:
# locust -f locustfile.py --host=http://localhost:8080
# 웹 UI: http://localhost:8089
```

### 6.2 성능 테스트 시나리오

```python
# /app/poc/mcps/tests/performance/test_load.py
"""부하 테스트 시나리오"""

import pytest
import asyncio
import aiohttp
from datetime import datetime
import statistics

class LoadTestScenarios:
    """부하 테스트 시나리오"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
        self.results = []
    
    async def make_request(self, session, method, url, **kwargs):
        """단일 요청"""
        start = datetime.now()
        
        try:
            async with session.request(method, url, **kwargs) as response:
                await response.text()
                elapsed = (datetime.now() - start).total_seconds()
                
                return {
                    "status": response.status,
                    "elapsed": elapsed,
                    "success": 200 <= response.status < 300
                }
        except Exception as e:
            elapsed = (datetime.now() - start).total_seconds()
            return {
                "status": 0,
                "elapsed": elapsed,
                "success": False,
                "error": str(e)
            }
    
    async def concurrent_requests(
        self,
        num_requests: int,
        endpoint: str,
        method: str = "GET"
    ):
        """동시 요청 테스트"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            url = f"{self.base_url}{endpoint}"
            
            tasks = [
                self.make_request(session, method, url)
                for _ in range(num_requests)
            ]
            
            results = await asyncio.gather(*tasks)
            return results
    
    def analyze_results(self, results):
        """결과 분석"""
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        elapsed_times = [r["elapsed"] for r in successful]
        
        analysis = {
            "total_requests": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) * 100,
            "avg_response_time": statistics.mean(elapsed_times) if elapsed_times else 0,
            "min_response_time": min(elapsed_times) if elapsed_times else 0,
            "max_response_time": max(elapsed_times) if elapsed_times else 0,
            "median_response_time": statistics.median(elapsed_times) if elapsed_times else 0,
            "p95_response_time": statistics.quantiles(elapsed_times, n=20)[18] if len(elapsed_times) >= 20 else 0,
            "p99_response_time": statistics.quantiles(elapsed_times, n=100)[98] if len(elapsed_times) >= 100 else 0
        }
        
        return analysis

@pytest.mark.asyncio
async def test_search_load():
    """검색 API 부하 테스트"""
    load_test = LoadTestScenarios(
        base_url="http://localhost:8080",
        token="test-token"
    )
    
    # 100개 동시 요청
    results = await load_test.concurrent_requests(
        num_requests=100,
        endpoint="/api/v1/search?q=테스트"
    )
    
    analysis = load_test.analyze_results(results)
    
    # 성능 기준 검증
    assert analysis["success_rate"] >= 95, "성공률 95% 이상"
    assert analysis["avg_response_time"] < 1.0, "평균 응답 시간 1초 이하"
    assert analysis["p95_response_time"] < 2.0, "95 percentile 2초 이하"
    
    print("\n검색 API 부하 테스트 결과:")
    print(f"  총 요청: {analysis['total_requests']}")
    print(f"  성공: {analysis['successful']}")
    print(f"  실패: {analysis['failed']}")
    print(f"  성공률: {analysis['success_rate']:.2f}%")
    print(f"  평균 응답: {analysis['avg_response_time']:.3f}초")
    print(f"  P95: {analysis['p95_response_time']:.3f}초")

@pytest.mark.asyncio
async def test_spike_load():
    """스파이크 부하 테스트 (급격한 트래픽 증가)"""
    load_test = LoadTestScenarios(
        base_url="http://localhost:8080",
        token="test-token"
    )
    
    # 점진적 증가
    for num_users in [10, 50, 100, 200, 100, 50]:
        print(f"\n동시 사용자: {num_users}")
        
        results = await load_test.concurrent_requests(
            num_requests=num_users,
            endpoint="/api/v1/dashboard"
        )
        
        analysis = load_test.analyze_results(results)
        
        print(f"  성공률: {analysis['success_rate']:.2f}%")
        print(f"  평균 응답: {analysis['avg_response_time']:.3f}초")
        
        # 짧은 대기
        await asyncio.sleep(1)
```

### 6.3 성능 테스트 실행 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/tests/performance/run_performance_tests.sh
# 성능 테스트 실행

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="${SCRIPT_DIR}/reports"

echo "=========================================="
echo "  성능 테스트 시작"
echo "=========================================="

# 리포트 디렉토리 생성
mkdir -p "${REPORT_DIR}"

# ==============================================
# 1. 부하 테스트 (Locust)
# ==============================================

echo ""
echo "[1/3] 부하 테스트 (Locust)..."

# Headless 모드로 실행
locust -f "${SCRIPT_DIR}/locustfile.py" \
    --host=http://localhost:8080 \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --html="${REPORT_DIR}/locust_report.html" \
    --csv="${REPORT_DIR}/locust"

echo "부하 테스트 완료"

# ==============================================
# 2. 스트레스 테스트
# ==============================================

echo ""
echo "[2/3] 스트레스 테스트..."

pytest "${SCRIPT_DIR}/test_load.py" \
    -v \
    --html="${REPORT_DIR}/stress_test_report.html" \
    --self-contained-html

echo "스트레스 테스트 완료"

# ==============================================
# 3. API 응답 시간 측정
# ==============================================

echo ""
echo "[3/3] API 응답 시간 측정..."

# Apache Bench
ab -n 1000 -c 10 -g "${REPORT_DIR}/ab_results.tsv" \
    http://localhost:8080/api/v1/health > "${REPORT_DIR}/ab_report.txt"

echo "API 응답 시간 측정 완료"

# ==============================================
# 결과 요약
# ==============================================

echo ""
echo "=========================================="
echo "  성능 테스트 완료"
echo "=========================================="
echo ""
echo "리포트 위치: ${REPORT_DIR}"
echo "  - Locust 리포트: locust_report.html"
echo "  - 스트레스 테스트: stress_test_report.html"
echo "  - Apache Bench: ab_report.txt"
echo ""
```

***

## 7. CI/CD 파이프라인

### 7.1 GitHub Actions 워크플로우

```yaml
# /app/poc/mcps/.github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '18'

jobs:
  # ==============================================
  # 코드 품질 검사
  # ==============================================
  lint:
    name: Lint & Code Quality
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Cache pip packages
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
      
      - name: Install dependencies
        run: |
          pip install flake8 black isort mypy pylint
          pip install -r requirements.txt
      
      - name: Run Black (Code formatting)
        run: black --check .
      
      - name: Run isort (Import sorting)
        run: isort --check-only .
      
      - name: Run flake8 (Linting)
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
      
      - name: Run mypy (Type checking)
        run: mypy app/ --ignore-missing-imports
      
      - name: Run pylint (Static analysis)
        run: pylint app/ --fail-under=8.0

  # ==============================================
  # 단위 테스트
  # ==============================================
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ \
            -v \
            --cov=app \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
      
      - name: Archive coverage reports
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: htmlcov/

  # ==============================================
  # 통합 테스트
  # ==============================================
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    
    services:
      mariadb:
        image: mariadb:10.11
        env:
          MYSQL_ROOT_PASSWORD: test_password
          MYSQL_DATABASE: test_db
        ports:
          - 3306:3306
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: --health-cmd="redis-cli ping" --health-interval=10s --health-timeout=5s --health-retries=3
      
      elasticsearch:
        image: elasticsearch:8.11.0
        env:
          discovery.type: single-node
          xpack.security.enabled: false
        ports:
          - 9200:9200
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      
      - name: Wait for services
        run: |
          sleep 30
          curl -f http://localhost:9200/_cluster/health || exit 1
      
      - name: Run integration tests
        env:
          DB_HOST: localhost
          DB_PORT: 3306
          DB_PASSWORD: test_password
          REDIS_HOST: localhost
          ES_HOST: localhost
        run: |
          pytest tests/integration/ -v --tb=short

  # ==============================================
  # E2E 테스트
  # ==============================================
  e2e-tests:
    name: E2E Tests
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
      
      - name: Install Chrome
        run: |
          wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
          sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
          sudo apt-get update
          sudo apt-get install -y google-chrome-stable
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
          npm install -g playwright
          playwright install
      
      - name: Start application
        run: |
          # 백그라운드에서 앱 시작
          python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 &
          sleep 10
      
      - name: Run E2E tests
        run: |
          pytest tests/e2e/ -v --html=e2e-report.html --self-contained-html
      
      - name: Upload E2E test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-report
          path: e2e-report.html

  # ==============================================
  # 보안 스캔
  # ==============================================
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install safety bandit pip-audit
          pip install -r requirements.txt
      
      - name: Run Safety (Dependency check)
        run: safety check --json
      
      - name: Run Bandit (Security issues)
        run: bandit -r app/ -f json -o bandit-report.json
      
      - name: Run pip-audit (Vulnerability scan)
        run: pip-audit
      
      - name: Upload security reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json

  # ==============================================
  # Docker 이미지 빌드
  # ==============================================
  build-docker:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: [lint, unit-tests, integration-tests]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push API Gateway
        uses: docker/build-push-action@v4
        with:
          context: ./api-gateway
          push: true
          tags: |
            myorg/mcps-api-gateway:${{ github.sha }}
            myorg/mcps-api-gateway:latest
          cache-from: type=registry,ref=myorg/mcps-api-gateway:latest
          cache-to: type=inline
      
      - name: Build and push MCP Host
        uses: docker/build-push-action@v4
        with:
          context: ./mcp-host
          push: true
          tags: |
            myorg/mcps-mcp-host:${{ github.sha }}
            myorg/mcps-mcp-host:latest
      
      - name: Build and push Frontend
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          tags: |
            myorg/mcps-frontend:${{ github.sha }}
            myorg/mcps-frontend:latest
```

### 7.2 GitLab CI/CD 파이프라인

```yaml
# /app/poc/mcps/.gitlab-ci.yml
stages:
  - lint
  - test
  - security
  - build
  - deploy

variables:
  PYTHON_VERSION: "3.11"
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: ""

# ==============================================
# 템플릿
# ==============================================
.python_template: &python_template
  image: python:${PYTHON_VERSION}
  before_script:
    - pip install --upgrade pip
    - pip install -r requirements.txt

# ==============================================
# 린트
# ==============================================
lint:code-quality:
  stage: lint
  <<: *python_template
  script:
    - pip install flake8 black isort mypy
    - black --check .
    - isort --check-only .
    - flake8 .
    - mypy app/ --ignore-missing-imports
  only:
    - merge_requests
    - main
    - develop

# ==============================================
# 단위 테스트
# ==============================================
test:unit:
  stage: test
  <<: *python_template
  script:
    - pip install -r tests/requirements-test.txt
    - pytest tests/unit/ -v --cov=app --cov-report=xml --cov-report=html --cov-report=term
  coverage: '/(?i)total.*? (100(?:\.0+)?\%|[1-9]?\d(?:\.\d+)?\%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - htmlcov/
    expire_in: 1 week

# ==============================================
# 통합 테스트
# ==============================================
test:integration:
  stage: test
  <<: *python_template
  services:
    - name: mariadb:10.11
      alias: mariadb
    - name: redis:7-alpine
      alias: redis
    - name: elasticsearch:8.11.0
      alias: elasticsearch
  variables:
    MYSQL_ROOT_PASSWORD: test_password
    MYSQL_DATABASE: test_db
    DB_HOST: mariadb
    REDIS_HOST: redis
    ES_HOST: elasticsearch
  script:
    - pip install -r tests/requirements-test.txt
    - sleep 30  # 서비스 대기
    - pytest tests/integration/ -v
  only:
    - merge_requests
    - main
    - develop

# ==============================================
# E2E 테스트
# ==============================================
test:e2e:
  stage: test
  image: mcr.microsoft.com/playwright/python:v1.40.0-focal
  script:
    - pip install -r requirements.txt
    - pip install -r tests/requirements-test.txt
    - playwright install
    - python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 &
    - sleep 10
    - pytest tests/e2e/ -v --html=e2e-report.html --self-contained-html
  artifacts:
    paths:
      - e2e-report.html
    expire_in: 1 week
  only:
    - main
    - develop

# ==============================================
# 보안 스캔
# ==============================================
security:scan:
  stage: security
  <<: *python_template
  script:
    - pip install safety bandit pip-audit
    - safety check
    - bandit -r app/ -f json -o bandit-report.json
    - pip-audit
  artifacts:
    paths:
      - bandit-report.json
    expire_in: 1 week
  allow_failure: true

# ==============================================
# Docker 빌드
# ==============================================
build:docker:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    # API Gateway
    - docker build -t $CI_REGISTRY_IMAGE/api-gateway:$CI_COMMIT_SHA ./api-gateway
    - docker push $CI_REGISTRY_IMAGE/api-gateway:$CI_COMMIT_SHA
    
    # MCP Host
    - docker build -t $CI_REGISTRY_IMAGE/mcp-host:$CI_COMMIT_SHA ./mcp-host
    - docker push $CI_REGISTRY_IMAGE/mcp-host:$CI_COMMIT_SHA
    
    # Frontend
    - docker build -t $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA ./frontend
    - docker push $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA
  only:
    - main
    - develop

# ==============================================
# 배포 (스테이징)
# ==============================================
deploy:staging:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - chmod 700 ~/.ssh
  script:
    - ssh $STAGING_USER@$STAGING_HOST "
        cd /app/mcps &&
        docker-compose pull &&
        docker-compose up -d &&
        docker-compose ps
      "
  environment:
    name: staging
    url: https://staging.mcps.example.com
  only:
    - develop

# ==============================================
# 배포 (프로덕션)
# ==============================================
deploy:production:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - chmod 700 ~/.ssh
  script:
    - ssh $PROD_USER@$PROD_HOST "
        cd /app/mcps &&
        docker-compose pull &&
        docker-compose up -d &&
        docker-compose ps
      "
  environment:
    name: production
    url: https://mcps.example.com
  when: manual
  only:
    - main
```

***

## 8. 배포 자동화

### 8.1 배포 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/scripts/deploy/deploy.sh
# 배포 자동화 스크립트

set -e

# ==============================================
# 설정
# ==============================================

ENVIRONMENT=${1:-"staging"}
VERSION=${2:-"latest"}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname $(dirname "$SCRIPT_DIR"))"

echo "=========================================="
echo "  배포 시작"
echo "=========================================="
echo "환경: ${ENVIRONMENT}"
echo "버전: ${VERSION}"
echo "=========================================="

# 환경별 설정 로드
case ${ENVIRONMENT} in
    "staging")
        DEPLOY_HOST="staging.mcps.example.com"
        DEPLOY_USER="deploy"
        DEPLOY_PATH="/app/mcps"
        ;;
    "production")
        DEPLOY_HOST="mcps.example.com"
        DEPLOY_USER="deploy"
        DEPLOY_PATH="/app/mcps"
        ;;
    *)
        echo "Error: Unknown environment: ${ENVIRONMENT}"
        exit 1
        ;;
esac

# ==============================================
# 1. 사전 검사
# ==============================================

echo ""
echo "[1/7] 사전 검사..."

# SSH 연결 확인
if ! ssh -o ConnectTimeout=10 ${DEPLOY_USER}@${DEPLOY_HOST} "echo 'SSH OK'"; then
    echo "Error: SSH 연결 실패"
    exit 1
fi

# 디스크 공간 확인
DISK_USAGE=$(ssh ${DEPLOY_USER}@${DEPLOY_HOST} "df -h ${DEPLOY_PATH} | awk 'NR==2 {print \$5}' | cut -d'%' -f1")
if [ ${DISK_USAGE} -gt 80 ]; then
    echo "Warning: 디스크 사용률 높음 (${DISK_USAGE}%)"
fi

echo "사전 검사 완료"

# ==============================================
# 2. 백업
# ==============================================

echo ""
echo "[2/7] 현재 버전 백업..."

ssh ${DEPLOY_USER}@${DEPLOY_HOST} << 'ENDSSH'
BACKUP_DIR="/data/backups/deployments"
BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"

mkdir -p ${BACKUP_DIR}
cd /app/mcps

# Docker 이미지 저장
docker-compose config --services | while read service; do
    docker save ${service}:current -o ${BACKUP_DIR}/${BACKUP_NAME}_${service}.tar
done

# 설정 파일 백업
tar -czf ${BACKUP_DIR}/${BACKUP_NAME}_config.tar.gz \
    .env \
    docker-compose.yml \
    nginx/

echo "백업 완료: ${BACKUP_NAME}"
ENDSSH

echo "백업 완료"

# ==============================================
# 3. 코드 배포
# ==============================================

echo ""
echo "[3/7] 코드 배포..."

# Git 배포 (또는 Docker 이미지 pull)
ssh ${DEPLOY_USER}@${DEPLOY_HOST} << ENDSSH
cd ${DEPLOY_PATH}

# Git pull (옵션 1)
# git fetch origin
# git checkout ${VERSION}
# git pull origin ${VERSION}

# Docker 이미지 pull (옵션 2)
docker pull myorg/mcps-api-gateway:${VERSION}
docker pull myorg/mcps-mcp-host:${VERSION}
docker pull myorg/mcps-frontend:${VERSION}

# 이미지 태그 변경
docker tag myorg/mcps-api-gateway:${VERSION} myorg/mcps-api-gateway:current
docker tag myorg/mcps-mcp-host:${VERSION} myorg/mcps-mcp-host:current
docker tag myorg/mcps-frontend:${VERSION} myorg/mcps-frontend:current
ENDSSH

echo "코드 배포 완료"

# ==============================================
# 4. Database 마이그레이션
# ==============================================

echo ""
echo "[4/7] Database 마이그레이션..."

ssh ${DEPLOY_USER}@${DEPLOY_HOST} << 'ENDSSH'
cd /app/mcps

# Alembic 마이그레이션 (예시)
docker-compose run --rm api-gateway alembic upgrade head

echo "Database 마이그레이션 완료"
ENDSSH

# ==============================================
# 5. 헬스체크 (배포 전)
# ==============================================

echo ""
echo "[5/7] 배포 전 헬스체크..."

HEALTH_CHECK_URL="https://${DEPLOY_HOST}/health"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${HEALTH_CHECK_URL})

if [ "${HEALTH_STATUS}" != "200" ]; then
    echo "Warning: 현재 서비스 상태 이상 (${HEALTH_STATUS})"
fi

# ==============================================
# 6. 서비스 재시작 (Rolling Update)
# ==============================================

echo ""
echo "[6/7] 서비스 재시작 (Rolling Update)..."

ssh ${DEPLOY_USER}@${DEPLOY_HOST} << 'ENDSSH'
cd /app/mcps

# Docker Compose로 순차 재시작
for service in api-gateway mcp-host frontend; do
    echo "재시작: ${service}"
    
    # 새 컨테이너 시작
    docker-compose up -d --no-deps --scale ${service}=2 ${service}
    
    # 헬스체크 대기
    sleep 10
    
    # 기존 컨테이너 중지
    docker-compose up -d --no-deps --scale ${service}=1 --remove-orphans ${service}
    
    echo "${service} 재시작 완료"
done
ENDSSH

echo "서비스 재시작 완료"

# ==============================================
# 7. 배포 후 검증
# ==============================================

echo ""
echo "[7/7] 배포 후 검증..."

# 헬스체크
for i in {1..30}; do
    HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${HEALTH_CHECK_URL})
    
    if [ "${HEALTH_STATUS}" = "200" ]; then
        echo "헬스체크 성공"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "Error: 헬스체크 실패"
        
        # 롤백
        echo "롤백 시작..."
        bash "${SCRIPT_DIR}/rollback.sh"
        exit 1
    fi
    
    echo "헬스체크 대기 중... (${i}/30)"
    sleep 2
done

# 연기 테스트 (Smoke Test)
echo ""
echo "연기 테스트 실행 중..."

# 주요 엔드포인트 테스트
ENDPOINTS=(
    "/health"
    "/api/v1/documents"
    "/api/v1/search"
)

for endpoint in "${ENDPOINTS[@]}"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${DEPLOY_HOST}${endpoint}")
    
    if [ "${STATUS}" != "200" ] && [ "${STATUS}" != "401" ]; then
        echo "Error: ${endpoint} 테스트 실패 (${STATUS})"
        exit 1
    fi
    
    echo "  ${endpoint}: OK"
done

echo ""
echo "=========================================="
echo "  배포 완료!"
echo "=========================================="
echo "환경: ${ENVIRONMENT}"
echo "버전: ${VERSION}"
echo "URL: https://${DEPLOY_HOST}"
echo "=========================================="

# Slack 알림 (선택)
# curl -X POST ${SLACK_WEBHOOK_URL} \
#     -H 'Content-Type: application/json' \
#     -d "{
#         \"text\": \"✅ ${ENVIRONMENT} 배포 완료\",
#         \"attachments\": [{
#             \"color\": \"good\",
#             \"fields\": [
#                 {\"title\": \"환경\", \"value\": \"${ENVIRONMENT}\", \"short\": true},
#                 {\"title\": \"버전\", \"value\": \"${VERSION}\", \"short\": true}
#             ]
#         }]
#     }"
```

### 8.2 롤백 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/scripts/deploy/rollback.sh
# 롤백 스크립트

set -e

ENVIRONMENT=${1:-"staging"}

echo "=========================================="
echo "  롤백 시작"
echo "=========================================="

case ${ENVIRONMENT} in
    "staging")
        DEPLOY_HOST="staging.mcps.example.com"
        DEPLOY_USER="deploy"
        ;;
    "production")
        DEPLOY_HOST="mcps.example.com"
        DEPLOY_USER="deploy"
        ;;
esac

# 최신 백업 찾기
LATEST_BACKUP=$(ssh ${DEPLOY_USER}@${DEPLOY_HOST} \
    "ls -t /data/backups/deployments/backup_*.tar | head -1")

echo "롤백 대상: ${LATEST_BACKUP}"

# 롤백 실행
ssh ${DEPLOY_USER}@${DEPLOY_HOST} << ENDSSH
cd /app/mcps

# Docker 이미지 복원
for backup_file in /data/backups/deployments/backup_*_*.tar; do
    docker load -i \${backup_file}
done

# 서비스 재시작
docker-compose down
docker-compose up -d

echo "롤백 완료"
ENDSSH

echo ""
echo "=========================================="
echo "  롤백 완료!"
echo "=========================================="
```


## 9. 모니터링 및 알림

### 9.1 배포 모니터링

```python
# /app/poc/mcps/scripts/deploy/monitor_deployment.py
"""배포 모니터링"""

import asyncio
import aiohttp
from typing import Dict, List
from datetime import datetime
import json

class DeploymentMonitor:
    """배포 모니터링 클래스"""
    
    def __init__(self, base_url: str, check_interval: int = 30):
        self.base_url = base_url
        self.check_interval = check_interval
        self.metrics = []
    
    async def check_health(self) -> Dict:
        """헬스체크"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    status = response.status
                    data = await response.json()
                    
                    return {
                        "timestamp": datetime.now().isoformat(),
                        "status": status,
                        "healthy": status == 200,
                        "data": data
                    }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "status": 0,
                "healthy": False,
                "error": str(e)
            }
    
    async def check_response_time(self, endpoint: str) -> Dict:
        """응답 시간 확인"""
        start = datetime.now()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}{endpoint}",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    await response.text()
                    
                    elapsed = (datetime.now() - start).total_seconds()
                    
                    return {
                        "endpoint": endpoint,
                        "response_time": elapsed,
                        "status": response.status,
                        "ok": elapsed < 1.0  # 1초 이내
                    }
        except Exception as e:
            elapsed = (datetime.now() - start).total_seconds()
            return {
                "endpoint": endpoint,
                "response_time": elapsed,
                "status": 0,
                "ok": False,
                "error": str(e)
            }
    
    async def check_error_rate(self) -> Dict:
        """에러율 확인"""
        endpoints = [
            "/api/v1/documents",
            "/api/v1/search",
            "/api/v1/users"
        ]
        
        results = []
        for endpoint in endpoints:
            result = await self.check_response_time(endpoint)
            results.append(result)
        
        total = len(results)
        errors = sum(1 for r in results if not r["ok"])
        error_rate = (errors / total * 100) if total > 0 else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_checks": total,
            "errors": errors,
            "error_rate": error_rate,
            "threshold_exceeded": error_rate > 5.0  # 5% 이상
        }
    
    async def monitor_deployment(self, duration_minutes: int = 30):
        """배포 모니터링 (지정된 시간 동안)"""
        print(f"배포 모니터링 시작 ({duration_minutes}분)")
        print("=" * 50)
        
        start_time = datetime.now()
        check_count = 0
        issues = []
        
        while True:
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            if elapsed >= duration_minutes:
                break
            
            check_count += 1
            print(f"\n[체크 #{check_count}] {datetime.now().strftime('%H:%M:%S')}")
            
            # 1. 헬스체크
            health = await self.check_health()
            print(f"  헬스: {'✅' if health['healthy'] else '❌'}")
            
            if not health['healthy']:
                issues.append({
                    "time": datetime.now().isoformat(),
                    "type": "health_check_failed",
                    "details": health
                })
            
            # 2. 응답 시간
            response_time = await self.check_response_time("/api/v1/health")
            print(f"  응답 시간: {response_time['response_time']:.3f}초")
            
            if response_time['response_time'] > 2.0:
                issues.append({
                    "time": datetime.now().isoformat(),
                    "type": "slow_response",
                    "details": response_time
                })
            
            # 3. 에러율
            error_rate = await self.check_error_rate()
            print(f"  에러율: {error_rate['error_rate']:.1f}%")
            
            if error_rate['threshold_exceeded']:
                issues.append({
                    "time": datetime.now().isoformat(),
                    "type": "high_error_rate",
                    "details": error_rate
                })
            
            # 메트릭 저장
            self.metrics.append({
                "timestamp": datetime.now().isoformat(),
                "health": health,
                "response_time": response_time,
                "error_rate": error_rate
            })
            
            # 대기
            await asyncio.sleep(self.check_interval)
        
        # 결과 요약
        print("\n" + "=" * 50)
        print("모니터링 결과 요약")
        print("=" * 50)
        print(f"총 체크 수: {check_count}")
        print(f"발견된 이슈: {len(issues)}")
        
        if issues:
            print("\n⚠️  이슈 상세:")
            for idx, issue in enumerate(issues, 1):
                print(f"\n  [{idx}] {issue['type']}")
                print(f"      시간: {issue['time']}")
        else:
            print("\n✅ 이슈 없음")
        
        # 메트릭 저장
        with open("/data/reports/deployment_metrics.json", "w") as f:
            json.dump(self.metrics, f, indent=2)
        
        return len(issues) == 0

async def main():
    """메인 함수"""
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    monitor = DeploymentMonitor(base_url)
    success = await monitor.monitor_deployment(duration)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
```

### 9.2 알림 설정

```python
# /app/poc/mcps/scripts/deploy/notifications.py
"""배포 알림"""

import requests
from typing import Dict, Any
from enum import Enum

class NotificationLevel(str, Enum):
    """알림 레벨"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class NotificationManager:
    """알림 관리자"""
    
    def __init__(self, config: Dict[str, Any]):
        self.slack_webhook = config.get("slack_webhook")
        self.email_config = config.get("email")
        self.teams_webhook = config.get("teams_webhook")
    
    def send_slack_notification(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        fields: Dict[str, str] = None
    ):
        """Slack 알림 전송"""
        if not self.slack_webhook:
            return
        
        # 색상 매핑
        colors = {
            NotificationLevel.INFO: "#36a64f",      # 녹색
            NotificationLevel.WARNING: "#ff9900",   # 주황색
            NotificationLevel.ERROR: "#ff0000",     # 빨간색
            NotificationLevel.SUCCESS: "#00ff00"    # 밝은 녹색
        }
        
        # 이모지 매핑
        emojis = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.SUCCESS: "✅"
        }
        
        payload = {
            "text": f"{emojis[level]} {title}",
            "attachments": [{
                "color": colors[level],
                "text": message,
                "fields": [
                    {"title": k, "value": v, "short": True}
                    for k, v in (fields or {}).items()
                ],
                "footer": "MCP Deployment System",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        try:
            response = requests.post(
                self.slack_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Slack 알림 전송 실패: {e}")
    
    def send_teams_notification(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO
    ):
        """Microsoft Teams 알림 전송"""
        if not self.teams_webhook:
            return
        
        colors = {
            NotificationLevel.INFO: "0078D4",
            NotificationLevel.WARNING: "FF8C00",
            NotificationLevel.ERROR: "D13438",
            NotificationLevel.SUCCESS: "28A745"
        }
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": colors[level],
            "title": title,
            "text": message
        }
        
        try:
            response = requests.post(
                self.teams_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Teams 알림 전송 실패: {e}")
    
    def notify_deployment_start(self, environment: str, version: str):
        """배포 시작 알림"""
        self.send_slack_notification(
            title="배포 시작",
            message=f"{environment} 환경에 버전 {version} 배포를 시작합니다.",
            level=NotificationLevel.INFO,
            fields={
                "환경": environment,
                "버전": version,
                "시작 시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    
    def notify_deployment_success(self, environment: str, version: str, duration: int):
        """배포 성공 알림"""
        self.send_slack_notification(
            title="배포 성공",
            message=f"{environment} 환경 배포가 성공적으로 완료되었습니다.",
            level=NotificationLevel.SUCCESS,
            fields={
                "환경": environment,
                "버전": version,
                "소요 시간": f"{duration}초"
            }
        )
    
    def notify_deployment_failure(
        self,
        environment: str,
        version: str,
        error: str
    ):
        """배포 실패 알림"""
        self.send_slack_notification(
            title="배포 실패",
            message=f"{environment} 환경 배포가 실패했습니다.\n에러: {error}",
            level=NotificationLevel.ERROR,
            fields={
                "환경": environment,
                "버전": version,
                "에러": error
            }
        )
    
    def notify_rollback(self, environment: str, reason: str):
        """롤백 알림"""
        self.send_slack_notification(
            title="롤백 실행",
            message=f"{environment} 환경이 롤백되었습니다.",
            level=NotificationLevel.WARNING,
            fields={
                "환경": environment,
                "사유": reason,
                "시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

# 사용 예시
if __name__ == "__main__":
    from datetime import datetime
    
    config = {
        "slack_webhook": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    }
    
    notifier = NotificationManager(config)
    
    # 배포 시작 알림
    notifier.notify_deployment_start("production", "v1.2.3")
```

### 9.3 통합 배포 스크립트 (알림 포함)

```bash
#!/bin/bash
# /app/poc/mcps/scripts/deploy/deploy_with_notifications.sh
# 알림이 포함된 배포 스크립트

set -e

ENVIRONMENT=${1:-"staging"}
VERSION=${2:-"latest"}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Slack Webhook URL (환경 변수에서 가져오기)
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# ==============================================
# 알림 함수
# ==============================================

send_notification() {
    local TITLE=$1
    local MESSAGE=$2
    local LEVEL=${3:-"info"}
    
    if [ -z "${SLACK_WEBHOOK_URL}" ]; then
        return
    fi
    
    local COLOR
    local EMOJI
    
    case ${LEVEL} in
        "success")
            COLOR="good"
            EMOJI="✅"
            ;;
        "error")
            COLOR="danger"
            EMOJI="❌"
            ;;
        "warning")
            COLOR="warning"
            EMOJI="⚠️"
            ;;
        *)
            COLOR="#36a64f"
            EMOJI="ℹ️"
            ;;
    esac
    
    curl -X POST ${SLACK_WEBHOOK_URL} \
        -H 'Content-Type: application/json' \
        -d "{
            \"text\": \"${EMOJI} ${TITLE}\",
            \"attachments\": [{
                \"color\": \"${COLOR}\",
                \"text\": \"${MESSAGE}\",
                \"fields\": [
                    {\"title\": \"환경\", \"value\": \"${ENVIRONMENT}\", \"short\": true},
                    {\"title\": \"버전\", \"value\": \"${VERSION}\", \"short\": true}
                ],
                \"footer\": \"MCP Deployment\",
                \"ts\": $(date +%s)
            }]
        }" > /dev/null 2>&1
}

# ==============================================
# 배포 시작
# ==============================================

START_TIME=$(date +%s)

send_notification \
    "배포 시작" \
    "${ENVIRONMENT} 환경에 버전 ${VERSION} 배포를 시작합니다." \
    "info"

# ==============================================
# 배포 실행
# ==============================================

echo "배포 실행 중..."

if bash "${SCRIPT_DIR}/deploy.sh" ${ENVIRONMENT} ${VERSION}; then
    # 성공
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    send_notification \
        "배포 성공" \
        "${ENVIRONMENT} 환경 배포가 성공적으로 완료되었습니다. (소요 시간: ${DURATION}초)" \
        "success"
    
    # 배포 후 모니터링 시작
    echo ""
    echo "배포 후 모니터링 시작 (30분)..."
    
    python3 "${SCRIPT_DIR}/monitor_deployment.py" \
        "https://${ENVIRONMENT}.mcps.example.com" \
        30
    
    if [ $? -eq 0 ]; then
        send_notification \
            "모니터링 완료" \
            "배포 후 30분 모니터링 결과: 이상 없음" \
            "success"
    else
        send_notification \
            "모니터링 경고" \
            "배포 후 모니터링에서 이슈가 발견되었습니다. 확인이 필요합니다." \
            "warning"
    fi
    
    exit 0
else
    # 실패
    send_notification \
        "배포 실패" \
        "${ENVIRONMENT} 환경 배포가 실패했습니다. 즉시 확인이 필요합니다." \
        "error"
    
    # 자동 롤백 여부 확인
    if [ "${AUTO_ROLLBACK}" = "true" ]; then
        send_notification \
            "자동 롤백 시작" \
            "배포 실패로 인해 자동 롤백을 시작합니다." \
            "warning"
        
        bash "${SCRIPT_DIR}/rollback.sh" ${ENVIRONMENT}
        
        send_notification \
            "롤백 완료" \
            "이전 버전으로 롤백이 완료되었습니다." \
            "warning"
    fi
    
    exit 1
fi
```

***

## 10. 테스트 데이터 관리

### 10.1 테스트 데이터 생성

```python
# /app/poc/mcps/tests/fixtures/generate_test_data.py
"""테스트 데이터 생성"""

from faker import Faker
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

fake = Faker('ko_KR')  # 한국어 데이터

class TestDataGenerator:
    """테스트 데이터 생성기"""
    
    def __init__(self, seed: int = 42):
        Faker.seed(seed)
        random.seed(seed)
    
    def generate_users(self, count: int = 100) -> List[Dict]:
        """사용자 데이터 생성"""
        users = []
        roles = ["user", "admin", "manager", "guest"]
        
        for i in range(count):
            user = {
                "id": f"USER-{i+1:04d}",
                "username": fake.user_name(),
                "email": fake.email(),
                "name": fake.name(),
                "role": random.choice(roles),
                "department": fake.job(),
                "created_at": fake.date_time_between(
                    start_date="-2y",
                    end_date="now"
                ).isoformat(),
                "is_active": random.choice([True, True, True, False]),
            }
            users.append(user)
        
        return users
    
    def generate_documents(self, count: int = 1000) -> List[Dict]:
        """문서 데이터 생성"""
        documents = []
        classifications = ["public", "internal", "confidential", "secret"]
        categories = ["정책", "가이드", "매뉴얼", "보고서", "제안서", "계약서"]
        
        for i in range(count):
            created_at = fake.date_time_between(
                start_date="-1y",
                end_date="now"
            )
            
            doc = {
                "id": f"DOC-{i+1:06d}",
                "title": fake.catch_phrase(),
                "content": "\n\n".join(fake.paragraphs(nb=5)),
                "classification": random.choice(classifications),
                "category": random.choice(categories),
                "tags": random.sample(
                    ["중요", "긴급", "검토필요", "승인완료", "진행중", "완료"],
                    k=random.randint(1, 3)
                ),
                "author_id": f"USER-{random.randint(1, 100):04d}",
                "created_at": created_at.isoformat(),
                "updated_at": (
                    created_at + timedelta(days=random.randint(0, 30))
                ).isoformat(),
                "version": random.randint(1, 10),
                "views": random.randint(0, 1000),
                "downloads": random.randint(0, 100)
            }
            documents.append(doc)
        
        return documents
    
    def generate_search_queries(self, count: int = 500) -> List[Dict]:
        """검색 쿼리 데이터 생성"""
        queries = []
        keywords = [
            "보안", "정책", "가이드", "매뉴얼", "프로세스",
            "승인", "계약", "제안", "보고", "분석",
            "개발", "운영", "관리", "시스템", "데이터"
        ]
        
        for i in range(count):
            query = {
                "id": f"QUERY-{i+1:06d}",
                "query": " ".join(random.sample(keywords, k=random.randint(1, 3))),
                "user_id": f"USER-{random.randint(1, 100):04d}",
                "timestamp": fake.date_time_between(
                    start_date="-3m",
                    end_date="now"
                ).isoformat(),
                "result_count": random.randint(0, 100),
                "clicked_result": random.choice([True, False])
            }
            queries.append(query)
        
        return queries
    
    def generate_audit_logs(self, count: int = 5000) -> List[Dict]:
        """감사 로그 데이터 생성"""
        logs = []
        actions = ["create", "read", "update", "delete", "search", "download"]
        
        for i in range(count):
            log = {
                "id": f"LOG-{i+1:08d}",
                "user_id": f"USER-{random.randint(1, 100):04d}",
                "action": random.choice(actions),
                "resource_type": random.choice(["document", "user", "system"]),
                "resource_id": f"DOC-{random.randint(1, 1000):06d}",
                "ip_address": fake.ipv4(),
                "timestamp": fake.date_time_between(
                    start_date="-1m",
                    end_date="now"
                ).isoformat(),
                "success": random.choice([True, True, True, False]),
                "details": {
                    "user_agent": fake.user_agent(),
                    "duration_ms": random.randint(10, 5000)
                }
            }
            logs.append(log)
        
        return logs
    
    def save_to_json(self, data: List[Dict], filename: str):
        """JSON 파일로 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"저장 완료: {filename} ({len(data)}개 항목)")

# ==============================================
# 메인 실행
# ==============================================

if __name__ == "__main__":
    import os
    
    generator = TestDataGenerator(seed=42)
    
    # 출력 디렉토리 생성
    output_dir = "/app/poc/mcps/tests/fixtures/data"
    os.makedirs(output_dir, exist_ok=True)
    
    print("테스트 데이터 생성 중...")
    print("=" * 50)
    
    # 사용자 데이터
    users = generator.generate_users(100)
    generator.save_to_json(users, f"{output_dir}/users.json")
    
    # 문서 데이터
    documents = generator.generate_documents(1000)
    generator.save_to_json(documents, f"{output_dir}/documents.json")
    
    # 검색 쿼리
    queries = generator.generate_search_queries(500)
    generator.save_to_json(queries, f"{output_dir}/search_queries.json")
    
    # 감사 로그
    audit_logs = generator.generate_audit_logs(5000)
    generator.save_to_json(audit_logs, f"{output_dir}/audit_logs.json")
    
    print("=" * 50)
    print("테스트 데이터 생성 완료!")
```

### 10.2 테스트 데이터 로딩

```python
# /app/poc/mcps/tests/fixtures/load_test_data.py
"""테스트 데이터 로딩"""

import json
import asyncio
from typing import List, Dict
import aiohttp
from tqdm import tqdm

class TestDataLoader:
    """테스트 데이터 로더"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def load_json(self, filename: str) -> List[Dict]:
        """JSON 파일 로드"""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def create_user(self, session: aiohttp.ClientSession, user: Dict):
        """사용자 생성"""
        async with session.post(
            f"{self.base_url}/api/v1/users",
            json=user,
            headers=self.headers
        ) as response:
            if response.status in [200, 201]:
                return await response.json()
            else:
                error = await response.text()
                print(f"사용자 생성 실패: {error}")
                return None
    
    async def create_document(self, session: aiohttp.ClientSession, doc: Dict):
        """문서 생성"""
        async with session.post(
            f"{self.base_url}/api/v1/documents",
            json=doc,
            headers=self.headers
        ) as response:
            if response.status in [200, 201]:
                return await response.json()
            else:
                return None
    
    async def bulk_create(
        self,
        items: List[Dict],
        create_func,
        batch_size: int = 50
    ):
        """대량 생성"""
        async with aiohttp.ClientSession() as session:
            results = []
            
            for i in tqdm(range(0, len(items), batch_size), desc="로딩 중"):
                batch = items[i:i+batch_size]
                
                tasks = [create_func(session, item) for item in batch]
                batch_results = await asyncio.gather(*tasks)
                
                results.extend(batch_results)
                
                # Rate limiting
                await asyncio.sleep(0.1)
            
            return results
    
    async def load_users(self, filename: str):
        """사용자 데이터 로딩"""
        users = self.load_json(filename)
        print(f"사용자 {len(users)}명 로딩 중...")
        
        results = await self.bulk_create(users, self.create_user)
        
        success_count = sum(1 for r in results if r is not None)
        print(f"사용자 로딩 완료: {success_count}/{len(users)}")
    
    async def load_documents(self, filename: str):
        """문서 데이터 로딩"""
        documents = self.load_json(filename)
        print(f"문서 {len(documents)}개 로딩 중...")
        
        results = await self.bulk_create(documents, self.create_document)
        
        success_count = sum(1 for r in results if r is not None)
        print(f"문서 로딩 완료: {success_count}/{len(documents)}")

async def main():
    """메인 함수"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python load_test_data.py <base_url> <token>")
        sys.exit(1)
    
    base_url = sys.argv[1]
    token = sys.argv[2]
    
    loader = TestDataLoader(base_url, token)
    
    print("=" * 50)
    print("테스트 데이터 로딩 시작")
    print("=" * 50)
    
    # 사용자 로딩
    await loader.load_users("tests/fixtures/data/users.json")
    
    # 문서 로딩
    await loader.load_documents("tests/fixtures/data/documents.json")
    
    print("=" * 50)
    print("테스트 데이터 로딩 완료!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
```

### 10.3 테스트 데이터 정리

```python
# /app/poc/mcps/tests/fixtures/cleanup_test_data.py
"""테스트 데이터 정리"""

import asyncio
import aiohttp
from typing import List

class TestDataCleanup:
    """테스트 데이터 정리"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    async def delete_all_documents(self):
        """모든 테스트 문서 삭제"""
        async with aiohttp.ClientSession() as session:
            # 문서 목록 조회
            async with session.get(
                f"{self.base_url}/api/v1/documents?limit=10000",
                headers=self.headers
            ) as response:
                if response.status != 200:
                    print("문서 목록 조회 실패")
                    return
                
                data = await response.json()
                documents = data.get("documents", [])
            
            print(f"삭제할 문서: {len(documents)}개")
            
            # 문서 삭제
            for doc in documents:
                if doc["id"].startswith("DOC-"):  # 테스트 데이터만
                    async with session.delete(
                        f"{self.base_url}/api/v1/documents/{doc['id']}",
                        headers=self.headers
                    ) as response:
                        if response.status in [200, 204]:
                            print(f"  삭제: {doc['id']}")
                        else:
                            print(f"  실패: {doc['id']}")
    
    async def delete_all_users(self):
        """모든 테스트 사용자 삭제"""
        async with aiohttp.ClientSession() as session:
            # 사용자 목록 조회
            async with session.get(
                f"{self.base_url}/api/v1/admin/users",
                headers=self.headers
            ) as response:
                if response.status != 200:
                    print("사용자 목록 조회 실패")
                    return
                
                data = await response.json()
                users = data.get("users", [])
            
            print(f"삭제할 사용자: {len(users)}개")
            
            # 사용자 삭제
            for user in users:
                if user["id"].startswith("USER-"):  # 테스트 데이터만
                    async with session.delete(
                        f"{self.base_url}/api/v1/admin/users/{user['id']}",
                        headers=self.headers
                    ) as response:
                        if response.status in [200, 204]:
                            print(f"  삭제: {user['id']}")
                        else:
                            print(f"  실패: {user['id']}")
    
    async def cleanup_all(self):
        """전체 테스트 데이터 정리"""
        print("=" * 50)
        print("테스트 데이터 정리 시작")
        print("=" * 50)
        
        print("\n[1/2] 문서 삭제 중...")
        await self.delete_all_documents()
        
        print("\n[2/2] 사용자 삭제 중...")
        await self.delete_all_users()
        
        print("\n" + "=" * 50)
        print("테스트 데이터 정리 완료!")
        print("=" * 50)

async def main():
    """메인 함수"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python cleanup_test_data.py <base_url> <admin_token>")
        sys.exit(1)
    
    base_url = sys.argv[1]
    token = sys.argv[2]
    
    cleanup = TestDataCleanup(base_url, token)
    await cleanup.cleanup_all()

if __name__ == "__main__":
    asyncio.run(main())
```

### 10.4 테스트 데이터 관리 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/tests/fixtures/manage_test_data.sh
# 테스트 데이터 관리 스크립트

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_URL=${BASE_URL:-"http://localhost:8080"}
ADMIN_TOKEN=${ADMIN_TOKEN:-""}

# ==============================================
# 함수
# ==============================================

generate_data() {
    echo "테스트 데이터 생성 중..."
    python3 "${SCRIPT_DIR}/generate_test_data.py"
}

load_data() {
    echo "테스트 데이터 로딩 중..."
    
    if [ -z "${ADMIN_TOKEN}" ]; then
        echo "Error: ADMIN_TOKEN이 설정되지 않았습니다."
        exit 1
    fi
    
    python3 "${SCRIPT_DIR}/load_test_data.py" "${BASE_URL}" "${ADMIN_TOKEN}"
}

cleanup_data() {
    echo "테스트 데이터 정리 중..."
    
    if [ -z "${ADMIN_TOKEN}" ]; then
        echo "Error: ADMIN_TOKEN이 설정되지 않았습니다."
        exit 1
    fi
    
    python3 "${SCRIPT_DIR}/cleanup_test_data.py" "${BASE_URL}" "${ADMIN_TOKEN}"
}

show_stats() {
    echo "테스트 데이터 통계:"
    echo "===================="
    
    for file in "${SCRIPT_DIR}/data"/*.json; do
        if [ -f "${file}" ]; then
            COUNT=$(jq '. | length' "${file}")
            echo "  $(basename ${file}): ${COUNT}개"
        fi
    done
}

# ==============================================
# 메인
# ==============================================

case ${1} in
    "generate")
        generate_data
        ;;
    "load")
        load_data
        ;;
    "cleanup")
        cleanup_data
        ;;
    "stats")
        show_stats
        ;;
    "reset")
        echo "테스트 데이터 리셋 중..."
        cleanup_data
        generate_data
        load_data
        ;;
    *)
        echo "Usage: $0 {generate|load|cleanup|stats|reset}"
        echo ""
        echo "Commands:"
        echo "  generate - 테스트 데이터 생성 (JSON 파일)"
        echo "  load     - 테스트 데이터 로딩 (DB에 삽입)"
        echo "  cleanup  - 테스트 데이터 정리 (DB에서 삭제)"
        echo "  stats    - 테스트 데이터 통계"
        echo "  reset    - 전체 리셋 (cleanup + generate + load)"
        echo ""
        echo "Environment Variables:"
        echo "  BASE_URL     - API 서버 URL (default: http://localhost:8080)"
        echo "  ADMIN_TOKEN  - 관리자 토큰 (필수)"
        exit 1
        ;;
esac
```

***

## 11. 베스트 프랙티스

### 11.1 테스트 작성 가이드

```python
"""
테스트 작성 베스트 프랙티스

1. 테스트 명명 규칙
   - test_<function_name>_<scenario>_<expected_result>
   - 예: test_create_document_with_valid_data_returns_success

2. AAA 패턴 사용
   - Arrange: 테스트 준비
   - Act: 테스트 실행
   - Assert: 결과 검증

3. 독립적인 테스트
   - 각 테스트는 다른 테스트에 의존하지 않아야 함
   - 테스트 순서가 바뀌어도 동작해야 함

4. 명확한 단언문
   - 하나의 테스트에는 하나의 논리적 개념만
   - 여러 assert는 같은 개념을 검증하는 경우만

5. 테스트 데이터
   - Fixture를 활용한 재사용
   - 하드코딩 대신 Factory 패턴 사용

6. Mock 사용
   - 외부 의존성은 Mock으로 대체
   - 실제 외부 API 호출 최소화

7. 테스트 커버리지
   - 중요 비즈니스 로직은 100% 커버
   - 에지 케이스와 에러 처리 포함
"""

# 좋은 예시
def test_create_document_with_empty_title_raises_validation_error():
    """빈 제목으로 문서 생성 시 검증 에러 발생"""
    # Arrange
    doc_data = {
        "title": "",  # 빈 제목
        "content": "내용",
        "classification": "internal"
    }
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        create_document(doc_data)
    
    assert "제목" in str(exc_info.value)

# 나쁜 예시
def test_document():
    """무엇을 테스트하는지 불명확"""
    doc = create_document({"title": "test"})
    assert doc
    assert doc.title == "test"
    doc2 = get_document(doc.id)
    assert doc2.id == doc.id
    # 너무 많은 것을 한 번에 테스트
```

### 11.2 CI/CD 체크리스트

```markdown
# CI/CD 체크리스트

## Pre-Deployment (배포 전)
- [ ] 모든 테스트 통과 (단위, 통합, E2E)
- [ ] 코드 리뷰 완료
- [ ] 린트 및 포맷 검사 통과
- [ ] 보안 스캔 통과
- [ ] 버전 번호 업데이트
- [ ] CHANGELOG 업데이트
- [ ] Database 마이그레이션 스크립트 준비
- [ ] 롤백 계획 수립

## Deployment (배포)
- [ ] 배포 알림 전송
- [ ] 현재 버전 백업
- [ ] Database 마이그레이션 실행
- [ ] 새 버전 배포
- [ ] 헬스체크 통과
- [ ] 연기 테스트 통과

## Post-Deployment (배포 후)
- [ ] 배포 성공 알림
- [ ] 30분 모니터링
- [ ] 에러율 확인
- [ ] 응답 시간 확인
- [ ] 사용자 피드백 수집
- [ ] 문서 업데이트
```

***

## 12. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

***

## 13. 참고 자료

- [Pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [Locust Documentation](https://docs.locust.io/)
- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Docker Documentation](https://docs.docker.com/)

***










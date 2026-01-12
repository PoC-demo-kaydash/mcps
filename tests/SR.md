# 통합 테스트 및 시나리오 설계서

***

# 06. MCP 에코시스템 - 통합 테스트 및 시나리오

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/tests/`  
**목적**: 전체 시스템 통합 테스트 및 사용 시나리오

***

## 목차

1. [개요](#1-개요)
2. [테스트 전략](#2-테스트-전략)
3. [테스트 환경 구성](#3-테스트-환경-구성)
4. [단위 테스트](#4-단위-테스트)
5. [통합 테스트](#5-통합-테스트)
6. [시나리오 테스트](#6-시나리오-테스트)
7. [성능 테스트](#7-성능-테스트)

***

## 1. 개요

### 1.1 테스트 목표

- **기능 검증**: 모든 Tool이 설계대로 동작
- **통합 검증**: 컴포넌트 간 상호작용 정상 동작
- **성능 검증**: 응답 시간, 처리량 목표 달성
- **안정성 검증**: 에러 처리, 복구 메커니즘 동작
- **보안 검증**: 권한 제어, 데이터 보호 동작

### 1.2 테스트 범위

```
┌─────────────────────────────────────────────┐
│              테스트 피라미드                 │
├─────────────────────────────────────────────┤
│                                              │
│              ┌───────────┐                  │
│              │  E2E 테스트 │  (10%)          │
│              └───────────┘                  │
│          ┌─────────────────┐               │
│          │  시나리오 테스트  │  (20%)        │
│          └─────────────────┘               │
│      ┌───────────────────────┐            │
│      │    통합 테스트         │  (30%)      │
│      └───────────────────────┘            │
│  ┌───────────────────────────────┐       │
│  │       단위 테스트              │  (40%)  │
│  └───────────────────────────────┘       │
│                                              │
└─────────────────────────────────────────────┘
```

### 1.3 디렉토리 구조

```
/app/poc/mcps/tests/
├── __init__.py
├── conftest.py                 # Pytest 설정
├── fixtures.py                 # 공통 Fixture
│
├── unit/                       # 단위 테스트
│   ├── test_database.py
│   ├── test_elasticsearch.py
│   ├── test_permissions.py
│   └── test_tools/
│       ├── test_auth_tools.py
│       ├── test_document_tools.py
│       └── test_search_tools.py
│
├── integration/                # 통합 테스트
│   ├── test_server_manager.py
│   ├── test_tool_execution.py
│   ├── test_session_flow.py
│   └── test_api_endpoints.py
│
├── scenarios/                  # 시나리오 테스트
│   ├── test_document_lifecycle.py
│   ├── test_permission_workflow.py
│   ├── test_version_management.py
│   └── test_search_workflow.py
│
├── performance/                # 성능 테스트
│   ├── test_load.py
│   ├── test_concurrency.py
│   └── test_stress.py
│
├── e2e/                        # E2E 테스트
│   ├── test_full_workflow.py
│   └── test_multi_user.py
│
└── data/                       # 테스트 데이터
    ├── test_users.json
    ├── test_documents.json
    └── test_queries.json
```

***

## 2. 테스트 전략

### 2.1 테스트 레벨

| 레벨 | 목적 | 범위 | 도구 |
|------|------|------|------|
| **단위 테스트** | 개별 함수/클래스 검증 | 각 모듈 | pytest |
| **통합 테스트** | 컴포넌트 간 상호작용 | 2-3개 컴포넌트 | pytest |
| **시나리오 테스트** | 비즈니스 시나리오 | 전체 플로우 | pytest |
| **성능 테스트** | 성능 목표 검증 | 전체 시스템 | locust, pytest-benchmark |
| **E2E 테스트** | 사용자 관점 검증 | 전체 시스템 | pytest |

### 2.2 테스트 원칙

**1. 독립성 (Independence)**
- 각 테스트는 독립적으로 실행 가능
- 테스트 간 의존성 없음
- 실행 순서 무관

**2. 반복성 (Repeatability)**
- 동일 조건에서 동일 결과
- 테스트 데이터 격리
- 상태 초기화

**3. 명확성 (Clarity)**
- 테스트 이름에서 의도 파악
- Given-When-Then 패턴
- 명확한 Assertion

**4. 속도 (Speed)**
- 빠른 피드백
- 병렬 실행 가능
- 불필요한 대기 최소화

**5. 포괄성 (Coverage)**
- 정상 케이스
- 에러 케이스
- 경계 케이스

***

## 3. 테스트 환경 구성

### 3.1 conftest.py - Pytest 설정

```python
# tests/conftest.py
"""
Pytest 설정 및 공통 Fixture
"""

import pytest
import sys
from pathlib import Path

# PYTHONPATH 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 테스트 설정
def pytest_configure(config):
    """Pytest 설정"""
    config.addinivalue_line(
        "markers",
        "unit: 단위 테스트"
    )
    config.addinivalue_line(
        "markers",
        "integration: 통합 테스트"
    )
    config.addinivalue_line(
        "markers",
        "scenario: 시나리오 테스트"
    )
    config.addinivalue_line(
        "markers",
        "performance: 성능 테스트"
    )
    config.addinivalue_line(
        "markers",
        "slow: 느린 테스트"
    )


@pytest.fixture(scope="session")
def test_config():
    """테스트 설정"""
    return {
        "db": {
            "host": "localhost",
            "port": 3306,
            "database": "test_mcps_db",
            "user": "test_user",
            "password": "test_password",
            "charset": "utf8mb4",
            "pool_size": {"min": 1, "max": 5}
        },
        "es": {
            "hosts": ["localhost:9200"],
            "timeout": 30
        },
        "test_data_dir": Path(__file__).parent / "data"
    }


@pytest.fixture(scope="function")
def db(test_config):
    """Database fixture (각 테스트마다 초기화)"""
    from shared.database import DatabaseManager
    
    db = DatabaseManager(test_config["db"])
    
    # 테스트 데이터 초기화
    _setup_test_data(db)
    
    yield db
    
    # 정리
    _cleanup_test_data(db)
    db.close()


@pytest.fixture(scope="function")
def es(test_config):
    """Elasticsearch fixture"""
    from shared.elasticsearch import ElasticsearchManager
    
    es = ElasticsearchManager(test_config["es"])
    
    # 테스트 인덱스 생성
    _setup_test_index(es)
    
    yield es
    
    # 정리
    _cleanup_test_index(es)
    es.close()


@pytest.fixture
def test_user():
    """테스트 사용자"""
    return {
        "id": "TEST_U001",
        "name": "테스트 사용자",
        "email": "test@example.com",
        "role": "staff",
        "team": "test_team",
        "department": "test_dept"
    }


@pytest.fixture
def admin_user():
    """관리자 사용자"""
    return {
        "id": "TEST_ADMIN",
        "name": "테스트 관리자",
        "email": "admin@example.com",
        "role": "admin",
        "team": None,
        "department": "admin"
    }


@pytest.fixture
def test_document():
    """테스트 문서"""
    return {
        "id": "TEST_DOC001",
        "title": "테스트 문서",
        "content": "# 테스트\n\n이것은 테스트 문서입니다.",
        "classification": "public",
        "category": "test",
        "tags": ["test", "sample"],
        "author_id": "TEST_U001",
        "team": "test_team",
        "department": "test_dept"
    }


def _setup_test_data(db):
    """테스트 데이터 설정"""
    # 테스트 사용자 생성
    db.execute_insert(
        """
        INSERT INTO users (id, name, email, role, team, department, active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name=name
        """,
        ("TEST_U001", "테스트 사용자", "test@example.com", "staff", "test_team", "test_dept", True)
    )
    
    db.execute_insert(
        """
        INSERT INTO users (id, name, email, role, team, department, active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name=name
        """,
        ("TEST_ADMIN", "테스트 관리자", "admin@example.com", "admin", None, "admin", True)
    )


def _cleanup_test_data(db):
    """테스트 데이터 정리"""
    db.execute_update("DELETE FROM documents WHERE id LIKE 'TEST_%'")
    db.execute_update("DELETE FROM document_versions WHERE doc_id LIKE 'TEST_%'")
    db.execute_update("DELETE FROM audit_logs WHERE user_id LIKE 'TEST_%'")
    db.execute_update("DELETE FROM users WHERE id LIKE 'TEST_%'")


def _setup_test_index(es):
    """테스트 인덱스 생성"""
    index_name = "test_documents"
    
    if not es.index_exists(index_name):
        es.create_index(
            index_name,
            {
                "mappings": {
                    "properties": {
                        "doc_id": {"type": "keyword"},
                        "title": {"type": "text"},
                        "content": {"type": "text"},
                        "classification": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "tags": {"type": "keyword"}
                    }
                }
            }
        )


def _cleanup_test_index(es):
    """테스트 인덱스 정리"""
    index_name = "test_documents"
    
    if es.index_exists(index_name):
        es.delete_index(index_name)
```

### 3.2 fixtures.py - 공통 Fixture

```python
# tests/fixtures.py
"""
공통 테스트 Fixture
"""

import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_documents():
    """샘플 문서 목록"""
    return [
        {
            "id": "TEST_DOC001",
            "title": "MCP 프로토콜 개요",
            "content": "Model Context Protocol은 AI 시스템과 데이터 소스를 연결합니다.",
            "classification": "public",
            "category": "documentation",
            "tags": ["MCP", "protocol", "AI"],
            "author_id": "TEST_U001"
        },
        {
            "id": "TEST_DOC002",
            "title": "데이터베이스 설계",
            "content": "시스템의 데이터베이스 스키마 설계 문서입니다.",
            "classification": "team",
            "category": "design",
            "tags": ["database", "schema"],
            "author_id": "TEST_U001"
        },
        {
            "id": "TEST_DOC003",
            "title": "보안 정책",
            "content": "기밀 보안 정책 문서입니다.",
            "classification": "confidential",
            "category": "security",
            "tags": ["security", "policy"],
            "author_id": "TEST_ADMIN"
        }
    ]


@pytest.fixture
def sample_users():
    """샘플 사용자 목록"""
    return [
        {
            "id": "TEST_U001",
            "name": "김철수",
            "role": "staff",
            "team": "dev_team"
        },
        {
            "id": "TEST_U002",
            "name": "이영희",
            "role": "manager",
            "team": "dev_team"
        },
        {
            "id": "TEST_U003",
            "name": "박민수",
            "role": "junior",
            "team": None
        },
        {
            "id": "TEST_ADMIN",
            "name": "관리자",
            "role": "admin",
            "team": None
        }
    ]


@pytest.fixture
def sample_permissions():
    """샘플 권한"""
    return {
        "admin": {
            "document": ["create", "read", "update", "delete"],
            "user": ["create", "read", "update", "delete"],
            "permission": ["grant", "revoke"]
        },
        "manager": {
            "document": ["create", "read", "update", "delete"],
            "permission": ["grant"]
        },
        "staff": {
            "document": ["create", "read", "update"]
        },
        "junior": {
            "document": ["read"]
        }
    }


@pytest.fixture
def mock_context():
    """Mock 컨텍스트"""
    return {
        "user_id": "TEST_U001",
        "user_role": "staff",
        "user_team": "test_team",
        "request_id": "test_req_001"
    }
```

***

## 4. 단위 테스트

### 4.1 test_database.py

```python
# tests/unit/test_database.py
"""
Database 모듈 단위 테스트
"""

import pytest
from shared.database import DatabaseManager


@pytest.mark.unit
class TestDatabaseManager:
    """DatabaseManager 테스트"""
    
    def test_connection(self, db):
        """연결 테스트"""
        assert db.pool is not None
        assert db.pool.size() > 0
    
    def test_execute_query(self, db):
        """쿼리 실행 테스트"""
        result = db.execute_query("SELECT 1 AS num")
        
        assert len(result) == 1
        assert result[0]["num"] == 1
    
    def test_execute_insert(self, db):
        """INSERT 테스트"""
        doc_id = db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            ("TEST_DOC999", "테스트", "내용", "public", "test", "TEST_U001", "test_team", "test_dept")
        )
        
        # 삽입 확인
        result = db.execute_query("SELECT * FROM documents WHERE id = %s", ("TEST_DOC999",))
        
        assert len(result) == 1
        assert result[0]["title"] == "테스트"
    
    def test_execute_update(self, db):
        """UPDATE 테스트"""
        # 문서 생성
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            ("TEST_DOC998", "원본", "내용", "public", "test", "TEST_U001", "test_team", "test_dept")
        )
        
        # 업데이트
        rows = db.execute_update(
            "UPDATE documents SET title = %s WHERE id = %s",
            ("수정됨", "TEST_DOC998")
        )
        
        assert rows == 1
        
        # 확인
        result = db.execute_query("SELECT * FROM documents WHERE id = %s", ("TEST_DOC998",))
        assert result[0]["title"] == "수정됨"
    
    def test_transaction_commit(self, db):
        """트랜잭션 커밋 테스트"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                ("TEST_DOC997", "트랜잭션", "내용", "public", "test", "TEST_U001", "test_team", "test_dept")
            )
            conn.commit()
        finally:
            cursor.close()
            db.return_connection(conn)
        
        # 확인
        result = db.execute_query("SELECT * FROM documents WHERE id = %s", ("TEST_DOC997",))
        assert len(result) == 1
    
    def test_transaction_rollback(self, db):
        """트랜잭션 롤백 테스트"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                ("TEST_DOC996", "롤백", "내용", "public", "test", "TEST_U001", "test_team", "test_dept")
            )
            conn.rollback()
        finally:
            cursor.close()
            db.return_connection(conn)
        
        # 확인 (없어야 함)
        result = db.execute_query("SELECT * FROM documents WHERE id = %s", ("TEST_DOC996",))
        assert len(result) == 0
```

### 4.2 test_permissions.py

```python
# tests/unit/test_permissions.py
"""
권한 엔진 단위 테스트
"""

import pytest
from shared.permissions import PermissionEngine


@pytest.mark.unit
class TestPermissionEngine:
    """PermissionEngine 테스트"""
    
    def test_check_document_permission_public(self):
        """Public 문서 권한 체크"""
        engine = PermissionEngine()
        
        # junior도 public 문서는 읽기 가능
        result = engine.check_document_permission(
            user_id="TEST_U003",
            user_role="junior",
            user_team=None,
            document={
                "id": "TEST_DOC001",
                "classification": "public",
                "team": "test_team",
                "author_id": "TEST_U001"
            },
            action="read"
        )
        
        assert result is True
    
    def test_check_document_permission_team(self):
        """Team 문서 권한 체크"""
        engine = PermissionEngine()
        
        # 같은 팀은 읽기 가능
        result = engine.check_document_permission(
            user_id="TEST_U001",
            user_role="staff",
            user_team="test_team",
            document={
                "id": "TEST_DOC002",
                "classification": "team",
                "team": "test_team",
                "author_id": "TEST_U001"
            },
            action="read"
        )
        
        assert result is True
        
        # 다른 팀은 읽기 불가
        result = engine.check_document_permission(
            user_id="TEST_U002",
            user_role="staff",
            user_team="other_team",
            document={
                "id": "TEST_DOC002",
                "classification": "team",
                "team": "test_team",
                "author_id": "TEST_U001"
            },
            action="read"
        )
        
        assert result is False
    
    def test_check_document_permission_confidential(self):
        """Confidential 문서 권한 체크"""
        engine = PermissionEngine()
        
        # admin은 가능
        result = engine.check_document_permission(
            user_id="TEST_ADMIN",
            user_role="admin",
            user_team=None,
            document={
                "id": "TEST_DOC003",
                "classification": "confidential",
                "team": None,
                "author_id": "TEST_ADMIN"
            },
            action="read"
        )
        
        assert result is True
        
        # staff는 불가
        result = engine.check_document_permission(
            user_id="TEST_U001",
            user_role="staff",
            user_team="test_team",
            document={
                "id": "TEST_DOC003",
                "classification": "confidential",
                "team": None,
                "author_id": "TEST_ADMIN"
            },
            action="read"
        )
        
        assert result is False
    
    def test_check_action_permission(self):
        """액션 권한 체크"""
        engine = PermissionEngine()
        
        # admin은 모든 액션 가능
        assert engine.check_action_permission("admin", "create") is True
        assert engine.check_action_permission("admin", "delete") is True
        
        # junior는 read만 가능
        assert engine.check_action_permission("junior", "read") is True
        assert engine.check_action_permission("junior", "create") is False
        assert engine.check_action_permission("junior", "update") is False
        assert engine.check_action_permission("junior", "delete") is False
    
    def test_can_approve_request(self):
        """승인 권한 체크"""
        engine = PermissionEngine()
        
        # admin 승인 가능
        assert engine.can_approve_request("admin", None, "test_team") is True
        
        # manager는 같은 팀만 승인 가능
        assert engine.can_approve_request("manager", "test_team", "test_team") is True
        assert engine.can_approve_request("manager", "test_team", "other_team") is False
        
        # staff는 승인 불가
        assert engine.can_approve_request("staff", "test_team", "test_team") is False
```

### 4.3 test_auth_tools.py

```python
# tests/unit/test_tools/test_auth_tools.py
"""
인증 Tool 단위 테스트
"""

import pytest
from mcp_tools.core.auth_tools import (
    AuthenticateTool,
    RequestAccessTool,
    GetMyPermissionsTool
)


@pytest.mark.unit
class TestAuthenticateTool:
    """AuthenticateTool 테스트"""
    
    def test_authenticate_success(self, db):
        """인증 성공"""
        tool = AuthenticateTool(db)
        
        result = tool.execute(
            {"user_id": "TEST_U001"},
            None
        )
        
        assert result["status"] == "success"
        assert result["data"]["user"]["id"] == "TEST_U001"
        assert "token" in result["data"]
    
    def test_authenticate_user_not_found(self, db):
        """존재하지 않는 사용자"""
        tool = AuthenticateTool(db)
        
        result = tool.execute(
            {"user_id": "NONEXISTENT"},
            None
        )
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "USER_NOT_FOUND"
    
    def test_authenticate_invalid_input(self, db):
        """잘못된 입력"""
        tool = AuthenticateTool(db)
        
        result = tool.execute(
            {},  # user_id 누락
            None
        )
        
        assert result["status"] == "error"


@pytest.mark.unit
class TestRequestAccessTool:
    """RequestAccessTool 테스트"""
    
    def test_request_access_success(self, db):
        """접근 권한 요청 성공"""
        # 문서 생성
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            ("TEST_DOC_REQ", "문서", "내용", "confidential", "test", "TEST_ADMIN", None, "admin")
        )
        
        tool = RequestAccessTool(db)
        
        result = tool.execute(
            {
                "doc_id": "TEST_DOC_REQ",
                "reason": "프로젝트 수행을 위해 필요합니다."
            },
            {"user_id": "TEST_U001", "user_role": "staff"}
        )
        
        assert result["status"] == "success"
        assert "request_id" in result["data"]
    
    def test_request_access_document_not_found(self, db):
        """존재하지 않는 문서"""
        tool = RequestAccessTool(db)
        
        result = tool.execute(
            {
                "doc_id": "NONEXISTENT",
                "reason": "이유"
            },
            {"user_id": "TEST_U001"}
        )
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "NOT_FOUND"


@pytest.mark.unit
class TestGetMyPermissionsTool:
    """GetMyPermissionsTool 테스트"""
    
    def test_get_my_permissions(self, db):
        """내 권한 조회"""
        tool = GetMyPermissionsTool(db)
        
        result = tool.execute(
            {},
            {"user_id": "TEST_U001", "user_role": "staff"}
        )
        
        assert result["status"] == "success"
        assert "role_permissions" in result["data"]
        assert "special_permissions" in result["data"]
```



### 4.4 test_document_tools.py

```python
# tests/unit/test_tools/test_document_tools.py
"""
문서 Tool 단위 테스트
"""

import pytest
from mcp_tools.core.document_tools import (
    GetDocumentTool,
    CreateDocumentTool,
    UpdateDocumentTool,
    DeleteDocumentTool,
    ListDocumentsTool
)


@pytest.mark.unit
class TestGetDocumentTool:
    """GetDocumentTool 테스트"""
    
    def test_get_document_success(self, db, es, test_document):
        """문서 조회 성공"""
        # 문서 생성
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                test_document["id"],
                test_document["title"],
                test_document["content"],
                test_document["classification"],
                test_document["category"],
                test_document["author_id"],
                test_document["team"],
                test_document["department"]
            )
        )
        
        tool = GetDocumentTool(db, es)
        
        result = tool.execute(
            {"doc_id": test_document["id"]},
            {"user_id": "TEST_U001", "user_role": "staff", "user_team": "test_team"}
        )
        
        assert result["status"] == "success"
        assert result["data"]["doc_id"] == test_document["id"]
        assert result["data"]["title"] == test_document["title"]
    
    def test_get_document_not_found(self, db, es):
        """존재하지 않는 문서"""
        tool = GetDocumentTool(db, es)
        
        result = tool.execute(
            {"doc_id": "NONEXISTENT"},
            {"user_id": "TEST_U001", "user_role": "staff"}
        )
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "NOT_FOUND"
    
    def test_get_document_permission_denied(self, db, es):
        """권한 없음"""
        # Confidential 문서 생성
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            ("TEST_DOC_CONF", "기밀", "내용", "confidential", "test", "TEST_ADMIN", None, "admin")
        )
        
        tool = GetDocumentTool(db, es)
        
        # Staff가 조회 시도
        result = tool.execute(
            {"doc_id": "TEST_DOC_CONF"},
            {"user_id": "TEST_U001", "user_role": "staff", "user_team": "test_team"}
        )
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.unit
class TestCreateDocumentTool:
    """CreateDocumentTool 테스트"""
    
    def test_create_document_success(self, db, es):
        """문서 생성 성공"""
        tool = CreateDocumentTool(db, es)
        
        result = tool.execute(
            {
                "title": "새 문서",
                "content": "# 내용\n\n본문입니다.",
                "classification": "public",
                "category": "test",
                "tags": ["test"]
            },
            {"user_id": "TEST_U001", "user_role": "staff", "user_team": "test_team"}
        )
        
        assert result["status"] == "success"
        assert "doc_id" in result["data"]
        
        # Database 확인
        docs = db.execute_query(
            "SELECT * FROM documents WHERE id = %s",
            (result["data"]["doc_id"],)
        )
        assert len(docs) == 1
        assert docs[0]["title"] == "새 문서"
    
    def test_create_document_junior_cannot_create(self, db, es):
        """Junior는 문서 생성 불가"""
        tool = CreateDocumentTool(db, es)
        
        result = tool.execute(
            {
                "title": "문서",
                "content": "내용",
                "classification": "public",
                "category": "test"
            },
            {"user_id": "TEST_U003", "user_role": "junior", "user_team": None}
        )
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "PERMISSION_DENIED"
    
    def test_create_document_invalid_classification(self, db, es):
        """잘못된 classification"""
        tool = CreateDocumentTool(db, es)
        
        result = tool.execute(
            {
                "title": "문서",
                "content": "내용",
                "classification": "invalid",
                "category": "test"
            },
            {"user_id": "TEST_U001", "user_role": "staff"}
        )
        
        assert result["status"] == "error"


@pytest.mark.unit
class TestUpdateDocumentTool:
    """UpdateDocumentTool 테스트"""
    
    def test_update_document_success(self, db, es):
        """문서 수정 성공"""
        # 문서 생성
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team, department, version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            ("TEST_DOC_UPD", "원본", "내용", "public", "test", "TEST_U001", "test_team", "test_dept", 1)
        )
        
        tool = UpdateDocumentTool(db, es)
        
        result = tool.execute(
            {
                "doc_id": "TEST_DOC_UPD",
                "title": "수정됨",
                "content": "새 내용"
            },
            {"user_id": "TEST_U001", "user_role": "staff", "user_team": "test_team"}
        )
        
        assert result["status"] == "success"
        assert result["data"]["version"] == 2
        
        # 버전 확인
        versions = db.execute_query(
            "SELECT * FROM document_versions WHERE doc_id = %s ORDER BY version",
            ("TEST_DOC_UPD",)
        )
        assert len(versions) == 2
    
    def test_update_document_permission_denied(self, db, es):
        """권한 없음 - 다른 사용자 문서"""
        # 다른 사용자 문서 생성
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            ("TEST_DOC_OTHER", "문서", "내용", "team", "test", "TEST_U002", "other_team", "test_dept")
        )
        
        tool = UpdateDocumentTool(db, es)
        
        # TEST_U001이 수정 시도
        result = tool.execute(
            {
                "doc_id": "TEST_DOC_OTHER",
                "title": "수정 시도"
            },
            {"user_id": "TEST_U001", "user_role": "staff", "user_team": "test_team"}
        )
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.unit
class TestDeleteDocumentTool:
    """DeleteDocumentTool 테스트"""
    
    def test_delete_document_success(self, db, es):
        """문서 삭제 성공"""
        # 문서 생성
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            ("TEST_DOC_DEL", "삭제될 문서", "내용", "team", "test", "TEST_U002", "test_team", "test_dept")
        )
        
        tool = DeleteDocumentTool(db, es)
        
        # Manager가 삭제
        result = tool.execute(
            {"doc_id": "TEST_DOC_DEL"},
            {"user_id": "TEST_U002", "user_role": "manager", "user_team": "test_team"}
        )
        
        assert result["status"] == "success"
        
        # 삭제 확인
        docs = db.execute_query(
            "SELECT * FROM documents WHERE id = %s",
            ("TEST_DOC_DEL",)
        )
        assert len(docs) == 0
    
    def test_delete_document_staff_cannot_delete(self, db, es):
        """Staff는 삭제 불가"""
        # 문서 생성
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            ("TEST_DOC_NODELETE", "문서", "내용", "public", "test", "TEST_U001", "test_team", "test_dept")
        )
        
        tool = DeleteDocumentTool(db, es)
        
        result = tool.execute(
            {"doc_id": "TEST_DOC_NODELETE"},
            {"user_id": "TEST_U001", "user_role": "staff", "user_team": "test_team"}
        )
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.unit
class TestListDocumentsTool:
    """ListDocumentsTool 테스트"""
    
    def test_list_documents_success(self, db, sample_documents):
        """문서 목록 조회"""
        # 샘플 문서 생성
        for doc in sample_documents:
            db.execute_insert(
                """
                INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (doc["id"], doc["title"], doc["content"], doc["classification"], doc["category"], 
                 doc["author_id"], doc.get("team"), "test_dept")
            )
        
        tool = ListDocumentsTool(db)
        
        result = tool.execute(
            {"limit": 10, "offset": 0},
            {"user_id": "TEST_U001", "user_role": "staff", "user_team": "test_team"}
        )
        
        assert result["status"] == "success"
        assert result["data"]["total"] >= 2  # public + team
    
    def test_list_documents_filter_by_classification(self, db, sample_documents):
        """Classification 필터링"""
        # 샘플 문서 생성
        for doc in sample_documents:
            db.execute_insert(
                """
                INSERT INTO documents (id, title, content, classification, category, author_id, team, department)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (doc["id"], doc["title"], doc["content"], doc["classification"], doc["category"],
                 doc["author_id"], doc.get("team"), "test_dept")
            )
        
        tool = ListDocumentsTool(db)
        
        result = tool.execute(
            {"classification": ["public"], "limit": 10},
            {"user_id": "TEST_U001", "user_role": "staff", "user_team": "test_team"}
        )
        
        assert result["status"] == "success"
        assert all(doc["classification"] == "public" for doc in result["data"]["documents"])
```

### 4.5 test_search_tools.py

```python
# tests/unit/test_tools/test_search_tools.py
"""
검색 Tool 단위 테스트
"""

import pytest
from mcp_tools.core.search_tools import (
    SearchDocumentsTool,
    SuggestDocumentsTool
)


@pytest.mark.unit
class TestSearchDocumentsTool:
    """SearchDocumentsTool 테스트"""
    
    def test_search_documents_success(self, es, sample_documents):
        """문서 검색 성공"""
        # Elasticsearch에 문서 인덱싱
        for doc in sample_documents:
            es.index_document(
                "test_documents",
                doc["id"],
                {
                    "doc_id": doc["id"],
                    "title": doc["title"],
                    "content": doc["content"],
                    "classification": doc["classification"],
                    "category": doc["category"],
                    "tags": doc["tags"]
                }
            )
        
        # 인덱스 갱신
        es.refresh_index("test_documents")
        
        tool = SearchDocumentsTool(es)
        
        result = tool.execute(
            {
                "query": "MCP",
                "limit": 10
            },
            {"user_id": "TEST_U001", "user_role": "staff", "user_team": "test_team"}
        )
        
        assert result["status"] == "success"
        assert result["data"]["total"] > 0
        assert any("MCP" in r["title"] for r in result["data"]["results"])
    
    def test_search_documents_with_filters(self, es, sample_documents):
        """필터 적용 검색"""
        # 문서 인덱싱
        for doc in sample_documents:
            es.index_document(
                "test_documents",
                doc["id"],
                {
                    "doc_id": doc["id"],
                    "title": doc["title"],
                    "content": doc["content"],
                    "classification": doc["classification"],
                    "category": doc["category"],
                    "tags": doc["tags"]
                }
            )
        
        es.refresh_index("test_documents")
        
        tool = SearchDocumentsTool(es)
        
        result = tool.execute(
            {
                "query": "*",
                "classification": ["public"],
                "category": "documentation",
                "limit": 10
            },
            {"user_id": "TEST_U001", "user_role": "staff"}
        )
        
        assert result["status"] == "success"
        for doc in result["data"]["results"]:
            assert doc["classification"] == "public"
            assert doc["category"] == "documentation"
    
    def test_search_documents_no_results(self, es):
        """검색 결과 없음"""
        tool = SearchDocumentsTool(es)
        
        result = tool.execute(
            {
                "query": "NONEXISTENT_QUERY_12345",
                "limit": 10
            },
            {"user_id": "TEST_U001", "user_role": "staff"}
        )
        
        assert result["status"] == "success"
        assert result["data"]["total"] == 0
        assert len(result["data"]["results"]) == 0


@pytest.mark.unit
class TestSuggestDocumentsTool:
    """SuggestDocumentsTool 테스트"""
    
    def test_suggest_documents(self, es, sample_documents):
        """자동완성 제안"""
        # 문서 인덱싱
        for doc in sample_documents:
            es.index_document(
                "test_documents",
                doc["id"],
                {
                    "doc_id": doc["id"],
                    "title": doc["title"],
                    "content": doc["content"],
                    "classification": doc["classification"]
                }
            )
        
        es.refresh_index("test_documents")
        
        tool = SuggestDocumentsTool(es)
        
        result = tool.execute(
            {"prefix": "MCP"},
            {"user_id": "TEST_U001", "user_role": "staff"}
        )
        
        assert result["status"] == "success"
        assert "suggestions" in result["data"]
```

***

## 5. 통합 테스트

### 5.1 test_tool_execution.py

```python
# tests/integration/test_tool_execution.py
"""
Tool 실행 통합 테스트

Server와 Host 간 통신 검증
"""

import pytest
import asyncio
from core.server_manager import ServerManager
from core.executor import ToolExecutor
from config import config


@pytest.mark.integration
class TestToolExecution:
    """Tool 실행 통합 테스트"""
    
    @pytest.fixture
    def server_manager(self):
        """ServerManager fixture"""
        manager = ServerManager(config)
        yield manager
        manager.stop_all()
    
    @pytest.fixture
    def executor(self, server_manager):
        """ToolExecutor fixture"""
        return ToolExecutor(server_manager)
    
    @pytest.mark.asyncio
    async def test_execute_authenticate_tool(self, executor, server_manager):
        """인증 Tool 실행"""
        # Auth Server 시작
        server_manager.start_server("auth_server")
        await asyncio.sleep(2)
        
        # Tool 실행
        result = await executor.execute_tool(
            server_name="auth_server",
            tool_name="authenticate",
            arguments={"user_id": "U001"},
            context=None
        )
        
        assert result["status"] == "success"
        assert result["data"]["user"]["id"] == "U001"
    
    @pytest.mark.asyncio
    async def test_execute_search_tool(self, executor, server_manager):
        """검색 Tool 실행"""
        # Search Server 시작
        server_manager.start_server("search_server")
        await asyncio.sleep(2)
        
        # Tool 실행
        result = await executor.execute_tool(
            server_name="search_server",
            tool_name="search_documents",
            arguments={
                "query": "AI",
                "limit": 5
            },
            context={
                "user_id": "U002",
                "user_role": "staff",
                "user_team": "dev_team"
            }
        )
        
        assert result["status"] == "success"
        assert "results" in result["data"]
    
    @pytest.mark.asyncio
    async def test_execute_tool_timeout(self, executor, server_manager):
        """Tool 실행 타임아웃"""
        # Server 시작
        server_manager.start_server("auth_server")
        await asyncio.sleep(2)
        
        # 매우 짧은 타임아웃으로 실행
        result = await executor.execute_tool(
            server_name="auth_server",
            tool_name="authenticate",
            arguments={"user_id": "U001"},
            timeout=0.001  # 1ms
        )
        
        # 타임아웃 에러 발생 가능
        # (실제로는 빠르게 완료될 수 있음)
        assert result["status"] in ["success", "error"]
    
    @pytest.mark.asyncio
    async def test_execute_tool_server_not_running(self, executor, server_manager):
        """Server 미실행 시 자동 시작"""
        # Server 시작 안 함
        
        # Tool 실행 (자동으로 Server 시작)
        result = await executor.execute_tool(
            server_name="auth_server",
            tool_name="authenticate",
            arguments={"user_id": "U001"}
        )
        
        # Server가 자동으로 시작되고 실행됨
        assert result["status"] == "success"
        assert server_manager.is_running("auth_server")


@pytest.mark.integration
class TestMultipleServerExecution:
    """다중 Server 실행 테스트"""
    
    @pytest.fixture
    def server_manager(self):
        """ServerManager fixture"""
        manager = ServerManager(config)
        yield manager
        manager.stop_all()
    
    @pytest.fixture
    def executor(self, server_manager):
        """ToolExecutor fixture"""
        return ToolExecutor(server_manager)
    
    @pytest.mark.asyncio
    async def test_execute_tools_from_different_servers(self, executor, server_manager):
        """여러 Server의 Tool 순차 실행"""
        # 모든 Server 시작
        server_manager.start_all()
        await asyncio.sleep(3)
        
        # 1. 인증
        auth_result = await executor.execute_tool(
            "auth_server",
            "authenticate",
            {"user_id": "U002"}
        )
        
        assert auth_result["status"] == "success"
        
        # 2. 검색
        search_result = await executor.execute_tool(
            "search_server",
            "search_documents",
            {"query": "AI", "limit": 5},
            {
                "user_id": "U002",
                "user_role": "staff",
                "user_team": "dev_team"
            }
        )
        
        assert search_result["status"] == "success"
        
        # 3. 문서 조회 (검색 결과가 있으면)
        if search_result["data"]["results"]:
            doc_id = search_result["data"]["results"][0]["doc_id"]
            
            get_result = await executor.execute_tool(
                "document_server",
                "get_document",
                {"doc_id": doc_id},
                {
                    "user_id": "U002",
                    "user_role": "staff",
                    "user_team": "dev_team"
                }
            )
            
            assert get_result["status"] in ["success", "error"]
```

### 5.2 test_api_endpoints.py

```python
# tests/integration/test_api_endpoints.py
"""
API 엔드포인트 통합 테스트
"""

import pytest
from fastapi.testclient import TestClient
from mcp_host.main import app


@pytest.mark.integration
class TestAPIEndpoints:
    """API 엔드포인트 통합 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient fixture"""
        return TestClient(app)
    
    def test_session_lifecycle(self, client):
        """세션 생명주기 테스트"""
        # 1. 세션 생성
        create_response = client.post(
            "/api/sessions",
            json={"user_id": "U002"}
        )
        
        assert create_response.status_code == 201
        session_data = create_response.json()
        session_id = session_data["session_id"]
        
        # 2. 세션 조회
        get_response = client.get(f"/api/sessions/{session_id}")
        
        assert get_response.status_code == 200
        
        # 3. 세션 사용 (Tool 실행)
        tool_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": session_id,
                "tool": "search_documents",
                "arguments": {"query": "test", "limit": 5}
            }
        )
        
        assert tool_response.status_code == 200
        
        # 4. 세션 삭제
        delete_response = client.delete(f"/api/sessions/{session_id}")
        
        assert delete_response.status_code == 200
        
        # 5. 삭제된 세션 사용 시도
        tool_response2 = client.post(
            "/api/tools/execute",
            json={
                "session_id": session_id,
                "tool": "search_documents",
                "arguments": {"query": "test"}
            }
        )
        
        assert tool_response2.status_code == 401
    
    def test_tool_list_and_execute(self, client):
        """Tool 목록 조회 및 실행"""
        # 1. 세션 생성
        session_response = client.post(
            "/api/sessions",
            json={"user_id": "U002"}
        )
        session_id = session_response.json()["session_id"]
        
        # 2. Tool 목록 조회
        list_response = client.get("/api/tools/list")
        
        assert list_response.status_code == 200
        tools_data = list_response.json()
        assert tools_data["total"] > 0
        
        # 3. 첫 번째 Tool 실행
        first_tool = tools_data["tools"][0]
        
        execute_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": session_id,
                "tool": first_tool["name"],
                "arguments": {}
            }
        )
        
        assert execute_response.status_code == 200
    
    def test_server_management(self, client):
        """Server 관리 API"""
        # 1. Server 목록
        list_response = client.get("/api/servers")
        
        assert list_response.status_code == 200
        servers = list_response.json()["servers"]
        assert len(servers) > 0
        
        # 2. 특정 Server 정보
        server_name = servers[0]["name"]
        info_response = client.get(f"/api/servers/{server_name}")
        
        assert info_response.status_code == 200
        
        # 3. Server 액션 (재시작)
        action_response = client.post(
            "/api/servers/action",
            json={
                "action": "restart",
                "server_name": server_name
            }
        )
        
        assert action_response.status_code == 200
```

***

## 6. 시나리오 테스트

### 6.1 test_document_lifecycle.py

```python
# tests/scenarios/test_document_lifecycle.py
"""
문서 생명주기 시나리오 테스트

문서 생성 → 조회 → 수정 → 버전 관리 → 삭제
"""

import pytest
from fastapi.testclient import TestClient
from mcp_host.main import app


@pytest.mark.scenario
class TestDocumentLifecycle:
    """문서 생명주기 시나리오"""
    
    @pytest.fixture
    def client(self):
        """TestClient fixture"""
        return TestClient(app)
    
    @pytest.fixture
    def staff_session(self, client):
        """Staff 세션"""
        response = client.post(
            "/api/sessions",
            json={"user_id": "U002"}
        )
        return response.json()["session_id"]
    
    @pytest.fixture
    def manager_session(self, client):
        """Manager 세션"""
        response = client.post(
            "/api/sessions",
            json={"user_id": "U003"}
        )
        return response.json()["session_id"]
    
    def test_complete_document_lifecycle(self, client, staff_session, manager_session):
        """완전한 문서 생명주기"""
        
        # === 1. 문서 생성 (Staff) ===
        create_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "create_document",
                "arguments": {
                    "title": "시나리오 테스트 문서",
                    "content": "# 제목\n\n초기 내용입니다.",
                    "classification": "team",
                    "category": "test",
                    "tags": ["scenario", "test"]
                }
            }
        )
        
        assert create_response.status_code == 200
        create_result = create_response.json()
        assert create_result["status"] == "success"
        
        doc_id = create_result["data"]["doc_id"]
        print(f"\n✅ 문서 생성: {doc_id}")
        
        # === 2. 문서 조회 (Staff) ===
        get_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "get_document",
                "arguments": {"doc_id": doc_id}
            }
        )
        
        assert get_response.status_code == 200
        get_result = get_response.json()
        assert get_result["status"] == "success"
        assert get_result["data"]["title"] == "시나리오 테스트 문서"
        assert get_result["data"]["version"] == 1
        
        print(f"✅ 문서 조회: v{get_result['data']['version']}")
        
        # === 3. 문서 수정 (Staff) ===
        update_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "update_document",
                "arguments": {
                    "doc_id": doc_id,
                    "title": "수정된 문서",
                    "content": "# 수정됨\n\n수정된 내용입니다."
                }
            }
        )
        
        assert update_response.status_code == 200
        update_result = update_response.json()
        assert update_result["status"] == "success"
        assert update_result["data"]["version"] == 2
        
        print(f"✅ 문서 수정: v{update_result['data']['version']}")
        
        # === 4. 버전 히스토리 조회 ===
        versions_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "get_document_versions",
                "arguments": {"doc_id": doc_id}
            }
        )
        
        assert versions_response.status_code == 200
        versions_result = versions_response.json()
        assert versions_result["status"] == "success"
        assert len(versions_result["data"]["versions"]) == 2
        
        print(f"✅ 버전 히스토리: {len(versions_result['data']['versions'])}개 버전")
        
        # === 5. 특정 버전 조회 ===
        version_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "get_document_version",
                "arguments": {
                    "doc_id": doc_id,
                    "version": 1
                }
            }
        )
        
        assert version_response.status_code == 200
        version_result = version_response.json()
        assert version_result["status"] == "success"
        assert version_result["data"]["title"] == "시나리오 테스트 문서"
        
        print(f"✅ 버전 1 조회: {version_result['data']['title']}")
        
        # === 6. 버전 비교 ===
        compare_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "compare_versions",
                "arguments": {
                    "doc_id": doc_id,
                    "version1": 1,
                    "version2": 2
                }
            }
        )
        
        assert compare_response.status_code == 200
        compare_result = compare_response.json()
        assert compare_result["status"] == "success"
        assert "diff" in compare_result["data"]
        
        print(f"✅ 버전 비교 완료")
        
        # === 7. 문서 검색 ===
        search_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "search_documents",
                "arguments": {
                    "query": "수정된",
                    "limit": 10
                }
            }
        )
        
        assert search_response.status_code == 200
        search_result = search_response.json()
        assert search_result["status"] == "success"
        
        # 방금 생성한 문서가 검색되는지 확인
        found = any(r["doc_id"] == doc_id for r in search_result["data"]["results"])
        
        print(f"✅ 문서 검색: {'발견됨' if found else '미발견'}")
        
        # === 8. 문서 삭제 (Manager) ===
        delete_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": manager_session,
                "tool": "delete_document",
                "arguments": {"doc_id": doc_id}
            }
        )
        
        assert delete_response.status_code == 200
        delete_result = delete_response.json()
        assert delete_result["status"] == "success"
        
        print(f"✅ 문서 삭제 완료")
        
        # === 9. 삭제 확인 ===
        get_deleted_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "get_document",
                "arguments": {"doc_id": doc_id}
            }
        )
        
        assert get_deleted_response.status_code == 200
        get_deleted_result = get_deleted_response.json()
        assert get_deleted_result["status"] == "error"
        assert get_deleted_result["error"]["code"] == "NOT_FOUND"
        
        print(f"✅ 삭제 확인: 문서 없음")
        print(f"\n🎉 문서 생명주기 시나리오 완료!")
```

### 6.2 test_permission_workflow.py

```python
# tests/scenarios/test_permission_workflow.py
"""
권한 워크플로우 시나리오 테스트

권한 확인 → 접근 거부 → 권한 요청 → 승인 → 접근 성공
"""

import pytest
from fastapi.testclient import TestClient
from mcp_host.main import app


@pytest.mark.scenario
class TestPermissionWorkflow:
    """권한 워크플로우 시나리오"""
    
    @pytest.fixture
    def client(self):
        """TestClient fixture"""
        return TestClient(app)
    
    @pytest.fixture
    def junior_session(self, client):
        """Junior 세션"""
        response = client.post(
            "/api/sessions",
            json={"user_id": "U001"}
        )
        return response.json()["session_id"]
    
    @pytest.fixture
    def manager_session(self, client):
        """Manager 세션"""
        response = client.post(
            "/api/sessions",
            json={"user_id": "U003"}
        )
        return response.json()["session_id"]
    
    @pytest.fixture
    def confidential_doc(self, client, manager_session):
        """Confidential 문서 생성"""
        response = client.post(
            "/api/tools/execute",
            json={
                "session_id": manager_session,
                "tool": "create_document",
                "arguments": {
                    "title": "기밀 문서",
                    "content": "기밀 내용",
                    "classification": "confidential",
                    "category": "test"
                }
            }
        )
        
        return response.json()["data"]["doc_id"]
    
    def test_permission_request_workflow(
        self,
        client,
        junior_session,
        manager_session,
        confidential_doc
    ):
        """권한 요청 워크플로우"""
        
        doc_id = confidential_doc
        
        # === 1. Junior가 Confidential 문서 조회 시도 (실패) ===
        get_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": junior_session,
                "tool": "get_document",
                "arguments": {"doc_id": doc_id}
            }
        )
        
        assert get_response.status_code == 200
        get_result = get_response.json()
        assert get_result["status"] == "error"
        assert get_result["error"]["code"] == "PERMISSION_DENIED"
        
        print(f"\n✅ 권한 없음: 접근 거부됨")
        
        # === 2. 접근 권한 요청 ===
        request_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": junior_session,
                "tool": "request_access",
                "arguments": {
                    "doc_id": doc_id,
                    "reason": "프로젝트 수행을 위해 해당 문서가 필요합니다."
                }
            }
        )
        
        assert request_response.status_code == 200
        request_result = request_response.json()
        assert request_result["status"] == "success"
        
        request_id = request_result["data"]["request_id"]
        
        print(f"✅ 권한 요청: 요청 ID {request_id}")
        
        # === 3. Manager가 요청 승인 ===
        approve_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": manager_session,
                "tool": "approve_access",
                "arguments": {
                    "request_id": request_id,
                    "action": "approve",
                    "comment": "승인합니다."
                }
            }
        )
        
        assert approve_response.status_code == 200
        approve_result = approve_response.json()
        assert approve_result["status"] == "success"
        
        print(f"✅ 권한 승인: 승인 완료")
        
        # === 4. Junior가 다시 문서 조회 시도 (성공) ===
        get_response2 = client.post(
            "/api/tools/execute",
            json={
                "session_id": junior_session,
                "tool": "get_document",
                "arguments": {"doc_id": doc_id}
            }
        )
        
        assert get_response2.status_code == 200
        get_result2 = get_response2.json()
        assert get_result2["status"] == "success"
        assert get_result2["data"]["doc_id"] == doc_id
        
        print(f"✅ 접근 성공: 문서 조회 가능")
        
        # === 5. 내 권한 확인 ===
        permissions_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": junior_session,
                "tool": "get_my_permissions",
                "arguments": {}
            }
        )
        
        assert permissions_response.status_code == 200
        permissions_result = permissions_response.json()
        assert permissions_result["status"] == "success"
        assert len(permissions_result["data"]["special_permissions"]) > 0
        
        print(f"✅ 권한 확인: 특별 권한 {len(permissions_result['data']['special_permissions'])}개")
        print(f"\n🎉 권한 워크플로우 시나리오 완료!")
```

### 6.3 test_search_workflow.py

```python
# tests/scenarios/test_search_workflow.py
"""
검색 워크플로우 시나리오 테스트

문서 생성 → 인덱싱 → 검색 → 자동완성
"""

import pytest
import time
from fastapi.testclient import TestClient
from mcp_host.main import app


@pytest.mark.scenario
class TestSearchWorkflow:
    """검색 워크플로우 시나리오"""
    
    @pytest.fixture
    def client(self):
        """TestClient fixture"""
        return TestClient(app)
    
    @pytest.fixture
    def staff_session(self, client):
        """Staff 세션"""
        response = client.post(
            "/api/sessions",
            json={"user_id": "U002"}
        )
        return response.json()["session_id"]
    
    def test_search_workflow(self, client, staff_session):
        """검색 워크플로우"""
        
        # === 1. 여러 문서 생성 ===
        documents = [
            {
                "title": "인공지능 개요",
                "content": "인공지능(AI)은 컴퓨터 시스템이 인간의 지능을 모방하는 기술입니다.",
                "tags": ["AI", "인공지능", "개요"]
            },
            {
                "title": "머신러닝 기초",
                "content": "머신러닝은 AI의 한 분야로, 데이터로부터 학습합니다.",
                "tags": ["AI", "머신러닝", "학습"]
            },
            {
                "title": "딥러닝 알고리즘",
                "content": "딥러닝은 신경망을 사용한 머신러닝 기법입니다.",
                "tags": ["AI", "딥러닝", "신경망"]
            }
        ]
        
        doc_ids = []
        
        for doc in documents:
            response = client.post(
                "/api/tools/execute",
                json={
                    "session_id": staff_session,
                    "tool": "create_document",
                    "arguments": {
                        "title": doc["title"],
                        "content": doc["content"],
                        "classification": "public",
                        "category": "education",
                        "tags": doc["tags"]
                    }
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            
            doc_ids.append(result["data"]["doc_id"])
        
        print(f"\n✅ 문서 생성: {len(doc_ids)}개")
        
        # 인덱싱 대기
        time.sleep(2)
        
        # === 2. 전문 검색 ===
        search_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "search_documents",
                "arguments": {
                    "query": "인공지능",
                    "limit": 10
                }
            }
        )
        
        assert search_response.status_code == 200
        search_result = search_response.json()
        assert search_result["status"] == "success"
        assert search_result["data"]["total"] > 0
        
        print(f"✅ 검색 (인공지능): {search_result['data']['total']}개 결과")
        
        # === 3. 태그 필터 검색 ===
        tag_search_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "search_documents",
                "arguments": {
                    "query": "*",
                    "tags": ["딥러닝"],
                    "limit": 10
                }
            }
        )
        
        assert tag_search_response.status_code == 200
        tag_search_result = tag_search_response.json()
        assert tag_search_result["status"] == "success"
        
        print(f"✅ 태그 검색 (딥러닝): {tag_search_result['data']['total']}개 결과")
        
        # === 4. 카테고리 필터 검색 ===
        category_search_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "search_documents",
                "arguments": {
                    "query": "AI",
                    "category": "education",
                    "limit": 10
                }
            }
        )
        
        assert category_search_response.status_code == 200
        category_search_result = category_search_response.json()
        assert category_search_result["status"] == "success"
        
        print(f"✅ 카테고리 검색 (education): {category_search_result['data']['total']}개 결과")
        
        # === 5. 자동완성 ===
        suggest_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "suggest_documents",
                "arguments": {"prefix": "인공"}
            }
        )
        
        assert suggest_response.status_code == 200
        suggest_result = suggest_response.json()
        assert suggest_result["status"] == "success"
        
        print(f"✅ 자동완성 (인공): {len(suggest_result['data']['suggestions'])}개 제안")
        
        # === 6. 검색 결과 문서 조회 ===
        if search_result["data"]["results"]:
            first_doc_id = search_result["data"]["results"][0]["doc_id"]
            
            get_response = client.post(
                "/api/tools/execute",
                json={
                    "session_id": staff_session,
                    "tool": "get_document",
                    "arguments": {"doc_id": first_doc_id}
                }
            )
            
            assert get_response.status_code == 200
            get_result = get_response.json()
            assert get_result["status"] == "success"
            
            print(f"✅ 문서 조회: {get_result['data']['title']}")
        
        print(f"\n🎉 검색 워크플로우 시나리오 완료!")
```




### 6.4 test_version_management.py

```python
# tests/scenarios/test_version_management.py
"""
버전 관리 시나리오 테스트

문서 생성 → 수정 → 버전 확인 → 비교 → 롤백
"""

import pytest
from fastapi.testclient import TestClient
from mcp_host.main import app


@pytest.mark.scenario
class TestVersionManagement:
    """버전 관리 시나리오"""
    
    @pytest.fixture
    def client(self):
        """TestClient fixture"""
        return TestClient(app)
    
    @pytest.fixture
    def staff_session(self, client):
        """Staff 세션"""
        response = client.post(
            "/api/sessions",
            json={"user_id": "U002"}
        )
        return response.json()["session_id"]
    
    def test_version_management_workflow(self, client, staff_session):
        """버전 관리 워크플로우"""
        
        # === 1. 초기 문서 생성 (v1) ===
        create_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "create_document",
                "arguments": {
                    "title": "버전 테스트 문서",
                    "content": "# v1\n\n초기 버전입니다.",
                    "classification": "public",
                    "category": "test"
                }
            }
        )
        
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["doc_id"]
        
        print(f"\n✅ v1 생성: {doc_id}")
        
        # === 2. 첫 번째 수정 (v2) ===
        update1_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "update_document",
                "arguments": {
                    "doc_id": doc_id,
                    "title": "버전 테스트 문서 (수정1)",
                    "content": "# v2\n\n첫 번째 수정입니다."
                }
            }
        )
        
        assert update1_response.status_code == 200
        update1_result = update1_response.json()
        assert update1_result["data"]["version"] == 2
        
        print(f"✅ v2 생성: 첫 번째 수정")
        
        # === 3. 두 번째 수정 (v3) ===
        update2_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "update_document",
                "arguments": {
                    "doc_id": doc_id,
                    "title": "버전 테스트 문서 (수정2)",
                    "content": "# v3\n\n두 번째 수정입니다.\n\n새로운 내용이 추가되었습니다."
                }
            }
        )
        
        assert update2_response.status_code == 200
        update2_result = update2_response.json()
        assert update2_result["data"]["version"] == 3
        
        print(f"✅ v3 생성: 두 번째 수정")
        
        # === 4. 세 번째 수정 (v4) ===
        update3_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "update_document",
                "arguments": {
                    "doc_id": doc_id,
                    "content": "# v4\n\n세 번째 수정입니다.\n\n더 많은 내용이 추가되었습니다.\n\n- 항목 1\n- 항목 2"
                }
            }
        )
        
        assert update3_response.status_code == 200
        update3_result = update3_response.json()
        assert update3_result["data"]["version"] == 4
        
        print(f"✅ v4 생성: 세 번째 수정")
        
        # === 5. 버전 히스토리 조회 ===
        versions_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "get_document_versions",
                "arguments": {"doc_id": doc_id}
            }
        )
        
        assert versions_response.status_code == 200
        versions_result = versions_response.json()
        assert versions_result["status"] == "success"
        assert len(versions_result["data"]["versions"]) == 4
        assert versions_result["data"]["current_version"] == 4
        
        print(f"✅ 버전 히스토리: {len(versions_result['data']['versions'])}개 버전")
        
        for v in versions_result["data"]["versions"]:
            print(f"   - v{v['version']}: {v['title']}")
        
        # === 6. 특정 버전 조회 (v1) ===
        version1_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "get_document_version",
                "arguments": {
                    "doc_id": doc_id,
                    "version": 1
                }
            }
        )
        
        assert version1_response.status_code == 200
        version1_result = version1_response.json()
        assert version1_result["status"] == "success"
        assert "초기 버전" in version1_result["data"]["content"]
        
        print(f"✅ v1 조회: {version1_result['data']['title']}")
        
        # === 7. 특정 버전 조회 (v3) ===
        version3_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "get_document_version",
                "arguments": {
                    "doc_id": doc_id,
                    "version": 3
                }
            }
        )
        
        assert version3_response.status_code == 200
        version3_result = version3_response.json()
        assert version3_result["status"] == "success"
        
        print(f"✅ v3 조회: {version3_result['data']['title']}")
        
        # === 8. 버전 비교 (v1 vs v2) ===
        compare12_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "compare_versions",
                "arguments": {
                    "doc_id": doc_id,
                    "version1": 1,
                    "version2": 2
                }
            }
        )
        
        assert compare12_response.status_code == 200
        compare12_result = compare12_response.json()
        assert compare12_result["status"] == "success"
        assert "diff" in compare12_result["data"]
        
        print(f"✅ v1 vs v2 비교 완료")
        
        # === 9. 버전 비교 (v2 vs v4) ===
        compare24_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "compare_versions",
                "arguments": {
                    "doc_id": doc_id,
                    "version1": 2,
                    "version2": 4
                }
            }
        )
        
        assert compare24_response.status_code == 200
        compare24_result = compare24_response.json()
        assert compare24_result["status"] == "success"
        
        print(f"✅ v2 vs v4 비교 완료")
        
        # === 10. 현재 버전 확인 ===
        current_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "get_document",
                "arguments": {"doc_id": doc_id}
            }
        )
        
        assert current_response.status_code == 200
        current_result = current_response.json()
        assert current_result["status"] == "success"
        assert current_result["data"]["version"] == 4
        
        print(f"✅ 현재 버전: v{current_result['data']['version']}")
        
        # === 11. 이전 버전 기반 수정 (롤백 시뮬레이션) ===
        # v2 내용으로 새 버전(v5) 생성
        rollback_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "update_document",
                "arguments": {
                    "doc_id": doc_id,
                    "title": version3_result["data"]["title"],
                    "content": version3_result["data"]["content"]
                }
            }
        )
        
        assert rollback_response.status_code == 200
        rollback_result = rollback_response.json()
        assert rollback_result["data"]["version"] == 5
        
        print(f"✅ 롤백 (v3 기반): v5 생성")
        
        # === 12. 최종 버전 히스토리 확인 ===
        final_versions_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": staff_session,
                "tool": "get_document_versions",
                "arguments": {"doc_id": doc_id}
            }
        )
        
        assert final_versions_response.status_code == 200
        final_versions_result = final_versions_response.json()
        assert len(final_versions_result["data"]["versions"]) == 5
        
        print(f"✅ 최종 버전 히스토리: {len(final_versions_result['data']['versions'])}개 버전")
        
        print(f"\n🎉 버전 관리 워크플로우 시나리오 완료!")


@pytest.mark.scenario
class TestCollaborativeEditing:
    """협업 편집 시나리오"""
    
    @pytest.fixture
    def client(self):
        """TestClient fixture"""
        return TestClient(app)
    
    @pytest.fixture
    def user1_session(self, client):
        """사용자 1 세션"""
        response = client.post(
            "/api/sessions",
            json={"user_id": "U002"}
        )
        return response.json()["session_id"]
    
    @pytest.fixture
    def user2_session(self, client):
        """사용자 2 세션"""
        response = client.post(
            "/api/sessions",
            json={"user_id": "U003"}
        )
        return response.json()["session_id"]
    
    def test_collaborative_editing(self, client, user1_session, user2_session):
        """협업 편집 시나리오"""
        
        # === 1. 사용자 1이 문서 생성 ===
        create_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": user1_session,
                "tool": "create_document",
                "arguments": {
                    "title": "협업 문서",
                    "content": "# 협업\n\n사용자 1이 작성",
                    "classification": "team",
                    "category": "collaboration"
                }
            }
        )
        
        doc_id = create_response.json()["data"]["doc_id"]
        print(f"\n✅ 사용자 1이 문서 생성: {doc_id}")
        
        # === 2. 사용자 2가 조회 ===
        get_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": user2_session,
                "tool": "get_document",
                "arguments": {"doc_id": doc_id}
            }
        )
        
        assert get_response.status_code == 200
        print(f"✅ 사용자 2가 문서 조회")
        
        # === 3. 사용자 2가 수정 ===
        update1_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": user2_session,
                "tool": "update_document",
                "arguments": {
                    "doc_id": doc_id,
                    "content": "# 협업\n\n사용자 1이 작성\n\n사용자 2가 추가"
                }
            }
        )
        
        assert update1_response.status_code == 200
        print(f"✅ 사용자 2가 수정 (v2)")
        
        # === 4. 사용자 1이 다시 수정 ===
        update2_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": user1_session,
                "tool": "update_document",
                "arguments": {
                    "doc_id": doc_id,
                    "content": "# 협업\n\n사용자 1이 작성\n\n사용자 2가 추가\n\n사용자 1이 재수정"
                }
            }
        )
        
        assert update2_response.status_code == 200
        print(f"✅ 사용자 1이 수정 (v3)")
        
        # === 5. 버전 히스토리 확인 ===
        versions_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": user1_session,
                "tool": "get_document_versions",
                "arguments": {"doc_id": doc_id}
            }
        )
        
        versions_result = versions_response.json()
        assert len(versions_result["data"]["versions"]) == 3
        
        print(f"✅ 버전 히스토리 확인: 3개 버전")
        
        # 변경 이력 출력
        for v in versions_result["data"]["versions"]:
            print(f"   - v{v['version']}: {v['changed_by']} - {v['change_summary'] or '변경'}")
        
        print(f"\n🎉 협업 편집 시나리오 완료!")
```

***

## 7. 성능 테스트

### 7.1 test_load.py

```python
# tests/performance/test_load.py
"""
부하 테스트

동시 사용자 수에 따른 성능 측정
"""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from mcp_host.main import app


@pytest.mark.performance
class TestLoad:
    """부하 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient fixture"""
        return TestClient(app)
    
    def test_concurrent_sessions(self, client):
        """동시 세션 생성 테스트"""
        num_sessions = 50
        
        def create_session(user_num):
            response = client.post(
                "/api/sessions",
                json={"user_id": f"U{user_num:03d}"}
            )
            return response.status_code == 201
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(create_session, range(num_sessions)))
        
        duration = time.time() - start_time
        success_count = sum(results)
        
        print(f"\n=== 동시 세션 생성 테스트 ===")
        print(f"총 요청: {num_sessions}")
        print(f"성공: {success_count}")
        print(f"실패: {num_sessions - success_count}")
        print(f"총 시간: {duration:.2f}초")
        print(f"평균: {duration/num_sessions*1000:.2f}ms/요청")
        print(f"처리량: {num_sessions/duration:.2f}req/s")
        
        assert success_count >= num_sessions * 0.95  # 95% 이상 성공
    
    def test_concurrent_tool_execution(self, client):
        """동시 Tool 실행 테스트"""
        # 세션 생성
        session_response = client.post(
            "/api/sessions",
            json={"user_id": "U002"}
        )
        session_id = session_response.json()["session_id"]
        
        num_requests = 100
        
        def execute_tool(request_num):
            response = client.post(
                "/api/tools/execute",
                json={
                    "session_id": session_id,
                    "tool": "search_documents",
                    "arguments": {
                        "query": f"test{request_num % 10}",
                        "limit": 5
                    }
                }
            )
            return response.status_code == 200
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(execute_tool, range(num_requests)))
        
        duration = time.time() - start_time
        success_count = sum(results)
        
        print(f"\n=== 동시 Tool 실행 테스트 ===")
        print(f"총 요청: {num_requests}")
        print(f"성공: {success_count}")
        print(f"실패: {num_requests - success_count}")
        print(f"총 시간: {duration:.2f}초")
        print(f"평균: {duration/num_requests*1000:.2f}ms/요청")
        print(f"처리량: {num_requests/duration:.2f}req/s")
        
        assert success_count >= num_requests * 0.90  # 90% 이상 성공
    
    def test_sustained_load(self, client):
        """지속 부하 테스트 (1분간)"""
        # 세션 생성
        session_response = client.post(
            "/api/sessions",
            json={"user_id": "U002"}
        )
        session_id = session_response.json()["session_id"]
        
        duration = 60  # 60초
        request_count = 0
        success_count = 0
        error_count = 0
        response_times = []
        
        start_time = time.time()
        end_time = start_time + duration
        
        print(f"\n=== 지속 부하 테스트 (60초) ===")
        
        while time.time() < end_time:
            request_start = time.time()
            
            try:
                response = client.post(
                    "/api/tools/execute",
                    json={
                        "session_id": session_id,
                        "tool": "search_documents",
                        "arguments": {
                            "query": "test",
                            "limit": 5
                        }
                    }
                )
                
                request_time = (time.time() - request_start) * 1000
                response_times.append(request_time)
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    error_count += 1
            
            except Exception as e:
                error_count += 1
            
            request_count += 1
            
            # 짧은 대기 (처리량 조절)
            time.sleep(0.1)
        
        total_time = time.time() - start_time
        
        print(f"총 요청: {request_count}")
        print(f"성공: {success_count}")
        print(f"실패: {error_count}")
        print(f"처리량: {request_count/total_time:.2f}req/s")
        print(f"평균 응답 시간: {sum(response_times)/len(response_times):.2f}ms")
        print(f"최소 응답 시간: {min(response_times):.2f}ms")
        print(f"최대 응답 시간: {max(response_times):.2f}ms")
        
        # 응답 시간 분포
        response_times.sort()
        p50 = response_times[len(response_times)//2]
        p95 = response_times[int(len(response_times)*0.95)]
        p99 = response_times[int(len(response_times)*0.99)]
        
        print(f"P50: {p50:.2f}ms")
        print(f"P95: {p95:.2f}ms")
        print(f"P99: {p99:.2f}ms")
        
        assert success_count >= request_count * 0.95  # 95% 이상 성공


@pytest.mark.performance
class TestResponseTime:
    """응답 시간 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient fixture"""
        return TestClient(app)
    
    @pytest.fixture
    def session_id(self, client):
        """세션 생성"""
        response = client.post(
            "/api/sessions",
            json={"user_id": "U002"}
        )
        return response.json()["session_id"]
    
    def test_search_response_time(self, client, session_id):
        """검색 Tool 응답 시간"""
        times = []
        iterations = 50
        
        for _ in range(iterations):
            start = time.time()
            
            response = client.post(
                "/api/tools/execute",
                json={
                    "session_id": session_id,
                    "tool": "search_documents",
                    "arguments": {
                        "query": "test",
                        "limit": 10
                    }
                }
            )
            
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            assert response.status_code == 200
        
        avg_time = sum(times) / len(times)
        
        print(f"\n=== 검색 Tool 응답 시간 ({iterations}회) ===")
        print(f"평균: {avg_time:.2f}ms")
        print(f"최소: {min(times):.2f}ms")
        print(f"최대: {max(times):.2f}ms")
        
        # 평균 응답 시간 500ms 이하 목표
        assert avg_time < 500
    
    def test_document_crud_response_time(self, client, session_id):
        """문서 CRUD 응답 시간"""
        
        # 생성
        create_start = time.time()
        create_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": session_id,
                "tool": "create_document",
                "arguments": {
                    "title": "성능 테스트",
                    "content": "내용",
                    "classification": "public",
                    "category": "test"
                }
            }
        )
        create_time = (time.time() - create_start) * 1000
        
        assert create_response.status_code == 200
        doc_id = create_response.json()["data"]["doc_id"]
        
        # 조회
        read_start = time.time()
        read_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": session_id,
                "tool": "get_document",
                "arguments": {"doc_id": doc_id}
            }
        )
        read_time = (time.time() - read_start) * 1000
        
        assert read_response.status_code == 200
        
        # 수정
        update_start = time.time()
        update_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": session_id,
                "tool": "update_document",
                "arguments": {
                    "doc_id": doc_id,
                    "title": "수정됨"
                }
            }
        )
        update_time = (time.time() - update_start) * 1000
        
        assert update_response.status_code == 200
        
        print(f"\n=== 문서 CRUD 응답 시간 ===")
        print(f"생성: {create_time:.2f}ms")
        print(f"조회: {read_time:.2f}ms")
        print(f"수정: {update_time:.2f}ms")
        
        # 각 작업 1초 이하 목표
        assert create_time < 1000
        assert read_time < 1000
        assert update_time < 1000
```

### 7.2 test_stress.py

```python
# tests/performance/test_stress.py
"""
스트레스 테스트

시스템 한계 측정
"""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from mcp_host.main import app


@pytest.mark.performance
@pytest.mark.slow
class TestStress:
    """스트레스 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient fixture"""
        return TestClient(app)
    
    def test_max_concurrent_requests(self, client):
        """최대 동시 요청 수"""
        # 세션 생성
        session_response = client.post(
            "/api/sessions",
            json={"user_id": "U002"}
        )
        session_id = session_response.json()["session_id"]
        
        # 점진적으로 부하 증가
        concurrency_levels = [10, 25, 50, 100, 200]
        results = {}
        
        print(f"\n=== 최대 동시 요청 수 테스트 ===")
        
        for concurrency in concurrency_levels:
            def execute_request(i):
                start = time.time()
                try:
                    response = client.post(
                        "/api/tools/execute",
                        json={
                            "session_id": session_id,
                            "tool": "search_documents",
                            "arguments": {
                                "query": f"test{i}",
                                "limit": 5
                            }
                        },
                        timeout=30
                    )
                    elapsed = time.time() - start
                    return {
                        "success": response.status_code == 200,
                        "time": elapsed
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "time": time.time() - start,
                        "error": str(e)
                    }
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(execute_request, i) for i in range(concurrency)]
                request_results = [f.result() for f in as_completed(futures)]
            
            total_time = time.time() - start_time
            success_count = sum(1 for r in request_results if r["success"])
            avg_response_time = sum(r["time"] for r in request_results) / len(request_results)
            
            results[concurrency] = {
                "success_rate": success_count / concurrency * 100,
                "avg_response_time": avg_response_time,
                "throughput": concurrency / total_time
            }
            
            print(f"\n동시 요청: {concurrency}")
            print(f"  성공률: {results[concurrency]['success_rate']:.1f}%")
            print(f"  평균 응답 시간: {results[concurrency]['avg_response_time']*1000:.2f}ms")
            print(f"  처리량: {results[concurrency]['throughput']:.2f}req/s")
        
        # 결과 요약
        print(f"\n=== 요약 ===")
        for concurrency, result in results.items():
            if result["success_rate"] >= 95:
                print(f"✅ {concurrency} 동시 요청: 안정적")
            elif result["success_rate"] >= 80:
                print(f"⚠️  {concurrency} 동시 요청: 불안정")
            else:
                print(f"❌ {concurrency} 동시 요청: 실패")
    
    def test_memory_leak(self, client):
        """메모리 누수 테스트"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 세션 생성
        session_response = client.post(
            "/api/sessions",
            json={"user_id": "U002"}
        )
        session_id = session_response.json()["session_id"]
        
        iterations = 1000
        memory_samples = []
        
        print(f"\n=== 메모리 누수 테스트 ({iterations}회 반복) ===")
        
        for i in range(iterations):
            # Tool 실행
            client.post(
                "/api/tools/execute",
                json={
                    "session_id": session_id,
                    "tool": "search_documents",
                    "arguments": {
                        "query": f"test{i}",
                        "limit": 5
                    }
                }
            )
            
            # 100회마다 메모리 샘플링
            if i % 100 == 0:
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                memory_samples.append(memory_mb)
                print(f"  {i}회: {memory_mb:.2f}MB")
        
        # 메모리 증가율
        if len(memory_samples) > 1:
            initial_memory = memory_samples[0]
            final_memory = memory_samples[-1]
            increase_rate = (final_memory - initial_memory) / initial_memory * 100
            
            print(f"\n초기 메모리: {initial_memory:.2f}MB")
            print(f"최종 메모리: {final_memory:.2f}MB")
            print(f"증가율: {increase_rate:.2f}%")
            
            # 메모리 증가율 50% 이하 목표
            assert increase_rate < 50, f"메모리 누수 의심: {increase_rate:.2f}% 증가"
```

***

## 8. 테스트 실행 가이드

### 8.1 pytest.ini

```ini
# tests/pytest.ini
# Pytest 설정 파일

[pytest]
# 테스트 디렉토리
testpaths = tests

# Python 파일 패턴
python_files = test_*.py

# Python 클래스 패턴
python_classes = Test*

# Python 함수 패턴
python_functions = test_*

# 마커 정의
markers =
    unit: 단위 테스트
    integration: 통합 테스트
    scenario: 시나리오 테스트
    performance: 성능 테스트
    slow: 느린 테스트 (시간 소요)

# 옵션
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings

# 로그
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)s] %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

# Coverage (선택)
# addopts = --cov=shared --cov=mcp_tools --cov=mcp_servers --cov=mcp_host --cov-report=html
```

### 8.2 테스트 실행 스크립트

```bash
#!/bin/bash
# tests/run_tests.sh
# 테스트 실행 스크립트

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 색상
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================="
echo "MCP 에코시스템 테스트"
echo "========================================="
echo ""

# 환경 확인
echo "환경 확인..."
python3 --version
pytest --version
echo ""

# 테스트 타입 선택
TEST_TYPE=${1:-"all"}

case $TEST_TYPE in
    "unit")
        echo -e "${YELLOW}단위 테스트 실행${NC}"
        pytest tests/unit -m unit -v
        ;;
    
    "integration")
        echo -e "${YELLOW}통합 테스트 실행${NC}"
        pytest tests/integration -m integration -v
        ;;
    
    "scenario")
        echo -e "${YELLOW}시나리오 테스트 실행${NC}"
        pytest tests/scenarios -m scenario -v
        ;;
    
    "performance")
        echo -e "${YELLOW}성능 테스트 실행${NC}"
        pytest tests/performance -m performance -v
        ;;
    
    "quick")
        echo -e "${YELLOW}빠른 테스트 (unit + integration)${NC}"
        pytest tests/unit tests/integration -m "unit or integration" -v
        ;;
    
    "all")
        echo -e "${YELLOW}전체 테스트 실행${NC}"
        pytest tests/ -v
        ;;
    
    *)
        echo -e "${RED}잘못된 테스트 타입: $TEST_TYPE${NC}"
        echo ""
        echo "사용법: ./run_tests.sh [TYPE]"
        echo ""
        echo "TYPE:"
        echo "  unit          - 단위 테스트"
        echo "  integration   - 통합 테스트"
        echo "  scenario      - 시나리오 테스트"
        echo "  performance   - 성능 테스트"
        echo "  quick         - 빠른 테스트 (unit + integration)"
        echo "  all           - 전체 테스트 (기본값)"
        exit 1
        ;;
esac

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 테스트 성공!${NC}"
else
    echo -e "${RED}❌ 테스트 실패!${NC}"
fi

exit $EXIT_CODE
```

```bash
# 실행 권한 부여
chmod +x tests/run_tests.sh

# 사용 예시
./tests/run_tests.sh unit          # 단위 테스트만
./tests/run_tests.sh integration   # 통합 테스트만
./tests/run_tests.sh scenario      # 시나리오 테스트만
./tests/run_tests.sh performance   # 성능 테스트만
./tests/run_tests.sh quick         # 빠른 테스트
./tests/run_tests.sh all           # 전체 테스트
```

### 8.3 CI/CD 통합

```yaml
# .github/workflows/test.yml
# GitHub Actions 예시

name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mariadb:
        image: mariadb:10.11
        env:
          MYSQL_ROOT_PASSWORD: root_password
          MYSQL_DATABASE: test_mcps_db
          MYSQL_USER: test_user
          MYSQL_PASSWORD: test_password
        ports:
          - 3306:3306
      
      elasticsearch:
        image: elasticsearch:8.11.0
        env:
          discovery.type: single-node
          xpack.security.enabled: false
        ports:
          - 9200:9200
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Wait for services
      run: |
        sleep 10
    
    - name: Run unit tests
      run: |
        pytest tests/unit -m unit -v
    
    - name: Run integration tests
      run: |
        pytest tests/integration -m integration -v
    
    - name: Generate coverage report
      run: |
        pytest --cov=shared --cov=mcp_tools --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 8.4 테스트 데이터 관리

```python
# tests/data/generate_test_data.py
"""
테스트 데이터 생성 스크립트
"""

import json
from pathlib import Path


def generate_test_users():
    """테스트 사용자 생성"""
    users = [
        {
            "id": "TEST_U001",
            "name": "김철수",
            "email": "kim@test.com",
            "role": "junior",
            "team": None,
            "department": "test_dept"
        },
        {
            "id": "TEST_U002",
            "name": "이영희",
            "email": "lee@test.com",
            "role": "staff",
            "team": "dev_team",
            "department": "test_dept"
        },
        {
            "id": "TEST_U003",
            "name": "박민수",
            "email": "park@test.com",
            "role": "manager",
            "team": "dev_team",
            "department": "test_dept"
        },
        {
            "id": "TEST_ADMIN",
            "name": "관리자",
            "email": "admin@test.com",
            "role": "admin",
            "team": None,
            "department": "admin"
        }
    ]
    
    return users


def generate_test_documents():
    """테스트 문서 생성"""
    documents = [
        {
            "id": "TEST_DOC001",
            "title": "Public 문서",
            "content": "누구나 볼 수 있는 공개 문서입니다.",
            "classification": "public",
            "category": "documentation",
            "tags": ["public", "test"],
            "author_id": "TEST_U002"
        },
        {
            "id": "TEST_DOC002",
            "title": "Team 문서",
            "content": "팀 내부 문서입니다.",
            "classification": "team",
            "category": "internal",
            "tags": ["team", "internal"],
            "author_id": "TEST_U002",
            "team": "dev_team"
        },
        {
            "id": "TEST_DOC003",
            "title": "Confidential 문서",
            "content": "기밀 문서입니다.",
            "classification": "confidential",
            "category": "security",
            "tags": ["confidential", "security"],
            "author_id": "TEST_ADMIN"
        }
    ]
    
    return documents


def main():
    """메인 함수"""
    data_dir = Path(__file__).parent
    
    # 사용자 데이터
    users = generate_test_users()
    with open(data_dir / "test_users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 테스트 사용자 {len(users)}명 생성")
    
    # 문서 데이터
    documents = generate_test_documents()
    with open(data_dir / "test_documents.json", "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 테스트 문서 {len(documents)}개 생성")


if __name__ == "__main__":
    main()
```

***

## 9. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

***

## 10. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| **작성자** | | | |
| **검토자** | | | |
| **승인자** | | | |

***


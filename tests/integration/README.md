# Integration Tests

## 개요

이 디렉토리는 여러 컴포넌트 간의 통합 테스트를 포함합니다.

## 테스트 원칙

- **실제 환경**: 실제 DB, ES와 연동하여 테스트
- **격리된 환경**: 테스트용 DB/ES 사용 (mcps_test)
- **데이터 클린업**: 각 테스트 후 데이터 정리
- **트랜잭션**: 가능한 경우 트랜잭션 롤백

## 테스트 구조

```
integration/
├── test_database_integration.py       # DB 연동 테스트
├── test_elasticsearch_integration.py  # ES 연동 테스트
├── test_mcp_host_integration.py       # MCP Host 통합 테스트
├── test_api_gateway_integration.py    # API Gateway 통합 테스트
└── test_mcp_server_integration.py     # MCP Server 통합 테스트
```

## 실행 방법

```bash
# 전체 통합 테스트 실행
pytest tests/integration/

# 특정 파일 테스트
pytest tests/integration/test_database_integration.py

# 상세 로그 포함
pytest tests/integration/ -v -s
```

## 사전 준비

### 1. 테스트 DB 생성

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS mcps_test;"
mysql -u root -p mcps_test < data/database/schema.sql
```

### 2. 테스트 ES 인덱스 생성

```bash
python scripts/init_elasticsearch.py --index-prefix mcps_test
```

### 3. 환경 변수 설정

```bash
# .env.test 파일 생성
cp .env .env.test

# 테스트 DB/ES 설정
MARIADB_DATABASE=mcps_test
ES_INDEX_PREFIX=mcps_test
```

## 작성 가이드

### 테스트 파일명
- `test_<컴포넌트>_integration.py` 형식
- 예: `test_database_integration.py`

### Fixture 활용

```python
import pytest
from shared.database import DatabaseManager

@pytest.fixture(scope="function")
def db_manager():
    """각 테스트마다 DB 연결 생성 및 정리"""
    config = load_test_config()
    db = DatabaseManager(config)
    yield db
    # Cleanup
    db.execute_query("DELETE FROM users WHERE id LIKE 'TEST%'")
    db.close()

def test_user_crud_operations(db_manager):
    """사용자 CRUD 통합 테스트"""
    # Create
    user_id = "TEST001"
    db_manager.execute_query(
        "INSERT INTO users (id, name, role) VALUES (%s, %s, %s)",
        (user_id, "Test User", "staff")
    )
    
    # Read
    result = db_manager.execute_query(
        "SELECT * FROM users WHERE id = %s", (user_id,)
    )
    assert len(result) == 1
    assert result[0]["name"] == "Test User"
    
    # Update
    db_manager.execute_query(
        "UPDATE users SET role = %s WHERE id = %s",
        ("manager", user_id)
    )
    result = db_manager.execute_query(
        "SELECT role FROM users WHERE id = %s", (user_id,)
    )
    assert result[0]["role"] == "manager"
    
    # Delete
    db_manager.execute_query("DELETE FROM users WHERE id = %s", (user_id,))
    result = db_manager.execute_query(
        "SELECT * FROM users WHERE id = %s", (user_id,)
    )
    assert len(result) == 0
```

## 주의사항

1. **테스트 데이터 격리**: 테스트 ID는 `TEST` 접두사 사용
2. **병렬 실행 주의**: DB 경합 가능성 있음
3. **실행 시간**: 단위 테스트보다 느림 (DB/ES 연동)
4. **CI/CD**: 테스트 환경 자동 구성 필요

## 필요한 패키지

```txt
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.26.0
```

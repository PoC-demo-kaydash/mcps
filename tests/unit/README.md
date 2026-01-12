# Unit Tests

## 개요

이 디렉토리는 개별 모듈과 함수의 단위 테스트를 포함합니다.

## 테스트 원칙

- **독립성**: 각 테스트는 독립적으로 실행 가능
- **Mock 사용**: 외부 의존성(DB, ES)은 Mock으로 처리
- **빠른 실행**: 단위 테스트는 빠르게 실행되어야 함
- **명확한 검증**: 하나의 기능만 테스트

## 테스트 구조

```
unit/
├── test_shared.py              # shared 모듈 테스트
├── test_database.py            # DatabaseManager 테스트
├── test_elasticsearch.py       # ElasticsearchManager 테스트
├── test_permissions.py         # PermissionEngine 테스트
├── test_mcp_protocol.py        # MCP Protocol 테스트
└── test_utils.py               # 유틸리티 함수 테스트
```

## 실행 방법

```bash
# 전체 단위 테스트 실행
pytest tests/unit/

# 특정 파일 테스트
pytest tests/unit/test_shared.py

# 커버리지 포함
pytest tests/unit/ --cov=shared --cov-report=html
```

## 작성 가이드

### 테스트 파일명
- `test_<모듈명>.py` 형식
- 예: `test_database.py`

### 테스트 함수명
- `test_<기능>_<시나리오>()` 형식
- 예: `test_get_user_by_id_success()`
- 예: `test_get_user_by_id_not_found()`

### 예제

```python
import pytest
from unittest.mock import Mock, patch
from shared.database import DatabaseManager

def test_execute_query_success():
    """쿼리 실행 성공 테스트"""
    # Arrange
    db = DatabaseManager(config)
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [{"id": "U001"}]
    
    # Act
    with patch.object(db, 'get_connection') as mock_conn:
        mock_conn.return_value.cursor.return_value = mock_cursor
        result = db.execute_query("SELECT * FROM users WHERE id = %s", ("U001",))
    
    # Assert
    assert len(result) == 1
    assert result[0]["id"] == "U001"

def test_execute_query_empty_result():
    """쿼리 결과 없음 테스트"""
    db = DatabaseManager(config)
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = []
    
    with patch.object(db, 'get_connection') as mock_conn:
        mock_conn.return_value.cursor.return_value = mock_cursor
        result = db.execute_query("SELECT * FROM users WHERE id = %s", ("INVALID",))
    
    assert len(result) == 0
```

## 필요한 패키지

```txt
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-asyncio==0.21.1
```

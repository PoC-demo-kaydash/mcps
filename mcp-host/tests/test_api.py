"""
API 엔드포인트 테스트

FastAPI 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from main import app
from api.routes import setup_dependencies
from models.session import Session
from datetime import datetime, timedelta


@pytest.fixture
def mock_server_manager():
    """Mock ServerManager"""
    manager = Mock()
    manager.is_running = Mock(return_value=True)
    manager.get_server_info = Mock(return_value={
        "name": "test_server",
        "status": "running",
        "pid": 12345,
        "uptime": 100.0,
        "restart_count": 0,
        "last_error": None,
        "enabled": True,
        "auto_start": True
    })
    manager.list_servers = Mock(return_value=[])
    manager.start_server = Mock(return_value=True)
    manager.stop_server = Mock(return_value=True)
    manager.restart_server = Mock(return_value=True)
    manager.health_check = Mock(return_value={
        "total": 1,
        "running": 1,
        "stopped": 0,
        "healthy": True
    })
    return manager


@pytest.fixture
def mock_session_manager():
    """Mock SessionManager"""
    manager = Mock()
    
    # Mock session
    mock_session = Session(
        session_id="test-session-id",
        user_id="U001",
        user_role="engineer",
        user_team="dev_team",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        last_activity=datetime.utcnow()
    )
    
    manager.create_session = AsyncMock(return_value=mock_session)
    manager.get_session = Mock(return_value=mock_session)
    manager.delete_session = Mock(return_value=True)
    
    return manager


@pytest.fixture
def mock_router():
    """Mock Router"""
    router = Mock()
    router.get_server_for_tool = Mock(return_value="test_server")
    router.list_all_tools = Mock(return_value=[
        {
            "name": "test_tool",
            "server": "test_server",
            "category": "test",
            "description": "Test tool",
            "inputSchema": {},
            "requiredPermissions": []
        }
    ])
    router.get_tool_metadata = Mock(return_value={
        "name": "test_tool",
        "server": "test_server",
        "category": "test",
        "description": "Test tool",
        "inputSchema": {},
        "requiredPermissions": []
    })
    return router


@pytest.fixture
def mock_executor():
    """Mock ToolExecutor"""
    executor = Mock()
    executor.execute_tool = AsyncMock(return_value={
        "status": "success",
        "result": {"data": "test"},
        "execution_time": 0.1
    })
    return executor


@pytest.fixture
def mock_metrics():
    """Mock MetricsCollector"""
    metrics = Mock()
    metrics.record_tool_call = Mock()
    metrics.record_session_created = Mock()
    metrics.record_session_deleted = Mock()
    metrics.get_all_stats = Mock(return_value={
        "uptime": 100.0,
        "tools": {
            "total_calls": 10,
            "total_errors": 0,
            "success_rate": 1.0,
            "stats": []
        },
        "servers": {"stats": []},
        "sessions": {
            "created": 5,
            "deleted": 2,
            "active": 3
        }
    })
    return metrics


@pytest.fixture
def client(mock_server_manager, mock_session_manager, mock_router, mock_executor, mock_metrics):
    """TestClient with mocked dependencies"""
    setup_dependencies(
        mock_server_manager,
        mock_session_manager,
        mock_router,
        mock_executor,
        mock_metrics
    )
    return TestClient(app)


class TestSessionAPI:
    """세션 API 테스트"""
    
    def test_create_session(self, client):
        """세션 생성 테스트"""
        response = client.post(
            "/api/sessions",
            json={"username": "U001", "password": "password"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "session_id" in data["data"]
    
    def test_get_session_info(self, client):
        """세션 정보 조회 테스트"""
        response = client.get("/api/sessions/test-session-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["user_id"] == "U001"
    
    def test_delete_session(self, client):
        """세션 삭제 테스트"""
        response = client.delete("/api/sessions/test-session-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestToolAPI:
    """Tool API 테스트"""
    
    def test_execute_tool(self, client):
        """Tool 실행 테스트"""
        response = client.post(
            "/api/tools/execute",
            json={
                "tool_name": "test_tool",
                "arguments": {"key": "value"}
            },
            headers={"X-Session-ID": "test-session-id"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["tool_name"] == "test_tool"
    
    def test_execute_tool_no_session(self, client):
        """세션 없이 Tool 실행 테스트"""
        response = client.post(
            "/api/tools/execute",
            json={
                "tool_name": "test_tool",
                "arguments": {"key": "value"}
            }
        )
        
        assert response.status_code == 401
    
    def test_list_tools(self, client):
        """Tool 목록 조회 테스트"""
        response = client.get("/api/tools/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "tools" in data["data"]
    
    def test_get_tool_info(self, client):
        """Tool 정보 조회 테스트"""
        response = client.get("/api/tools/test_tool")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "test_tool"


class TestServerAPI:
    """Server API 테스트"""
    
    def test_list_servers(self, client):
        """Server 목록 조회 테스트"""
        response = client.get("/api/servers")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_server_info(self, client):
        """Server 정보 조회 테스트"""
        response = client.get("/api/servers/test_server")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "test_server"
    
    def test_server_action_start(self, client):
        """Server 시작 액션 테스트"""
        response = client.post(
            "/api/servers/action",
            json={"server_name": "test_server", "action": "start"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestHealthAPI:
    """헬스 체크 API 테스트"""
    
    def test_health_check(self, client):
        """헬스 체크 테스트"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "servers" in data


class TestMetricsAPI:
    """메트릭 API 테스트"""
    
    def test_get_metrics(self, client):
        """메트릭 조회 테스트"""
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "tools" in data["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

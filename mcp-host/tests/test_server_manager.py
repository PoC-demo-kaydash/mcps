"""
ServerManager 테스트

Server 시작/중지/재시작 테스트
"""

import pytest
import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from config import Config
from core.server_manager import ServerManager, ServerProcess


@pytest.fixture
def mock_config():
    """Mock Config"""
    config = Mock(spec=Config)
    config.project_root = Path("/app/poc/mcps")
    
    # Mock server config
    server_config = Mock()
    server_config.name = "test_server"
    server_config.path = "mcp-servers/core"
    server_config.main = "main.py"
    server_config.python = "/app/miniconda3/envs/mcp_env/bin/python"
    server_config.enabled = True
    server_config.auto_start = True
    server_config.env = None
    
    config.get_server = Mock(return_value=server_config)
    config.list_server_names = Mock(return_value=["test_server"])
    
    return config


@pytest.fixture
def server_manager(mock_config):
    """ServerManager 인스턴스"""
    return ServerManager(mock_config)


class TestServerManager:
    """ServerManager 테스트"""
    
    @patch('subprocess.Popen')
    def test_start_server_success(self, mock_popen, server_manager):
        """Server 시작 성공 테스트"""
        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll = Mock(return_value=None)
        mock_popen.return_value = mock_process
        
        # Server 시작
        success = server_manager.start_server("test_server")
        
        assert success is True
        assert "test_server" in server_manager.processes
        assert server_manager.processes["test_server"].process == mock_process
    
    @patch('subprocess.Popen')
    def test_start_server_already_running(self, mock_popen, server_manager):
        """이미 실행 중인 Server 시작 테스트"""
        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll = Mock(return_value=None)
        mock_popen.return_value = mock_process
        
        # 첫 번째 시작
        server_manager.start_server("test_server")
        
        # 두 번째 시작 (이미 실행 중)
        success = server_manager.start_server("test_server")
        
        assert success is True
        assert mock_popen.call_count == 1  # 한 번만 호출
    
    def test_stop_server_success(self, server_manager):
        """Server 중지 성공 테스트"""
        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll = Mock(return_value=None)
        mock_process.wait = Mock()
        
        # 프로세스 추가
        from datetime import datetime
        server_manager.processes["test_server"] = ServerProcess(
            name="test_server",
            process=mock_process,
            started_at=datetime.utcnow()
        )
        
        # Server 중지
        success = server_manager.stop_server("test_server")
        
        assert success is True
        assert "test_server" not in server_manager.processes
        mock_process.terminate.assert_called_once()
    
    def test_stop_server_not_running(self, server_manager):
        """실행 중이지 않은 Server 중지 테스트"""
        success = server_manager.stop_server("test_server")
        
        assert success is True
    
    @patch('subprocess.Popen')
    def test_restart_server(self, mock_popen, server_manager):
        """Server 재시작 테스트"""
        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll = Mock(return_value=None)
        mock_process.wait = Mock()
        mock_popen.return_value = mock_process
        
        # 프로세스 추가
        from datetime import datetime
        server_manager.processes["test_server"] = ServerProcess(
            name="test_server",
            process=mock_process,
            started_at=datetime.utcnow()
        )
        
        # Server 재시작
        success = server_manager.restart_server("test_server")
        
        assert success is True
    
    def test_is_running(self, server_manager):
        """Server 실행 여부 확인 테스트"""
        # Mock process
        mock_process = MagicMock()
        mock_process.poll = Mock(return_value=None)
        
        # 프로세스 추가
        from datetime import datetime
        server_manager.processes["test_server"] = ServerProcess(
            name="test_server",
            process=mock_process,
            started_at=datetime.utcnow()
        )
        
        # 실행 중
        assert server_manager.is_running("test_server") is True
        
        # 실행 중이지 않음
        assert server_manager.is_running("other_server") is False
    
    def test_get_server_info(self, server_manager):
        """Server 정보 조회 테스트"""
        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll = Mock(return_value=None)
        
        # 프로세스 추가
        from datetime import datetime
        server_manager.processes["test_server"] = ServerProcess(
            name="test_server",
            process=mock_process,
            started_at=datetime.utcnow()
        )
        
        # Server 정보 조회
        info = server_manager.get_server_info("test_server")
        
        assert info is not None
        assert info["name"] == "test_server"
        assert info["status"] == "running"
        assert info["pid"] == 12345
    
    def test_list_servers(self, server_manager):
        """Server 목록 조회 테스트"""
        servers = server_manager.list_servers()
        
        assert isinstance(servers, list)
        assert len(servers) >= 0
    
    def test_health_check(self, server_manager):
        """헬스 체크 테스트"""
        health = server_manager.health_check()
        
        assert "total" in health
        assert "running" in health
        assert "stopped" in health
        assert "healthy" in health


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

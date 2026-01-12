"""
인증 Tool 테스트

pytest를 사용한 단위 테스트
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import Mock, MagicMock
from mcp_tools.core.auth_tools import (
    AuthenticateTool,
    RequestAccessTool,
    ApproveAccessTool,
    GetMyPermissionsTool
)


@pytest.fixture
def mock_db():
    """Mock DatabaseManager"""
    db = Mock()
    db.fetch_one = MagicMock()
    db.fetch_all = MagicMock()
    db.execute = MagicMock()
    return db


@pytest.fixture
def auth_tool(mock_db):
    """AuthenticateTool fixture"""
    return AuthenticateTool(mock_db)


@pytest.fixture
def request_access_tool(mock_db):
    """RequestAccessTool fixture"""
    return RequestAccessTool(mock_db)


@pytest.fixture
def approve_access_tool(mock_db):
    """ApproveAccessTool fixture"""
    return ApproveAccessTool(mock_db)


@pytest.fixture
def get_permissions_tool(mock_db):
    """GetMyPermissionsTool fixture"""
    return GetMyPermissionsTool(mock_db)


class TestAuthenticateTool:
    """AuthenticateTool 테스트"""
    
    def test_metadata(self, auth_tool):
        """메타데이터 확인"""
        metadata = auth_tool.metadata
        assert metadata.name == "authenticate"
        assert metadata.category == "auth"
        assert "user_id" in metadata.input_schema["required"]
    
    def test_successful_authentication(self, auth_tool, mock_db):
        """정상 인증 테스트"""
        # Mock 사용자 데이터
        mock_db.fetch_one.return_value = {
            "id": "USER_001",
            "name": "Test User",
            "role": "engineer",
            "team": "dev",
            "active": True
        }
        
        arguments = {"user_id": "USER_001"}
        result = auth_tool.execute(arguments)
        
        assert result["status"] == "success"
        assert "token" in result["data"]
        assert result["data"]["user"]["id"] == "USER_001"
    
    def test_user_not_found(self, auth_tool, mock_db):
        """존재하지 않는 사용자 테스트"""
        mock_db.fetch_one.return_value = None
        
        arguments = {"user_id": "INVALID_USER"}
        result = auth_tool.execute(arguments)
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "NOT_FOUND"
    
    def test_inactive_user(self, auth_tool, mock_db):
        """비활성 사용자 테스트"""
        mock_db.fetch_one.return_value = {
            "id": "USER_001",
            "name": "Inactive User",
            "role": "engineer",
            "team": "dev",
            "active": False
        }
        
        arguments = {"user_id": "USER_001"}
        result = auth_tool.execute(arguments)
        
        assert result["status"] == "error"
        assert "inactive" in result["error"]["message"].lower()


class TestRequestAccessTool:
    """RequestAccessTool 테스트"""
    
    def test_metadata(self, request_access_tool):
        """메타데이터 확인"""
        metadata = request_access_tool.metadata
        assert metadata.name == "request_access"
        assert "doc_id" in metadata.input_schema["required"]
        assert "reason" in metadata.input_schema["required"]
    
    def test_successful_request(self, request_access_tool, mock_db):
        """정상 권한 요청 테스트"""
        mock_db.fetch_one.return_value = {
            "id": "DOC_001",
            "title": "Test Document",
            "classification": "confidential"
        }
        mock_db.execute.return_value = None
        
        arguments = {
            "doc_id": "DOC_001",
            "reason": "Need for project"
        }
        context = {"user_id": "USER_001"}
        
        result = request_access_tool.execute(arguments, context)
        
        assert result["status"] == "success"
        assert result["data"]["status"] == "pending"
    
    def test_document_not_found(self, request_access_tool, mock_db):
        """존재하지 않는 문서 테스트"""
        mock_db.fetch_one.return_value = None
        
        arguments = {
            "doc_id": "INVALID_DOC",
            "reason": "Test"
        }
        context = {"user_id": "USER_001"}
        
        result = request_access_tool.execute(arguments, context)
        
        assert result["status"] == "error"


class TestApproveAccessTool:
    """ApproveAccessTool 테스트"""
    
    def test_metadata(self, approve_access_tool):
        """메타데이터 확인"""
        metadata = approve_access_tool.metadata
        assert metadata.name == "approve_access"
        assert "admin:approve" in metadata.required_permissions
    
    def test_successful_approval(self, approve_access_tool, mock_db):
        """정상 승인 테스트"""
        mock_db.fetch_one.side_effect = [
            # 권한 요청 조회
            {
                "id": "REQ_001",
                "user_id": "USER_001",
                "doc_id": "DOC_001",
                "status": "pending"
            },
            # 문서 조회
            {
                "id": "DOC_001",
                "classification": "confidential"
            }
        ]
        
        arguments = {
            "request_id": "REQ_001",
            "approve": True
        }
        context = {
            "user_id": "ADMIN_001",
            "user_role": "executive"
        }
        
        result = approve_access_tool.execute(arguments, context)
        
        assert result["status"] == "success"
        assert result["data"]["approved"] is True
    
    def test_permission_denied(self, approve_access_tool):
        """권한 없음 테스트"""
        arguments = {
            "request_id": "REQ_001",
            "approve": True
        }
        context = {
            "user_id": "USER_001",
            "user_role": "engineer"
        }
        
        result = approve_access_tool.execute(arguments, context)
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "PERMISSION_DENIED"


class TestGetMyPermissionsTool:
    """GetMyPermissionsTool 테스트"""
    
    def test_metadata(self, get_permissions_tool):
        """메타데이터 확인"""
        metadata = get_permissions_tool.metadata
        assert metadata.name == "get_my_permissions"
    
    def test_get_permissions(self, get_permissions_tool, mock_db):
        """권한 조회 테스트"""
        mock_db.fetch_all.return_value = [
            {
                "doc_id": "DOC_001",
                "permission_type": "read"
            },
            {
                "doc_id": "DOC_002",
                "permission_type": "write"
            }
        ]
        
        context = {
            "user_id": "USER_001",
            "user_role": "engineer"
        }
        
        result = get_permissions_tool.execute({}, context)
        
        assert result["status"] == "success"
        assert "role_permissions" in result["data"]
        assert "document_permissions" in result["data"]
        assert len(result["data"]["document_permissions"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

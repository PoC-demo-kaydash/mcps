"""
문서 Tool 테스트

pytest를 사용한 단위 테스트
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import Mock, MagicMock
from mcp_tools.core.document_tools import (
    GetDocumentTool,
    CreateDocumentTool,
    UpdateDocumentTool,
    DeleteDocumentTool,
    ListDocumentsTool
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
def mock_es():
    """Mock ElasticsearchManager"""
    es = Mock()
    es.index_document = MagicMock()
    es.update_document = MagicMock()
    es.delete_document = MagicMock()
    return es


@pytest.fixture
def get_doc_tool(mock_db):
    """GetDocumentTool fixture"""
    return GetDocumentTool(mock_db)


@pytest.fixture
def create_doc_tool(mock_db, mock_es):
    """CreateDocumentTool fixture"""
    return CreateDocumentTool(mock_db, mock_es)


@pytest.fixture
def update_doc_tool(mock_db, mock_es):
    """UpdateDocumentTool fixture"""
    return UpdateDocumentTool(mock_db, mock_es)


@pytest.fixture
def delete_doc_tool(mock_db, mock_es):
    """DeleteDocumentTool fixture"""
    return DeleteDocumentTool(mock_db, mock_es)


@pytest.fixture
def list_docs_tool(mock_db):
    """ListDocumentsTool fixture"""
    return ListDocumentsTool(mock_db)


class TestGetDocumentTool:
    """GetDocumentTool 테스트"""
    
    def test_metadata(self, get_doc_tool):
        """메타데이터 확인"""
        metadata = get_doc_tool.metadata
        assert metadata.name == "get_document"
        assert "doc_id" in metadata.input_schema["required"]
    
    def test_successful_get(self, get_doc_tool, mock_db):
        """정상 조회 테스트"""
        mock_db.fetch_all.return_value = [{
            "id": "DOC_001",
            "title": "Test Document",
            "content": "Content",
            "author_id": "USER_001",
            "classification": "public",
            "team": None,
            "version": 1
        }]
        
        arguments = {"doc_id": "DOC_001"}
        context = {
            "user_id": "USER_001",
            "user_role": "engineer"
        }
        
        result = get_doc_tool.execute(arguments, context)
        
        assert result["status"] == "success"
        assert result["data"]["id"] == "DOC_001"
    
    def test_document_not_found(self, get_doc_tool, mock_db):
        """존재하지 않는 문서 테스트"""
        mock_db.fetch_all.return_value = []
        
        arguments = {"doc_id": "INVALID_DOC"}
        result = get_doc_tool.execute(arguments)
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "NOT_FOUND"


class TestCreateDocumentTool:
    """CreateDocumentTool 테스트"""
    
    def test_metadata(self, create_doc_tool):
        """메타데이터 확인"""
        metadata = create_doc_tool.metadata
        assert metadata.name == "create_document"
        assert "title" in metadata.input_schema["required"]
        assert "content" in metadata.input_schema["required"]
    
    def test_successful_create(self, create_doc_tool, mock_db, mock_es):
        """정상 생성 테스트"""
        arguments = {
            "title": "New Document",
            "content": "Content",
            "classification": "public"
        }
        context = {
            "user_id": "USER_001",
            "user_role": "engineer"
        }
        
        result = create_doc_tool.execute(arguments, context)
        
        assert result["status"] == "success"
        assert "doc_id" in result["data"]
        assert result["data"]["title"] == "New Document"
        mock_db.execute.assert_called()
        mock_es.index_document.assert_called()
    
    def test_confidential_permission_denied(self, create_doc_tool):
        """기밀 문서 권한 없음 테스트"""
        arguments = {
            "title": "Confidential Doc",
            "content": "Secret",
            "classification": "confidential"
        }
        context = {
            "user_id": "USER_001",
            "user_role": "engineer"
        }
        
        result = create_doc_tool.execute(arguments, context)
        
        assert result["status"] == "error"


class TestUpdateDocumentTool:
    """UpdateDocumentTool 테스트"""
    
    def test_metadata(self, update_doc_tool):
        """메타데이터 확인"""
        metadata = update_doc_tool.metadata
        assert metadata.name == "update_document"
        assert "doc_id" in metadata.input_schema["required"]
    
    def test_successful_update(self, update_doc_tool, mock_db, mock_es):
        """정상 업데이트 테스트"""
        mock_db.fetch_all.return_value = [{
            "id": "DOC_001",
            "title": "Old Title",
            "content": "Old Content",
            "author_id": "USER_001",
            "classification": "public",
            "team": None,
            "version": 1
        }]
        
        arguments = {
            "doc_id": "DOC_001",
            "title": "New Title"
        }
        context = {
            "user_id": "USER_001",
            "user_role": "engineer"
        }
        
        result = update_doc_tool.execute(arguments, context)
        
        assert result["status"] == "success"
        mock_db.execute.assert_called()
        mock_es.update_document.assert_called()
    
    def test_permission_denied(self, update_doc_tool, mock_db):
        """권한 없음 테스트"""
        mock_db.fetch_all.return_value = [{
            "id": "DOC_001",
            "title": "Document",
            "content": "Content",
            "author_id": "USER_002",
            "classification": "confidential",
            "team": None,
            "version": 1
        }]
        
        arguments = {
            "doc_id": "DOC_001",
            "title": "New Title"
        }
        context = {
            "user_id": "USER_001",
            "user_role": "engineer"
        }
        
        result = update_doc_tool.execute(arguments, context)
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "PERMISSION_DENIED"


class TestDeleteDocumentTool:
    """DeleteDocumentTool 테스트"""
    
    def test_metadata(self, delete_doc_tool):
        """메타데이터 확인"""
        metadata = delete_doc_tool.metadata
        assert metadata.name == "delete_document"
        assert "doc_id" in metadata.input_schema["required"]
    
    def test_successful_delete(self, delete_doc_tool, mock_db, mock_es):
        """정상 삭제 테스트"""
        mock_db.fetch_all.return_value = [{
            "id": "DOC_001",
            "title": "Document",
            "content": "Content",
            "author_id": "USER_001",
            "classification": "public",
            "team": None
        }]
        
        arguments = {"doc_id": "DOC_001"}
        context = {
            "user_id": "USER_001",
            "user_role": "executive"
        }
        
        result = delete_doc_tool.execute(arguments, context)
        
        assert result["status"] == "success"
        mock_es.delete_document.assert_called_with("DOC_001")


class TestListDocumentsTool:
    """ListDocumentsTool 테스트"""
    
    def test_metadata(self, list_docs_tool):
        """메타데이터 확인"""
        metadata = list_docs_tool.metadata
        assert metadata.name == "list_documents"
    
    def test_successful_list(self, list_docs_tool, mock_db):
        """정상 목록 조회 테스트"""
        mock_db.fetch_all.return_value = [
            {
                "id": "DOC_001",
                "title": "Document 1",
                "classification": "public",
                "author_name": "User 1"
            },
            {
                "id": "DOC_002",
                "title": "Document 2",
                "classification": "public",
                "author_name": "User 2"
            }
        ]
        mock_db.fetch_one.return_value = {"total": 2}
        
        arguments = {"limit": 10}
        context = {
            "user_id": "USER_001",
            "user_role": "engineer"
        }
        
        result = list_docs_tool.execute(arguments, context)
        
        assert result["status"] == "success"
        assert result["data"]["total"] == 2
        assert len(result["data"]["documents"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

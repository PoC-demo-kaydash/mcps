"""
검색 Tool 테스트

pytest를 사용한 단위 테스트
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import Mock, MagicMock
from mcp_tools.core.search_tools import (
    SearchDocumentsTool,
    SuggestDocumentsTool
)


@pytest.fixture
def mock_es():
    """Mock ElasticsearchManager"""
    es = Mock()
    es.search_documents = MagicMock()
    es.suggest_documents = MagicMock()
    return es


@pytest.fixture
def search_tool(mock_es):
    """SearchDocumentsTool fixture"""
    return SearchDocumentsTool(mock_es)


@pytest.fixture
def suggest_tool(mock_es):
    """SuggestDocumentsTool fixture"""
    return SuggestDocumentsTool(mock_es)


class TestSearchDocumentsTool:
    """SearchDocumentsTool 테스트"""
    
    def test_metadata(self, search_tool):
        """메타데이터 확인"""
        metadata = search_tool.metadata
        assert metadata.name == "search_documents"
        assert metadata.category == "search"
        assert "query" in metadata.input_schema["required"]
    
    def test_successful_search(self, search_tool, mock_es):
        """정상 검색 테스트"""
        # Mock 검색 결과
        mock_es.search_documents.return_value = {
            "total": 2,
            "hits": [
                {
                    "id": "DOC_001",
                    "title": "Test Document 1",
                    "score": 0.95
                },
                {
                    "id": "DOC_002",
                    "title": "Test Document 2",
                    "score": 0.85
                }
            ]
        }
        
        arguments = {
            "query": "test",
            "limit": 10
        }
        context = {
            "user_id": "USER_001",
            "user_role": "engineer"
        }
        
        result = search_tool.execute(arguments, context)
        
        assert result["status"] == "success"
        assert result["data"]["total"] == 2
        assert len(result["data"]["results"]) == 2
        assert result["data"]["query"] == "test"
    
    def test_empty_search_results(self, search_tool, mock_es):
        """검색 결과 없음 테스트"""
        mock_es.search_documents.return_value = {
            "total": 0,
            "hits": []
        }
        
        arguments = {"query": "nonexistent"}
        result = search_tool.execute(arguments)
        
        assert result["status"] == "success"
        assert result["data"]["total"] == 0
        assert len(result["data"]["results"]) == 0
    
    def test_search_with_filters(self, search_tool, mock_es):
        """필터링 검색 테스트"""
        mock_es.search_documents.return_value = {
            "total": 1,
            "hits": [
                {
                    "id": "DOC_001",
                    "title": "Public Document",
                    "classification": "public"
                }
            ]
        }
        
        arguments = {
            "query": "document",
            "classification": ["public"],
            "category": "tech"
        }
        context = {
            "user_id": "USER_001",
            "user_role": "engineer"
        }
        
        result = search_tool.execute(arguments, context)
        
        assert result["status"] == "success"
        # ElasticsearchManager.search_documents 호출 확인
        mock_es.search_documents.assert_called_once()
        call_args = mock_es.search_documents.call_args
        assert call_args[1]["query_text"] == "document"
        assert "public" in call_args[1]["classifications"]
        assert call_args[1]["category"] == "tech"
    
    def test_search_with_pagination(self, search_tool, mock_es):
        """페이지네이션 검색 테스트"""
        mock_es.search_documents.return_value = {
            "total": 50,
            "hits": []
        }
        
        arguments = {
            "query": "test",
            "limit": 20,
            "offset": 10
        }
        
        result = search_tool.execute(arguments)
        
        assert result["status"] == "success"
        call_args = mock_es.search_documents.call_args
        assert call_args[1]["size"] == 20
        assert call_args[1]["from_"] == 10
    
    def test_invalid_query(self, search_tool):
        """잘못된 쿼리 테스트"""
        arguments = {}  # query 누락
        result = search_tool.execute(arguments)
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "INVALID_INPUT"


class TestSuggestDocumentsTool:
    """SuggestDocumentsTool 테스트"""
    
    def test_metadata(self, suggest_tool):
        """메타데이터 확인"""
        metadata = suggest_tool.metadata
        assert metadata.name == "suggest_documents"
        assert "prefix" in metadata.input_schema["required"]
    
    def test_successful_suggest(self, suggest_tool, mock_es):
        """정상 자동완성 테스트"""
        # Mock 자동완성 결과
        mock_es.suggest_documents.return_value = {
            "suggestions": [
                "Test Document 1",
                "Test Document 2",
                "Test API Documentation"
            ]
        }
        
        arguments = {
            "prefix": "test",
            "limit": 5
        }
        
        result = suggest_tool.execute(arguments)
        
        assert result["status"] == "success"
        assert len(result["data"]["suggestions"]) == 3
        mock_es.suggest_documents.assert_called_once_with("test", 5)
    
    def test_empty_suggestions(self, suggest_tool, mock_es):
        """자동완성 결과 없음 테스트"""
        mock_es.suggest_documents.return_value = {
            "suggestions": []
        }
        
        arguments = {"prefix": "xyz"}
        result = suggest_tool.execute(arguments)
        
        assert result["status"] == "success"
        assert len(result["data"]["suggestions"]) == 0
    
    def test_short_prefix(self, suggest_tool, mock_es):
        """짧은 prefix 테스트"""
        mock_es.suggest_documents.return_value = {
            "suggestions": ["Test"]
        }
        
        arguments = {"prefix": "t"}
        result = suggest_tool.execute(arguments)
        
        assert result["status"] == "success"
    
    def test_invalid_prefix(self, suggest_tool):
        """잘못된 prefix 테스트"""
        arguments = {}  # prefix 누락
        result = suggest_tool.execute(arguments)
        
        assert result["status"] == "error"
        assert result["error"]["code"] == "INVALID_INPUT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

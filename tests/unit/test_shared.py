"""
Shared 모듈 테스트
==================

모든 shared 모듈의 import 및 기본 기능을 테스트합니다.

실행:
    python -m pytest tests/test_shared.py -v
    또는
    python tests/test_shared.py
"""

import sys
import os

# shared 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from datetime import datetime, timedelta


class TestImports(unittest.TestCase):
    """모듈 Import 테스트"""
    
    def test_import_init(self):
        """shared/__init__.py import"""
        from shared import CONFIG, initialize, cleanup
        self.assertIsInstance(CONFIG, dict)
        self.assertTrue(callable(initialize))
        self.assertTrue(callable(cleanup))
    
    def test_import_logging_config(self):
        """shared/logging_config.py import"""
        from shared.logging_config import (
            setup_logging, get_logger,
            log_exceptions, log_execution_time
        )
        self.assertTrue(callable(setup_logging))
        self.assertTrue(callable(get_logger))
    
    def test_import_utils(self):
        """shared/utils.py import"""
        from shared.utils import (
            generate_id, now_iso, now_kst,
            validate_role, validate_classification,
            retry, hash_password
        )
        self.assertTrue(callable(generate_id))
        self.assertTrue(callable(validate_role))
    
    def test_import_cache(self):
        """shared/cache.py import"""
        from shared.cache import (
            Cache, CacheEntry, cached, cached_property,
            PermissionCache, UserCache, ToolCache
        )
        self.assertTrue(callable(Cache))
        self.assertTrue(callable(cached))
    
    def test_import_database(self):
        """shared/database.py import"""
        from shared.database import DatabaseManager
        self.assertTrue(callable(DatabaseManager))
    
    def test_import_queries(self):
        """shared/queries.py import"""
        from shared.queries import (
            UserQueries, DocumentQueries, PermissionQueries,
            ToolQueries, ServerQueries, AuditLogQueries,
            DocumentVersionQueries, AccessRequestQueries
        )
        self.assertTrue(hasattr(UserQueries, 'get_by_id'))
        self.assertTrue(hasattr(DocumentQueries, 'search'))
    
    def test_import_elasticsearch(self):
        """shared/elasticsearch.py import"""
        from shared.elasticsearch import (
            ElasticsearchManager, CLASSIFICATION_LEVELS
        )
        self.assertTrue(callable(ElasticsearchManager))
        self.assertIsInstance(CLASSIFICATION_LEVELS, dict)
    
    def test_import_permissions(self):
        """shared/permissions.py import"""
        from shared.permissions import (
            PermissionEngine, Role, Classification, Action,
            User, Document, Permission, ROLE_MAP
        )
        self.assertTrue(callable(PermissionEngine))
        self.assertEqual(Role.JUNIOR.value, 1)
        self.assertEqual(Classification.PUBLIC.value, 1)
    
    def test_import_mcp_protocol(self):
        """shared/mcp_protocol.py import"""
        from shared.mcp_protocol import (
            MCPServer, Tool, ToolResult, Resource,
            JSONRPCRequest, JSONRPCResponse, ErrorCode
        )
        self.assertTrue(callable(MCPServer))
        self.assertTrue(callable(ToolResult.text))


class TestUtils(unittest.TestCase):
    """유틸리티 함수 테스트"""
    
    def test_generate_id(self):
        """ID 생성 테스트"""
        from shared.utils import generate_id
        
        # 기본 ID
        id1 = generate_id()
        self.assertTrue(len(id1) > 0)
        
        # 프리픽스 ID
        user_id = generate_id("U")
        self.assertTrue(user_id.startswith("U"))
        
        doc_id = generate_id("DOC")
        self.assertTrue(doc_id.startswith("DOC"))
        
        # 유일성
        ids = [generate_id() for _ in range(100)]
        self.assertEqual(len(ids), len(set(ids)))
    
    def test_validate_role(self):
        """역할 검증 테스트"""
        from shared.utils import validate_role
        
        self.assertTrue(validate_role("junior"))
        self.assertTrue(validate_role("staff"))
        self.assertTrue(validate_role("manager"))
        self.assertTrue(validate_role("executive"))
        self.assertTrue(validate_role("admin"))
        self.assertFalse(validate_role("invalid"))
        self.assertFalse(validate_role(""))
    
    def test_validate_classification(self):
        """보안등급 검증 테스트"""
        from shared.utils import validate_classification
        
        self.assertTrue(validate_classification("public"))
        self.assertTrue(validate_classification("internal"))
        self.assertTrue(validate_classification("confidential"))
        self.assertTrue(validate_classification("secret"))
        self.assertTrue(validate_classification("top_secret"))
        self.assertFalse(validate_classification("invalid"))
    
    def test_now_iso(self):
        """ISO 시간 테스트"""
        from shared.utils import now_iso
        
        iso_time = now_iso()
        self.assertIn("T", iso_time)
        # ISO 8601 형식 확인
        datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
    
    def test_hash_password(self):
        """비밀번호 해싱 테스트"""
        from shared.utils import hash_password, verify_password
        
        password = "test123"
        hashed = hash_password(password)
        
        self.assertNotEqual(password, hashed)
        self.assertTrue(hashed.startswith("$2b$"))
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong", hashed))


class TestCache(unittest.TestCase):
    """캐시 테스트"""
    
    def test_cache_basic(self):
        """기본 캐시 동작 테스트"""
        from shared.cache import Cache
        
        cache = Cache(max_size=10, default_ttl=60)
        
        # Set & Get
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")
        
        # Miss
        self.assertIsNone(cache.get("nonexistent"))
        
        # Delete
        cache.delete("key1")
        self.assertIsNone(cache.get("key1"))
    
    def test_cache_ttl(self):
        """TTL 테스트"""
        from shared.cache import Cache
        import time
        
        cache = Cache(max_size=10, default_ttl=1)  # 1초 TTL
        
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")
        
        time.sleep(1.1)  # TTL 만료 대기
        self.assertIsNone(cache.get("key1"))
    
    def test_cache_lru(self):
        """LRU 정책 테스트"""
        from shared.cache import Cache
        
        cache = Cache(max_size=3, default_ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # key1 접근
        cache.get("key1")
        
        # 새 항목 추가 -> LRU(key2) 제거
        cache.set("key4", "value4")
        
        self.assertIsNotNone(cache.get("key1"))  # 접근했으므로 유지
        self.assertIsNone(cache.get("key2"))     # LRU로 제거됨
        self.assertIsNotNone(cache.get("key3"))
        self.assertIsNotNone(cache.get("key4"))
    
    def test_cache_decorator(self):
        """@cached 데코레이터 테스트"""
        from shared.cache import cached, Cache, set_default_cache
        
        # 테스트용 캐시 설정
        test_cache = Cache(max_size=100, default_ttl=60)
        set_default_cache(test_cache)
        
        call_count = 0
        
        @cached(ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # 첫 호출
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)
        
        # 캐시된 결과
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)  # 함수 호출 안됨
        
        # 다른 인자
        result3 = expensive_function(10)
        self.assertEqual(result3, 20)
        self.assertEqual(call_count, 2)
    
    def test_cache_stats(self):
        """캐시 통계 테스트"""
        from shared.cache import Cache
        
        cache = Cache(max_size=10, default_ttl=60)
        
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        
        stats = cache.get_stats()
        self.assertEqual(stats["hits"], 2)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["size"], 1)


class TestPermissions(unittest.TestCase):
    """권한 관리 테스트"""
    
    def test_role_hierarchy(self):
        """역할 계층 테스트"""
        from shared.permissions import Role, ROLE_MAP
        
        self.assertEqual(Role.JUNIOR.value, 1)
        self.assertEqual(Role.STAFF.value, 2)
        self.assertEqual(Role.MANAGER.value, 3)
        self.assertEqual(Role.EXECUTIVE.value, 4)
        self.assertEqual(Role.ADMIN.value, 5)
        
        self.assertTrue(Role.EXECUTIVE > Role.MANAGER)
        self.assertTrue(Role.JUNIOR < Role.STAFF)
    
    def test_classification_hierarchy(self):
        """보안등급 계층 테스트"""
        from shared.permissions import Classification, CLASSIFICATION_MAP
        
        self.assertEqual(Classification.PUBLIC.value, 1)
        self.assertEqual(Classification.TOP_SECRET.value, 5)
        
        self.assertTrue(Classification.SECRET > Classification.CONFIDENTIAL)
    
    def test_permission_engine_role_check(self):
        """권한 엔진 역할 확인 테스트"""
        from shared.permissions import PermissionEngine, User
        
        engine = PermissionEngine()
        
        junior = User(
            user_id="U001",
            username="junior1",
            role="junior",
            classification_level=2
        )
        
        executive = User(
            user_id="U002",
            username="exec1",
            role="executive",
            classification_level=4
        )
        
        # 역할 확인
        self.assertTrue(engine.has_role(junior, "junior"))
        self.assertFalse(engine.has_role(junior, "staff"))
        
        self.assertTrue(engine.has_role(executive, "junior"))
        self.assertTrue(engine.has_role(executive, "staff"))
        self.assertTrue(engine.has_role(executive, "executive"))
        self.assertFalse(engine.has_role(executive, "admin"))
    
    def test_permission_engine_document_access(self):
        """권한 엔진 문서 접근 테스트"""
        from shared.permissions import PermissionEngine, User, Document
        
        engine = PermissionEngine()
        
        user_internal = User(
            user_id="U001",
            username="user1",
            role="staff",
            classification_level=2  # internal
        )
        
        user_secret = User(
            user_id="U002",
            username="user2",
            role="staff",
            classification_level=4  # secret
        )
        
        doc_public = Document(
            doc_id="DOC001",
            title="Public Doc",
            author_id="U003",
            classification="public"
        )
        
        doc_secret = Document(
            doc_id="DOC002",
            title="Secret Doc",
            author_id="U003",
            classification="secret"
        )
        
        # internal 사용자는 public 문서 접근 가능
        self.assertTrue(engine.can_view_document(user_internal, doc_public))
        
        # internal 사용자는 secret 문서 접근 불가
        self.assertFalse(engine.can_view_document(user_internal, doc_secret))
        
        # secret 사용자는 모든 문서 접근 가능
        self.assertTrue(engine.can_view_document(user_secret, doc_public))
        self.assertTrue(engine.can_view_document(user_secret, doc_secret))


class TestQueries(unittest.TestCase):
    """쿼리 테스트"""
    
    def test_user_queries(self):
        """사용자 쿼리 테스트"""
        from shared.queries import UserQueries
        
        # get_by_id
        query, params = UserQueries.get_by_id("U001")
        self.assertIn("SELECT", query)
        self.assertIn("user_id", query)
        self.assertEqual(params, ["U001"])
        
        # create
        query, params = UserQueries.create(
            user_id="U001",
            username="test",
            email="test@test.com",
            password_hash="hash123"
        )
        self.assertIn("INSERT", query)
        self.assertIn("U001", params)
    
    def test_document_queries(self):
        """문서 쿼리 테스트"""
        from shared.queries import DocumentQueries
        
        # search
        query, params = DocumentQueries.search(
            title="보고서",
            classification="confidential"
        )
        self.assertIn("SELECT", query)
        self.assertIn("LIKE", query)
        self.assertIn("%보고서%", params)
        self.assertIn("confidential", params)


class TestMCPProtocol(unittest.TestCase):
    """MCP 프로토콜 테스트"""
    
    def test_tool_result(self):
        """ToolResult 테스트"""
        from shared.mcp_protocol import ToolResult
        
        # 텍스트 결과
        result = ToolResult.text("Hello World")
        self.assertEqual(result.content[0]["type"], "text")
        self.assertEqual(result.content[0]["text"], "Hello World")
        self.assertFalse(result.isError)
        
        # 에러 결과
        error = ToolResult.error("Something went wrong")
        self.assertTrue(error.isError)
    
    def test_jsonrpc_messages(self):
        """JSON-RPC 메시지 테스트"""
        from shared.mcp_protocol import JSONRPCRequest, JSONRPCResponse, JSONRPCError
        
        # Request
        request = JSONRPCRequest(
            method="tools/call",
            id=1,
            params={"name": "test"}
        )
        req_dict = request.to_dict()
        self.assertEqual(req_dict["jsonrpc"], "2.0")
        self.assertEqual(req_dict["method"], "tools/call")
        self.assertEqual(req_dict["id"], 1)
        
        # Response
        response = JSONRPCResponse(id=1, result={"success": True})
        resp_dict = response.to_dict()
        self.assertEqual(resp_dict["id"], 1)
        self.assertIn("result", resp_dict)
        
        # Error Response
        error = JSONRPCError(code=-32600, message="Invalid Request")
        error_response = JSONRPCResponse(id=1, error=error.to_dict())
        err_dict = error_response.to_dict()
        self.assertIn("error", err_dict)
        self.assertEqual(err_dict["error"]["code"], -32600)
    
    def test_mcp_server_tool_registration(self):
        """MCP 서버 Tool 등록 테스트"""
        from shared.mcp_protocol import MCPServer
        
        server = MCPServer(name="test-server", version="1.0.0")
        
        @server.tool(description="Test tool")
        def test_tool(arg1: str, arg2: int = 10) -> str:
            return f"{arg1}: {arg2}"
        
        self.assertIn("test_tool", server._tools)
        tool = server._tools["test_tool"]
        self.assertEqual(tool["name"], "test_tool")
        self.assertEqual(tool["description"], "Test tool")
        self.assertIn("properties", tool["inputSchema"])


class TestConfig(unittest.TestCase):
    """설정 테스트"""
    
    def test_config_structure(self):
        """CONFIG 구조 테스트"""
        from shared import CONFIG
        
        # 필수 섹션 확인
        self.assertIn("database", CONFIG)
        self.assertIn("elasticsearch", CONFIG)
        self.assertIn("jwt", CONFIG)
        self.assertIn("logging", CONFIG)
        self.assertIn("cache", CONFIG)
        self.assertIn("mcp", CONFIG)
    
    def test_config_database(self):
        """데이터베이스 설정 테스트"""
        from shared import CONFIG
        
        db_config = CONFIG["database"]
        self.assertIn("host", db_config)
        self.assertIn("port", db_config)
        self.assertIn("user", db_config)
        self.assertIn("database", db_config)
    
    def test_config_elasticsearch(self):
        """Elasticsearch 설정 테스트"""
        from shared import CONFIG
        
        es_config = CONFIG["elasticsearch"]
        self.assertIn("host", es_config)
        self.assertIn("port", es_config)


def run_tests():
    """테스트 실행"""
    # 테스트 스위트 구성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 클래스 추가
    suite.addTests(loader.loadTestsFromTestCase(TestImports))
    suite.addTests(loader.loadTestsFromTestCase(TestUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestCache))
    suite.addTests(loader.loadTestsFromTestCase(TestPermissions))
    suite.addTests(loader.loadTestsFromTestCase(TestQueries))
    suite.addTests(loader.loadTestsFromTestCase(TestMCPProtocol))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

# mcp-tools 개발가이드 설계서

***

# 03. MCP 에코시스템 - mcp-tools 개발가이드

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/mcp-tools/`  
**목적**: Tool 개발 및 확장 가이드

***

## 목차

1. [개요](#1-개요)
2. [아키텍처](#2-아키텍처)
3. [Tool 개발 가이드](#3-tool-개발-가이드)
4. [카테고리별 Tool 구현](#4-카테고리별-tool-구현)
5. [테스트 및 배포](#5-테스트-및-배포)
6. [확장 가이드](#6-확장-가이드)

***

## 1. 개요

### 1.1 목적

mcp-tools는 MCP 에코시스템의 Tool을 정의하고 관리하는 모듈입니다.

### 1.2 디렉토리 구조

```
/app/poc/mcps/mcp-tools/
├── __init__.py                 # 패키지 초기화
├── base.py                     # 기본 Tool 클래스
├── registry.py                 # Tool 레지스트리
├── validator.py                # 입력 검증
│
├── core/                       # 핵심 Tool
│   ├── __init__.py
│   ├── auth_tools.py          # 인증/권한 Tool
│   ├── document_tools.py      # 문서 CRUD Tool
│   ├── search_tools.py        # 검색 Tool
│   ├── version_tools.py       # 버전 관리 Tool
│   └── audit_tools.py         # 감사 Tool
│
├── utils/                      # 유틸리티 Tool
│   ├── __init__.py
│   ├── text_tools.py          # 텍스트 처리
│   ├── file_tools.py          # 파일 처리
│   └── format_tools.py        # 포맷 변환
│
├── templates/                  # Tool 템플릿
│   ├── tool_template.py       # 기본 템플릿
│   └── async_tool_template.py # 비동기 템플릿
│
└── tests/                      # 테스트
    ├── test_auth_tools.py
    ├── test_document_tools.py
    └── test_search_tools.py
```

### 1.3 설계 원칙

**1. 단일 책임 원칙 (SRP)**
- 각 Tool은 하나의 명확한 기능만 수행
- 예: `search_documents`, `get_document`

**2. 입출력 명확화**
- JSON Schema로 입력 정의
- 표준 응답 형식

**3. 재사용성**
- 공통 로직은 shared 모듈 활용
- Tool 간 의존성 최소화

**4. 에러 처리**
- 일관된 에러 응답
- 상세한 에러 메시지

**5. 보안**
- 모든 Tool은 권한 확인
- 입력 검증 필수

***

## 2. 아키텍처

### 2.1 Tool 생명주기

```
┌─────────────────────────────────────────────────┐
│              Tool 생명주기                       │
└─────────────────────────────────────────────────┘

1. 등록 (Registration)
   ├─ Tool 클래스 정의
   ├─ 메타데이터 설정 (name, description, schema)
   └─ Registry에 등록

2. 검증 (Validation)
   ├─ 입력 스키마 검증
   ├─ 권한 확인
   └─ 리소스 존재 확인

3. 실행 (Execution)
   ├─ 비즈니스 로직 실행
   ├─ 데이터베이스/Elasticsearch 작업
   └─ 결과 반환

4. 로깅 (Logging)
   ├─ 실행 로그 기록
   ├─ 감사 로그 생성
   └─ 에러 로깅
```

### 2.2 Tool 실행 흐름

```
┌──────────┐       ┌──────────┐       ┌──────────┐
│ MCP Host │──────▶│   Tool   │──────▶│  Result  │
└──────────┘       └──────────┘       └──────────┘
     │                  │                    │
     │                  │                    │
     ▼                  ▼                    ▼
  Request          Validation           Response
  {                    │                    │
    tool: "...",       ├─ Schema           {
    args: {...}        ├─ Permission        status: "...",
  }                    └─ Business          data: {...}
                                          }
```

***

## 3. Tool 개발 가이드

### 3.1 base.py - 기본 Tool 클래스

```python
# mcp-tools/base.py
"""
Tool 기본 클래스
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolMetadata:
    """Tool 메타데이터"""
    name: str
    description: str
    category: str
    department: str
    version: str
    required_permissions: List[str]
    input_schema: dict
    output_schema: dict
    examples: List[dict] = None


class BaseTool(ABC):
    """
    Tool 기본 클래스
    
    모든 Tool은 이 클래스를 상속받아야 함
    """
    
    def __init__(self):
        """초기화"""
        self.metadata = self._define_metadata()
        self.logger = logging.getLogger(f"tool.{self.metadata.name}")
    
    @abstractmethod
    def _define_metadata(self) -> ToolMetadata:
        """
        Tool 메타데이터 정의 (필수 구현)
        
        Returns:
            ToolMetadata
        """
        pass
    
    @abstractmethod
    def execute(
        self,
        arguments: dict,
        context: Optional[dict] = None
    ) -> dict:
        """
        Tool 실행 (필수 구현)
        
        Args:
            arguments: Tool 입력 인자
            context: 실행 컨텍스트 {
                "user_id": "U001",
                "user_role": "staff",
                "user_team": "dev_team",
                "request_id": "req_123"
            }
        
        Returns:
            {
                "status": "success" | "error",
                "data": {...},
                "error": {...}  # status가 error일 때
            }
        """
        pass
    
    def validate_arguments(self, arguments: dict) -> tuple[bool, Optional[str]]:
        """
        입력 인자 검증
        
        Args:
            arguments: 입력 인자
        
        Returns:
            (valid: bool, error_message: Optional[str])
        """
        # JSON Schema 검증 (간단한 버전)
        schema = self.metadata.input_schema
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # 필수 필드 확인
        for field in required:
            if field not in arguments:
                return False, f"Missing required field: {field}"
        
        # 타입 확인
        for field, value in arguments.items():
            if field in properties:
                expected_type = properties[field].get("type")
                
                # 타입 매핑
                type_map = {
                    "string": str,
                    "integer": int,
                    "number": (int, float),
                    "boolean": bool,
                    "array": list,
                    "object": dict
                }
                
                if expected_type in type_map:
                    expected_python_type = type_map[expected_type]
                    if not isinstance(value, expected_python_type):
                        return False, f"Field '{field}' must be {expected_type}"
        
        return True, None
    
    def check_permission(
        self,
        user_role: str,
        required_permissions: List[str]
    ) -> tuple[bool, Optional[str]]:
        """
        권한 확인
        
        Args:
            user_role: 사용자 역할
            required_permissions: 필요한 권한 목록
        
        Returns:
            (authorized: bool, error_message: Optional[str])
        """
        # shared.permissions 사용
        from shared.permissions import PermissionEngine
        
        perm_engine = PermissionEngine()
        
        # Tool 실행 권한 확인
        has_permission = perm_engine.check_tool_permission(
            user_role,
            self.metadata.name,
            "execute"
        )
        
        if not has_permission:
            return False, f"Permission denied: {user_role} cannot execute {self.metadata.name}"
        
        return True, None
    
    def create_success_response(self, data: Any) -> dict:
        """
        성공 응답 생성
        
        Args:
            data: 응답 데이터
        
        Returns:
            {
                "status": "success",
                "data": data
            }
        """
        return {
            "status": "success",
            "data": data
        }
    
    def create_error_response(
        self,
        error_message: str,
        error_code: Optional[str] = None,
        details: Optional[dict] = None
    ) -> dict:
        """
        에러 응답 생성
        
        Args:
            error_message: 에러 메시지
            error_code: 에러 코드
            details: 추가 정보
        
        Returns:
            {
                "status": "error",
                "error": {
                    "message": "...",
                    "code": "...",
                    "details": {...}
                }
            }
        """
        error = {
            "message": error_message
        }
        
        if error_code:
            error["code"] = error_code
        
        if details:
            error["details"] = details
        
        return {
            "status": "error",
            "error": error
        }
    
    def log_execution(
        self,
        context: dict,
        arguments: dict,
        result: dict,
        execution_time_ms: float
    ):
        """
        실행 로그 기록
        
        Args:
            context: 실행 컨텍스트
            arguments: 입력 인자
            result: 실행 결과
            execution_time_ms: 실행 시간 (ms)
        """
        self.logger.info(
            f"Tool executed: {self.metadata.name} "
            f"by {context.get('user_id')} "
            f"in {execution_time_ms:.2f}ms "
            f"status={result['status']}"
        )


class AsyncBaseTool(BaseTool):
    """
    비동기 Tool 기본 클래스
    """
    
    @abstractmethod
    async def execute(
        self,
        arguments: dict,
        context: Optional[dict] = None
    ) -> dict:
        """비동기 실행"""
        pass
```

### 3.2 validator.py - 입력 검증

```python
# mcp-tools/validator.py
"""
Tool 입력 검증
"""

import jsonschema
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """검증 에러"""
    pass


class ToolValidator:
    """
    Tool 입력 검증기
    
    JSON Schema 기반 검증
    """
    
    @staticmethod
    def validate(arguments: dict, schema: dict) -> tuple[bool, Optional[str]]:
        """
        JSON Schema 검증
        
        Args:
            arguments: 입력 인자
            schema: JSON Schema
        
        Returns:
            (valid: bool, error_message: Optional[str])
        
        Example:
            schema = {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100}
                },
                "required": ["query"]
            }
            
            valid, error = ToolValidator.validate(args, schema)
        """
        try:
            jsonschema.validate(instance=arguments, schema=schema)
            return True, None
        except jsonschema.ValidationError as e:
            error_message = f"Validation error: {e.message}"
            logger.warning(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Validation failed: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    @staticmethod
    def validate_doc_id(doc_id: str) -> bool:
        """문서 ID 형식 검증"""
        import re
        pattern = r'^DOC_[A-Z0-9]{8}$'
        return bool(re.match(pattern, doc_id))
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """사용자 ID 형식 검증"""
        import re
        pattern = r'^U\d{3}$'
        return bool(re.match(pattern, user_id))
    
    @staticmethod
    def validate_classification(classification: str) -> bool:
        """문서 등급 검증"""
        valid_classifications = ["public", "team", "confidential"]
        return classification in valid_classifications
    
    @staticmethod
    def validate_pagination(limit: int, offset: int) -> tuple[bool, Optional[str]]:
        """페이지네이션 검증"""
        if limit < 1 or limit > 100:
            return False, "limit must be between 1 and 100"
        
        if offset < 0:
            return False, "offset must be non-negative"
        
        return True, None
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """
        문자열 정제
        
        Args:
            text: 입력 텍스트
            max_length: 최대 길이
        
        Returns:
            정제된 문자열
        """
        # 공백 정규화
        text = " ".join(text.split())
        
        # 최대 길이 제한
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> tuple[bool, Optional[str]]:
        """
        날짜 범위 검증
        
        Args:
            start_date: 시작일 (ISO 8601)
            end_date: 종료일 (ISO 8601)
        
        Returns:
            (valid, error_message)
        """
        from datetime import datetime
        
        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            
            if start > end:
                return False, "start_date must be before end_date"
            
            # 최대 1년 범위
            delta = end - start
            if delta.days > 365:
                return False, "Date range cannot exceed 1 year"
            
            return True, None
        
        except ValueError as e:
            return False, f"Invalid date format: {e}"
```

### 3.3 registry.py - Tool 레지스트리

```python
# mcp-tools/registry.py
"""
Tool 레지스트리
"""

from typing import Dict, List, Optional
from .base import BaseTool, ToolMetadata
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Tool 레지스트리
    
    모든 Tool을 등록하고 관리
    """
    
    def __init__(self):
        """초기화"""
        self.tools: Dict[str, BaseTool] = {}
        self.metadata_cache: Dict[str, ToolMetadata] = {}
    
    def register(self, tool: BaseTool):
        """
        Tool 등록
        
        Args:
            tool: Tool 인스턴스
        
        Example:
            registry = ToolRegistry()
            registry.register(SearchDocumentsTool())
        """
        name = tool.metadata.name
        
        if name in self.tools:
            logger.warning(f"Tool already registered: {name}, overwriting")
        
        self.tools[name] = tool
        self.metadata_cache[name] = tool.metadata
        
        logger.info(f"Tool registered: {name} (v{tool.metadata.version})")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Tool 가져오기
        
        Args:
            name: Tool 이름
        
        Returns:
            Tool 인스턴스 또는 None
        """
        return self.tools.get(name)
    
    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """
        Tool 메타데이터 가져오기
        
        Args:
            name: Tool 이름
        
        Returns:
            ToolMetadata 또는 None
        """
        return self.metadata_cache.get(name)
    
    def list_tools(
        self,
        category: Optional[str] = None,
        department: Optional[str] = None
    ) -> List[ToolMetadata]:
        """
        Tool 목록 조회
        
        Args:
            category: 카테고리 필터
            department: 부서 필터
        
        Returns:
            List[ToolMetadata]
        """
        tools = list(self.metadata_cache.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        if department:
            tools = [t for t in tools if t.department == department]
        
        return tools
    
    def exists(self, name: str) -> bool:
        """Tool 존재 여부"""
        return name in self.tools
    
    def get_categories(self) -> List[str]:
        """카테고리 목록"""
        categories = set(t.category for t in self.metadata_cache.values())
        return sorted(categories)
    
    def get_departments(self) -> List[str]:
        """부서 목록"""
        departments = set(t.department for t in self.metadata_cache.values())
        return sorted(departments)
    
    def search_tools(self, query: str) -> List[ToolMetadata]:
        """
        Tool 검색
        
        Args:
            query: 검색어 (이름 또는 설명)
        
        Returns:
            List[ToolMetadata]
        """
        query_lower = query.lower()
        
        results = [
            metadata
            for metadata in self.metadata_cache.values()
            if query_lower in metadata.name.lower()
            or query_lower in metadata.description.lower()
        ]
        
        return results
    
    def get_stats(self) -> dict:
        """
        레지스트리 통계
        
        Returns:
            {
                "total": 10,
                "by_category": {"search": 2, "document": 5},
                "by_department": {"core": 8, "finance": 2}
            }
        """
        from collections import Counter
        
        categories = Counter(t.category for t in self.metadata_cache.values())
        departments = Counter(t.department for t in self.metadata_cache.values())
        
        return {
            "total": len(self.tools),
            "by_category": dict(categories),
            "by_department": dict(departments)
        }


# 전역 레지스트리
_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """전역 레지스트리 가져오기"""
    return _global_registry


def register_tool(tool: BaseTool):
    """Tool 등록 (편의 함수)"""
    _global_registry.register(tool)
```

***

## 4. 카테고리별 Tool 구현

### 4.1 core/search_tools.py - 검색 Tool

```python
# mcp-tools/core/search_tools.py
"""
문서 검색 Tool
"""

from ..base import BaseTool, ToolMetadata
from shared.elasticsearch import ElasticsearchManager
from shared.permissions import PermissionEngine
from shared.logging_config import get_logger
import time

logger = get_logger(__name__)


class SearchDocumentsTool(BaseTool):
    """
    문서 전문 검색 Tool
    
    Elasticsearch 기반 검색
    """
    
    def __init__(self, es_manager: ElasticsearchManager):
        """
        초기화
        
        Args:
            es_manager: Elasticsearch 매니저
        """
        self.es = es_manager
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        """메타데이터 정의"""
        return ToolMetadata(
            name="search_documents",
            description="문서 전문 검색 (Elasticsearch 기반)",
            category="search",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색어",
                        "minLength": 1
                    },
                    "classification": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["public", "team", "confidential"]
                        },
                        "description": "문서 등급 필터"
                    },
                    "category": {
                        "type": "string",
                        "description": "카테고리 필터"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "최대 결과 수",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "offset": {
                        "type": "integer",
                        "description": "오프셋",
                        "default": 0,
                        "minimum": 0
                    }
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "total": {"type": "integer"},
                    "query": {"type": "string"},
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "doc_id": {"type": "string"},
                                "title": {"type": "string"},
                                "snippet": {"type": "string"},
                                "classification": {"type": "string"},
                                "category": {"type": "string"},
                                "score": {"type": "number"}
                            }
                        }
                    }
                }
            },
            examples=[
                {
                    "name": "공개 문서 검색",
                    "input": {
                        "query": "예산",
                        "classification": ["public"],
                        "limit": 10
                    }
                }
            ]
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """
        검색 실행
        
        Args:
            arguments: {
                "query": "예산",
                "classification": ["public", "team"],
                "category": "finance",
                "limit": 10,
                "offset": 0
            }
            context: {
                "user_id": "U001",
                "user_role": "staff",
                "user_team": "dev_team"
            }
        
        Returns:
            {
                "status": "success",
                "data": {
                    "total": 5,
                    "query": "예산",
                    "results": [...]
                }
            }
        """
        start_time = time.time()
        
        try:
            # 1. 입력 검증
            valid, error = self.validate_arguments(arguments)
            if not valid:
                return self.create_error_response(error, "INVALID_INPUT")
            
            # 2. 권한 확인
            if context:
                authorized, error = self.check_permission(
                    context["user_role"],
                    self.metadata.required_permissions
                )
                if not authorized:
                    return self.create_error_response(error, "PERMISSION_DENIED")
            
            # 3. 검색 파라미터 추출
            query_text = arguments["query"]
            limit = arguments.get("limit", 10)
            offset = arguments.get("offset", 0)
            
            # 4. 접근 가능한 문서 등급 필터
            if context:
                accessible_classifications = self.perm_engine.get_accessible_classifications(
                    context["user_role"],
                    action="read"
                )
                
                # 사용자가 지정한 등급과 접근 가능한 등급의 교집합
                requested_classifications = arguments.get("classification")
                if requested_classifications:
                    classifications = list(
                        set(requested_classifications) & set(accessible_classifications)
                    )
                else:
                    classifications = accessible_classifications
            else:
                classifications = arguments.get("classification", ["public"])
            
            # 5. 검색 실행
            result = self.es.search_documents(
                query_text=query_text,
                classification=classifications,
                category=arguments.get("category"),
                team=context.get("user_team") if context else None,
                size=limit,
                from_=offset
            )
            
            # 6. 결과 반환
            execution_time = (time.time() - start_time) * 1000
            
            if context:
                self.log_execution(context, arguments, result, execution_time)
            
            return self.create_success_response({
                "total": result["total"],
                "query": query_text,
                "results": result["results"],
                "execution_time_ms": round(execution_time, 2)
            })
        
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return self.create_error_response(
                str(e),
                "SEARCH_ERROR",
                {"query": arguments.get("query")}
            )


class SuggestDocumentsTool(BaseTool):
    """
    문서 자동완성 Tool
    """
    
    def __init__(self, es_manager: ElasticsearchManager):
        self.es = es_manager
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="suggest_documents",
            description="문서 제목 자동완성",
            category="search",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "prefix": {
                        "type": "string",
                        "description": "검색 접두사",
                        "minLength": 1
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["prefix"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "suggestions": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """자동완성 실행"""
        try:
            prefix = arguments["prefix"]
            limit = arguments.get("limit", 5)
            
            # Elasticsearch suggest 쿼리
            body = {
                "suggest": {
                    "title_suggest": {
                        "prefix": prefix,
                        "completion": {
                            "field": "title.suggest",
                            "size": limit
                        }
                    }
                }
            }
            
            response = self.es.client.search(index="documents", body=body)
            
            suggestions = []
            if "suggest" in response:
                options = response["suggest"]["title_suggest"][0]["options"]
                suggestions = [opt["text"] for opt in options]
            
            return self.create_success_response({
                "suggestions": suggestions
            })
        
        except Exception as e:
            logger.error(f"Suggest failed: {e}")
            return self.create_error_response(str(e), "SUGGEST_ERROR")
```

### 4.2 core/document_tools.py - 문서 CRUD Tool

```python
# mcp-tools/core/document_tools.py
"""
문서 CRUD Tool
"""

from ..base import BaseTool, ToolMetadata
from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
from shared.permissions import PermissionEngine
from shared.utils import generate_id, now_iso
from shared.logging_config import get_logger
import queries

logger = get_logger(__name__)


class GetDocumentTool(BaseTool):
    """문서 상세 조회 Tool"""
    
    def __init__(self, db: DatabaseManager, es: ElasticsearchManager):
        self.db = db
        self.es = es
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_document",
            description="문서 상세 정보 조회",
            category="document",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "description": "문서 ID"
                    }
                },
                "required": ["doc_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "classification": {"type": "string"},
                    "category": {"type": "string"},
                    "author": {"type": "object"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """문서 조회"""
        try:
            doc_id = arguments["doc_id"]
            
            # 1. 문서 조회
            from shared.queries import GET_DOCUMENT_BY_ID
            docs = self.db.execute_query(GET_DOCUMENT_BY_ID, (doc_id,))
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            # 2. 권한 확인
            if context:
                has_permission = self.perm_engine.check_document_permission(
                    user_id=context["user_id"],
                    user_role=context["user_role"],
                    user_team=context.get("user_team"),
                    document={
                        "id": doc["id"],
                        "classification": doc["classification"],
                        "team": doc["team"],
                        "author_id": doc["author_id"]
                    },
                    action="read"
                )
                
                if not has_permission:
                    return self.create_error_response(
                        "Permission denied",
                        "PERMISSION_DENIED"
                    )
            
            # 3. 응답 생성
            return self.create_success_response({
                "doc_id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "classification": doc["classification"],
                "category": doc["category"],
                "team": doc["team"],
                "author": {
                    "id": doc["author_id"],
                    "name": doc["author_name"]
                },
                "version": doc["version"],
                "created_at": doc["created_at"].isoformat() if doc["created_at"] else None,
                "updated_at": doc["updated_at"].isoformat() if doc["updated_at"] else None
            })
        
        except Exception as e:
            logger.error(f"Get document failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "DATABASE_ERROR")


class CreateDocumentTool(BaseTool):
    """문서 생성 Tool"""
    
    def __init__(self, db: DatabaseManager, es: ElasticsearchManager):
        self.db = db
        self.es = es
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="create_document",
            description="새 문서 생성",
            category="document",
            department="core",
            version="1.0.0",
            required_permissions=["document:create"],
            input_schema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "문서 제목",
                        "minLength": 1,
                        "maxLength": 255
                    },
                    "content": {
                        "type": "string",
                        "description": "문서 내용 (Markdown)"
                    },
                    "classification": {
                        "type": "string",
                        "enum": ["public", "team", "confidential"],
                        "description": "문서 등급"
                    },
                    "category": {
                        "type": "string",
                        "description": "카테고리"
                    }
                },
                "required": ["title", "content", "classification"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "message": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """문서 생성"""
        try:
            # 1. 권한 확인
            if context:
                classification = arguments["classification"]
                
                # classification에 따른 권한 확인
                accessible = self.perm_engine.get_accessible_classifications(
                    context["user_role"],
                    action="create"
                )
                
                if classification not in accessible:
                    return self.create_error_response(
                        f"Cannot create {classification} document",
                        "PERMISSION_DENIED"
                    )
            
            # 2. 문서 ID 생성
            doc_id = generate_id("DOC", 8)
            
            # 3. team 설정
            team = None
            if arguments["classification"] == "team":
                if context and context.get("user_team"):
                    team = context["user_team"]
                else:
                    return self.create_error_response(
                        "Team document requires user team",
                        "INVALID_INPUT"
                    )
            
            # 4. DB 저장
            from shared.queries import CREATE_DOCUMENT
            self.db.execute_insert(
                CREATE_DOCUMENT,
                (
                    doc_id,
                    arguments["title"],
                    arguments["content"],
                    arguments["classification"],
                    arguments.get("category", "general"),
                    context["user_id"] if context else "SYSTEM",
                    team,
                    None,  # file_path
                    1      # version
                )
            )
            
            # 5. Elasticsearch 색인
            self.es.index_document(
                "documents",
                doc_id,
                {
                    "doc_id": doc_id,
                    "title": arguments["title"],
                    "content": arguments["content"],
                    "classification": arguments["classification"],
                    "category": arguments.get("category", "general"),
                    "author_id": context["user_id"] if context else "SYSTEM",
                    "team": team,
                    "created_at": now_iso(),
                    "version": 1
                }
            )
            
            logger.info(f"Document created: {doc_id} by {context.get('user_id')}")
            
            return self.create_success_response({
                "doc_id": doc_id,
                "message": f"Document created successfully: {doc_id}"
            })
        
        except Exception as e:
            logger.error(f"Create document failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "CREATE_ERROR")


class UpdateDocumentTool(BaseTool):
    """문서 수정 Tool"""
    
    def __init__(self, db: DatabaseManager, es: ElasticsearchManager):
        self.db = db
        self.es = es
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="update_document",
            description="문서 수정",
            category="document",
            department="core",
            version="1.0.0",
            required_permissions=["document:update"],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "classification": {"type": "string"}
                },
                "required": ["doc_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "version": {"type": "integer"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """문서 수정"""
        try:
            doc_id = arguments["doc_id"]
            
            # 1. 기존 문서 조회
            from shared.queries import GET_DOCUMENT_BY_ID
            docs = self.db.execute_query(GET_DOCUMENT_BY_ID, (doc_id,))
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            # 2. 권한 확인
            if context:
                has_permission = self.perm_engine.check_document_permission(
                    user_id=context["user_id"],
                    user_role=context["user_role"],
                    user_team=context.get("user_team"),
                    document={
                        "id": doc["id"],
                        "classification": doc["classification"],
                        "team": doc["team"],
                        "author_id": doc["author_id"]
                    },
                    action="update"
                )
                
                if not has_permission:
                    return self.create_error_response(
                        "Permission denied",
                        "PERMISSION_DENIED"
                    )
            
            # 3. 업데이트 필드 준비
            updates = {}
            if "title" in arguments:
                updates["title"] = arguments["title"]
            if "content" in arguments:
                updates["content"] = arguments["content"]
            if "classification" in arguments:
                updates["classification"] = arguments["classification"]
            
            if not updates:
                return self.create_error_response(
                    "No fields to update",
                    "INVALID_INPUT"
                )
            
            # 4. 버전 증가
            new_version = doc["version"] + 1
            updates["version"] = new_version
            
            # 5. DB 업데이트
            from shared.queries import UPDATE_DOCUMENT
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            query = f"UPDATE documents SET {set_clause}, updated_at = NOW() WHERE id = %s"
            
            params = list(updates.values()) + [doc_id]
            self.db.execute_update(query, tuple(params))
            
            # 6. Elasticsearch 업데이트
            es_update = {k: v for k, v in updates.items() if k != "version"}
            es_update["updated_at"] = now_iso()
            es_update["version"] = new_version
            
            self.es.update_document("documents", doc_id, es_update)
            
            logger.info(f"Document updated: {doc_id} to v{new_version}")
            
            return self.create_success_response({
                "message": f"Document updated to version {new_version}",
                "version": new_version
            })
        
        except Exception as e:
            logger.error(f"Update document failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "UPDATE_ERROR")


class DeleteDocumentTool(BaseTool):
    """문서 삭제 Tool"""
    
    def __init__(self, db: DatabaseManager, es: ElasticsearchManager):
        self.db = db
        self.es = es
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="delete_document",
            description="문서 삭제",
            category="document",
            department="core",
            version="1.0.0",
            required_permissions=["document:delete"],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"}
                },
                "required": ["doc_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """문서 삭제"""
        try:
            doc_id = arguments["doc_id"]
            
            # 1. 문서 조회
            from shared.queries import GET_DOCUMENT_BY_ID
            docs = self.db.execute_query(GET_DOCUMENT_BY_ID, (doc_id,))
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            # 2. 권한 확인
            if context:
                has_permission = self.perm_engine.check_document_permission(
                    user_id=context["user_id"],
                    user_role=context["user_role"],
                    user_team=context.get("user_team"),
                    document={
                        "id": doc["id"],
                        "classification": doc["classification"],
                        "team": doc["team"],
                        "author_id": doc["author_id"]
                    },
                    action="delete"
                )
                
                if not has_permission:
                    return self.create_error_response(
                        "Permission denied",
                        "PERMISSION_DENIED"
                    )
            
            # 3. DB 삭제
            from shared.queries import DELETE_DOCUMENT
            self.db.execute_update(DELETE_DOCUMENT, (doc_id,))
            
            # 4. Elasticsearch 삭제
            self.es.delete_document("documents", doc_id)
            
            logger.info(f"Document deleted: {doc_id} by {context.get('user_id')}")
            
            return self.create_success_response({
                "message": f"Document deleted: {doc_id}"
            })
        
        except Exception as e:
            logger.error(f"Delete document failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "DELETE_ERROR")


class ListDocumentsTool(BaseTool):
    """문서 목록 조회 Tool"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="list_documents",
            description="문서 목록 조회 (페이지네이션)",
            category="document",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "classification": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "category": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "total": {"type": "integer"},
                    "documents": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """문서 목록 조회"""
        try:
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            
            # 1. 접근 가능한 등급
            if context:
                accessible = self.perm_engine.get_accessible_classifications(
                    context["user_role"],
                    action="read"
                )
                
                requested = arguments.get("classification")
                if requested:
                    classifications = list(set(requested) & set(accessible))
                else:
                    classifications = accessible
            else:
                classifications = ["public"]
            
            # 2. 쿼리 구성
            from shared.queries import GET_DOCUMENTS_BY_CLASSIFICATION
            
            placeholders = ", ".join(["%s"] * len(classifications))
            query = f"""
                SELECT 
                    d.id, d.title, d.classification, d.category,
                    d.author_id, u.name AS author_name,
                    d.created_at, d.updated_at
                FROM documents d
                LEFT JOIN users u ON d.author_id = u.id
                WHERE d.classification IN ({placeholders})
            """
            
            params = list(classifications)
            
            # 카테고리 필터
            if arguments.get("category"):
                query += " AND d.category = %s"
                params.append(arguments["category"])
            
            # team 필터 (team 등급인 경우)
            if "team" in classifications and context and context.get("user_team"):
                query += " AND (d.classification != 'team' OR d.team = %s)"
                params.append(context["user_team"])
            
            query += " ORDER BY d.updated_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # 3. 실행
            documents = self.db.execute_query(query, tuple(params))
            
            # 4. 총 개수
            count_query = f"SELECT COUNT(*) AS total FROM documents d WHERE d.classification IN ({placeholders})"
            count_params = list(classifications)
            
            if arguments.get("category"):
                count_query += " AND d.category = %s"
                count_params.append(arguments["category"])
            
            result = self.db.execute_query(count_query, tuple(count_params))
            total = result[0]["total"]
            
            # 5. 응답
            return self.create_success_response({
                "total": total,
                "limit": limit,
                "offset": offset,
                "documents": [
                    {
                        "doc_id": doc["id"],
                        "title": doc["title"],
                        "classification": doc["classification"],
                        "category": doc["category"],
                        "author": {
                            "id": doc["author_id"],
                            "name": doc["author_name"]
                        },
                        "created_at": doc["created_at"].isoformat() if doc["created_at"] else None,
                        "updated_at": doc["updated_at"].isoformat() if doc["updated_at"] else None
                    }
                    for doc in documents
                ]
            })
        
        except Exception as e:
            logger.error(f"List documents failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "LIST_ERROR")
```




### 4.3 core/auth_tools.py - 인증/권한 Tool

```python
# mcp-tools/core/auth_tools.py
"""
인증 및 권한 관리 Tool
"""

from ..base import BaseTool, ToolMetadata
from shared.database import DatabaseManager
from shared.logging_config import get_logger

logger = get_logger(__name__)


class AuthenticateTool(BaseTool):
    """
    사용자 인증 Tool
    
    PoC에서는 user_id만으로 인증 (실제 운영에서는 토큰 기반)
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="authenticate",
            description="사용자 인증 (PoC: 사용자 선택)",
            category="auth",
            department="core",
            version="1.0.0",
            required_permissions=[],  # 인증 전이므로 권한 불필요
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "사용자 ID"
                    }
                },
                "required": ["user_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "role": {"type": "string"},
                            "team": {"type": "string"},
                            "department": {"type": "string"}
                        }
                    },
                    "token": {"type": "string"},
                    "message": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """
        사용자 인증
        
        Args:
            arguments: {"user_id": "U001"}
        
        Returns:
            {
                "status": "success",
                "data": {
                    "user": {...},
                    "token": "...",
                    "message": "Authentication successful"
                }
            }
        """
        try:
            user_id = arguments["user_id"]
            
            # 1. 사용자 조회
            from shared.queries import GET_USER_BY_ID
            users = self.db.execute_query(GET_USER_BY_ID, (user_id,))
            
            if not users:
                return self.create_error_response(
                    f"User not found: {user_id}",
                    "USER_NOT_FOUND"
                )
            
            user = users[0]
            
            # 2. 활성 상태 확인
            if not user["active"]:
                return self.create_error_response(
                    "User account is inactive",
                    "USER_INACTIVE"
                )
            
            # 3. 토큰 생성 (PoC: 간단한 토큰)
            # 실제 운영에서는 JWT 등 사용
            import hashlib
            import time
            token = hashlib.sha256(
                f"{user_id}:{time.time()}".encode()
            ).hexdigest()[:32]
            
            # 4. 감사 로그
            from shared.queries import CREATE_AUDIT_LOG
            self.db.execute_insert(
                CREATE_AUDIT_LOG,
                (user_id, "login", "user", user_id, None, "success", None, None)
            )
            
            logger.info(f"User authenticated: {user_id} ({user['name']})")
            
            return self.create_success_response({
                "user": {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                    "team": user["team"],
                    "department": user["department"],
                    "position": user["position"]
                },
                "token": token,
                "message": f"Welcome, {user['name']}!"
            })
        
        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "AUTH_ERROR")


class RequestAccessTool(BaseTool):
    """
    문서 접근 권한 요청 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="request_access",
            description="문서 접근 권한 요청",
            category="auth",
            department="core",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "description": "문서 ID"
                    },
                    "reason": {
                        "type": "string",
                        "description": "요청 사유",
                        "minLength": 10,
                        "maxLength": 1000
                    }
                },
                "required": ["doc_id", "reason"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "request_id": {"type": "integer"},
                    "message": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """
        접근 권한 요청
        
        Args:
            arguments: {
                "doc_id": "DOC001",
                "reason": "프로젝트 수행을 위해 필요합니다..."
            }
            context: {"user_id": "U001"}
        
        Returns:
            {
                "status": "success",
                "data": {
                    "request_id": 123,
                    "message": "Access request submitted"
                }
            }
        """
        try:
            if not context or "user_id" not in context:
                return self.create_error_response(
                    "Authentication required",
                    "AUTH_REQUIRED"
                )
            
            doc_id = arguments["doc_id"]
            reason = arguments["reason"]
            user_id = context["user_id"]
            
            # 1. 문서 존재 확인
            from shared.queries import GET_DOCUMENT_BY_ID
            docs = self.db.execute_query(GET_DOCUMENT_BY_ID, (doc_id,))
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            # 2. 이미 요청했는지 확인
            existing = self.db.execute_query(
                """
                SELECT id FROM access_requests
                WHERE user_id = %s AND resource_id = %s AND status = 'pending'
                """,
                (user_id, doc_id)
            )
            
            if existing:
                return self.create_error_response(
                    "Access request already pending",
                    "DUPLICATE_REQUEST"
                )
            
            # 3. 요청 생성
            from shared.queries import CREATE_ACCESS_REQUEST
            request_id = self.db.execute_insert(
                CREATE_ACCESS_REQUEST,
                (user_id, "document", doc_id, reason, "pending")
            )
            
            logger.info(f"Access request created: {request_id} by {user_id} for {doc_id}")
            
            return self.create_success_response({
                "request_id": request_id,
                "message": "Access request submitted successfully. Waiting for approval."
            })
        
        except Exception as e:
            logger.error(f"Request access failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "REQUEST_ERROR")


class ApproveAccessTool(BaseTool):
    """
    접근 권한 승인 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="approve_access",
            description="접근 권한 요청 승인/거부",
            category="auth",
            department="core",
            version="1.0.0",
            required_permissions=["admin:approve"],
            input_schema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "integer",
                        "description": "요청 ID"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["approve", "reject"],
                        "description": "승인 또는 거부"
                    },
                    "comment": {
                        "type": "string",
                        "description": "검토 의견"
                    }
                },
                "required": ["request_id", "action"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """권한 승인/거부"""
        try:
            if not context:
                return self.create_error_response(
                    "Authentication required",
                    "AUTH_REQUIRED"
                )
            
            # 1. 승인 권한 확인
            from shared.permissions import PermissionEngine
            perm_engine = PermissionEngine()
            
            can_approve = perm_engine.can_approve_request(
                approver_role=context["user_role"],
                approver_team=context.get("user_team"),
                requester_team=None  # 요청자 팀 확인 필요
            )
            
            if not can_approve:
                return self.create_error_response(
                    "Permission denied: cannot approve requests",
                    "PERMISSION_DENIED"
                )
            
            # 2. 요청 조회
            request_id = arguments["request_id"]
            requests = self.db.execute_query(
                "SELECT * FROM access_requests WHERE id = %s",
                (request_id,)
            )
            
            if not requests:
                return self.create_error_response(
                    f"Request not found: {request_id}",
                    "NOT_FOUND"
                )
            
            request = requests[0]
            
            if request["status"] != "pending":
                return self.create_error_response(
                    f"Request already {request['status']}",
                    "INVALID_STATUS"
                )
            
            # 3. 승인/거부 처리
            action = arguments["action"]
            status = "approved" if action == "approve" else "rejected"
            
            self.db.execute_update(
                """
                UPDATE access_requests
                SET status = %s, reviewed_at = NOW(), reviewed_by = %s, review_comment = %s
                WHERE id = %s
                """,
                (status, context["user_id"], arguments.get("comment"), request_id)
            )
            
            # 4. 승인된 경우 권한 부여
            if status == "approved":
                from shared.queries import CREATE_PERMISSION
                self.db.execute_insert(
                    CREATE_PERMISSION,
                    (
                        request["user_id"],
                        None,  # role
                        request["resource_type"],
                        request["resource_id"],
                        '["read"]',
                        context["user_id"],
                        f"Approved via request #{request_id}",
                        None  # expires_at
                    )
                )
            
            logger.info(f"Request {request_id} {status} by {context['user_id']}")
            
            return self.create_success_response({
                "message": f"Request {status} successfully"
            })
        
        except Exception as e:
            logger.error(f"Approve access failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "APPROVE_ERROR")


class GetMyPermissionsTool(BaseTool):
    """
    내 권한 조회 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_my_permissions",
            description="내 권한 목록 조회",
            category="auth",
            department="core",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {}
            },
            output_schema={
                "type": "object",
                "properties": {
                    "role_permissions": {"type": "object"},
                    "special_permissions": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """내 권한 조회"""
        try:
            if not context:
                return self.create_error_response(
                    "Authentication required",
                    "AUTH_REQUIRED"
                )
            
            # 1. 역할 기반 권한
            from shared.permissions import PermissionEngine
            perm_engine = PermissionEngine()
            
            role_permissions = perm_engine.get_permission_summary(
                context["user_role"]
            )
            
            # 2. 특별 권한 (DB)
            special_permissions = self.db.execute_query(
                """
                SELECT 
                    resource_type, resource_id, actions,
                    granted_by, reason, expires_at
                FROM permissions
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (context["user_id"],)
            )
            
            return self.create_success_response({
                "role": context["user_role"],
                "role_permissions": role_permissions,
                "special_permissions": [
                    {
                        "resource_type": p["resource_type"],
                        "resource_id": p["resource_id"],
                        "actions": p["actions"],
                        "granted_by": p["granted_by"],
                        "reason": p["reason"],
                        "expires_at": p["expires_at"].isoformat() if p["expires_at"] else None
                    }
                    for p in special_permissions
                ]
            })
        
        except Exception as e:
            logger.error(f"Get permissions failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "PERMISSION_ERROR")
```

### 4.4 core/version_tools.py - 버전 관리 Tool

```python
# mcp-tools/core/version_tools.py
"""
문서 버전 관리 Tool
"""

from ..base import BaseTool, ToolMetadata
from shared.database import DatabaseManager
from shared.permissions import PermissionEngine
from shared.logging_config import get_logger

logger = get_logger(__name__)


class GetDocumentVersionsTool(BaseTool):
    """
    문서 버전 히스토리 조회 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_document_versions",
            description="문서 버전 히스토리 조회",
            category="version",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "description": "문서 ID"
                    }
                },
                "required": ["doc_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "current_version": {"type": "integer"},
                    "versions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "version": {"type": "integer"},
                                "title": {"type": "string"},
                                "changed_by": {"type": "string"},
                                "change_summary": {"type": "string"},
                                "created_at": {"type": "string"}
                            }
                        }
                    }
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """
        버전 히스토리 조회
        
        Args:
            arguments: {"doc_id": "DOC001"}
            context: {"user_id": "U001", "user_role": "staff"}
        
        Returns:
            {
                "status": "success",
                "data": {
                    "doc_id": "DOC001",
                    "current_version": 3,
                    "versions": [...]
                }
            }
        """
        try:
            doc_id = arguments["doc_id"]
            
            # 1. 문서 권한 확인
            from shared.queries import GET_DOCUMENT_BY_ID
            docs = self.db.execute_query(GET_DOCUMENT_BY_ID, (doc_id,))
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            if context:
                has_permission = self.perm_engine.check_document_permission(
                    user_id=context["user_id"],
                    user_role=context["user_role"],
                    user_team=context.get("user_team"),
                    document={
                        "id": doc["id"],
                        "classification": doc["classification"],
                        "team": doc["team"],
                        "author_id": doc["author_id"]
                    },
                    action="read"
                )
                
                if not has_permission:
                    return self.create_error_response(
                        "Permission denied",
                        "PERMISSION_DENIED"
                    )
            
            # 2. 버전 히스토리 조회
            from shared.queries import GET_DOCUMENT_VERSIONS
            versions = self.db.execute_query(GET_DOCUMENT_VERSIONS, (doc_id,))
            
            return self.create_success_response({
                "doc_id": doc_id,
                "current_version": doc["version"],
                "versions": [
                    {
                        "version": v["version"],
                        "title": v["title"],
                        "changed_by": v["changed_by"],
                        "change_summary": v["change_summary"],
                        "created_at": v["created_at"].isoformat() if v["created_at"] else None
                    }
                    for v in versions
                ]
            })
        
        except Exception as e:
            logger.error(f"Get versions failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "VERSION_ERROR")


class GetDocumentVersionTool(BaseTool):
    """
    특정 버전 문서 조회 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_document_version",
            description="특정 버전 문서 내용 조회",
            category="version",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "version": {"type": "integer"}
                },
                "required": ["doc_id", "version"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "version": {"type": "integer"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "changed_by": {"type": "string"},
                    "created_at": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """특정 버전 조회"""
        try:
            doc_id = arguments["doc_id"]
            version = arguments["version"]
            
            # 1. 권한 확인 (현재 문서 기준)
            from shared.queries import GET_DOCUMENT_BY_ID
            docs = self.db.execute_query(GET_DOCUMENT_BY_ID, (doc_id,))
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            if context:
                has_permission = self.perm_engine.check_document_permission(
                    user_id=context["user_id"],
                    user_role=context["user_role"],
                    user_team=context.get("user_team"),
                    document={
                        "id": doc["id"],
                        "classification": doc["classification"],
                        "team": doc["team"],
                        "author_id": doc["author_id"]
                    },
                    action="read"
                )
                
                if not has_permission:
                    return self.create_error_response(
                        "Permission denied",
                        "PERMISSION_DENIED"
                    )
            
            # 2. 버전 조회
            from shared.queries import GET_DOCUMENT_VERSION
            versions = self.db.execute_query(GET_DOCUMENT_VERSION, (doc_id, version))
            
            if not versions:
                return self.create_error_response(
                    f"Version {version} not found for document {doc_id}",
                    "VERSION_NOT_FOUND"
                )
            
            version_data = versions[0]
            
            return self.create_success_response({
                "doc_id": doc_id,
                "version": version_data["version"],
                "title": version_data["title"],
                "content": version_data["content"],
                "changed_by": version_data["changed_by"],
                "change_summary": version_data["change_summary"],
                "created_at": version_data["created_at"].isoformat() if version_data["created_at"] else None
            })
        
        except Exception as e:
            logger.error(f"Get version failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "VERSION_ERROR")


class CompareVersionsTool(BaseTool):
    """
    문서 버전 비교 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.perm_engine = PermissionEngine()
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="compare_versions",
            description="두 버전 비교 (diff)",
            category="version",
            department="core",
            version="1.0.0",
            required_permissions=["document:read"],
            input_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "version1": {"type": "integer"},
                    "version2": {"type": "integer"}
                },
                "required": ["doc_id", "version1", "version2"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "version1": {"type": "integer"},
                    "version2": {"type": "integer"},
                    "diff": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """버전 비교"""
        try:
            doc_id = arguments["doc_id"]
            version1 = arguments["version1"]
            version2 = arguments["version2"]
            
            # 1. 권한 확인
            from shared.queries import GET_DOCUMENT_BY_ID
            docs = self.db.execute_query(GET_DOCUMENT_BY_ID, (doc_id,))
            
            if not docs:
                return self.create_error_response(
                    f"Document not found: {doc_id}",
                    "NOT_FOUND"
                )
            
            doc = docs[0]
            
            if context:
                has_permission = self.perm_engine.check_document_permission(
                    user_id=context["user_id"],
                    user_role=context["user_role"],
                    user_team=context.get("user_team"),
                    document={
                        "id": doc["id"],
                        "classification": doc["classification"],
                        "team": doc["team"],
                        "author_id": doc["author_id"]
                    },
                    action="read"
                )
                
                if not has_permission:
                    return self.create_error_response(
                        "Permission denied",
                        "PERMISSION_DENIED"
                    )
            
            # 2. 두 버전 조회
            from shared.queries import GET_DOCUMENT_VERSION
            v1_data = self.db.execute_query(GET_DOCUMENT_VERSION, (doc_id, version1))
            v2_data = self.db.execute_query(GET_DOCUMENT_VERSION, (doc_id, version2))
            
            if not v1_data or not v2_data:
                return self.create_error_response(
                    "One or both versions not found",
                    "VERSION_NOT_FOUND"
                )
            
            # 3. Diff 생성 (간단한 버전)
            import difflib
            
            content1 = v1_data[0]["content"].splitlines()
            content2 = v2_data[0]["content"].splitlines()
            
            diff = difflib.unified_diff(
                content1,
                content2,
                fromfile=f"v{version1}",
                tofile=f"v{version2}",
                lineterm=""
            )
            
            diff_text = "\n".join(diff)
            
            return self.create_success_response({
                "doc_id": doc_id,
                "version1": version1,
                "version2": version2,
                "diff": diff_text
            })
        
        except Exception as e:
            logger.error(f"Compare versions failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "COMPARE_ERROR")
```

### 4.5 core/audit_tools.py - 감사 Tool

```python
# mcp-tools/core/audit_tools.py
"""
감사 로그 Tool
"""

from ..base import BaseTool, ToolMetadata
from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
from shared.logging_config import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)


class GetAuditLogsTool(BaseTool):
    """
    감사 로그 조회 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_audit_logs",
            description="감사 로그 조회 (관리자 전용)",
            category="audit",
            department="core",
            version="1.0.0",
            required_permissions=["admin:manage"],
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "사용자 ID 필터"
                    },
                    "action": {
                        "type": "string",
                        "description": "액션 필터"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "시작일 (ISO 8601)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "종료일 (ISO 8601)"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 100,
                        "maximum": 1000
                    },
                    "offset": {
                        "type": "integer",
                        "default": 0
                    }
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "total": {"type": "integer"},
                    "logs": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """
        감사 로그 조회
        
        Args:
            arguments: {
                "user_id": "U001",
                "action": "document_view",
                "start_date": "2026-01-01T00:00:00Z",
                "end_date": "2026-01-31T23:59:59Z",
                "limit": 100,
                "offset": 0
            }
        """
        try:
            # 1. 권한 확인 (admin만)
            if context and context["user_role"] != "admin":
                return self.create_error_response(
                    "Admin permission required",
                    "PERMISSION_DENIED"
                )
            
            # 2. 쿼리 구성
            query = """
                SELECT 
                    a.id, a.user_id, a.action, a.resource_type, a.resource_id,
                    a.result, a.ip_address, a.created_at,
                    u.name AS user_name
                FROM audit_logs a
                LEFT JOIN users u ON a.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            # 필터 추가
            if arguments.get("user_id"):
                query += " AND a.user_id = %s"
                params.append(arguments["user_id"])
            
            if arguments.get("action"):
                query += " AND a.action = %s"
                params.append(arguments["action"])
            
            if arguments.get("start_date"):
                query += " AND a.created_at >= %s"
                params.append(arguments["start_date"])
            
            if arguments.get("end_date"):
                query += " AND a.created_at <= %s"
                params.append(arguments["end_date"])
            
            # 페이지네이션
            limit = arguments.get("limit", 100)
            offset = arguments.get("offset", 0)
            
            query += " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # 3. 실행
            logs = self.db.execute_query(query, tuple(params))
            
            # 4. 총 개수
            count_query = query.split("ORDER BY")[0].replace(
                "SELECT a.id, a.user_id, a.action, a.resource_type, a.resource_id, a.result, a.ip_address, a.created_at, u.name AS user_name",
                "SELECT COUNT(*) AS total"
            )
            result = self.db.execute_query(count_query, tuple(params[:-2]))
            total = result[0]["total"]
            
            return self.create_success_response({
                "total": total,
                "limit": limit,
                "offset": offset,
                "logs": [
                    {
                        "id": log["id"],
                        "user_id": log["user_id"],
                        "user_name": log["user_name"],
                        "action": log["action"],
                        "resource_type": log["resource_type"],
                        "resource_id": log["resource_id"],
                        "result": log["result"],
                        "ip_address": log["ip_address"],
                        "created_at": log["created_at"].isoformat() if log["created_at"] else None
                    }
                    for log in logs
                ]
            })
        
        except Exception as e:
            logger.error(f"Get audit logs failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "AUDIT_ERROR")


class GetMyActivityTool(BaseTool):
    """
    내 활동 로그 조회 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_my_activity",
            description="내 활동 로그 조회",
            category="audit",
            department="core",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "최근 N일",
                        "default": 7,
                        "minimum": 1,
                        "maximum": 90
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "maximum": 200
                    }
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "total": {"type": "integer"},
                    "activities": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """내 활동 조회"""
        try:
            if not context or "user_id" not in context:
                return self.create_error_response(
                    "Authentication required",
                    "AUTH_REQUIRED"
                )
            
            user_id = context["user_id"]
            days = arguments.get("days", 7)
            limit = arguments.get("limit", 50)
            
            # 날짜 범위
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 활동 조회
            from shared.queries import GET_AUDIT_LOGS_BY_USER
            activities = self.db.execute_query(
                """
                SELECT 
                    id, action, resource_type, resource_id,
                    result, created_at
                FROM audit_logs
                WHERE user_id = %s AND created_at >= %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, start_date, limit)
            )
            
            return self.create_success_response({
                "total": len(activities),
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "activities": [
                    {
                        "id": act["id"],
                        "action": act["action"],
                        "resource_type": act["resource_type"],
                        "resource_id": act["resource_id"],
                        "result": act["result"],
                        "created_at": act["created_at"].isoformat() if act["created_at"] else None
                    }
                    for act in activities
                ]
            })
        
        except Exception as e:
            logger.error(f"Get my activity failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "ACTIVITY_ERROR")


class GetStatisticsTool(BaseTool):
    """
    통계 조회 Tool
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_statistics",
            description="시스템 통계 조회 (관리자 전용)",
            category="audit",
            department="core",
            version="1.0.0",
            required_permissions=["admin:manage"],
            input_schema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["documents", "users", "activities"],
                        "description": "통계 타입"
                    },
                    "period": {
                        "type": "string",
                        "enum": ["day", "week", "month"],
                        "default": "week"
                    }
                },
                "required": ["type"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "period": {"type": "string"},
                    "data": {"type": "object"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """통계 조회"""
        try:
            # 권한 확인
            if context and context["user_role"] != "admin":
                return self.create_error_response(
                    "Admin permission required",
                    "PERMISSION_DENIED"
                )
            
            stat_type = arguments["type"]
            period = arguments.get("period", "week")
            
            # 기간 계산
            end_date = datetime.now()
            if period == "day":
                start_date = end_date - timedelta(days=1)
            elif period == "week":
                start_date = end_date - timedelta(days=7)
            else:  # month
                start_date = end_date - timedelta(days=30)
            
            data = {}
            
            if stat_type == "documents":
                # 문서 통계
                result = self.db.execute_query(
                    """
                    SELECT 
                        COUNT(*) AS total,
                        SUM(CASE WHEN classification = 'public' THEN 1 ELSE 0 END) AS public_count,
                        SUM(CASE WHEN classification = 'team' THEN 1 ELSE 0 END) AS team_count,
                        SUM(CASE WHEN classification = 'confidential' THEN 1 ELSE 0 END) AS confidential_count,
                        SUM(CASE WHEN created_at >= %s THEN 1 ELSE 0 END) AS recent_count
                    FROM documents
                    """,
                    (start_date,)
                )
                
                data = result[0]
            
            elif stat_type == "users":
                # 사용자 통계
                result = self.db.execute_query(
                    """
                    SELECT 
                        COUNT(*) AS total,
                        SUM(CASE WHEN active = TRUE THEN 1 ELSE 0 END) AS active_count,
                        SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) AS admin_count,
                        SUM(CASE WHEN role = 'manager' THEN 1 ELSE 0 END) AS manager_count,
                        SUM(CASE WHEN role = 'staff' THEN 1 ELSE 0 END) AS staff_count,
                        SUM(CASE WHEN role = 'junior' THEN 1 ELSE 0 END) AS junior_count
                    FROM users
                    """
                )
                
                data = result[0]
            
            elif stat_type == "activities":
                # 활동 통계
                result = self.db.execute_query(
                    """
                    SELECT 
                        COUNT(*) AS total,
                        SUM(CASE WHEN action LIKE 'document_%' THEN 1 ELSE 0 END) AS document_actions,
                        SUM(CASE WHEN action = 'login' THEN 1 ELSE 0 END) AS login_count,
                        SUM(CASE WHEN result = 'failure' THEN 1 ELSE 0 END) AS failure_count
                    FROM audit_logs
                    WHERE created_at >= %s
                    """,
                    (start_date,)
                )
                
                data = result[0]
            
            return self.create_success_response({
                "type": stat_type,
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "data": data
            })
        
        except Exception as e:
            logger.error(f"Get statistics failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "STATISTICS_ERROR")
```

***

## 5. 테스트 및 배포

### 5.1 Tool 테스트

```python
# mcp-tools/tests/test_document_tools.py
"""
문서 Tool 테스트
"""

import pytest
from mcp_tools.core.document_tools import (
    GetDocumentTool,
    CreateDocumentTool,
    UpdateDocumentTool,
    DeleteDocumentTool
)
from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager


@pytest.fixture
def db():
    """테스트용 DB"""
    config = {
        "host": "localhost",
        "port": 3306,
        "database": "test_mcps_db",
        "user": "test_user",
        "password": "test_password",
        "charset": "utf8mb4",
        "pool_size": {"min": 1, "max": 5}
    }
    db = DatabaseManager(config)
    yield db
    db.close()


@pytest.fixture
def es():
    """테스트용 ES"""
    config = {
        "hosts": ["localhost:9200"],
        "timeout": 30
    }
    es = ElasticsearchManager(config)
    yield es
    es.close()


@pytest.fixture
def context():
    """테스트용 컨텍스트"""
    return {
        "user_id": "U002",
        "user_role": "staff",
        "user_team": "dev_team",
        "request_id": "test_req_001"
    }


def test_get_document_tool(db, es, context):
    """문서 조회 테스트"""
    tool = GetDocumentTool(db, es)
    
    # 존재하는 문서 조회
    result = tool.execute(
        {"doc_id": "DOC001"},
        context
    )
    
    assert result["status"] == "success"
    assert result["data"]["doc_id"] == "DOC001"
    assert "title" in result["data"]
    assert "content" in result["data"]


def test_get_document_not_found(db, es, context):
    """존재하지 않는 문서 조회"""
    tool = GetDocumentTool(db, es)
    
    result = tool.execute(
        {"doc_id": "DOC999"},
        context
    )
    
    assert result["status"] == "error"
    assert result["error"]["code"] == "NOT_FOUND"


def test_create_document_tool(db, es, context):
    """문서 생성 테스트"""
    tool = CreateDocumentTool(db, es)
    
    result = tool.execute(
        {
            "title": "테스트 문서",
            "content": "# 테스트\n\n내용...",
            "classification": "public",
            "category": "test"
        },
        context
    )
    
    assert result["status"] == "success"
    assert "doc_id" in result["data"]
    
    # 생성된 문서 조회
    get_tool = GetDocumentTool(db, es)
    get_result = get_tool.execute(
        {"doc_id": result["data"]["doc_id"]},
        context
    )
    
    assert get_result["status"] == "success"
    assert get_result["data"]["title"] == "테스트 문서"


def test_create_document_permission_denied(db, es):
    """권한 없음 - 문서 생성"""
    tool = CreateDocumentTool(db, es)
    
    # junior는 confidential 생성 불가
    junior_context = {
        "user_id": "U001",
        "user_role": "junior",
        "user_team": None
    }
    
    result = tool.execute(
        {
            "title": "기밀 문서",
            "content": "내용",
            "classification": "confidential"
        },
        junior_context
    )
    
    assert result["status"] == "error"
    assert result["error"]["code"] == "PERMISSION_DENIED"


def test_update_document_tool(db, es, context):
    """문서 수정 테스트"""
    tool = UpdateDocumentTool(db, es)
    
    result = tool.execute(
        {
            "doc_id": "DOC001",
            "title": "수정된 제목",
            "content": "수정된 내용"
        },
        context
    )
    
    assert result["status"] == "success"
    assert "version" in result["data"]


def test_delete_document_tool(db, es):
    """문서 삭제 테스트"""
    # 먼저 테스트 문서 생성
    create_tool = CreateDocumentTool(db, es)
    manager_context = {
        "user_id": "U003",
        "user_role": "manager",
        "user_team": "dev_team"
    }
    
    create_result = create_tool.execute(
        {
            "title": "삭제할 문서",
            "content": "내용",
            "classification": "team"
        },
        manager_context
    )
    
    doc_id = create_result["data"]["doc_id"]
    
    # 삭제
    delete_tool = DeleteDocumentTool(db, es)
    delete_result = delete_tool.execute(
        {"doc_id": doc_id},
        manager_context
    )
    
    assert delete_result["status"] == "success"
    
    # 삭제 확인
    get_tool = GetDocumentTool(db, es)
    get_result = get_tool.execute(
        {"doc_id": doc_id},
        manager_context
    )
    
    assert get_result["status"] == "error"
    assert get_result["error"]["code"] == "NOT_FOUND"
```

### 5.2 통합 테스트

```python
# mcp-tools/tests/test_integration.py
"""
Tool 통합 테스트
"""

import pytest
from mcp_tools.registry import ToolRegistry
from mcp_tools.core.document_tools import *
from mcp_tools.core.search_tools import *
from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager


@pytest.fixture
def registry(db, es):
    """Tool 레지스트리"""
    registry = ToolRegistry()
    
    # Tool 등록
    registry.register(SearchDocumentsTool(es))
    registry.register(GetDocumentTool(db, es))
    registry.register(CreateDocumentTool(db, es))
    registry.register(UpdateDocumentTool(db, es))
    registry.register(DeleteDocumentTool(db, es))
    
    return registry


def test_document_workflow(registry):
    """문서 전체 워크플로우 테스트"""
    context = {
        "user_id": "U002",
        "user_role": "staff",
        "user_team": "dev_team"
    }
    
    # 1. 문서 생성
    create_tool = registry.get_tool("create_document")
    create_result = create_tool.execute(
        {
            "title": "통합 테스트 문서",
            "content": "# 테스트\n\n내용입니다.",
            "classification": "team",
            "category": "test"
        },
        context
    )
    
    assert create_result["status"] == "success"
    doc_id = create_result["data"]["doc_id"]
    
    # 2. 문서 조회
    get_tool = registry.get_tool("get_document")
    get_result = get_tool.execute({"doc_id": doc_id}, context)
    
    assert get_result["status"] == "success"
    assert get_result["data"]["title"] == "통합 테스트 문서"
    
    # 3. 문서 수정
    update_tool = registry.get_tool("update_document")
    update_result = update_tool.execute(
        {
            "doc_id": doc_id,
            "title": "수정된 테스트 문서"
        },
        context
    )
    
    assert update_result["status"] == "success"
    
    # 4. 검색
    search_tool = registry.get_tool("search_documents")
    search_result = search_tool.execute(
        {
            "query": "테스트",
            "classification": ["team"]
        },
        context
    )
    
    assert search_result["status"] == "success"
    assert search_result["data"]["total"] > 0
    
    # 생성한 문서가 검색 결과에 있는지 확인
    found = any(
        r["doc_id"] == doc_id
        for r in search_result["data"]["results"]
    )
    assert found


def test_permission_enforcement(registry):
    """권한 강제 테스트"""
    junior_context = {
        "user_id": "U001",
        "user_role": "junior",
        "user_team": None
    }
    
    # 1. junior는 team 문서 읽기 불가
    get_tool = registry.get_tool("get_document")
    result = get_tool.execute(
        {"doc_id": "DOC004"},  # team 문서
        junior_context
    )
    
    assert result["status"] == "error"
    assert result["error"]["code"] == "PERMISSION_DENIED"
    
    # 2. junior는 문서 생성 불가
    create_tool = registry.get_tool("create_document")
    result = create_tool.execute(
        {
            "title": "테스트",
            "content": "내용",
            "classification": "public"
        },
        junior_context
    )
    
    assert result["status"] == "error"
```

***

## 6. 확장 가이드

### 6.1 새 Tool 추가 절차

**1단계: Tool 클래스 작성**

```python
# mcp-tools/custom/my_tool.py

from mcp_tools.base import BaseTool, ToolMetadata

class MyCustomTool(BaseTool):
    """커스텀 Tool"""
    
    def __init__(self, db, es):
        self.db = db
        self.es = es
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="my_custom_tool",
            description="커스텀 기능",
            category="custom",
            department="my_dept",
            version="1.0.0",
            required_permissions=["custom:execute"],
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                },
                "required": ["param1"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """실행 로직"""
        try:
            # 입력 검증
            valid, error = self.validate_arguments(arguments)
            if not valid:
                return self.create_error_response(error, "INVALID_INPUT")
            
            # 권한 확인
            if context:
                authorized, error = self.check_permission(
                    context["user_role"],
                    self.metadata.required_permissions
                )
                if not authorized:
                    return self.create_error_response(error, "PERMISSION_DENIED")
            
            # 비즈니스 로직
            param1 = arguments["param1"]
            result = f"Processed: {param1}"
            
            return self.create_success_response({
                "result": result
            })
        
        except Exception as e:
            return self.create_error_response(str(e), "EXECUTION_ERROR")
```

**2단계: Tool 등록**

```python
# mcp-tools/__init__.py

from .custom.my_tool import MyCustomTool
from .registry import register_tool

def initialize_tools(db, es):
    """Tool 초기화 및 등록"""
    
    # 기존 Tool
    from .core.document_tools import *
    from .core.search_tools import *
    
    register_tool(GetDocumentTool(db, es))
    register_tool(SearchDocumentsTool(es))
    # ...
    
    # 커스텀 Tool 등록
    register_tool(MyCustomTool(db, es))
```

**3단계: registry.json 업데이트**

```json
{
  "tools": [
    {
      "name": "my_custom_tool",
      "description": "커스텀 기능",
      "category": "custom",
      "department": "my_dept",
      "version": "1.0.0",
      "server": "custom_server",
      "enabled": true,
      "required_permissions": ["custom:execute"],
      "input_schema": {...},
      "output_schema": {...}
    }
  ]
}
```

**4단계: 테스트 작성**

```python
# mcp-tools/tests/test_my_tool.py

import pytest
from mcp_tools.custom.my_tool import MyCustomTool

def test_my_custom_tool(db, es):
    """커스텀 Tool 테스트"""
    tool = MyCustomTool(db, es)
    
    result = tool.execute(
        {"param1": "test"},
        {"user_id": "U001", "user_role": "admin"}
    )
    
    assert result["status"] == "success"
    assert "result" in result["data"]
```

### 6.2 Tool 템플릿

```python
# mcp-tools/templates/tool_template.py
"""
Tool 템플릿

새 Tool 작성 시 이 템플릿을 복사하여 사용
"""

from mcp_tools.base import BaseTool, ToolMetadata
from shared.logging_config import get_logger

logger = get_logger(__name__)


class TemplateTool(BaseTool):
    """
    Tool 설명
    
    상세 설명...
    """
    
    def __init__(self, db, es):
        """
        초기화
        
        Args:
            db: DatabaseManager
            es: ElasticsearchManager
        """
        self.db = db
        self.es = es
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        """메타데이터 정의"""
        return ToolMetadata(
            name="tool_name",
            description="Tool 설명",
            category="category",  # search, document, auth, etc.
            department="department",  # core, finance, hr, etc.
            version="1.0.0",
            required_permissions=["permission:action"],
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "파라미터 설명"
                    }
                },
                "required": ["param1"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            },
            examples=[
                {
                    "name": "예제 1",
                    "input": {"param1": "value"},
                    "output": {"result": "output"}
                }
            ]
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """
        Tool 실행
        
        Args:
            arguments: 입력 인자
            context: 실행 컨텍스트
        
        Returns:
            {
                "status": "success" | "error",
                "data": {...} | "error": {...}
            }
        """
        try:
            # 1. 입력 검증
            valid, error = self.validate_arguments(arguments)
            if not valid:
                return self.create_error_response(error, "INVALID_INPUT")
            
            # 2. 권한 확인
            if context:
                authorized, error = self.check_permission(
                    context["user_role"],
                    self.metadata.required_permissions
                )
                if not authorized:
                    return self.create_error_response(error, "PERMISSION_DENIED")
            
            # 3. 비즈니스 로직
            param1 = arguments["param1"]
            
            # TODO: 실제 로직 구현
            result = {"result": f"Processed: {param1}"}
            
            # 4. 성공 응답
            return self.create_success_response(result)
        
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "EXECUTION_ERROR")
```

### 6.3 베스트 프랙티스

**1. Tool 명명 규칙**
- 동사 + 명사: `search_documents`, `create_document`
- 명확하고 간결하게
- 약어 최소화

**2. 입력 검증**
- JSON Schema 활용
- 타입 검증 필수
- 범위 제한 (limit, offset 등)

**3. 에러 처리**
- 모든 예외 캐치
- 의미 있는 에러 메시지
- 에러 코드 표준화

**4. 로깅**
- 실행 시작/종료 로그
- 에러 상세 로그 (스택 트레이스 포함)
- 성능 로그 (실행 시간)

**5. 테스트**
- 단위 테스트 필수
- 엣지 케이스 테스트
- 권한 테스트

***

## 7. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

***

## 8. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| **작성자** | | | |
| **검토자** | | | |
| **승인자** | | | |

***


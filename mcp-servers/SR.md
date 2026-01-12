# MCP Servers 전체 설계서

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/mcp-servers/`  
**목적**: MCP 서버 아키텍처 및 구현 가이드

***

## 목차

1. [개요](#1-개요)
2. [MCP 프로토콜 이해](#2-mcp-프로토콜-이해)
3. [전체 아키텍처](#3-전체-아키텍처)
4. [Core MCP 서버](#4-core-mcp-서버)
5. [Search MCP 서버](#5-search-mcp-서버)
6. [Analytics MCP 서버](#6-analytics-mcp-서버)
7. [공통 모듈](#7-공통-모듈)
8. [통신 프로토콜](#8-통신-프로토콜)
9. [보안 및 인증](#9-보안-및-인증)
10. [배포 및 운영](#10-배포-및-운영)

***

## 1. 개요

### 1.1 MCP (Model Context Protocol) 소개

```
┌─────────────────────────────────────────────────────────┐
│                   MCP 프로토콜 개념                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [LLM / AI Agent]                                       │
│         │                                                │
│         │ MCP Protocol (JSON-RPC)                       │
│         ▼                                                │
│  [MCP Host/Client]                                      │
│         │                                                │
│         ├───────┬───────┬───────┐                       │
│         │       │       │       │                        │
│         ▼       ▼       ▼       ▼                        │
│   [Core MCP] [Search] [Analytics] [Custom...]           │
│   Server     Server   Server      Servers               │
│         │       │       │       │                        │
│         └───────┴───────┴───────┘                       │
│                 │                                        │
│                 ▼                                        │
│         [Backend Services]                              │
│         - Database                                      │
│         - Elasticsearch                                 │
│         - Redis                                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 1.2 MCP 서버 역할

| MCP 서버 | 역할 | 주요 기능 |
|---------|------|----------|
| **Core** | 문서 CRUD | 문서 생성, 조회, 수정, 삭제, 메타데이터 관리 |
| **Search** | 검색 및 발견 | 전문 검색, 필터링, 추천, 유사 문서 |
| **Analytics** | 분석 및 통계 | 사용 통계, 트렌드 분석, 리포트 생성 |

### 1.3 디렉토리 구조

```
/app/poc/mcps/mcp-servers/
├── README.md                      # 전체 개요
├── requirements.txt               # 공통 의존성
├── pyproject.toml                # 프로젝트 설정
│
├── core/                         # Core MCP 서버
│   ├── __init__.py
│   ├── server.py                # 메인 서버
│   ├── config.py                # 설정
│   ├── tools/                   # MCP Tools
│   │   ├── __init__.py
│   │   ├── document_tools.py   # 문서 관련 tools
│   │   ├── metadata_tools.py   # 메타데이터 tools
│   │   └── validation_tools.py # 검증 tools
│   ├── resources/               # MCP Resources
│   │   ├── __init__.py
│   │   └── document_resource.py
│   ├── prompts/                 # MCP Prompts
│   │   ├── __init__.py
│   │   └── document_prompts.py
│   ├── models/                  # 데이터 모델
│   │   ├── __init__.py
│   │   ├── document.py
│   │   └── metadata.py
│   ├── services/                # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── document_service.py
│   │   └── validation_service.py
│   ├── tests/
│   │   ├── test_tools.py
│   │   └── test_server.py
│   └── README.md
│
├── search/                      # Search MCP 서버
│   ├── __init__.py
│   ├── server.py
│   ├── config.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search_tools.py
│   │   ├── filter_tools.py
│   │   └── recommendation_tools.py
│   ├── resources/
│   │   ├── __init__.py
│   │   └── search_resource.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── search_prompts.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── query.py
│   │   └── result.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── elasticsearch_service.py
│   │   ├── ranking_service.py
│   │   └── recommendation_service.py
│   ├── tests/
│   └── README.md
│
├── analytics/                   # Analytics MCP 서버
│   ├── __init__.py
│   ├── server.py
│   ├── config.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── stats_tools.py
│   │   ├── report_tools.py
│   │   └── visualization_tools.py
│   ├── resources/
│   │   ├── __init__.py
│   │   └── analytics_resource.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── analytics_prompts.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── metric.py
│   │   └── report.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── statistics_service.py
│   │   └── reporting_service.py
│   ├── tests/
│   └── README.md
│
├── common/                      # 공통 모듈
│   ├── __init__.py
│   ├── base_server.py          # 기본 서버 클래스
│   ├── protocol.py             # MCP 프로토콜 구현
│   ├── errors.py               # 에러 정의
│   ├── utils.py                # 유틸리티
│   ├── logging.py              # 로깅 설정
│   ├── database.py             # DB 연결
│   └── cache.py                # 캐시 관리
│
├── scripts/                     # 유틸리티 스크립트
│   ├── start_all.sh            # 모든 서버 시작
│   ├── stop_all.sh             # 모든 서버 중지
│   └── test_all.sh             # 전체 테스트
│
└── docs/                        # 추가 문서
    ├── mcp_protocol.md
    ├── tool_development.md
    └── deployment.md
```

***

## 2. MCP 프로토콜 이해

### 2.1 MCP 핵심 개념

```python
# MCP의 3가지 주요 구성 요소

# 1. Tools - 실행 가능한 함수
"""
Tool은 LLM이 호출할 수 있는 함수입니다.
예: search_documents, create_document, get_statistics
"""

# 2. Resources - 읽기 가능한 데이터
"""
Resource는 LLM이 컨텍스트로 사용할 수 있는 데이터입니다.
예: document://123, template://standard
"""

# 3. Prompts - 사전 정의된 프롬프트 템플릿
"""
Prompt는 재사용 가능한 프롬프트 템플릿입니다.
예: summarize_document, generate_report
"""
```

### 2.2 JSON-RPC 2.0 프로토콜

```json
// Request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_documents",
    "arguments": {
      "query": "보안 정책",
      "limit": 10
    }
  }
}

// Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "검색 결과: 5개 문서 발견"
      },
      {
        "type": "resource",
        "resource": "document://DOC-001"
      }
    ]
  }
}

// Error Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": {
      "details": "Missing required parameter: query"
    }
  }
}
```

### 2.3 MCP 메시지 타입

```python
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

class MessageType(str, Enum):
    """MCP 메시지 타입"""
    # 초기화
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    
    # Tool 관련
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    
    # Resource 관련
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    RESOURCES_UNSUBSCRIBE = "resources/unsubscribe"
    
    # Prompt 관련
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    
    # Completion
    COMPLETION_COMPLETE = "completion/complete"
    
    # Logging
    LOGGING_SET_LEVEL = "logging/setLevel"

class ContentType(str, Enum):
    """컨텐츠 타입"""
    TEXT = "text"
    IMAGE = "image"
    RESOURCE = "resource"
    EMBEDDED_RESOURCE = "embeddedResource"

class Content(BaseModel):
    """MCP 컨텐츠"""
    type: ContentType
    text: Optional[str] = None
    data: Optional[str] = None  # base64 encoded
    uri: Optional[str] = None
    mimeType: Optional[str] = None

class Tool(BaseModel):
    """MCP Tool 정의"""
    name: str
    description: str
    inputSchema: Dict[str, Any]  # JSON Schema

class Resource(BaseModel):
    """MCP Resource 정의"""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

class Prompt(BaseModel):
    """MCP Prompt 정의"""
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = None
```

***

## 3. 전체 아키텍처

### 3.1 MCP 서버 간 통신

```
┌─────────────────────────────────────────────────────────┐
│              MCP 서버 통신 아키텍처                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [MCP Host/Client]                                      │
│         │                                                │
│         │ stdio / HTTP / WebSocket                      │
│         │                                                │
│  ┌──────┴──────────────────────────────────┐           │
│  │                                           │           │
│  ▼                                           ▼           │
│  [Core MCP Server]              [Search MCP Server]     │
│  - Port: 5001                   - Port: 5002            │
│  - Protocol: stdio/HTTP         - Protocol: stdio/HTTP  │
│  │                               │                       │
│  ├─ Tools:                      ├─ Tools:               │
│  │  • create_document            │  • search_documents   │
│  │  • get_document               │  • filter_documents   │
│  │  • update_document            │  • recommend          │
│  │  • delete_document            │                       │
│  │                               │                       │
│  ├─ Resources:                  ├─ Resources:           │
│  │  • document://id              │  • search://query     │
│  │  • template://name            │                       │
│  │                               │                       │
│  └─ Prompts:                    └─ Prompts:             │
│     • summarize                     • advanced_search    │
│                                                          │
│  [Analytics MCP Server]                                 │
│  - Port: 5003                                           │
│  - Protocol: stdio/HTTP                                 │
│  │                                                       │
│  ├─ Tools:                                              │
│  │  • get_statistics                                    │
│  │  • generate_report                                   │
│  │  • analyze_trends                                    │
│  │                                                       │
│  ├─ Resources:                                          │
│  │  • analytics://metric                                │
│  │                                                       │
│  └─ Prompts:                                            │
│     • monthly_report                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 3.2 데이터 흐름

```python
# 전체 데이터 흐름 예시

"""
1. LLM/Agent가 MCP Host에 요청
   "최근 작성된 보안 관련 문서를 찾아줘"

2. MCP Host가 적절한 MCP 서버 선택
   → Search MCP 서버로 라우팅

3. Search MCP 서버가 Tool 실행
   search_documents(query="보안", date_range="recent")
   
4. Search 서버가 Elasticsearch 조회
   
5. 결과를 MCP 프로토콜로 반환
   Content: [
     {type: "text", text: "3개 문서 발견"},
     {type: "resource", uri: "document://DOC-001"}
   ]

6. MCP Host가 추가 정보 필요 시 Core MCP 서버 호출
   get_document(id="DOC-001")

7. 최종 결과를 LLM에 반환
"""
```

***

## 4. Core MCP 서버

### 4.1 Core 서버 구조

```python
# /app/poc/mcps/mcp-servers/core/server.py
"""Core MCP 서버 - 문서 CRUD"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    Resource,
    Prompt,
    GetPromptResult,
    PromptMessage,
)

from .config import settings
from .tools import (
    create_document_tool,
    get_document_tool,
    update_document_tool,
    delete_document_tool,
    list_documents_tool,
    validate_document_tool,
)
from .resources import document_resource, template_resource
from .prompts import summarize_prompt, format_prompt

logger = logging.getLogger(__name__)

class CoreMCPServer:
    """Core MCP 서버 메인 클래스"""
    
    def __init__(self):
        self.server = Server("core-mcp-server")
        self.setup_handlers()
    
    def setup_handlers(self):
        """핸들러 설정"""
        
        # Tools 등록
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """사용 가능한 도구 목록"""
            return [
                Tool(
                    name="create_document",
                    description="새로운 문서를 생성합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "문서 제목"
                            },
                            "content": {
                                "type": "string",
                                "description": "문서 내용"
                            },
                            "classification": {
                                "type": "string",
                                "enum": ["public", "internal", "confidential", "secret"],
                                "description": "보안 등급"
                            },
                            "category": {
                                "type": "string",
                                "description": "문서 카테고리"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "태그 목록"
                            },
                            "author_id": {
                                "type": "string",
                                "description": "작성자 ID"
                            }
                        },
                        "required": ["title", "content", "classification", "author_id"]
                    }
                ),
                Tool(
                    name="get_document",
                    description="문서 ID로 문서를 조회합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "doc_id": {
                                "type": "string",
                                "description": "문서 ID"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "조회하는 사용자 ID"
                            }
                        },
                        "required": ["doc_id", "user_id"]
                    }
                ),
                Tool(
                    name="update_document",
                    description="기존 문서를 수정합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "doc_id": {
                                "type": "string",
                                "description": "문서 ID"
                            },
                            "title": {
                                "type": "string",
                                "description": "새 제목 (선택)"
                            },
                            "content": {
                                "type": "string",
                                "description": "새 내용 (선택)"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "수정하는 사용자 ID"
                            }
                        },
                        "required": ["doc_id", "user_id"]
                    }
                ),
                Tool(
                    name="delete_document",
                    description="문서를 삭제합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "doc_id": {
                                "type": "string",
                                "description": "문서 ID"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "삭제하는 사용자 ID"
                            }
                        },
                        "required": ["doc_id", "user_id"]
                    }
                ),
                Tool(
                    name="list_documents",
                    description="문서 목록을 조회합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "조회하는 사용자 ID"
                            },
                            "category": {
                                "type": "string",
                                "description": "카테고리 필터 (선택)"
                            },
                            "classification": {
                                "type": "string",
                                "description": "보안 등급 필터 (선택)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "최대 결과 수",
                                "default": 20
                            },
                            "offset": {
                                "type": "integer",
                                "description": "오프셋",
                                "default": 0
                            }
                        },
                        "required": ["user_id"]
                    }
                ),
                Tool(
                    name="validate_document",
                    description="문서 유효성을 검증합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "doc_id": {
                                "type": "string",
                                "description": "문서 ID"
                            }
                        },
                        "required": ["doc_id"]
                    }
                )
            ]
        
        # Tool 실행
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """도구 실행"""
            try:
                if name == "create_document":
                    result = await create_document_tool(**arguments)
                elif name == "get_document":
                    result = await get_document_tool(**arguments)
                elif name == "update_document":
                    result = await update_document_tool(**arguments)
                elif name == "delete_document":
                    result = await delete_document_tool(**arguments)
                elif name == "list_documents":
                    result = await list_documents_tool(**arguments)
                elif name == "validate_document":
                    result = await validate_document_tool(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=str(result))]
            
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Resources 등록
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """사용 가능한 리소스 목록"""
            return [
                Resource(
                    uri="document://{doc_id}",
                    name="Document Resource",
                    description="문서 내용을 가져옵니다",
                    mimeType="application/json"
                ),
                Resource(
                    uri="template://{template_name}",
                    name="Template Resource",
                    description="문서 템플릿을 가져옵니다",
                    mimeType="text/plain"
                )
            ]
        
        # Resource 읽기
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """리소스 읽기"""
            try:
                if uri.startswith("document://"):
                    doc_id = uri.replace("document://", "")
                    return await document_resource(doc_id)
                elif uri.startswith("template://"):
                    template_name = uri.replace("template://", "")
                    return await template_resource(template_name)
                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
            except Exception as e:
                logger.error(f"Resource read error: {e}")
                raise
        
        # Prompts 등록
        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """사용 가능한 프롬프트 목록"""
            return [
                Prompt(
                    name="summarize_document",
                    description="문서를 요약합니다",
                    arguments=[
                        {
                            "name": "doc_id",
                            "description": "문서 ID",
                            "required": True
                        },
                        {
                            "name": "length",
                            "description": "요약 길이 (short, medium, long)",
                            "required": False
                        }
                    ]
                ),
                Prompt(
                    name="format_document",
                    description="문서를 특정 형식으로 포맷팅합니다",
                    arguments=[
                        {
                            "name": "doc_id",
                            "description": "문서 ID",
                            "required": True
                        },
                        {
                            "name": "format",
                            "description": "출력 형식 (markdown, html, plain)",
                            "required": True
                        }
                    ]
                )
            ]
        
        # Prompt 가져오기
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
            """프롬프트 가져오기"""
            try:
                if name == "summarize_document":
                    messages = await summarize_prompt(**arguments)
                elif name == "format_document":
                    messages = await format_prompt(**arguments)
                else:
                    raise ValueError(f"Unknown prompt: {name}")
                
                return GetPromptResult(
                    description=f"Prompt: {name}",
                    messages=messages
                )
            except Exception as e:
                logger.error(f"Prompt error: {e}")
                raise
    
    async def run(self):
        """서버 실행"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

# 서버 실행
async def main():
    server = CoreMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.2 Core Tools 구현

```python
# /app/poc/mcps/mcp-servers/core/tools/document_tools.py
"""문서 관련 Tools 구현"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..services.document_service import DocumentService
from ..services.validation_service import ValidationService
from ..models.document import Document, DocumentCreate, DocumentUpdate

logger = logging.getLogger(__name__)

# 서비스 초기화
doc_service = DocumentService()
validation_service = ValidationService()

async def create_document_tool(
    title: str,
    content: str,
    classification: str,
    author_id: str,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    문서 생성 Tool
    
    Args:
        title: 문서 제목
        content: 문서 내용
        classification: 보안 등급
        author_id: 작성자 ID
        category: 카테고리 (선택)
        tags: 태그 목록 (선택)
    
    Returns:
        생성된 문서 정보
    """
    try:
        # 입력 검증
        if not title or not content:
            raise ValueError("제목과 내용은 필수입니다")
        
        if classification not in ["public", "internal", "confidential", "secret"]:
            raise ValueError("잘못된 보안 등급입니다")
        
        # 문서 생성
        doc_data = DocumentCreate(
            title=title,
            content=content,
            classification=classification,
            author_id=author_id,
            category=category,
            tags=tags or []
        )
        
        document = await doc_service.create_document(doc_data)
        
        logger.info(f"Document created: {document.id}")
        
        return {
            "success": True,
            "doc_id": document.id,
            "message": f"문서가 생성되었습니다: {document.id}",
            "document": document.dict()
        }
    
    except Exception as e:
        logger.error(f"Document creation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def get_document_tool(
    doc_id: str,
    user_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    문서 조회 Tool
    
    Args:
        doc_id: 문서 ID
        user_id: 조회하는 사용자 ID
    
    Returns:
        문서 정보
    """
    try:
        # 권한 확인
        has_permission = await doc_service.check_read_permission(doc_id, user_id)
        if not has_permission:
            raise PermissionError("문서 조회 권한이 없습니다")
        
        # 문서 조회
        document = await doc_service.get_document(doc_id)
        
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {doc_id}")
        
        # 조회 로그 기록
        await doc_service.log_access(doc_id, user_id, "read")
        
        return {
            "success": True,
            "document": document.dict()
        }
    
    except Exception as e:
        logger.error(f"Document retrieval failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def update_document_tool(
    doc_id: str,
    user_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    문서 수정 Tool
    
    Args:
        doc_id: 문서 ID
        user_id: 수정하는 사용자 ID
        title: 새 제목 (선택)
        content: 새 내용 (선택)
    
    Returns:
        수정된 문서 정보
    """
    try:
        # 권한 확인
        has_permission = await doc_service.check_write_permission(doc_id, user_id)
        if not has_permission:
            raise PermissionError("문서 수정 권한이 없습니다")
        
        # 문서 수정
        update_data = DocumentUpdate(
            title=title,
            content=content
        )
        
        document = await doc_service.update_document(doc_id, update_data, user_id)
        
        logger.info(f"Document updated: {doc_id} by {user_id}")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": "문서가 수정되었습니다",
            "document": document.dict()
        }
    
    except Exception as e:
        logger.error(f"Document update failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def delete_document_tool(
    doc_id: str,
    user_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    문서 삭제 Tool
    
    Args:
        doc_id: 문서 ID
        user_id: 삭제하는 사용자 ID
    
    Returns:
        삭제 결과
    """
    try:
        # 권한 확인
        has_permission = await doc_service.check_delete_permission(doc_id, user_id)
        if not has_permission:
            raise PermissionError("문서 삭제 권한이 없습니다")
        
        # 문서 삭제 (소프트 삭제)
        await doc_service.soft_delete_document(doc_id, user_id)
        
        logger.info(f"Document deleted: {doc_id} by {user_id}")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": "문서가 삭제되었습니다"
        }
    
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def list_documents_tool(
    user_id: str,
    category: Optional[str] = None,
    classification: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    **kwargs
) -> Dict[str, Any]:
    """
    문서 목록 조회 Tool
    
    Args:
        user_id: 조회하는 사용자 ID
        category: 카테고리 필터
        classification: 보안 등급 필터
        limit: 최대 결과 수
        offset: 오프셋
    
    Returns:
        문서 목록
    """
    try:
        # 문서 목록 조회
        documents, total = await doc_service.list_documents(
            user_id=user_id,
            category=category,
            classification=classification,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "total": total,
            "count": len(documents),
            "documents": [doc.dict() for doc in documents]
        }
    
    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def validate_document_tool(
    doc_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    문서 유효성 검증 Tool
    
    Args:
        doc_id: 문서 ID
    
    Returns:
        검증 결과
    """
    try:
        # 문서 조회
        document = await doc_service.get_document(doc_id)
        
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {doc_id}")
        
        # 유효성 검증
        is_valid, errors = await validation_service.validate_document(document)
        
        return {
            "success": True,
            "is_valid": is_valid,
            "errors": errors,
            "doc_id": doc_id
        }
    
    except Exception as e:
        logger.error(f"Document validation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```





### 4.3 Core Resources 구현

```python
# /app/poc/mcps/mcp-servers/core/resources/document_resource.py
"""Document Resource 구현"""

import logging
import json
from typing import Optional

from ..services.document_service import DocumentService

logger = logging.getLogger(__name__)
doc_service = DocumentService()

async def document_resource(doc_id: str) -> str:
    """
    문서 리소스를 가져옵니다
    
    Args:
        doc_id: 문서 ID
    
    Returns:
        JSON 형식의 문서 데이터
    """
    try:
        document = await doc_service.get_document(doc_id)
        
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {doc_id}")
        
        # 문서를 JSON으로 변환
        doc_data = {
            "id": document.id,
            "title": document.title,
            "content": document.content,
            "classification": document.classification,
            "category": document.category,
            "tags": document.tags,
            "author_id": document.author_id,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            "version": document.version
        }
        
        return json.dumps(doc_data, ensure_ascii=False, indent=2)
    
    except Exception as e:
        logger.error(f"Document resource error: {e}")
        raise

async def template_resource(template_name: str) -> str:
    """
    템플릿 리소스를 가져옵니다
    
    Args:
        template_name: 템플릿 이름
    
    Returns:
        템플릿 텍스트
    """
    templates = {
        "standard": """
# {title}

## 개요
{overview}

## 상세 내용
{content}

## 참고 사항
{notes}

---
작성자: {author}
작성일: {date}
""",
        "meeting": """
# 회의록: {title}

**일시**: {date}
**참석자**: {attendees}
**장소**: {location}

## 안건
{agenda}

## 논의 내용
{discussion}

## 결정 사항
{decisions}

## 후속 조치
{action_items}
""",
        "report": """
# {title}

**보고 기간**: {period}
**보고자**: {author}

## 요약
{summary}

## 세부 내용
{details}

## 결론 및 건의사항
{conclusion}
"""
    }
    
    template = templates.get(template_name)
    
    if not template:
        available = ", ".join(templates.keys())
        raise ValueError(f"알 수 없는 템플릿입니다: {template_name}. 사용 가능: {available}")
    
    return template
```

### 4.4 Core Prompts 구현

```python
# /app/poc/mcps/mcp-servers/core/prompts/document_prompts.py
"""Document Prompt 구현"""

import logging
from typing import Dict, List
from mcp.types import PromptMessage, TextContent

from ..services.document_service import DocumentService

logger = logging.getLogger(__name__)
doc_service = DocumentService()

async def summarize_prompt(
    doc_id: str,
    length: str = "medium"
) -> List[PromptMessage]:
    """
    문서 요약 프롬프트
    
    Args:
        doc_id: 문서 ID
        length: 요약 길이 (short, medium, long)
    
    Returns:
        프롬프트 메시지 리스트
    """
    try:
        # 문서 조회
        document = await doc_service.get_document(doc_id)
        
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {doc_id}")
        
        # 길이별 지침
        length_instructions = {
            "short": "3-5 문장으로 핵심 내용만 간단히",
            "medium": "1-2 단락으로 주요 내용을",
            "long": "3-4 단락으로 상세하게"
        }
        
        instruction = length_instructions.get(length, length_instructions["medium"])
        
        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"""다음 문서를 {instruction} 요약해주세요.

문서 제목: {document.title}
문서 내용:
---
{document.content}
---

요약 시 다음 사항을 고려해주세요:
- 문서의 핵심 주제와 목적
- 주요 내용과 결론
- 중요한 세부 사항

요약:"""
                )
            )
        ]
        
        return messages
    
    except Exception as e:
        logger.error(f"Summarize prompt error: {e}")
        raise

async def format_prompt(
    doc_id: str,
    format: str
) -> List[PromptMessage]:
    """
    문서 포맷팅 프롬프트
    
    Args:
        doc_id: 문서 ID
        format: 출력 형식 (markdown, html, plain)
    
    Returns:
        프롬프트 메시지 리스트
    """
    try:
        # 문서 조회
        document = await doc_service.get_document(doc_id)
        
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {doc_id}")
        
        # 포맷별 지침
        format_instructions = {
            "markdown": "Markdown 형식으로 변환하되, 제목은 #, ##로, 목록은 -, *로, 코드는 ```로 표시",
            "html": "HTML 형식으로 변환하되, 시맨틱 태그(<article>, <section>, <h1> 등) 사용",
            "plain": "모든 포맷팅을 제거하고 순수 텍스트로 변환"
        }
        
        instruction = format_instructions.get(format, format_instructions["markdown"])
        
        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"""다음 문서를 {format} 형식으로 변환해주세요.

지침: {instruction}

문서 제목: {document.title}
문서 내용:
---
{document.content}
---

변환 결과:"""
                )
            )
        ]
        
        return messages
    
    except Exception as e:
        logger.error(f"Format prompt error: {e}")
        raise
```

***

## 5. Search MCP 서버

### 5.1 Search 서버 구조

```python
# /app/poc/mcps/mcp-servers/search/server.py
"""Search MCP 서버 - 검색 및 발견"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource, Prompt, GetPromptResult

from .config import settings
from .tools import (
    search_documents_tool,
    filter_documents_tool,
    recommend_documents_tool,
    find_similar_tool,
    advanced_search_tool,
)
from .resources import search_result_resource
from .prompts import search_prompt

logger = logging.getLogger(__name__)

class SearchMCPServer:
    """Search MCP 서버 메인 클래스"""
    
    def __init__(self):
        self.server = Server("search-mcp-server")
        self.setup_handlers()
    
    def setup_handlers(self):
        """핸들러 설정"""
        
        # Tools 등록
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """사용 가능한 도구 목록"""
            return [
                Tool(
                    name="search_documents",
                    description="문서를 전문 검색합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색 쿼리"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "검색하는 사용자 ID"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "최대 결과 수",
                                "default": 10
                            },
                            "offset": {
                                "type": "integer",
                                "description": "오프셋",
                                "default": 0
                            }
                        },
                        "required": ["query", "user_id"]
                    }
                ),
                Tool(
                    name="filter_documents",
                    description="다양한 조건으로 문서를 필터링합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "사용자 ID"
                            },
                            "category": {
                                "type": "string",
                                "description": "카테고리"
                            },
                            "classification": {
                                "type": "string",
                                "description": "보안 등급"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "태그 목록"
                            },
                            "date_from": {
                                "type": "string",
                                "description": "시작 날짜 (YYYY-MM-DD)"
                            },
                            "date_to": {
                                "type": "string",
                                "description": "종료 날짜 (YYYY-MM-DD)"
                            },
                            "author_id": {
                                "type": "string",
                                "description": "작성자 ID"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 20
                            }
                        },
                        "required": ["user_id"]
                    }
                ),
                Tool(
                    name="recommend_documents",
                    description="사용자 기반 문서 추천",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "사용자 ID"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "추천 수",
                                "default": 5
                            }
                        },
                        "required": ["user_id"]
                    }
                ),
                Tool(
                    name="find_similar",
                    description="특정 문서와 유사한 문서를 찾습니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "doc_id": {
                                "type": "string",
                                "description": "기준 문서 ID"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "사용자 ID"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "결과 수",
                                "default": 5
                            }
                        },
                        "required": ["doc_id", "user_id"]
                    }
                ),
                Tool(
                    name="advanced_search",
                    description="고급 검색 (Bool 쿼리, 범위 검색 등)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "must": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "반드시 포함될 단어"
                            },
                            "should": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "포함되면 좋은 단어"
                            },
                            "must_not": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "제외할 단어"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "사용자 ID"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 10
                            }
                        },
                        "required": ["user_id"]
                    }
                )
            ]
        
        # Tool 실행
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """도구 실행"""
            try:
                if name == "search_documents":
                    result = await search_documents_tool(**arguments)
                elif name == "filter_documents":
                    result = await filter_documents_tool(**arguments)
                elif name == "recommend_documents":
                    result = await recommend_documents_tool(**arguments)
                elif name == "find_similar":
                    result = await find_similar_tool(**arguments)
                elif name == "advanced_search":
                    result = await advanced_search_tool(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=str(result))]
            
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Resources 등록
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """사용 가능한 리소스 목록"""
            return [
                Resource(
                    uri="search://{query_id}",
                    name="Search Result Resource",
                    description="저장된 검색 결과를 가져옵니다",
                    mimeType="application/json"
                )
            ]
        
        # Resource 읽기
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """리소스 읽기"""
            try:
                if uri.startswith("search://"):
                    query_id = uri.replace("search://", "")
                    return await search_result_resource(query_id)
                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
            except Exception as e:
                logger.error(f"Resource read error: {e}")
                raise
        
        # Prompts 등록
        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """사용 가능한 프롬프트 목록"""
            return [
                Prompt(
                    name="advanced_search",
                    description="고급 검색 쿼리를 구성합니다",
                    arguments=[
                        {
                            "name": "intent",
                            "description": "검색 의도 설명",
                            "required": True
                        }
                    ]
                )
            ]
        
        # Prompt 가져오기
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
            """프롬프트 가져오기"""
            try:
                if name == "advanced_search":
                    messages = await search_prompt(**arguments)
                else:
                    raise ValueError(f"Unknown prompt: {name}")
                
                return GetPromptResult(
                    description=f"Prompt: {name}",
                    messages=messages
                )
            except Exception as e:
                logger.error(f"Prompt error: {e}")
                raise
    
    async def run(self):
        """서버 실행"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

# 서버 실행
async def main():
    server = SearchMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### 5.2 Search Tools 구현

```python
# /app/poc/mcps/mcp-servers/search/tools/search_tools.py
"""검색 관련 Tools 구현"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from ..services.elasticsearch_service import ElasticsearchService
from ..services.ranking_service import RankingService
from ..services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

# 서비스 초기화
es_service = ElasticsearchService()
ranking_service = RankingService()
recommendation_service = RecommendationService()

async def search_documents_tool(
    query: str,
    user_id: str,
    limit: int = 10,
    offset: int = 0,
    **kwargs
) -> Dict[str, Any]:
    """
    문서 전문 검색 Tool
    
    Args:
        query: 검색 쿼리
        user_id: 사용자 ID
        limit: 최대 결과 수
        offset: 오프셋
    
    Returns:
        검색 결과
    """
    try:
        # Elasticsearch 검색
        results = await es_service.search(
            query=query,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # 랭킹 적용
        ranked_results = await ranking_service.rank_results(
            results=results,
            user_id=user_id,
            query=query
        )
        
        # 검색 로그 기록
        await es_service.log_search(
            user_id=user_id,
            query=query,
            result_count=len(ranked_results)
        )
        
        return {
            "success": True,
            "query": query,
            "total": len(ranked_results),
            "results": [
                {
                    "doc_id": r["id"],
                    "title": r["title"],
                    "snippet": r["snippet"],
                    "score": r["score"],
                    "category": r.get("category"),
                    "created_at": r.get("created_at")
                }
                for r in ranked_results
            ]
        }
    
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def filter_documents_tool(
    user_id: str,
    category: Optional[str] = None,
    classification: Optional[str] = None,
    tags: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    author_id: Optional[str] = None,
    limit: int = 20,
    **kwargs
) -> Dict[str, Any]:
    """
    문서 필터링 Tool
    
    Args:
        user_id: 사용자 ID
        category: 카테고리
        classification: 보안 등급
        tags: 태그 목록
        date_from: 시작 날짜
        date_to: 종료 날짜
        author_id: 작성자 ID
        limit: 최대 결과 수
    
    Returns:
        필터링된 문서 목록
    """
    try:
        # 필터 구성
        filters = {}
        
        if category:
            filters["category"] = category
        
        if classification:
            filters["classification"] = classification
        
        if tags:
            filters["tags"] = tags
        
        if date_from or date_to:
            filters["date_range"] = {
                "from": date_from,
                "to": date_to
            }
        
        if author_id:
            filters["author_id"] = author_id
        
        # Elasticsearch 필터 검색
        results = await es_service.filter_search(
            filters=filters,
            user_id=user_id,
            limit=limit
        )
        
        return {
            "success": True,
            "filters": filters,
            "total": len(results),
            "documents": results
        }
    
    except Exception as e:
        logger.error(f"Filter failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def recommend_documents_tool(
    user_id: str,
    limit: int = 5,
    **kwargs
) -> Dict[str, Any]:
    """
    문서 추천 Tool
    
    Args:
        user_id: 사용자 ID
        limit: 추천 수
    
    Returns:
        추천 문서 목록
    """
    try:
        # 사용자 기반 추천
        recommendations = await recommendation_service.recommend_for_user(
            user_id=user_id,
            limit=limit
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "recommendations": [
                {
                    "doc_id": r["doc_id"],
                    "title": r["title"],
                    "reason": r["reason"],
                    "score": r["score"]
                }
                for r in recommendations
            ]
        }
    
    except Exception as e:
        logger.error(f"Recommendation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def find_similar_tool(
    doc_id: str,
    user_id: str,
    limit: int = 5,
    **kwargs
) -> Dict[str, Any]:
    """
    유사 문서 찾기 Tool
    
    Args:
        doc_id: 기준 문서 ID
        user_id: 사용자 ID
        limit: 결과 수
    
    Returns:
        유사 문서 목록
    """
    try:
        # Elasticsearch More Like This 쿼리
        similar_docs = await es_service.find_similar(
            doc_id=doc_id,
            user_id=user_id,
            limit=limit
        )
        
        return {
            "success": True,
            "source_doc_id": doc_id,
            "similar_documents": [
                {
                    "doc_id": d["id"],
                    "title": d["title"],
                    "similarity_score": d["score"]
                }
                for d in similar_docs
            ]
        }
    
    except Exception as e:
        logger.error(f"Similar search failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def advanced_search_tool(
    user_id: str,
    must: Optional[List[str]] = None,
    should: Optional[List[str]] = None,
    must_not: Optional[List[str]] = None,
    limit: int = 10,
    **kwargs
) -> Dict[str, Any]:
    """
    고급 검색 Tool (Bool Query)
    
    Args:
        user_id: 사용자 ID
        must: 반드시 포함될 단어
        should: 포함되면 좋은 단어
        must_not: 제외할 단어
        limit: 결과 수
    
    Returns:
        검색 결과
    """
    try:
        # Bool 쿼리 구성
        bool_query = {
            "must": must or [],
            "should": should or [],
            "must_not": must_not or []
        }
        
        # Elasticsearch Bool 검색
        results = await es_service.bool_search(
            bool_query=bool_query,
            user_id=user_id,
            limit=limit
        )
        
        return {
            "success": True,
            "query": bool_query,
            "total": len(results),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Advanced search failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

***

## 6. Analytics MCP 서버

### 6.1 Analytics 서버 구조

```python
# /app/poc/mcps/mcp-servers/analytics/server.py
"""Analytics MCP 서버 - 분석 및 통계"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource, Prompt, GetPromptResult

from .config import settings
from .tools import (
    get_statistics_tool,
    generate_report_tool,
    analyze_trends_tool,
    user_activity_tool,
    document_metrics_tool,
)
from .resources import analytics_resource
from .prompts import report_prompt

logger = logging.getLogger(__name__)

class AnalyticsMCPServer:
    """Analytics MCP 서버 메인 클래스"""
    
    def __init__(self):
        self.server = Server("analytics-mcp-server")
        self.setup_handlers()
    
    def setup_handlers(self):
        """핸들러 설정"""
        
        # Tools 등록
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """사용 가능한 도구 목록"""
            return [
                Tool(
                    name="get_statistics",
                    description="시스템 통계를 조회합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "metric_type": {
                                "type": "string",
                                "enum": ["documents", "users", "searches", "all"],
                                "description": "통계 유형"
                            },
                            "period": {
                                "type": "string",
                                "enum": ["today", "week", "month", "year"],
                                "description": "기간",
                                "default": "today"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "관리자 ID"
                            }
                        },
                        "required": ["metric_type", "user_id"]
                    }
                ),
                Tool(
                    name="generate_report",
                    description="분석 리포트를 생성합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "report_type": {
                                "type": "string",
                                "enum": ["usage", "security", "performance", "comprehensive"],
                                "description": "리포트 유형"
                            },
                            "period": {
                                "type": "string",
                                "description": "기간 (예: 2024-01-01 to 2024-01-31)"
                            },
                            "format": {
                                "type": "string",
                                "enum": ["json", "markdown", "html"],
                                "default": "json"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "관리자 ID"
                            }
                        },
                        "required": ["report_type", "user_id"]
                    }
                ),
                Tool(
                    name="analyze_trends",
                    description="트렌드를 분석합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "metric": {
                                "type": "string",
                                "description": "분석할 메트릭 (예: document_creation, search_volume)"
                            },
                            "period": {
                                "type": "string",
                                "description": "분석 기간",
                                "default": "month"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "관리자 ID"
                            }
                        },
                        "required": ["metric", "user_id"]
                    }
                ),
                Tool(
                    name="user_activity",
                    description="사용자 활동을 분석합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_user_id": {
                                "type": "string",
                                "description": "분석 대상 사용자 ID (선택)"
                            },
                            "period": {
                                "type": "string",
                                "default": "week"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "관리자 ID"
                            }
                        },
                        "required": ["user_id"]
                    }
                ),
                Tool(
                    name="document_metrics",
                    description="문서 메트릭을 조회합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "doc_id": {
                                "type": "string",
                                "description": "문서 ID (선택)"
                            },
                            "metric_type": {
                                "type": "string",
                                "enum": ["views", "edits", "shares", "all"],
                                "default": "all"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "관리자 ID"
                            }
                        },
                        "required": ["user_id"]
                    }
                )
            ]
        
        # Tool 실행
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """도구 실행"""
            try:
                if name == "get_statistics":
                    result = await get_statistics_tool(**arguments)
                elif name == "generate_report":
                    result = await generate_report_tool(**arguments)
                elif name == "analyze_trends":
                    result = await analyze_trends_tool(**arguments)
                elif name == "user_activity":
                    result = await user_activity_tool(**arguments)
                elif name == "document_metrics":
                    result = await document_metrics_tool(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=str(result))]
            
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Resources 등록
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """사용 가능한 리소스 목록"""
            return [
                Resource(
                    uri="analytics://{metric_name}",
                    name="Analytics Resource",
                    description="분석 메트릭 데이터를 가져옵니다",
                    mimeType="application/json"
                )
            ]
        
        # Resource 읽기
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """리소스 읽기"""
            try:
                if uri.startswith("analytics://"):
                    metric_name = uri.replace("analytics://", "")
                    return await analytics_resource(metric_name)
                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
            except Exception as e:
                logger.error(f"Resource read error: {e}")
                raise
        
        # Prompts 등록
        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """사용 가능한 프롬프트 목록"""
            return [
                Prompt(
                    name="monthly_report",
                    description="월간 리포트를 생성합니다",
                    arguments=[
                        {
                            "name": "month",
                            "description": "월 (YYYY-MM)",
                            "required": True
                        }
                    ]
                )
            ]
        
        # Prompt 가져오기
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
            """프롬프트 가져오기"""
            try:
                if name == "monthly_report":
                    messages = await report_prompt(**arguments)
                else:
                    raise ValueError(f"Unknown prompt: {name}")
                
                return GetPromptResult(
                    description=f"Prompt: {name}",
                    messages=messages
                )
            except Exception as e:
                logger.error(f"Prompt error: {e}")
                raise
    
    async def run(self):
        """서버 실행"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

# 서버 실행
async def main():
    server = AnalyticsMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### 6.2 Analytics Tools 구현

```python
# /app/poc/mcps/mcp-servers/analytics/tools/stats_tools.py
"""통계 관련 Tools 구현"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from ..services.statistics_service import StatisticsService
from ..services.reporting_service import ReportingService

logger = logging.getLogger(__name__)

# 서비스 초기화
stats_service = StatisticsService()
reporting_service = ReportingService()

async def get_statistics_tool(
    metric_type: str,
    user_id: str,
    period: str = "today",
    **kwargs
) -> Dict[str, Any]:
    """
    시스템 통계 조회 Tool
    
    Args:
        metric_type: 통계 유형 (documents, users, searches, all)
        user_id: 관리자 ID
        period: 기간 (today, week, month, year)
    
    Returns:
        통계 데이터
    """
    try:
        # 권한 확인 (관리자만)
        is_admin = await stats_service.check_admin_permission(user_id)
        if not is_admin:
            raise PermissionError("관리자 권한이 필요합니다")
        
        # 기간 계산
        end_date = datetime.now()
        period_map = {
            "today": timedelta(days=1),
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "year": timedelta(days=365)
        }
        start_date = end_date - period_map.get(period, timedelta(days=1))
        
        # 통계 조회
        if metric_type == "documents":
            stats = await stats_service.get_document_stats(start_date, end_date)
        elif metric_type == "users":
            stats = await stats_service.get_user_stats(start_date, end_date)
        elif metric_type == "searches":
            stats = await stats_service.get_search_stats(start_date, end_date)
        elif metric_type == "all":
            stats = await stats_service.get_all_stats(start_date, end_date)
        else:
            raise ValueError(f"Unknown metric type: {metric_type}")
        
        return {
            "success": True,
            "metric_type": metric_type,
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "statistics": stats
        }
    
    except Exception as e:
        logger.error(f"Statistics retrieval failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_report_tool(
    report_type: str,
    user_id: str,
    period: Optional[str] = None,
    format: str = "json",
    **kwargs
) -> Dict[str, Any]:
    """
    리포트 생성 Tool
    
    Args:
        report_type: 리포트 유형
        user_id: 관리자 ID
        period: 기간
        format: 출력 형식
    
    Returns:
        생성된 리포트
    """
    try:
        # 권한 확인
        is_admin = await stats_service.check_admin_permission(user_id)
        if not is_admin:
            raise PermissionError("관리자 권한이 필요합니다")
        
        # 리포트 생성
        report = await reporting_service.generate_report(
            report_type=report_type,
            period=period,
            format=format
        )
        
        return {
            "success": True,
            "report_type": report_type,
            "format": format,
            "report": report
        }
    
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def analyze_trends_tool(
    metric: str,
    user_id: str,
    period: str = "month",
    **kwargs
) -> Dict[str, Any]:
    """
    트렌드 분석 Tool
    
    Args:
        metric: 분석할 메트릭
        user_id: 관리자 ID
        period: 분석 기간
    
    Returns:
        트렌드 분석 결과
    """
    try:
        # 권한 확인
        is_admin = await stats_service.check_admin_permission(user_id)
        if not is_admin:
            raise PermissionError("관리자 권한이 필요합니다")
        
        # 트렌드 분석
        trends = await stats_service.analyze_trends(
            metric=metric,
            period=period
        )
        
        return {
            "success": True,
            "metric": metric,
            "period": period,
            "trends": trends
        }
    
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def user_activity_tool(
    user_id: str,
    target_user_id: Optional[str] = None,
    period: str = "week",
    **kwargs
) -> Dict[str, Any]:
    """
    사용자 활동 분석 Tool
    
    Args:
        user_id: 관리자 ID
        target_user_id: 분석 대상 사용자 ID
        period: 분석 기간
    
    Returns:
        사용자 활동 데이터
    """
    try:
        # 권한 확인
        is_admin = await stats_service.check_admin_permission(user_id)
        if not is_admin:
            raise PermissionError("관리자 권한이 필요합니다")
        
        # 사용자 활동 조회
        if target_user_id:
            activity = await stats_service.get_user_activity(target_user_id, period)
        else:
            activity = await stats_service.get_all_users_activity(period)
        
        return {
            "success": True,
            "target_user_id": target_user_id,
            "period": period,
            "activity": activity
        }
    
    except Exception as e:
        logger.error(f"User activity analysis failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def document_metrics_tool(
    user_id: str,
    doc_id: Optional[str] = None,
    metric_type: str = "all",
    **kwargs
) -> Dict[str, Any]:
    """
    문서 메트릭 조회 Tool
    
    Args:
        user_id: 관리자 ID
        doc_id: 문서 ID
        metric_type: 메트릭 유형
    
    Returns:
        문서 메트릭 데이터
    """
    try:
        # 권한 확인
        is_admin = await stats_service.check_admin_permission(user_id)
        if not is_admin:
            raise PermissionError("관리자 권한이 필요합니다")
        
        # 문서 메트릭 조회
        if doc_id:
            metrics = await stats_service.get_document_metrics(doc_id, metric_type)
        else:
            metrics = await stats_service.get_all_documents_metrics(metric_type)
        
        return {
            "success": True,
            "doc_id": doc_id,
            "metric_type": metric_type,
            "metrics": metrics
        }
    
    except Exception as e:
        logger.error(f"Document metrics retrieval failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

***

## 7. 공통 모듈

### 7.1 기본 서버 클래스

```python
# /app/poc/mcps/mcp-servers/common/base_server.py
"""MCP 서버 기본 클래스"""

import logging
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from mcp.server import Server
from mcp.types import Tool, Resource, Prompt

logger = logging.getLogger(__name__)

class BaseMCPServer(ABC):
    """MCP 서버 기본 클래스"""
    
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.server = Server(server_name)
        self.logger = logging.getLogger(f"mcp.{server_name}")
    
    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """도구 목록 반환 (구현 필요)"""
        pass
    
    @abstractmethod
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """도구 실행 (구현 필요)"""
        pass
    
    def get_resources(self) -> List[Resource]:
        """리소스 목록 반환 (선택적 구현)"""
        return []
    
    async def read_resource(self, uri: str) -> str:
        """리소스 읽기 (선택적 구현)"""
        raise NotImplementedError("Resource reading not implemented")
    
    def get_prompts(self) -> List[Prompt]:
        """프롬프트 목록 반환 (선택적 구현)"""
        return []
    
    async def get_prompt_messages(self, name: str, arguments: Dict[str, str]) -> List:
        """프롬프트 메시지 반환 (선택적 구현)"""
        raise NotImplementedError("Prompt not implemented")
    
    def setup_handlers(self):
        """핸들러 설정"""
        
        @self.server.list_tools()
        async def list_tools():
            return self.get_tools()
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            try:
                result = await self.execute_tool(name, arguments)
                return result
            except Exception as e:
                self.logger.error(f"Tool execution error: {e}")
                raise
        
        if self.get_resources():
            @self.server.list_resources()
            async def list_resources():
                return self.get_resources()
            
            @self.server.read_resource()
            async def read_resource(uri: str):
                return await self.read_resource(uri)
        
        if self.get_prompts():
            @self.server.list_prompts()
            async def list_prompts():
                return self.get_prompts()
            
            @self.server.get_prompt()
            async def get_prompt(name: str, arguments: Dict[str, str]):
                return await self.get_prompt_messages(name, arguments)
    
    async def run(self):
        """서버 실행"""
        self.setup_handlers()
        self.logger.info(f"{self.server_name} starting...")
        # 실제 실행 로직은 서브클래스에서 구현
```

### 7.2 프로토콜 유틸리티

```python
# /app/poc/mcps/mcp-servers/common/protocol.py
"""MCP 프로토콜 유틸리티"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MCPRequest(BaseModel):
    """MCP 요청"""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)

class MCPResponse(BaseModel):
    """MCP 응답"""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class MCPError:
    """MCP 에러 코드"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # 커스텀 에러
    PERMISSION_DENIED = -32001
    RESOURCE_NOT_FOUND = -32002
    VALIDATION_ERROR = -32003

def create_error_response(
    id: Optional[int],
    code: int,
    message: str,
    data: Optional[Dict[str, Any]] = None
) -> MCPResponse:
    """에러 응답 생성"""
    return MCPResponse(
        id=id,
        error={
            "code": code,
            "message": message,
            "data": data or {}
        }
    )

def create_success_response(
    id: Optional[int],
    result: Any
) -> MCPResponse:
    """성공 응답 생성"""
    return MCPResponse(
        id=id,
        result=result
    )
```




### 7.3 에러 처리

```python
# /app/poc/mcps/mcp-servers/common/errors.py
"""MCP 서버 에러 정의"""

from typing import Optional

class MCPServerError(Exception):
    """MCP 서버 기본 에러"""
    def __init__(self, message: str, code: int = -32603):
        self.message = message
        self.code = code
        super().__init__(self.message)

class PermissionDeniedError(MCPServerError):
    """권한 없음 에러"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code=-32001)

class ResourceNotFoundError(MCPServerError):
    """리소스 없음 에러"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code=-32002)

class ValidationError(MCPServerError):
    """검증 에러"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, code=-32003)

class AuthenticationError(MCPServerError):
    """인증 에러"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code=-32004)

class RateLimitError(MCPServerError):
    """Rate Limit 에러"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, code=-32005)
```

### 7.4 공통 유틸리티

```python
# /app/poc/mcps/mcp-servers/common/utils.py
"""공통 유틸리티 함수"""

import hashlib
import json
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

def generate_id(prefix: str = "") -> str:
    """고유 ID 생성"""
    import uuid
    unique_id = str(uuid.uuid4())
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id

def hash_string(text: str) -> str:
    """문자열 해시"""
    return hashlib.sha256(text.encode()).hexdigest()

def sanitize_input(text: str) -> str:
    """입력 텍스트 정제"""
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # 특수 문자 이스케이프
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    return text.strip()

def validate_email(email: str) -> bool:
    """이메일 형식 검증"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def parse_date_range(period: str) -> tuple:
    """기간 문자열을 시작/종료 날짜로 파싱"""
    end_date = datetime.now()
    
    period_map = {
        'today': timedelta(days=1),
        'week': timedelta(days=7),
        'month': timedelta(days=30),
        'quarter': timedelta(days=90),
        'year': timedelta(days=365)
    }
    
    if period in period_map:
        start_date = end_date - period_map[period]
    else:
        # "2024-01-01 to 2024-01-31" 형식 파싱
        try:
            parts = period.split(' to ')
            start_date = datetime.fromisoformat(parts[0])
            end_date = datetime.fromisoformat(parts[1]) if len(parts) > 1 else end_date
        except:
            start_date = end_date - timedelta(days=7)  # 기본값: 1주일
    
    return start_date, end_date

def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """텍스트 자르기"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_file_size(size_bytes: int) -> str:
    """파일 크기 포맷팅"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """딕셔너리 깊은 병합"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
```

### 7.5 로깅 설정

```python
# /app/poc/mcps/mcp-servers/common/logging.py
"""로깅 설정"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

def setup_logging(
    server_name: str,
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    로깅 설정
    
    Args:
        server_name: 서버 이름
        log_level: 로그 레벨
        log_dir: 로그 디렉토리
        max_bytes: 최대 파일 크기
        backup_count: 백업 파일 수
    """
    # 로거 생성
    logger = logging.getLogger(f"mcp.{server_name}")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택적)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 일반 로그
        file_handler = RotatingFileHandler(
            log_dir / f"{server_name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 에러 로그
        error_handler = RotatingFileHandler(
            log_dir / f"{server_name}_error.log",
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    return logger
```

***

## 8. 통신 프로토콜

### 8.1 stdio 기반 통신

```python
# stdio 프로토콜 예시
"""
MCP Host와 MCP Server 간 stdio 통신

[MCP Host] → [MCP Server]
stdin으로 JSON-RPC 요청 전송

[MCP Server] → [MCP Host]  
stdout으로 JSON-RPC 응답 전송

stderr는 로그 출력용
"""

# 서버 시작 (stdio 모드)
async def run_stdio_server():
    from mcp.server.stdio import stdio_server
    
    server = Server("my-server")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

# 클라이언트에서 사용
# MCP Host는 서버 프로세스를 시작하고 stdin/stdout으로 통신
```

### 8.2 HTTP 기반 통신

```python
# /app/poc/mcps/mcp-servers/common/http_transport.py
"""HTTP 기반 통신"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict

class HTTPTransport:
    """HTTP 기반 MCP 통신"""
    
    def __init__(self, server_name: str, port: int = 5000):
        self.server_name = server_name
        self.port = port
        self.app = FastAPI(title=f"{server_name} MCP Server")
        self.setup_routes()
    
    def setup_routes(self):
        """라우트 설정"""
        
        @self.app.post("/mcp")
        async def handle_mcp_request(request: Request):
            """MCP 요청 처리"""
            try:
                body = await request.json()
                
                # JSON-RPC 요청 파싱
                method = body.get("method")
                params = body.get("params", {})
                req_id = body.get("id")
                
                # 메서드에 따라 처리
                result = await self.dispatch(method, params)
                
                # 응답 생성
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                })
            
            except Exception as e:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }, status_code=500)
        
        @self.app.get("/health")
        async def health_check():
            """헬스체크"""
            return {"status": "healthy", "server": self.server_name}
    
    async def dispatch(self, method: str, params: Dict[str, Any]) -> Any:
        """메서드 디스패치 (서브클래스에서 구현)"""
        raise NotImplementedError
    
    def run(self):
        """서버 실행"""
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
```

### 8.3 WebSocket 기반 통신

```python
# /app/poc/mcps/mcp-servers/common/websocket_transport.py
"""WebSocket 기반 통신"""

from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from typing import Dict, Set

class WebSocketTransport:
    """WebSocket 기반 MCP 통신"""
    
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """연결 수락"""
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """연결 종료"""
        self.active_connections.discard(websocket)
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """메시지 처리"""
        try:
            request = json.loads(message)
            
            # 메서드 처리
            method = request.get("method")
            params = request.get("params", {})
            req_id = request.get("id")
            
            result = await self.dispatch(method, params)
            
            # 응답 전송
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }
            
            await websocket.send_text(json.dumps(response))
        
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            await websocket.send_text(json.dumps(error_response))
    
    async def dispatch(self, method: str, params: Dict) -> Any:
        """메서드 디스패치"""
        raise NotImplementedError
    
    async def broadcast(self, message: Dict):
        """모든 연결에 메시지 브로드캐스트"""
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

# FastAPI에서 사용
# @app.websocket("/ws/mcp")
# async def websocket_endpoint(websocket: WebSocket):
#     transport = WebSocketTransport("my-server")
#     await transport.connect(websocket)
#     
#     try:
#         while True:
#             message = await websocket.receive_text()
#             await transport.handle_message(websocket, message)
#     except WebSocketDisconnect:
#         transport.disconnect(websocket)
```

***

## 9. 보안 및 인증

### 9.1 인증 미들웨어

```python
# /app/poc/mcps/mcp-servers/common/auth.py
"""인증 및 권한 관리"""

import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps

class AuthManager:
    """인증 관리자"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
    
    def create_token(
        self,
        user_id: str,
        permissions: list,
        expires_in: int = 3600
    ) -> str:
        """JWT 토큰 생성"""
        payload = {
            "user_id": user_id,
            "permissions": permissions,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
    
    def hash_password(self, password: str) -> str:
        """비밀번호 해시"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            self.secret_key.encode(),
            100000
        ).hex()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """비밀번호 검증"""
        return self.hash_password(password) == hashed

def require_auth(permissions: list = None):
    """인증 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 토큰 검증 로직
            token = kwargs.get('token') or kwargs.get('user_id')  # 임시
            
            if not token:
                raise PermissionError("Authentication required")
            
            # 권한 확인
            if permissions:
                # 실제 권한 확인 로직
                pass
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 사용 예시
# @require_auth(permissions=["admin"])
# async def admin_tool(**kwargs):
#     pass
```

### 9.2 권한 관리

```python
# /app/poc/mcps/mcp-servers/common/permissions.py
"""권한 관리"""

from enum import Enum
from typing import List, Set

class Permission(str, Enum):
    """권한 정의"""
    # 문서 권한
    DOC_READ = "doc:read"
    DOC_CREATE = "doc:create"
    DOC_UPDATE = "doc:update"
    DOC_DELETE = "doc:delete"
    
    # 검색 권한
    SEARCH_BASIC = "search:basic"
    SEARCH_ADVANCED = "search:advanced"
    
    # 분석 권한
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_REPORT = "analytics:report"
    
    # 관리자 권한
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"

class Role:
    """역할 정의"""
    
    GUEST = {
        Permission.DOC_READ,
        Permission.SEARCH_BASIC
    }
    
    USER = {
        Permission.DOC_READ,
        Permission.DOC_CREATE,
        Permission.DOC_UPDATE,
        Permission.SEARCH_BASIC,
        Permission.SEARCH_ADVANCED
    }
    
    ADMIN = {
        Permission.DOC_READ,
        Permission.DOC_CREATE,
        Permission.DOC_UPDATE,
        Permission.DOC_DELETE,
        Permission.SEARCH_BASIC,
        Permission.SEARCH_ADVANCED,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_REPORT,
        Permission.ADMIN_USERS,
        Permission.ADMIN_SYSTEM
    }

class PermissionChecker:
    """권한 확인"""
    
    @staticmethod
    def has_permission(user_permissions: Set[str], required: Permission) -> bool:
        """권한 확인"""
        return required.value in user_permissions
    
    @staticmethod
    def has_any_permission(user_permissions: Set[str], required: List[Permission]) -> bool:
        """하나 이상의 권한 확인"""
        return any(p.value in user_permissions for p in required)
    
    @staticmethod
    def has_all_permissions(user_permissions: Set[str], required: List[Permission]) -> bool:
        """모든 권한 확인"""
        return all(p.value in user_permissions for p in required)
```

### 9.3 Rate Limiting

```python
# /app/poc/mcps/mcp-servers/common/rate_limit.py
"""Rate Limiting"""

import time
from typing import Dict
from collections import defaultdict
import asyncio

class RateLimiter:
    """Rate Limiter"""
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(self, user_id: str) -> bool:
        """Rate limit 확인"""
        async with self.lock:
            now = time.time()
            
            # 만료된 요청 제거
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if now - req_time < self.window_seconds
            ]
            
            # Rate limit 확인
            if len(self.requests[user_id]) >= self.max_requests:
                return False
            
            # 요청 기록
            self.requests[user_id].append(now)
            return True
    
    async def get_remaining(self, user_id: str) -> int:
        """남은 요청 수 확인"""
        async with self.lock:
            now = time.time()
            
            # 만료된 요청 제거
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if now - req_time < self.window_seconds
            ]
            
            return max(0, self.max_requests - len(self.requests[user_id]))

# 데코레이터로 사용
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

def rate_limit(limiter: RateLimiter):
    """Rate limit 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id')
            
            if not await limiter.check_rate_limit(user_id):
                raise Exception("Rate limit exceeded")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

***

## 10. 배포 및 운영

### 10.1 서버 시작 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/mcp-servers/scripts/start_all.sh
# 모든 MCP 서버 시작

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  MCP Servers 시작"
echo "=========================================="

# 가상환경 활성화
source "${PROJECT_ROOT}/../.venv/bin/activate"

# 로그 디렉토리 생성
mkdir -p /data/logs/mcp-servers/{core,search,analytics}

# Core MCP 서버 시작
echo "[1/3] Core MCP Server 시작..."
nohup python -m mcp_servers.core.server \
    > /data/logs/mcp-servers/core/stdout.log 2>&1 &
CORE_PID=$!
echo "Core Server PID: ${CORE_PID}" > /tmp/mcp_core.pid

sleep 2

# Search MCP 서버 시작
echo "[2/3] Search MCP Server 시작..."
nohup python -m mcp_servers.search.server \
    > /data/logs/mcp-servers/search/stdout.log 2>&1 &
SEARCH_PID=$!
echo "Search Server PID: ${SEARCH_PID}" > /tmp/mcp_search.pid

sleep 2

# Analytics MCP 서버 시작
echo "[3/3] Analytics MCP Server 시작..."
nohup python -m mcp_servers.analytics.server \
    > /data/logs/mcp-servers/analytics/stdout.log 2>&1 &
ANALYTICS_PID=$!
echo "Analytics Server PID: ${ANALYTICS_PID}" > /tmp/mcp_analytics.pid

sleep 2

echo ""
echo "=========================================="
echo "  모든 MCP 서버 시작 완료"
echo "=========================================="
echo "Core Server PID: ${CORE_PID}"
echo "Search Server PID: ${SEARCH_PID}"
echo "Analytics Server PID: ${ANALYTICS_PID}"
echo ""
echo "상태 확인: ./scripts/status.sh"
echo "중지: ./scripts/stop_all.sh"
```

### 10.2 서버 중지 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/mcp-servers/scripts/stop_all.sh
# 모든 MCP 서버 중지

set -e

echo "=========================================="
echo "  MCP Servers 중지"
echo "=========================================="

# Core 서버 중지
if [ -f /tmp/mcp_core.pid ]; then
    CORE_PID=$(cat /tmp/mcp_core.pid)
    echo "[1/3] Core Server 중지 (PID: ${CORE_PID})..."
    kill ${CORE_PID} 2>/dev/null || echo "Core Server 이미 중지됨"
    rm /tmp/mcp_core.pid
fi

# Search 서버 중지
if [ -f /tmp/mcp_search.pid ]; then
    SEARCH_PID=$(cat /tmp/mcp_search.pid)
    echo "[2/3] Search Server 중지 (PID: ${SEARCH_PID})..."
    kill ${SEARCH_PID} 2>/dev/null || echo "Search Server 이미 중지됨"
    rm /tmp/mcp_search.pid
fi

# Analytics 서버 중지
if [ -f /tmp/mcp_analytics.pid ]; then
    ANALYTICS_PID=$(cat /tmp/mcp_analytics.pid)
    echo "[3/3] Analytics Server 중지 (PID: ${ANALYTICS_PID})..."
    kill ${ANALYTICS_PID} 2>/dev/null || echo "Analytics Server 이미 중지됨"
    rm /tmp/mcp_analytics.pid
fi

echo ""
echo "모든 MCP 서버가 중지되었습니다."
```

### 10.3 상태 확인 스크립트

```bash
#!/bin/bash
# /app/poc/mcps/mcp-servers/scripts/status.sh
# MCP 서버 상태 확인

echo "=========================================="
echo "  MCP Servers 상태"
echo "=========================================="
echo ""

# Core 서버
echo "[Core MCP Server]"
if [ -f /tmp/mcp_core.pid ]; then
    PID=$(cat /tmp/mcp_core.pid)
    if ps -p ${PID} > /dev/null; then
        echo "  상태: 실행 중"
        echo "  PID: ${PID}"
        echo "  메모리: $(ps -o rss= -p ${PID} | awk '{printf "%.2f MB\n", $1/1024}')"
    else
        echo "  상태: 중지됨 (PID 파일 존재하지만 프로세스 없음)"
    fi
else
    echo "  상태: 중지됨"
fi
echo ""

# Search 서버
echo "[Search MCP Server]"
if [ -f /tmp/mcp_search.pid ]; then
    PID=$(cat /tmp/mcp_search.pid)
    if ps -p ${PID} > /dev/null; then
        echo "  상태: 실행 중"
        echo "  PID: ${PID}"
        echo "  메모리: $(ps -o rss= -p ${PID} | awk '{printf "%.2f MB\n", $1/1024}')"
    else
        echo "  상태: 중지됨"
    fi
else
    echo "  상태: 중지됨"
fi
echo ""

# Analytics 서버
echo "[Analytics MCP Server]"
if [ -f /tmp/mcp_analytics.pid ]; then
    PID=$(cat /tmp/mcp_analytics.pid)
    if ps -p ${PID} > /dev/null; then
        echo "  상태: 실행 중"
        echo "  PID: ${PID}"
        echo "  메모리: $(ps -o rss= -p ${PID} | awk '{printf "%.2f MB\n", $1/1024}')"
    else
        echo "  상태: 중지됨"
    fi
else
    echo "  상태: 중지됨"
fi

echo ""
echo "=========================================="
```

### 10.4 systemd 서비스 파일

```ini
# /etc/systemd/system/mcp-core-server.service
[Unit]
Description=MCP Core Server
After=network.target mariadb.service

[Service]
Type=simple
User=mcps
Group=mcps
WorkingDirectory=/app/poc/mcps/mcp-servers
Environment="PATH=/app/poc/mcps/.venv/bin"
ExecStart=/app/poc/mcps/.venv/bin/python -m mcp_servers.core.server
Restart=always
RestartSec=10
StandardOutput=append:/data/logs/mcp-servers/core/stdout.log
StandardError=append:/data/logs/mcp-servers/core/stderr.log

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/mcp-search-server.service
[Unit]
Description=MCP Search Server
After=network.target elasticsearch.service

[Service]
Type=simple
User=mcps
Group=mcps
WorkingDirectory=/app/poc/mcps/mcp-servers
Environment="PATH=/app/poc/mcps/.venv/bin"
ExecStart=/app/poc/mcps/.venv/bin/python -m mcp_servers.search.server
Restart=always
RestartSec=10
StandardOutput=append:/data/logs/mcp-servers/search/stdout.log
StandardError=append:/data/logs/mcp-servers/search/stderr.log

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/mcp-analytics-server.service
[Unit]
Description=MCP Analytics Server
After=network.target mariadb.service

[Service]
Type=simple
User=mcps
Group=mcps
WorkingDirectory=/app/poc/mcps/mcp-servers
Environment="PATH=/app/poc/mcps/.venv/bin"
ExecStart=/app/poc/mcps/.venv/bin/python -m mcp_servers.analytics.server
Restart=always
RestartSec=10
StandardOutput=append:/data/logs/mcp-servers/analytics/stdout.log
StandardError=append:/data/logs/mcp-servers/analytics/stderr.log

[Install]
WantedBy=multi-user.target
```

### 10.5 설정 파일 예시

```python
# /app/poc/mcps/mcp-servers/core/config.py
"""Core MCP Server 설정"""

from pydantic_settings import BaseSettings
from typing import Optional

class CoreSettings(BaseSettings):
    """Core 서버 설정"""
    
    # 서버 설정
    server_name: str = "core-mcp-server"
    log_level: str = "INFO"
    
    # Database 설정
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "mcps_db"
    db_user: str = "mcps_user"
    db_password: str
    
    # Redis 설정
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # 보안 설정
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    # 로깅
    log_dir: Optional[str] = "/data/logs/mcp-servers/core"
    
    class Config:
        env_file = ".env"
        env_prefix = "CORE_"

settings = CoreSettings()
```

```ini
# /app/poc/mcps/mcp-servers/.env
# 환경 변수 설정

# Core Server
CORE_DB_PASSWORD=your_password_here
CORE_SECRET_KEY=your_secret_key_here

# Search Server
SEARCH_ES_HOST=localhost
SEARCH_ES_PORT=9200

# Analytics Server
ANALYTICS_DB_PASSWORD=your_password_here
```

### 10.6 Docker Compose 배포

```yaml
# /app/poc/mcps/mcp-servers/docker-compose.yml
version: '3.8'

services:
  mcp-core-server:
    build:
      context: .
      dockerfile: Dockerfile.core
    container_name: mcp-core-server
    environment:
      - CORE_DB_HOST=mariadb
      - CORE_DB_PASSWORD=${CORE_DB_PASSWORD}
      - CORE_SECRET_KEY=${CORE_SECRET_KEY}
    volumes:
      - /data/logs/mcp-servers/core:/app/logs
    depends_on:
      - mariadb
      - redis
    restart: unless-stopped
    networks:
      - mcps-network

  mcp-search-server:
    build:
      context: .
      dockerfile: Dockerfile.search
    container_name: mcp-search-server
    environment:
      - SEARCH_ES_HOST=elasticsearch
      - SEARCH_ES_PORT=9200
    volumes:
      - /data/logs/mcp-servers/search:/app/logs
    depends_on:
      - elasticsearch
    restart: unless-stopped
    networks:
      - mcps-network

  mcp-analytics-server:
    build:
      context: .
      dockerfile: Dockerfile.analytics
    container_name: mcp-analytics-server
    environment:
      - ANALYTICS_DB_HOST=mariadb
      - ANALYTICS_DB_PASSWORD=${ANALYTICS_DB_PASSWORD}
    volumes:
      - /data/logs/mcp-servers/analytics:/app/logs
    depends_on:
      - mariadb
    restart: unless-stopped
    networks:
      - mcps-network

networks:
  mcps-network:
    external: true
```

***

## 11. 테스트

### 11.1 단위 테스트 예시

```python
# /app/poc/mcps/mcp-servers/core/tests/test_tools.py
"""Core Tools 단위 테스트"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from mcp_servers.core.tools.document_tools import (
    create_document_tool,
    get_document_tool
)

@pytest.mark.asyncio
async def test_create_document_success():
    """문서 생성 성공 테스트"""
    result = await create_document_tool(
        title="테스트 문서",
        content="테스트 내용",
        classification="internal",
        author_id="user-001"
    )
    
    assert result["success"] is True
    assert "doc_id" in result
    assert result["message"].startswith("문서가 생성되었습니다")

@pytest.mark.asyncio
async def test_create_document_invalid_classification():
    """잘못된 보안 등급으로 문서 생성 실패 테스트"""
    result = await create_document_tool(
        title="테스트 문서",
        content="테스트 내용",
        classification="invalid",
        author_id="user-001"
    )
    
    assert result["success"] is False
    assert "error" in result

@pytest.mark.asyncio
async def test_get_document_permission_denied():
    """권한 없음 테스트"""
    result = await get_document_tool(
        doc_id="DOC-001",
        user_id="unauthorized-user"
    )
    
    assert result["success"] is False
    assert "권한" in result["error"]
```

### 11.2 통합 테스트

```python
# /app/poc/mcps/mcp-servers/tests/integration/test_server_integration.py
"""MCP 서버 통합 테스트"""

import pytest
from mcp.client import ClientSession
from mcp_servers.core.server import CoreMCPServer

@pytest.mark.asyncio
async def test_full_document_workflow():
    """전체 문서 워크플로우 테스트"""
    
    # 서버 시작
    server = CoreMCPServer()
    
    # 1. 문서 생성
    create_result = await server.execute_tool(
        "create_document",
        {
            "title": "통합 테스트 문서",
            "content": "테스트 내용",
            "classification": "internal",
            "author_id": "test-user"
        }
    )
    
    assert create_result["success"] is True
    doc_id = create_result["doc_id"]
    
    # 2. 문서 조회
    get_result = await server.execute_tool(
        "get_document",
        {
            "doc_id": doc_id,
            "user_id": "test-user"
        }
    )
    
    assert get_result["success"] is True
    assert get_result["document"]["title"] == "통합 테스트 문서"
    
    # 3. 문서 수정
    update_result = await server.execute_tool(
        "update_document",
        {
            "doc_id": doc_id,
            "user_id": "test-user",
            "title": "수정된 제목"
        }
    )
    
    assert update_result["success"] is True
    
    # 4. 문서 삭제
    delete_result = await server.execute_tool(
        "delete_document",
        {
            "doc_id": doc_id,
            "user_id": "test-user"
        }
    )
    
    assert delete_result["success"] is True
```

***

## 12. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

***

## 13. 참고 자료

- [MCP Protocol Specification](https://modelcontextprotocol.io/docs)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

***


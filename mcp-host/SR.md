# mcp-host 개발가이드 설계서

***

# 05. MCP 에코시스템 - mcp-host 개발가이드

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/mcp-host/`  
**목적**: MCP Host 개발 및 통합 가이드

***

## 목차

1. [개요](#1-개요)
2. [아키텍처](#2-아키텍처)
3. [핵심 컴포넌트](#3-핵심-컴포넌트)
4. [Server 관리](#4-server-관리)
5. [API 구현](#5-api-구현)
6. [배포 및 운영](#6-배포-및-운영)

***

## 1. 개요

### 1.1 목적

mcp-host는 MCP 에코시스템의 중앙 오케스트레이터로, 다음 역할을 수행합니다:

- MCP Server 관리 (시작/중지/재시작)
- Tool 요청 라우팅
- 세션 관리
- API Gateway 역할

### 1.2 디렉토리 구조

```
/app/poc/mcps/mcp-host/
├── main.py                     # 메인 애플리케이션
├── requirements.txt            # 의존성
├── config.py                   # 설정 관리
│
├── core/                       # 핵심 컴포넌트
│   ├── __init__.py
│   ├── server_manager.py      # Server 관리
│   ├── session_manager.py     # 세션 관리
│   ├── router.py              # 요청 라우팅
│   └── executor.py            # Tool 실행
│
├── api/                        # REST API
│   ├── __init__.py
│   ├── routes.py              # 라우트 정의
│   ├── schemas.py             # Pydantic 스키마
│   └── middleware.py          # 미들웨어
│
├── models/                     # 데이터 모델
│   ├── __init__.py
│   ├── session.py
│   ├── server.py
│   └── request.py
│
├── utils/                      # 유틸리티
│   ├── __init__.py
│   ├── cache.py
│   └── metrics.py
│
└── tests/                      # 테스트
    ├── test_server_manager.py
    ├── test_router.py
    └── test_api.py
```

### 1.3 기술 스택

- **웹 프레임워크**: FastAPI
- **비동기 처리**: asyncio
- **프로세스 관리**: subprocess
- **캐싱**: 메모리 캐시
- **로깅**: Python logging

***

## 2. 아키텍처

### 2.1 전체 구조

```
┌─────────────────────────────────────────────────┐
│                  MCP Host                        │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │            REST API                       │  │
│  │  - POST /api/sessions                     │  │
│  │  - POST /api/tools/execute                │  │
│  │  - GET /api/tools/list                    │  │
│  └──────────────────────────────────────────┘  │
│                    ▼                             │
│  ┌──────────────────────────────────────────┐  │
│  │         Session Manager                   │  │
│  │  - 세션 생성/관리                         │  │
│  │  - 사용자 컨텍스트                        │  │
│  └──────────────────────────────────────────┘  │
│                    ▼                             │
│  ┌──────────────────────────────────────────┐  │
│  │            Router                         │  │
│  │  - Tool → Server 매핑                     │  │
│  │  - 요청 라우팅                            │  │
│  └──────────────────────────────────────────┘  │
│                    ▼                             │
│  ┌──────────────────────────────────────────┐  │
│  │         Server Manager                    │  │
│  │  - Server 시작/중지                       │  │
│  │  - 프로세스 관리                          │  │
│  │  - 헬스 체크                              │  │
│  └──────────────────────────────────────────┘  │
│                    ▼                             │
│  ┌──────────────────────────────────────────┐  │
│  │           Executor                        │  │
│  │  - STDIO 통신                             │  │
│  │  - JSON-RPC 처리                          │  │
│  │  - 응답 수신                              │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
└─────────────────────────────────────────────────┘
            │              │              │
            ▼              ▼              ▼
      ┌─────────┐    ┌─────────┐    ┌─────────┐
      │ Server1 │    │ Server2 │    │ Server3 │
      └─────────┘    └─────────┘    └─────────┘
```

### 2.2 요청 흐름

```
1. Client → API Request
   POST /api/tools/execute
   {
     "session_id": "...",
     "tool": "search_documents",
     "arguments": {...}
   }

2. Session Manager → 세션 확인
   - 세션 유효성 검증
   - 사용자 컨텍스트 로드

3. Router → Server 결정
   - Tool → Server 매핑 조회
   - Server 가용성 확인

4. Server Manager → Server 확인
   - Server 실행 중?
   - 아니면 시작

5. Executor → Tool 실행
   - JSON-RPC 요청 생성
   - STDIO로 Server 통신
   - 응답 수신

6. API → 응답 반환
   - 결과 포맷팅
   - Client에게 응답
```

***

## 3. 핵심 컴포넌트

### 3.1 config.py - 설정 관리

```python
# mcp-host/config.py
"""
MCP Host 설정
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    """Database 설정"""
    host: str = "localhost"
    port: int = 3306
    database: str = "mcps_db"
    user: str = "mcps_user"
    password: str = "your_password"
    charset: str = "utf8mb4"
    pool_size: Dict[str, int] = {"min": 5, "max": 20}


class ElasticsearchConfig(BaseModel):
    """Elasticsearch 설정"""
    hosts: list = ["localhost:9200"]
    timeout: int = 30


class ServerConfig(BaseModel):
    """Server 설정"""
    name: str
    path: str
    python: str
    enabled: bool = True
    auto_start: bool = True
    restart_on_failure: bool = True
    max_restarts: int = 3
    timeout: int = 30


class HostConfig(BaseModel):
    """Host 설정"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1
    log_level: str = "INFO"


class Config:
    """
    통합 설정
    
    환경 변수 및 설정 파일에서 로드
    """
    
    def __init__(self):
        # 프로젝트 루트
        self.project_root = Path(__file__).parent.parent
        
        # Database
        self.database = DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            database=os.getenv("DB_NAME", "mcps_db"),
            user=os.getenv("DB_USER", "mcps_user"),
            password=os.getenv("DB_PASSWORD", "your_password")
        )
        
        # Elasticsearch
        self.elasticsearch = ElasticsearchConfig(
            hosts=[os.getenv("ES_HOST", "localhost:9200")],
            timeout=int(os.getenv("ES_TIMEOUT", 30))
        )
        
        # Host
        self.host = HostConfig(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", 8000)),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
        
        # Servers
        self.servers = self._load_servers()
        
        # Registry
        self.registry = self._load_registry()
    
    def _load_servers(self) -> Dict[str, ServerConfig]:
        """Server 설정 로드"""
        services_file = self.project_root / "config" / "services.json"
        
        with open(services_file, "r") as f:
            data = json.load(f)
        
        servers = {}
        for server_data in data["servers"]:
            server = ServerConfig(**server_data)
            servers[server.name] = server
        
        return servers
    
    def _load_registry(self) -> dict:
        """Tool 레지스트리 로드"""
        registry_file = self.project_root / "config" / "registry.json"
        
        with open(registry_file, "r") as f:
            return json.load(f)
    
    def get_server(self, server_name: str) -> ServerConfig:
        """Server 설정 가져오기"""
        return self.servers.get(server_name)
    
    def get_tool_registry(self) -> dict:
        """Tool 레지스트리 가져오기"""
        return self.registry


# 전역 설정 인스턴스
config = Config()
```

### 3.2 core/server_manager.py - Server 관리

```python
# mcp-host/core/server_manager.py
"""
MCP Server 관리자

Server 프로세스 시작/중지/재시작
"""

import subprocess
import time
import signal
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ServerProcess:
    """Server 프로세스 정보"""
    name: str
    process: subprocess.Popen
    started_at: datetime
    restart_count: int = 0


class ServerManager:
    """
    Server 관리자
    
    MCP Server 프로세스 관리
    """
    
    def __init__(self, config):
        """
        초기화
        
        Args:
            config: Config 인스턴스
        """
        self.config = config
        self.servers: Dict[str, ServerProcess] = {}
        self.max_restarts = 3
    
    def start_server(self, server_name: str) -> bool:
        """
        Server 시작
        
        Args:
            server_name: Server 이름
        
        Returns:
            bool: 성공 여부
        """
        # 이미 실행 중?
        if self.is_running(server_name):
            logger.warning(f"Server already running: {server_name}")
            return True
        
        # Server 설정
        server_config = self.config.get_server(server_name)
        if not server_config:
            logger.error(f"Server config not found: {server_name}")
            return False
        
        if not server_config.enabled:
            logger.warning(f"Server disabled: {server_name}")
            return False
        
        try:
            logger.info(f"Starting server: {server_name}")
            
            # 프로세스 시작
            process = subprocess.Popen(
                [server_config.python, "main.py"],
                cwd=server_config.path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # 등록
            self.servers[server_name] = ServerProcess(
                name=server_name,
                process=process,
                started_at=datetime.now()
            )
            
            # 시작 확인 (간단한 대기)
            time.sleep(2)
            
            if process.poll() is not None:
                # 프로세스가 즉시 종료됨
                logger.error(f"Server failed to start: {server_name}")
                return False
            
            logger.info(f"Server started: {server_name} (PID: {process.pid})")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start server {server_name}: {e}", exc_info=True)
            return False
    
    def stop_server(self, server_name: str, timeout: int = 10) -> bool:
        """
        Server 중지
        
        Args:
            server_name: Server 이름
            timeout: 종료 대기 시간 (초)
        
        Returns:
            bool: 성공 여부
        """
        if server_name not in self.servers:
            logger.warning(f"Server not running: {server_name}")
            return True
        
        server_process = self.servers[server_name]
        process = server_process.process
        
        try:
            logger.info(f"Stopping server: {server_name} (PID: {process.pid})")
            
            # SIGTERM 전송
            process.terminate()
            
            # 종료 대기
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # 강제 종료
                logger.warning(f"Force killing server: {server_name}")
                process.kill()
                process.wait(timeout=5)
            
            # 등록 해제
            del self.servers[server_name]
            
            logger.info(f"Server stopped: {server_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to stop server {server_name}: {e}", exc_info=True)
            return False
    
    def restart_server(self, server_name: str) -> bool:
        """
        Server 재시작
        
        Args:
            server_name: Server 이름
        
        Returns:
            bool: 성공 여부
        """
        logger.info(f"Restarting server: {server_name}")
        
        # 재시작 횟수 체크
        if server_name in self.servers:
            server_process = self.servers[server_name]
            server_process.restart_count += 1
            
            if server_process.restart_count > self.max_restarts:
                logger.error(
                    f"Max restart attempts exceeded for {server_name}. "
                    f"Manual intervention required."
                )
                return False
        
        # 중지
        self.stop_server(server_name)
        
        # 대기
        time.sleep(2)
        
        # 시작
        return self.start_server(server_name)
    
    def is_running(self, server_name: str) -> bool:
        """
        Server 실행 여부
        
        Args:
            server_name: Server 이름
        
        Returns:
            bool: 실행 중 여부
        """
        if server_name not in self.servers:
            return False
        
        process = self.servers[server_name].process
        return process.poll() is None
    
    def get_server_info(self, server_name: str) -> Optional[dict]:
        """
        Server 정보
        
        Args:
            server_name: Server 이름
        
        Returns:
            dict 또는 None
        """
        if server_name not in self.servers:
            return None
        
        server_process = self.servers[server_name]
        process = server_process.process
        
        return {
            "name": server_name,
            "pid": process.pid,
            "running": process.poll() is None,
            "started_at": server_process.started_at.isoformat(),
            "restart_count": server_process.restart_count
        }
    
    def list_servers(self) -> list:
        """
        전체 Server 목록
        
        Returns:
            list: Server 정보 목록
        """
        servers_list = []
        
        for server_name in self.config.servers.keys():
            info = self.get_server_info(server_name)
            
            if info:
                servers_list.append(info)
            else:
                servers_list.append({
                    "name": server_name,
                    "running": False
                })
        
        return servers_list
    
    def start_all(self):
        """전체 Server 시작"""
        logger.info("Starting all servers...")
        
        for server_name, server_config in self.config.servers.items():
            if server_config.auto_start and server_config.enabled:
                self.start_server(server_name)
                time.sleep(1)  # 순차 시작
    
    def stop_all(self):
        """전체 Server 중지"""
        logger.info("Stopping all servers...")
        
        for server_name in list(self.servers.keys()):
            self.stop_server(server_name)
    
    def health_check(self, server_name: str) -> bool:
        """
        Server 헬스 체크
        
        Args:
            server_name: Server 이름
        
        Returns:
            bool: 정상 여부
        """
        if not self.is_running(server_name):
            return False
        
        # TODO: 실제 헬스 체크 (tools/list 요청 등)
        return True
    
    def cleanup(self):
        """리소스 정리"""
        logger.info("Cleaning up server manager...")
        self.stop_all()
```

### 3.3 core/executor.py - Tool 실행

```python
# mcp-host/core/executor.py
"""
Tool 실행기

Server와 STDIO 통신하여 Tool 실행
"""

import json
import uuid
from typing import Any, Optional, Dict
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Tool 실행기
    
    Server와 JSON-RPC 통신
    """
    
    def __init__(self, server_manager):
        """
        초기화
        
        Args:
            server_manager: ServerManager 인스턴스
        """
        self.server_manager = server_manager
    
    async def execute_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict,
        context: Optional[dict] = None,
        timeout: int = 30
    ) -> dict:
        """
        Tool 실행
        
        Args:
            server_name: Server 이름
            tool_name: Tool 이름
            arguments: Tool 인자
            context: 실행 컨텍스트
            timeout: 타임아웃 (초)
        
        Returns:
            {
                "status": "success" | "error",
                "data": {...} | "error": {...},
                "execution_time_ms": 123.45
            }
        """
        start_time = datetime.now()
        
        try:
            # Server 확인
            if not self.server_manager.is_running(server_name):
                logger.info(f"Server not running, starting: {server_name}")
                success = self.server_manager.start_server(server_name)
                
                if not success:
                    return {
                        "status": "error",
                        "error": {
                            "code": "SERVER_START_FAILED",
                            "message": f"Failed to start server: {server_name}"
                        }
                    }
                
                # 시작 대기
                await asyncio.sleep(2)
            
            # Server 프로세스 가져오기
            server_process = self.server_manager.servers.get(server_name)
            if not server_process:
                return {
                    "status": "error",
                    "error": {
                        "code": "SERVER_NOT_FOUND",
                        "message": f"Server not found: {server_name}"
                    }
                }
            
            # JSON-RPC 요청 생성
            request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Context 추가
            if context:
                request["params"]["_context"] = context
            
            # 요청 전송
            request_json = json.dumps(request) + "\n"
            
            logger.debug(f"Sending request to {server_name}: {tool_name}")
            
            process = server_process.process
            process.stdin.write(request_json)
            process.stdin.flush()
            
            # 응답 수신 (타임아웃 포함)
            try:
                response_line = await asyncio.wait_for(
                    asyncio.to_thread(process.stdout.readline),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Tool execution timeout: {server_name}/{tool_name}")
                return {
                    "status": "error",
                    "error": {
                        "code": "TIMEOUT",
                        "message": f"Tool execution timeout ({timeout}s)"
                    }
                }
            
            # 응답 파싱
            response = json.loads(response_line)
            
            # 실행 시간 계산
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # JSON-RPC 응답 확인
            if "result" in response:
                result = response["result"]
                result["execution_time_ms"] = execution_time
                return result
            elif "error" in response:
                return {
                    "status": "error",
                    "error": response["error"],
                    "execution_time_ms": execution_time
                }
            else:
                return {
                    "status": "error",
                    "error": {
                        "code": "INVALID_RESPONSE",
                        "message": "Invalid JSON-RPC response"
                    }
                }
        
        except Exception as e:
            logger.error(
                f"Tool execution failed: {server_name}/{tool_name}",
                exc_info=True
            )
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "error",
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": str(e)
                },
                "execution_time_ms": execution_time
            }
    
    async def list_tools(self, server_name: str) -> dict:
        """
        Server의 Tool 목록 조회
        
        Args:
            server_name: Server 이름
        
        Returns:
            {
                "status": "success",
                "data": {
                    "tools": [...]
                }
            }
        """
        try:
            # Server 확인
            if not self.server_manager.is_running(server_name):
                success = self.server_manager.start_server(server_name)
                if not success:
                    return {
                        "status": "error",
                        "error": {
                            "code": "SERVER_START_FAILED",
                            "message": f"Failed to start server: {server_name}"
                        }
                    }
                
                await asyncio.sleep(2)
            
            # Server 프로세스
            server_process = self.server_manager.servers.get(server_name)
            if not server_process:
                return {
                    "status": "error",
                    "error": {
                        "code": "SERVER_NOT_FOUND",
                        "message": f"Server not found: {server_name}"
                    }
                }
            
            # JSON-RPC 요청
            request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/list",
                "params": {}
            }
            
            request_json = json.dumps(request) + "\n"
            
            process = server_process.process
            process.stdin.write(request_json)
            process.stdin.flush()
            
            # 응답 수신
            response_line = await asyncio.wait_for(
                asyncio.to_thread(process.stdout.readline),
                timeout=10
            )
            
            response = json.loads(response_line)
            
            if "result" in response:
                return {
                    "status": "success",
                    "data": response["result"]
                }
            else:
                return {
                    "status": "error",
                    "error": response.get("error", {"message": "Unknown error"})
                }
        
        except Exception as e:
            logger.error(f"List tools failed: {server_name}", exc_info=True)
            return {
                "status": "error",
                "error": {
                    "code": "LIST_ERROR",
                    "message": str(e)
                }
            }
```

### 3.4 core/router.py - 요청 라우팅

```python
# mcp-host/core/router.py
"""
요청 라우터

Tool → Server 매핑 및 라우팅
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Router:
    """
    요청 라우터
    
    Tool 이름을 보고 적절한 Server로 라우팅
    """
    
    def __init__(self, config):
        """
        초기화
        
        Args:
            config: Config 인스턴스
        """
        self.config = config
        self.tool_to_server_map = self._build_tool_map()
    
    def _build_tool_map(self) -> dict:
        """
        Tool → Server 매핑 구축
        
        Returns:
            {"tool_name": "server_name"}
        """
        mapping = {}
        
        registry = self.config.get_tool_registry()
        
        for tool in registry.get("tools", []):
            tool_name = tool["name"]
            server_name = tool["server"]
            
            mapping[tool_name] = server_name
        
        logger.info(f"Tool mapping built: {len(mapping)} tools")
        
        return mapping
    
    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """
        Tool에 해당하는 Server 찾기
        
        Args:
            tool_name: Tool 이름
        
        Returns:
            str: Server 이름 또는 None
        """
        return self.tool_to_server_map.get(tool_name)
    
    def is_tool_available(self, tool_name: str) -> bool:
        """
        Tool 사용 가능 여부
        
        Args:
            tool_name: Tool 이름
        
        Returns:
            bool: 사용 가능 여부
        """
        return tool_name in self.tool_to_server_map
    
    def list_all_tools(self) -> list:
        """
        전체 Tool 목록
        
        Returns:
            list: Tool 메타데이터 목록
        """
        registry = self.config.get_tool_registry()
        return registry.get("tools", [])
    
    def get_tool_metadata(self, tool_name: str) -> Optional[dict]:
        """
        Tool 메타데이터
        
        Args:
            tool_name: Tool 이름
        
        Returns:
            dict 또는 None
        """
        tools = self.list_all_tools()
        
        for tool in tools:
            if tool["name"] == tool_name:
                return tool
        
        return None
    
    def reload_mapping(self):
        """매핑 재로드 (registry.json 변경 시)"""
        logger.info("Reloading tool mapping...")
        self.tool_to_server_map = self._build_tool_map()
```

### 3.5 core/session_manager.py - 세션 관리

```python
# mcp-host/core/session_manager.py
"""
세션 관리자

사용자 세션 관리
"""

import uuid
from typing import Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """세션"""
    session_id: str
    user_id: str
    user_role: str
    user_team: Optional[str]
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    data: dict = field(default_factory=dict)


class SessionManager:
    """
    세션 관리자
    
    사용자 세션 생성 및 관리
    """
    
    def __init__(self, session_timeout: int = 3600):
        """
        초기화
        
        Args:
            session_timeout: 세션 타임아웃 (초)
        """
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = session_timeout
    
    def create_session(
        self,
        user_id: str,
        user_role: str,
        user_team: Optional[str] = None
    ) -> str:
        """
        세션 생성
        
        Args:
            user_id: 사용자 ID
            user_role: 사용자 역할
            user_team: 사용자 팀
        
        Returns:
            str: 세션 ID
        """
        session_id = str(uuid.uuid4())
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            user_role=user_role,
            user_team=user_team
        )
        
        self.sessions[session_id] = session
        
        logger.info(f"Session created: {session_id} for user {user_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        세션 조회
        
        Args:
            session_id: 세션 ID
        
        Returns:
            Session 또는 None
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        # 타임아웃 확인
        if self._is_expired(session):
            logger.info(f"Session expired: {session_id}")
            del self.sessions[session_id]
            return None
        
        # 마지막 접근 시간 갱신
        session.last_accessed = datetime.now()
        
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """
        세션 삭제
        
        Args:
            session_id: 세션 ID
        
        Returns:
            bool: 성공 여부
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session deleted: {session_id}")
            return True
        
        return False
    
    def _is_expired(self, session: Session) -> bool:
        """세션 만료 확인"""
        elapsed = (datetime.now() - session.last_accessed).total_seconds()
        return elapsed > self.session_timeout
    
    def cleanup_expired_sessions(self):
        """만료된 세션 정리"""
        expired = []
        
        for session_id, session in self.sessions.items():
            if self._is_expired(session):
                expired.append(session_id)
        
        for session_id in expired:
            del self.sessions[session_id]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def get_user_context(self, session_id: str) -> Optional[dict]:
        """
        사용자 컨텍스트 조회
        
        Args:
            session_id: 세션 ID
        
        Returns:
            {
                "user_id": "U001",
                "user_role": "staff",
                "user_team": "dev_team"
            }
        """
        session = self.get_session(session_id)
        
        if not session:
            return None
        
        return {
            "user_id": session.user_id,
            "user_role": session.user_role,
            "user_team": session.user_team
        }
    
    def list_active_sessions(self) -> list:
        """활성 세션 목록"""
        return [
            {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "last_accessed": session.last_accessed.isoformat()
            }
            for session in self.sessions.values()
            if not self._is_expired(session)
        ]
```


## 4. Server 관리

### 4.1 models/session.py - 데이터 모델

```python
# mcp-host/models/session.py
"""
세션 관련 데이터 모델
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SessionCreate(BaseModel):
    """세션 생성 요청"""
    user_id: str = Field(..., description="사용자 ID")


class SessionResponse(BaseModel):
    """세션 생성 응답"""
    session_id: str
    user_id: str
    user_role: str
    user_team: Optional[str]
    created_at: datetime
    message: str


class SessionInfo(BaseModel):
    """세션 정보"""
    session_id: str
    user_id: str
    user_role: str
    user_team: Optional[str]
    created_at: datetime
    last_accessed: datetime
```

### 4.2 models/request.py - 요청 모델

```python
# mcp-host/models/request.py
"""
Tool 실행 요청 모델
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class ToolExecuteRequest(BaseModel):
    """Tool 실행 요청"""
    session_id: str = Field(..., description="세션 ID")
    tool: str = Field(..., description="Tool 이름")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool 인자")


class ToolExecuteResponse(BaseModel):
    """Tool 실행 응답"""
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    execution_time_ms: float


class ToolListRequest(BaseModel):
    """Tool 목록 요청"""
    session_id: Optional[str] = None
    category: Optional[str] = None
    server: Optional[str] = None


class ToolInfo(BaseModel):
    """Tool 정보"""
    name: str
    description: str
    category: str
    server: str
    required_permissions: list
    input_schema: dict


class ToolListResponse(BaseModel):
    """Tool 목록 응답"""
    tools: list
    total: int
```

### 4.3 models/server.py - Server 모델

```python
# mcp-host/models/server.py
"""
Server 관련 모델
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ServerInfo(BaseModel):
    """Server 정보"""
    name: str
    running: bool
    pid: Optional[int] = None
    started_at: Optional[datetime] = None
    restart_count: Optional[int] = 0


class ServerListResponse(BaseModel):
    """Server 목록 응답"""
    servers: list
    total: int


class ServerActionRequest(BaseModel):
    """Server 액션 요청"""
    action: str  # start, stop, restart
    server_name: str


class ServerActionResponse(BaseModel):
    """Server 액션 응답"""
    status: str
    message: str
    server_info: Optional[ServerInfo] = None
```

***

## 5. API 구현

### 5.1 api/routes.py - API 라우트

```python
# mcp-host/api/routes.py
"""
REST API 라우트
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
import logging

from models.session import SessionCreate, SessionResponse, SessionInfo
from models.request import (
    ToolExecuteRequest, ToolExecuteResponse,
    ToolListRequest, ToolListResponse, ToolInfo
)
from models.server import (
    ServerListResponse, ServerActionRequest, ServerActionResponse, ServerInfo
)

logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter()

# 의존성 (main.py에서 주입)
_session_manager = None
_router = None
_executor = None
_server_manager = None


def set_dependencies(session_manager, tool_router, executor, server_manager):
    """의존성 설정"""
    global _session_manager, _router, _executor, _server_manager
    _session_manager = session_manager
    _router = tool_router
    _executor = executor
    _server_manager = server_manager


# ==================== 세션 API ====================

@router.post("/api/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: SessionCreate):
    """
    세션 생성 (인증)
    
    PoC에서는 user_id만으로 세션 생성
    실제 운영에서는 인증 토큰 검증
    """
    try:
        # 1. 사용자 조회 (Database)
        from shared.database import DatabaseManager
        from config import config
        
        db = DatabaseManager(config.database.dict())
        
        from shared.queries import GET_USER_BY_ID
        users = db.execute_query(GET_USER_BY_ID, (request.user_id,))
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {request.user_id}"
            )
        
        user = users[0]
        
        if not user["active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # 2. 세션 생성
        session_id = _session_manager.create_session(
            user_id=user["id"],
            user_role=user["role"],
            user_team=user["team"]
        )
        
        # 3. 감사 로그
        from shared.queries import CREATE_AUDIT_LOG
        db.execute_insert(
            CREATE_AUDIT_LOG,
            (user["id"], "session_create", "session", session_id, None, "success", None, None)
        )
        
        db.close()
        
        logger.info(f"Session created: {session_id} for user {request.user_id}")
        
        return SessionResponse(
            session_id=session_id,
            user_id=user["id"],
            user_role=user["role"],
            user_team=user["team"],
            created_at=_session_manager.get_session(session_id).created_at,
            message=f"Welcome, {user['name']}!"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/api/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """세션 정보 조회"""
    session = _session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    return SessionInfo(
        session_id=session.session_id,
        user_id=session.user_id,
        user_role=session.user_role,
        user_team=session.user_team,
        created_at=session.created_at,
        last_accessed=session.last_accessed
    )


@router.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제 (로그아웃)"""
    success = _session_manager.delete_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"message": "Session deleted successfully"}


# ==================== Tool API ====================

@router.post("/api/tools/execute", response_model=ToolExecuteResponse)
async def execute_tool(request: ToolExecuteRequest):
    """
    Tool 실행
    
    Args:
        request: {
            "session_id": "...",
            "tool": "search_documents",
            "arguments": {
                "query": "AI",
                "limit": 10
            }
        }
    
    Returns:
        {
            "status": "success",
            "data": {...},
            "execution_time_ms": 123.45
        }
    """
    try:
        # 1. 세션 확인
        context = _session_manager.get_user_context(request.session_id)
        
        if not context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        # 2. Tool → Server 매핑
        server_name = _router.get_server_for_tool(request.tool)
        
        if not server_name:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool not found: {request.tool}"
            )
        
        # 3. Tool 실행
        result = await _executor.execute_tool(
            server_name=server_name,
            tool_name=request.tool,
            arguments=request.arguments,
            context=context
        )
        
        # 4. 감사 로그 (실패한 경우에도 기록)
        from shared.database import DatabaseManager
        from shared.queries import CREATE_AUDIT_LOG
        from config import config
        
        db = DatabaseManager(config.database.dict())
        db.execute_insert(
            CREATE_AUDIT_LOG,
            (
                context["user_id"],
                f"tool_{request.tool}",
                "tool",
                request.tool,
                None,
                result["status"],
                None,
                None
            )
        )
        db.close()
        
        return ToolExecuteResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/api/tools/list", response_model=ToolListResponse)
async def list_tools(
    session_id: Optional[str] = None,
    category: Optional[str] = None,
    server: Optional[str] = None
):
    """
    Tool 목록 조회
    
    Query Parameters:
        - session_id: 세션 ID (선택, 권한 필터링 위해)
        - category: 카테고리 필터 (선택)
        - server: Server 필터 (선택)
    """
    try:
        # 전체 Tool 목록
        all_tools = _router.list_all_tools()
        
        # 필터링
        filtered_tools = all_tools
        
        if category:
            filtered_tools = [t for t in filtered_tools if t["category"] == category]
        
        if server:
            filtered_tools = [t for t in filtered_tools if t["server"] == server]
        
        # 권한 필터링 (세션이 있는 경우)
        if session_id:
            context = _session_manager.get_user_context(session_id)
            if context:
                # TODO: 권한에 따라 Tool 필터링
                pass
        
        return ToolListResponse(
            tools=filtered_tools,
            total=len(filtered_tools)
        )
    
    except Exception as e:
        logger.error(f"List tools failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/api/tools/{tool_name}", response_model=ToolInfo)
async def get_tool_info(tool_name: str):
    """Tool 상세 정보"""
    metadata = _router.get_tool_metadata(tool_name)
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_name}"
        )
    
    return ToolInfo(**metadata)


# ==================== Server 관리 API ====================

@router.get("/api/servers", response_model=ServerListResponse)
async def list_servers():
    """Server 목록"""
    try:
        servers = _server_manager.list_servers()
        
        return ServerListResponse(
            servers=servers,
            total=len(servers)
        )
    
    except Exception as e:
        logger.error(f"List servers failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/api/servers/{server_name}", response_model=ServerInfo)
async def get_server_info(server_name: str):
    """Server 정보"""
    info = _server_manager.get_server_info(server_name)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server not found: {server_name}"
        )
    
    return ServerInfo(**info)


@router.post("/api/servers/action", response_model=ServerActionResponse)
async def server_action(request: ServerActionRequest):
    """
    Server 액션 (start/stop/restart)
    
    Args:
        request: {
            "action": "start" | "stop" | "restart",
            "server_name": "auth_server"
        }
    """
    try:
        action = request.action
        server_name = request.server_name
        
        # 권한 확인 (TODO: admin만 가능)
        
        if action == "start":
            success = _server_manager.start_server(server_name)
            message = f"Server started: {server_name}" if success else "Failed to start server"
        
        elif action == "stop":
            success = _server_manager.stop_server(server_name)
            message = f"Server stopped: {server_name}" if success else "Failed to stop server"
        
        elif action == "restart":
            success = _server_manager.restart_server(server_name)
            message = f"Server restarted: {server_name}" if success else "Failed to restart server"
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}"
            )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )
        
        # Server 정보
        info = _server_manager.get_server_info(server_name)
        
        return ServerActionResponse(
            status="success",
            message=message,
            server_info=ServerInfo(**info) if info else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Server action failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== 헬스 체크 ====================

@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "mcp-host",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "MCP Host",
        "version": "1.0.0",
        "endpoints": {
            "sessions": "/api/sessions",
            "tools": "/api/tools",
            "servers": "/api/servers",
            "docs": "/docs"
        }
    }
```

### 5.2 api/middleware.py - 미들웨어

```python
# mcp-host/api/middleware.py
"""
API 미들웨어

로깅, CORS, 에러 처리
"""

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        """요청 처리"""
        # 요청 시작
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[{request_id}]"
        )
        
        # 요청 처리
        try:
            response = await call_next(request)
            
            # 실행 시간 계산
            duration = (time.time() - start_time) * 1000
            
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[{request_id}] - {response.status_code} ({duration:.2f}ms)"
            )
            
            # 응답 헤더 추가
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration:.2f}ms"
            
            return response
        
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[{request_id}] - {str(e)} ({duration:.2f}ms)",
                exc_info=True
            )
            
            raise


def setup_cors(app):
    """CORS 설정"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # PoC용, 실제 운영에서는 제한 필요
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

### 5.3 main.py - 메인 애플리케이션

```python
# mcp-host/main.py
"""
MCP Host 메인 애플리케이션
"""

import sys
from pathlib import Path

# PYTHONPATH 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import logging
import signal
import asyncio

from config import config
from core.server_manager import ServerManager
from core.session_manager import SessionManager
from core.router import Router
from core.executor import ToolExecutor

from api.routes import router, set_dependencies
from api.middleware import LoggingMiddleware, setup_cors

from shared.logging_config import setup_logging

# 로거 설정
logger = setup_logging(
    component="mcp_host",
    log_dir=Path("/app/poc/mcps/data/logs/mcp-host"),
    level=config.host.log_level
)

# FastAPI 앱 생성
app = FastAPI(
    title="MCP Host API",
    description="Model Context Protocol Host",
    version="1.0.0"
)

# 전역 관리자들
server_manager = None
session_manager = None
tool_router = None
executor = None


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작"""
    global server_manager, session_manager, tool_router, executor
    
    logger.info("=" * 50)
    logger.info("MCP Host starting...")
    logger.info("=" * 50)
    
    try:
        # 1. 관리자 초기화
        logger.info("Initializing managers...")
        
        server_manager = ServerManager(config)
        session_manager = SessionManager(session_timeout=3600)
        tool_router = Router(config)
        executor = ToolExecutor(server_manager)
        
        # 2. API 의존성 설정
        set_dependencies(session_manager, tool_router, executor, server_manager)
        
        # 3. Server 시작
        logger.info("Starting MCP servers...")
        server_manager.start_all()
        
        # 4. 세션 정리 태스크 시작
        asyncio.create_task(session_cleanup_task())
        
        logger.info("=" * 50)
        logger.info("MCP Host started successfully")
        logger.info(f"API available at: http://{config.host.host}:{config.host.port}")
        logger.info(f"Docs available at: http://{config.host.host}:{config.host.port}/docs")
        logger.info("=" * 50)
    
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료"""
    logger.info("=" * 50)
    logger.info("MCP Host shutting down...")
    logger.info("=" * 50)
    
    try:
        # Server 종료
        if server_manager:
            server_manager.stop_all()
        
        logger.info("MCP Host stopped")
    
    except Exception as e:
        logger.error(f"Shutdown error: {e}", exc_info=True)


async def session_cleanup_task():
    """세션 정리 태스크 (주기적)"""
    while True:
        try:
            await asyncio.sleep(300)  # 5분마다
            session_manager.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")


# 라우터 등록
app.include_router(router)

# 미들웨어 설정
app.add_middleware(LoggingMiddleware)
setup_cors(app)


# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc)
            }
        }
    )


def signal_handler(signum, frame):
    """시그널 핸들러"""
    logger.info(f"Received signal: {signum}")
    
    if server_manager:
        server_manager.stop_all()
    
    sys.exit(0)


def main():
    """메인 함수"""
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Uvicorn 실행
    uvicorn.run(
        app,
        host=config.host.host,
        port=config.host.port,
        log_level=config.host.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()
```

### 5.4 requirements.txt

```txt
# mcp-host/requirements.txt

# 웹 프레임워크
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6

# 프로젝트 공통 의존성
# (루트 requirements.txt 참조)
```

***

## 6. 배포 및 운영

### 6.1 시작 스크립트

```bash
#!/bin/bash
# mcp-host/start.sh
# MCP Host 시작

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/app/poc/mcps/data/logs/mcp-host"
PID_FILE="/tmp/mcp_host.pid"

# 이미 실행 중인지 확인
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "MCP Host is already running (PID: $PID)"
        exit 1
    else
        rm "$PID_FILE"
    fi
fi

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

# 환경 변수 로드
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
fi

# 가상 환경 활성화
source "$SCRIPT_DIR/venv/bin/activate"

# MCP Host 시작
echo "Starting MCP Host..."

nohup python "$SCRIPT_DIR/main.py" > "$LOG_DIR/mcp_host.out" 2>&1 &
PID=$!

echo $PID > "$PID_FILE"

echo "✅ MCP Host started (PID: $PID)"
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "Log: $LOG_DIR/mcp_host.out"
```

```bash
#!/bin/bash
# mcp-host/stop.sh
# MCP Host 중지

PID_FILE="/tmp/mcp_host.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "MCP Host is not running"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ps -p $PID > /dev/null 2>&1; then
    echo "Stopping MCP Host (PID: $PID)..."
    kill $PID
    
    # 종료 대기
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # 강제 종료
    if ps -p $PID > /dev/null 2>&1; then
        echo "Force killing MCP Host..."
        kill -9 $PID
    fi
    
    rm "$PID_FILE"
    echo "✅ MCP Host stopped"
else
    echo "Process $PID not found"
    rm "$PID_FILE"
    exit 1
fi
```

### 6.2 Systemd 서비스

```ini
# /etc/systemd/system/mcp-host.service

[Unit]
Description=MCP Host Service
After=network.target mariadb.service

[Service]
Type=simple
User=mcps
Group=mcps
WorkingDirectory=/app/poc/mcps/mcp-host

Environment="PYTHONPATH=/app/poc/mcps"
Environment="DB_HOST=localhost"
Environment="DB_PORT=3306"
Environment="DB_NAME=mcps_db"
Environment="DB_USER=mcps_user"
Environment="DB_PASSWORD=your_password"
Environment="ES_HOST=localhost:9200"
Environment="HOST=0.0.0.0"
Environment="PORT=8000"
Environment="LOG_LEVEL=INFO"

ExecStart=/app/poc/mcps/mcp-host/venv/bin/python main.py

Restart=always
RestartSec=10

StandardOutput=append:/app/poc/mcps/data/logs/mcp-host/mcp_host.log
StandardError=append:/app/poc/mcps/data/logs/mcp-host/mcp_host_error.log

[Install]
WantedBy=multi-user.target
```

```bash
#!/bin/bash
# mcp-host/install_systemd.sh
# Systemd 서비스 설치

SERVICE_FILE="/etc/systemd/system/mcp-host.service"

echo "Installing MCP Host systemd service..."

# 서비스 파일 생성 (위 내용)
# ...

# 서비스 활성화
systemctl daemon-reload
systemctl enable mcp-host.service

echo "✅ Service installed"
echo ""
echo "Start with: systemctl start mcp-host"
echo "Status: systemctl status mcp-host"
echo "Logs: journalctl -u mcp-host -f"
```

### 6.3 테스트

```python
# mcp-host/tests/test_api.py
"""
API 테스트
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "MCP Host"


def test_health():
    """헬스 체크 테스트"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_create_session():
    """세션 생성 테스트"""
    response = client.post(
        "/api/sessions",
        json={"user_id": "U001"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["user_id"] == "U001"
    
    return data["session_id"]


def test_list_tools():
    """Tool 목록 테스트"""
    response = client.get("/api/tools/list")
    
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert data["total"] > 0


def test_execute_tool():
    """Tool 실행 테스트"""
    # 1. 세션 생성
    session_response = client.post(
        "/api/sessions",
        json={"user_id": "U002"}
    )
    session_id = session_response.json()["session_id"]
    
    # 2. Tool 실행
    response = client.post(
        "/api/tools/execute",
        json={
            "session_id": session_id,
            "tool": "search_documents",
            "arguments": {
                "query": "AI",
                "limit": 5
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "execution_time_ms" in data


def test_invalid_session():
    """잘못된 세션 테스트"""
    response = client.post(
        "/api/tools/execute",
        json={
            "session_id": "invalid_session",
            "tool": "search_documents",
            "arguments": {}
        }
    )
    
    assert response.status_code == 401


def test_invalid_tool():
    """존재하지 않는 Tool 테스트"""
    # 세션 생성
    session_response = client.post(
        "/api/sessions",
        json={"user_id": "U002"}
    )
    session_id = session_response.json()["session_id"]
    
    # 존재하지 않는 Tool 실행
    response = client.post(
        "/api/tools/execute",
        json={
            "session_id": session_id,
            "tool": "nonexistent_tool",
            "arguments": {}
        }
    )
    
    assert response.status_code == 404


def test_list_servers():
    """Server 목록 테스트"""
    response = client.get("/api/servers")
    
    assert response.status_code == 200
    data = response.json()
    assert "servers" in data
    assert data["total"] > 0
```

### 6.4 통합 테스트

```python
# mcp-host/tests/test_integration.py
"""
통합 테스트

전체 워크플로우 테스트
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_full_workflow():
    """전체 워크플로우 테스트"""
    
    # 1. 세션 생성
    session_response = client.post(
        "/api/sessions",
        json={"user_id": "U002"}
    )
    
    assert session_response.status_code == 201
    session_id = session_response.json()["session_id"]
    
    # 2. Tool 목록 조회
    tools_response = client.get("/api/tools/list")
    assert tools_response.status_code == 200
    tools = tools_response.json()["tools"]
    assert len(tools) > 0
    
    # 3. 문서 검색
    search_response = client.post(
        "/api/tools/execute",
        json={
            "session_id": session_id,
            "tool": "search_documents",
            "arguments": {
                "query": "MCP",
                "limit": 5
            }
        }
    )
    
    assert search_response.status_code == 200
    search_result = search_response.json()
    assert search_result["status"] == "success"
    assert "results" in search_result["data"]
    
    # 4. 문서 조회
    if search_result["data"]["results"]:
        doc_id = search_result["data"]["results"][0]["doc_id"]
        
        get_response = client.post(
            "/api/tools/execute",
            json={
                "session_id": session_id,
                "tool": "get_document",
                "arguments": {
                    "doc_id": doc_id
                }
            }
        )
        
        assert get_response.status_code == 200
        get_result = get_response.json()
        assert get_result["status"] == "success"
        assert get_result["data"]["doc_id"] == doc_id
    
    # 5. 세션 삭제
    delete_response = client.delete(f"/api/sessions/{session_id}")
    assert delete_response.status_code == 200


def test_permission_workflow():
    """권한 워크플로우 테스트"""
    
    # 1. junior 사용자 세션
    session_response = client.post(
        "/api/sessions",
        json={"user_id": "U001"}  # junior
    )
    session_id = session_response.json()["session_id"]
    
    # 2. team 문서 조회 시도 (권한 없음)
    response = client.post(
        "/api/tools/execute",
        json={
            "session_id": session_id,
            "tool": "get_document",
            "arguments": {
                "doc_id": "DOC004"  # team 문서
            }
        }
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "error"
    assert "PERMISSION_DENIED" in result["error"]["code"]
    
    # 3. 접근 권한 요청
    request_response = client.post(
        "/api/tools/execute",
        json={
            "session_id": session_id,
            "tool": "request_access",
            "arguments": {
                "doc_id": "DOC004",
                "reason": "프로젝트 수행을 위해 필요합니다."
            }
        }
    )
    
    assert request_response.status_code == 200
    request_result = request_response.json()
    assert request_result["status"] == "success"
```

### 6.5 성능 테스트

```python
# mcp-host/tests/test_performance.py
"""
성능 테스트
"""

import time
import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_concurrent_requests():
    """동시 요청 테스트"""
    
    # 세션 생성
    session_response = client.post(
        "/api/sessions",
        json={"user_id": "U002"}
    )
    session_id = session_response.json()["session_id"]
    
    # 동시 요청 (10개)
    start_time = time.time()
    
    responses = []
    for i in range(10):
        response = client.post(
            "/api/tools/execute",
            json={
                "session_id": session_id,
                "tool": "search_documents",
                "arguments": {
                    "query": f"test{i}",
                    "limit": 5
                }
            }
        )
        responses.append(response)
    
    duration = time.time() - start_time
    
    # 검증
    for response in responses:
        assert response.status_code == 200
    
    print(f"\n10 concurrent requests completed in {duration:.2f}s")
    print(f"Average: {duration/10:.2f}s per request")


def test_response_time():
    """응답 시간 테스트"""
    
    # 세션 생성
    session_response = client.post(
        "/api/sessions",
        json={"user_id": "U002"}
    )
    session_id = session_response.json()["session_id"]
    
    # 10회 반복 측정
    times = []
    
    for _ in range(10):
        start = time.time()
        
        response = client.post(
            "/api/tools/execute",
            json={
                "session_id": session_id,
                "tool": "search_documents",
                "arguments": {
                    "query": "AI",
                    "limit": 5
                }
            }
        )
        
        duration = time.time() - start
        times.append(duration)
        
        assert response.status_code == 200
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    
    print(f"\nResponse time statistics:")
    print(f"  Average: {avg_time*1000:.2f}ms")
    print(f"  Min: {min_time*1000:.2f}ms")
    print(f"  Max: {max_time*1000:.2f}ms")
    
    # 평균 응답 시간 1초 이하
    assert avg_time < 1.0
```

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

"""
MCP 프로토콜 구현
=================

JSON-RPC 2.0 over STDIO 기반 MCP 프로토콜을 구현합니다.

특징:
- JSON-RPC 2.0 스펙 준수
- STDIO 통신 (stdin/stdout)
- Tool, Resource, Prompt 지원
- 양방향 통신 (Request/Response/Notification)

메시지 흐름:
1. Host -> Server: initialize
2. Server -> Host: initialize result (capabilities)
3. Host -> Server: tools/list, resources/list
4. Host -> Server: tools/call with arguments
5. Server -> Host: result or error

사용 예:
    from shared.mcp_protocol import MCPServer, Tool, ToolResult
    
    server = MCPServer(name="my-server", version="1.0.0")
    
    @server.tool()
    def my_tool(arg1: str, arg2: int) -> str:
        return f"Result: {arg1}, {arg2}"
    
    server.run()
"""

from typing import Any, Optional, Dict, List, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import sys
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)


# ===========================================
# JSON-RPC 에러 코드
# ===========================================

class ErrorCode(Enum):
    """JSON-RPC 2.0 에러 코드"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP 커스텀 에러
    TOOL_NOT_FOUND = -32000
    RESOURCE_NOT_FOUND = -32001
    PERMISSION_DENIED = -32002
    EXECUTION_ERROR = -32003


# ===========================================
# 메시지 타입
# ===========================================

@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 요청"""
    method: str
    id: Optional[Union[str, int]] = None
    params: Optional[Dict[str, Any]] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> Dict:
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
        }
        if self.id is not None:
            result["id"] = self.id
        if self.params is not None:
            result["params"] = self.params
        return result


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 응답"""
    id: Optional[Union[str, int]]
    result: Optional[Any] = None
    error: Optional[Dict] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> Dict:
        response = {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
        }
        if self.error is not None:
            response["error"] = self.error
        else:
            response["result"] = self.result
        return response


@dataclass
class JSONRPCError:
    """JSON-RPC 2.0 에러"""
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict:
        error = {
            "code": self.code,
            "message": self.message,
        }
        if self.data is not None:
            error["data"] = self.data
        return error


# ===========================================
# MCP 메시지 타입
# ===========================================

@dataclass
class Tool:
    """MCP Tool 정의"""
    name: str
    description: str
    inputSchema: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema,
        }


@dataclass
class ToolResult:
    """Tool 실행 결과"""
    content: List[Dict[str, Any]]
    isError: bool = False
    
    @classmethod
    def text(cls, text: str, is_error: bool = False) -> "ToolResult":
        """텍스트 결과 생성"""
        return cls(
            content=[{"type": "text", "text": text}],
            isError=is_error
        )
    
    @classmethod
    def json(cls, data: Any, is_error: bool = False) -> "ToolResult":
        """JSON 결과 생성"""
        return cls(
            content=[{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}],
            isError=is_error
        )
    
    @classmethod
    def error(cls, message: str) -> "ToolResult":
        """에러 결과 생성"""
        return cls(
            content=[{"type": "text", "text": message}],
            isError=True
        )
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "isError": self.isError,
        }


@dataclass
class Resource:
    """MCP Resource 정의"""
    uri: str
    name: str
    description: str = ""
    mimeType: str = "text/plain"
    
    def to_dict(self) -> Dict:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mimeType,
        }


@dataclass
class ResourceContent:
    """Resource 내용"""
    uri: str
    text: Optional[str] = None
    blob: Optional[str] = None  # base64 encoded
    mimeType: str = "text/plain"
    
    def to_dict(self) -> Dict:
        result = {
            "uri": self.uri,
            "mimeType": self.mimeType,
        }
        if self.text is not None:
            result["text"] = self.text
        if self.blob is not None:
            result["blob"] = self.blob
        return result


@dataclass
class Prompt:
    """MCP Prompt 정의"""
    name: str
    description: str
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
        }


@dataclass
class ServerCapabilities:
    """서버 기능"""
    tools: Optional[Dict] = None
    resources: Optional[Dict] = None
    prompts: Optional[Dict] = None
    logging: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        caps = {}
        if self.tools:
            caps["tools"] = self.tools
        if self.resources:
            caps["resources"] = self.resources
        if self.prompts:
            caps["prompts"] = self.prompts
        if self.logging:
            caps["logging"] = self.logging
        return caps


@dataclass
class ServerInfo:
    """서버 정보"""
    name: str
    version: str
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
        }


# ===========================================
# STDIO 통신
# ===========================================

class StdioTransport:
    """STDIO 통신 처리"""
    
    def __init__(self):
        self._running = False
    
    async def read_message(self) -> Optional[Dict]:
        """stdin에서 메시지 읽기"""
        try:
            loop = asyncio.get_event_loop()
            line = await loop.run_in_executor(None, sys.stdin.readline)
            
            if not line:
                return None
            
            line = line.strip()
            if not line:
                return None
            
            return json.loads(line)
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return None
        except Exception as e:
            logger.error(f"Read error: {e}")
            return None
    
    def write_message(self, message: Dict):
        """stdout으로 메시지 쓰기"""
        try:
            line = json.dumps(message, ensure_ascii=False)
            print(line, flush=True)
        except Exception as e:
            logger.error(f"Write error: {e}")
    
    def send_response(self, response: JSONRPCResponse):
        """응답 전송"""
        self.write_message(response.to_dict())
    
    def send_notification(self, method: str, params: Optional[Dict] = None):
        """알림 전송 (id 없음)"""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            notification["params"] = params
        self.write_message(notification)


# ===========================================
# MCP 서버
# ===========================================

class MCPServer:
    """
    MCP 서버 구현
    
    Example:
        server = MCPServer(name="document-server", version="1.0.0")
        
        @server.tool()
        def search_documents(query: str, limit: int = 10) -> str:
            # 검색 로직
            return json.dumps(results)
        
        @server.resource("doc://{doc_id}")
        def get_document(doc_id: str) -> str:
            return document_content
        
        server.run()
    """
    
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        capabilities: Optional[ServerCapabilities] = None
    ):
        """
        초기화
        
        Args:
            name: 서버 이름
            version: 서버 버전
            capabilities: 서버 기능 (None이면 자동 설정)
        """
        self.name = name
        self.version = version
        self.capabilities = capabilities
        
        # 등록된 핸들러
        self._tools: Dict[str, Dict] = {}
        self._resources: Dict[str, Dict] = {}
        self._prompts: Dict[str, Dict] = {}
        
        # 메시지 핸들러
        self._handlers: Dict[str, Callable] = {}
        
        # 전송 레이어
        self.transport = StdioTransport()
        
        # 기본 핸들러 등록
        self._register_default_handlers()
        
        # 상태
        self._initialized = False
        self._running = False
        
        logger.info(f"MCPServer created: {name} v{version}")
    
    def _register_default_handlers(self):
        """기본 메시지 핸들러 등록"""
        self._handlers["initialize"] = self._handle_initialize
        self._handlers["initialized"] = self._handle_initialized
        self._handlers["tools/list"] = self._handle_tools_list
        self._handlers["tools/call"] = self._handle_tools_call
        self._handlers["resources/list"] = self._handle_resources_list
        self._handlers["resources/read"] = self._handle_resources_read
        self._handlers["prompts/list"] = self._handle_prompts_list
        self._handlers["prompts/get"] = self._handle_prompts_get
        self._handlers["ping"] = self._handle_ping
    
    # ===========================================
    # Tool 등록
    # ===========================================
    
    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Dict] = None
    ):
        """
        Tool 데코레이터
        
        Args:
            name: Tool 이름 (기본: 함수명)
            description: 설명 (기본: docstring)
            schema: 입력 스키마 (기본: 함수 시그니처에서 추론)
        
        Example:
            @server.tool()
            def search(query: str, limit: int = 10) -> str:
                '''문서를 검색합니다.'''
                return json.dumps(results)
            
            @server.tool(name="advanced_search")
            def search_v2(query: str) -> str:
                return results
        """
        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or f"Tool: {tool_name}"
            
            # 스키마 추론
            if schema:
                input_schema = schema
            else:
                input_schema = self._infer_schema(func)
            
            self._tools[tool_name] = {
                "name": tool_name,
                "description": tool_desc.strip(),
                "inputSchema": input_schema,
                "handler": func
            }
            
            logger.debug(f"Tool registered: {tool_name}")
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def add_tool(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        schema: Optional[Dict] = None
    ):
        """
        프로그래밍 방식으로 Tool 추가
        
        Args:
            name: Tool 이름
            handler: 핸들러 함수
            description: 설명
            schema: 입력 스키마
        """
        self._tools[name] = {
            "name": name,
            "description": description or f"Tool: {name}",
            "inputSchema": schema or self._infer_schema(handler),
            "handler": handler
        }
        logger.debug(f"Tool added: {name}")
    
    def _infer_schema(self, func: Callable) -> Dict:
        """함수 시그니처에서 JSON Schema 추론"""
        import inspect
        
        sig = inspect.signature(func)
        hints = getattr(func, "__annotations__", {})
        
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue
            
            param_type = hints.get(param_name, str)
            json_type = self._python_type_to_json(param_type)
            
            properties[param_name] = {"type": json_type}
            
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
            else:
                properties[param_name]["default"] = param.default
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _python_type_to_json(self, python_type) -> str:
        """Python 타입을 JSON Schema 타입으로 변환"""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        
        # Generic types (List[str] 등) 처리
        origin = getattr(python_type, "__origin__", None)
        if origin is not None:
            if origin is list:
                return "array"
            if origin is dict:
                return "object"
        
        return type_map.get(python_type, "string")
    
    # ===========================================
    # Resource 등록
    # ===========================================
    
    def resource(
        self,
        uri_template: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        mime_type: str = "text/plain"
    ):
        """
        Resource 데코레이터
        
        Args:
            uri_template: URI 템플릿 (예: "doc://{doc_id}")
            name: Resource 이름
            description: 설명
            mime_type: MIME 타입
        
        Example:
            @server.resource("doc://{doc_id}")
            def get_document(doc_id: str) -> str:
                return document_content
        """
        def decorator(func: Callable):
            resource_name = name or func.__name__
            resource_desc = description or func.__doc__ or f"Resource: {resource_name}"
            
            self._resources[uri_template] = {
                "uri": uri_template,
                "name": resource_name,
                "description": resource_desc.strip(),
                "mimeType": mime_type,
                "handler": func
            }
            
            logger.debug(f"Resource registered: {uri_template}")
            
            return func
        
        return decorator
    
    # ===========================================
    # Prompt 등록
    # ===========================================
    
    def prompt(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        arguments: Optional[List[Dict]] = None
    ):
        """
        Prompt 데코레이터
        
        Example:
            @server.prompt()
            def summarize_document(doc_id: str, length: str = "short") -> List[Dict]:
                return [{"role": "user", "content": f"Summarize document {doc_id}..."}]
        """
        def decorator(func: Callable):
            prompt_name = name or func.__name__
            prompt_desc = description or func.__doc__ or f"Prompt: {prompt_name}"
            
            self._prompts[prompt_name] = {
                "name": prompt_name,
                "description": prompt_desc.strip(),
                "arguments": arguments or [],
                "handler": func
            }
            
            logger.debug(f"Prompt registered: {prompt_name}")
            
            return func
        
        return decorator
    
    # ===========================================
    # 메시지 핸들러
    # ===========================================
    
    async def _handle_initialize(
        self,
        request_id: Union[str, int],
        params: Dict
    ) -> JSONRPCResponse:
        """initialize 요청 처리"""
        logger.info(f"Initialize request from: {params.get('clientInfo', {})}")
        
        # 기능 설정
        capabilities = self.capabilities or ServerCapabilities(
            tools={"listChanged": True} if self._tools else None,
            resources={"listChanged": True, "subscribe": True} if self._resources else None,
            prompts={"listChanged": True} if self._prompts else None,
            logging={}
        )
        
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": capabilities.to_dict(),
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }
        
        return JSONRPCResponse(id=request_id, result=result)
    
    async def _handle_initialized(
        self,
        request_id: Union[str, int],
        params: Dict
    ) -> Optional[JSONRPCResponse]:
        """initialized 알림 처리"""
        self._initialized = True
        logger.info("Server initialized")
        return None  # 알림에는 응답 없음
    
    async def _handle_tools_list(
        self,
        request_id: Union[str, int],
        params: Dict
    ) -> JSONRPCResponse:
        """tools/list 요청 처리"""
        tools = [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"]
            }
            for t in self._tools.values()
        ]
        
        return JSONRPCResponse(id=request_id, result={"tools": tools})
    
    async def _handle_tools_call(
        self,
        request_id: Union[str, int],
        params: Dict
    ) -> JSONRPCResponse:
        """tools/call 요청 처리"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self._tools:
            error = JSONRPCError(
                code=ErrorCode.TOOL_NOT_FOUND.value,
                message=f"Tool not found: {tool_name}"
            )
            return JSONRPCResponse(id=request_id, error=error.to_dict())
        
        tool = self._tools[tool_name]
        handler = tool["handler"]
        
        try:
            # 핸들러 호출
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)
            
            # 결과 변환
            if isinstance(result, ToolResult):
                return JSONRPCResponse(id=request_id, result=result.to_dict())
            elif isinstance(result, dict):
                return JSONRPCResponse(id=request_id, result=ToolResult.json(result).to_dict())
            else:
                return JSONRPCResponse(id=request_id, result=ToolResult.text(str(result)).to_dict())
        
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            error = JSONRPCError(
                code=ErrorCode.EXECUTION_ERROR.value,
                message=str(e)
            )
            return JSONRPCResponse(id=request_id, error=error.to_dict())
    
    async def _handle_resources_list(
        self,
        request_id: Union[str, int],
        params: Dict
    ) -> JSONRPCResponse:
        """resources/list 요청 처리"""
        resources = [
            {
                "uri": r["uri"],
                "name": r["name"],
                "description": r["description"],
                "mimeType": r["mimeType"]
            }
            for r in self._resources.values()
        ]
        
        return JSONRPCResponse(id=request_id, result={"resources": resources})
    
    async def _handle_resources_read(
        self,
        request_id: Union[str, int],
        params: Dict
    ) -> JSONRPCResponse:
        """resources/read 요청 처리"""
        uri = params.get("uri", "")
        
        # URI 매칭
        handler = None
        match_params = {}
        
        for template, resource in self._resources.items():
            matched, extracted = self._match_uri_template(template, uri)
            if matched:
                handler = resource["handler"]
                match_params = extracted
                break
        
        if handler is None:
            error = JSONRPCError(
                code=ErrorCode.RESOURCE_NOT_FOUND.value,
                message=f"Resource not found: {uri}"
            )
            return JSONRPCResponse(id=request_id, error=error.to_dict())
        
        try:
            if asyncio.iscoroutinefunction(handler):
                content = await handler(**match_params)
            else:
                content = handler(**match_params)
            
            if isinstance(content, ResourceContent):
                result = {"contents": [content.to_dict()]}
            else:
                result = {"contents": [{"uri": uri, "text": str(content)}]}
            
            return JSONRPCResponse(id=request_id, result=result)
        
        except Exception as e:
            logger.error(f"Resource read error: {e}")
            error = JSONRPCError(
                code=ErrorCode.EXECUTION_ERROR.value,
                message=str(e)
            )
            return JSONRPCResponse(id=request_id, error=error.to_dict())
    
    async def _handle_prompts_list(
        self,
        request_id: Union[str, int],
        params: Dict
    ) -> JSONRPCResponse:
        """prompts/list 요청 처리"""
        prompts = [
            {
                "name": p["name"],
                "description": p["description"],
                "arguments": p["arguments"]
            }
            for p in self._prompts.values()
        ]
        
        return JSONRPCResponse(id=request_id, result={"prompts": prompts})
    
    async def _handle_prompts_get(
        self,
        request_id: Union[str, int],
        params: Dict
    ) -> JSONRPCResponse:
        """prompts/get 요청 처리"""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if prompt_name not in self._prompts:
            error = JSONRPCError(
                code=ErrorCode.METHOD_NOT_FOUND.value,
                message=f"Prompt not found: {prompt_name}"
            )
            return JSONRPCResponse(id=request_id, error=error.to_dict())
        
        prompt = self._prompts[prompt_name]
        handler = prompt["handler"]
        
        try:
            if asyncio.iscoroutinefunction(handler):
                messages = await handler(**arguments)
            else:
                messages = handler(**arguments)
            
            return JSONRPCResponse(
                id=request_id,
                result={"messages": messages}
            )
        
        except Exception as e:
            logger.error(f"Prompt get error: {e}")
            error = JSONRPCError(
                code=ErrorCode.EXECUTION_ERROR.value,
                message=str(e)
            )
            return JSONRPCResponse(id=request_id, error=error.to_dict())
    
    async def _handle_ping(
        self,
        request_id: Union[str, int],
        params: Dict
    ) -> JSONRPCResponse:
        """ping 요청 처리"""
        return JSONRPCResponse(id=request_id, result={})
    
    def _match_uri_template(
        self,
        template: str,
        uri: str
    ) -> tuple:
        """URI 템플릿 매칭"""
        import re
        
        # {param} 을 정규식 그룹으로 변환
        pattern = template
        param_names = []
        
        for match in re.finditer(r"\{(\w+)\}", template):
            param_names.append(match.group(1))
            pattern = pattern.replace(match.group(0), r"([^/]+)")
        
        pattern = f"^{pattern}$"
        
        match = re.match(pattern, uri)
        if match:
            extracted = dict(zip(param_names, match.groups()))
            return True, extracted
        
        return False, {}
    
    # ===========================================
    # 서버 실행
    # ===========================================
    
    async def _process_message(self, message: Dict):
        """메시지 처리"""
        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params", {})
        
        if method is None:
            # 응답 메시지 (현재는 무시)
            return
        
        handler = self._handlers.get(method)
        
        if handler is None:
            if request_id is not None:
                error = JSONRPCError(
                    code=ErrorCode.METHOD_NOT_FOUND.value,
                    message=f"Method not found: {method}"
                )
                response = JSONRPCResponse(id=request_id, error=error.to_dict())
                self.transport.send_response(response)
            return
        
        try:
            response = await handler(request_id, params)
            
            if response is not None:
                self.transport.send_response(response)
        
        except Exception as e:
            logger.error(f"Handler error: {e}")
            if request_id is not None:
                error = JSONRPCError(
                    code=ErrorCode.INTERNAL_ERROR.value,
                    message=str(e)
                )
                response = JSONRPCResponse(id=request_id, error=error.to_dict())
                self.transport.send_response(response)
    
    async def run_async(self):
        """비동기 서버 실행"""
        self._running = True
        logger.info(f"MCP Server starting: {self.name}")
        
        try:
            while self._running:
                message = await self.transport.read_message()
                
                if message is None:
                    # EOF
                    break
                
                await self._process_message(message)
        
        except KeyboardInterrupt:
            logger.info("Server interrupted")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self._running = False
            logger.info("MCP Server stopped")
    
    def run(self):
        """동기 서버 실행 (메인 진입점)"""
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            pass
    
    def stop(self):
        """서버 중지"""
        self._running = False


# ===========================================
# 유틸리티 함수
# ===========================================

def create_error_response(
    request_id: Union[str, int],
    code: ErrorCode,
    message: str,
    data: Any = None
) -> JSONRPCResponse:
    """에러 응답 생성"""
    error = JSONRPCError(code=code.value, message=message, data=data)
    return JSONRPCResponse(id=request_id, error=error.to_dict())


def parse_request(data: Dict) -> Optional[JSONRPCRequest]:
    """요청 파싱"""
    try:
        return JSONRPCRequest(
            method=data["method"],
            id=data.get("id"),
            params=data.get("params"),
            jsonrpc=data.get("jsonrpc", "2.0")
        )
    except KeyError:
        return None


# ===========================================
# Public API
# ===========================================

__all__ = [
    # 에러 코드
    "ErrorCode",
    
    # 메시지 타입
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    
    # MCP 타입
    "Tool",
    "ToolResult",
    "Resource",
    "ResourceContent",
    "Prompt",
    "ServerCapabilities",
    "ServerInfo",
    
    # 서버
    "MCPServer",
    "StdioTransport",
    
    # 유틸리티
    "create_error_response",
    "parse_request",
]

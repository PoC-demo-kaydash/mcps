"""
Tool 실행

STDIO 통신으로 MCP Server와 JSON-RPC 2.0 프로토콜 통신
"""

import json
import uuid
import asyncio
import time
from typing import Dict, Any, Optional
from shared.logging_config import get_logger

logger = get_logger(__name__)


class ToolExecutor:
    """
    Tool 실행기
    
    JSON-RPC 2.0 프로토콜로 Server와 통신하여 Tool 실행
    """
    
    def __init__(self, server_manager, router):
        """
        Args:
            server_manager: ServerManager 인스턴스
            router: Router 인스턴스
        """
        self.server_manager = server_manager
        self.router = router
        self.logger = logger
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_context: Optional[dict] = None,
        timeout: int = 30
    ) -> dict:
        """
        Tool 실행
        
        Args:
            tool_name: Tool 이름
            arguments: Tool 인자
            user_context: 사용자 컨텍스트 (user_id, user_role, user_team)
            timeout: 타임아웃 (초)
        
        Returns:
            dict: 실행 결과
        """
        start_time = time.time()
        
        try:
            # Tool → Server 매핑
            server_name = self.router.get_server_for_tool(tool_name)
            if not server_name:
                return {
                    "status": "error",
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Tool not found: {tool_name}"
                    },
                    "execution_time": time.time() - start_time
                }
            
            # Server 실행 확인
            if not self.server_manager.is_running(server_name):
                return {
                    "status": "error",
                    "error": {
                        "code": "SERVER_NOT_RUNNING",
                        "message": f"Server not running: {server_name}"
                    },
                    "execution_time": time.time() - start_time
                }
            
            # Server 프로세스 가져오기
            process_info = self.server_manager.processes.get(server_name)
            if not process_info:
                return {
                    "status": "error",
                    "error": {
                        "code": "SERVER_ERROR",
                        "message": f"Server process not found: {server_name}"
                    },
                    "execution_time": time.time() - start_time
                }
            
            process = process_info.process
            
            # JSON-RPC 요청 생성
            request_id = str(uuid.uuid4())
            
            # Tool 인자에 사용자 컨텍스트 추가
            params = {
                "name": tool_name,
                "arguments": arguments
            }
            
            if user_context:
                params["_context"] = user_context
            
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": params
            }
            
            # 요청 전송
            request_str = json.dumps(request) + "\n"
            process.stdin.write(request_str.encode())
            process.stdin.flush()
            
            self.logger.debug(f"Sent request to {server_name}: {tool_name}")
            
            # 응답 수신 (타임아웃 적용)
            response = await self._read_response(process, request_id, timeout)
            
            if response is None:
                return {
                    "status": "error",
                    "error": {
                        "code": "TIMEOUT",
                        "message": f"Tool execution timeout: {tool_name}"
                    },
                    "execution_time": time.time() - start_time
                }
            
            # 응답 처리
            execution_time = time.time() - start_time
            
            if "result" in response:
                return {
                    "status": "success",
                    "result": response["result"],
                    "execution_time": execution_time
                }
            elif "error" in response:
                return {
                    "status": "error",
                    "error": response["error"],
                    "execution_time": execution_time
                }
            else:
                return {
                    "status": "error",
                    "error": {
                        "code": "INVALID_RESPONSE",
                        "message": "Invalid JSON-RPC response"
                    },
                    "execution_time": execution_time
                }
        
        except Exception as e:
            self.logger.error(f"Tool execution error: {e}")
            return {
                "status": "error",
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": str(e)
                },
                "execution_time": time.time() - start_time
            }
    
    async def _read_response(
        self,
        process: Any,
        request_id: str,
        timeout: int
    ) -> Optional[dict]:
        """
        응답 읽기 (타임아웃 적용)
        
        Args:
            process: subprocess.Popen
            request_id: 요청 ID
            timeout: 타임아웃 (초)
        
        Returns:
            dict: JSON-RPC 응답 또는 None
        """
        try:
            # 비동기 읽기
            loop = asyncio.get_event_loop()
            
            # 타임아웃 적용
            line = await asyncio.wait_for(
                loop.run_in_executor(None, process.stdout.readline),
                timeout=timeout
            )
            
            if not line:
                return None
            
            response = json.loads(line.decode().strip())
            
            # 요청 ID 확인
            if response.get("id") != request_id:
                self.logger.warning(f"Response ID mismatch: {response.get('id')} != {request_id}")
                return None
            
            return response
        
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout reading response (request_id: {request_id})")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading response: {e}")
            return None
    
    async def list_tools(self, server_name: str) -> Optional[list]:
        """
        Server의 Tool 목록 조회
        
        Args:
            server_name: Server 이름
        
        Returns:
            list: Tool 목록 또는 None
        """
        try:
            # Router에서 Tool 목록 가져오기
            tools = self.router.list_tools_by_server(server_name)
            return tools
        
        except Exception as e:
            self.logger.error(f"Failed to list tools: {e}")
            return None

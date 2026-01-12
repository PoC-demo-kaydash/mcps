"""
비동기 Tool 템플릿

비동기 작업이 필요한 Tool 생성 시 참고용 템플릿
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_tools.base import AsyncBaseTool, ToolMetadata
from shared.logging_config import get_logger
import asyncio

logger = get_logger(__name__)


class ExampleAsyncTool(AsyncBaseTool):
    """
    예제 비동기 Tool
    
    비동기 작업 (HTTP 요청, 대용량 처리 등)이 필요한 경우 사용
    """
    
    def __init__(self):
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        """
        Tool 메타데이터 정의
        
        Returns:
            ToolMetadata: Tool 메타데이터
        """
        return ToolMetadata(
            name="example_async_tool",
            description="예제 비동기 Tool",
            category="example",
            department="async",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "format": "uri",
                        "description": "요청 URL"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 30,
                        "description": "타임아웃 (초)"
                    }
                },
                "required": ["url"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "data": {"type": "object"}
                }
            },
            examples=[
                {
                    "input": {
                        "url": "https://api.example.com/data",
                        "timeout": 30
                    },
                    "output": {
                        "status": 200,
                        "data": {"result": "success"}
                    }
                }
            ]
        )
    
    async def execute(self, arguments: dict, context: dict = None) -> dict:
        """
        비동기 Tool 실행
        
        Args:
            arguments: 입력 파라미터
            context: 실행 컨텍스트
        
        Returns:
            dict: 실행 결과
        """
        try:
            # 1. 입력 검증
            valid, error = self.validate_arguments(arguments)
            if not valid:
                return self.create_error_response(error, "INVALID_INPUT")
            
            # 2. 파라미터 추출
            url = arguments["url"]
            timeout = arguments.get("timeout", 30)
            
            # 3. 비동기 작업 실행
            logger.info(f"Starting async operation: {url}")
            
            # 예: HTTP 요청 (aiohttp 사용 시)
            # import aiohttp
            # async with aiohttp.ClientSession() as session:
            #     async with session.get(url, timeout=timeout) as response:
            #         data = await response.json()
            
            # 시뮬레이션
            await asyncio.sleep(1)
            data = {"result": "success", "url": url}
            
            # 4. 로깅
            self.log_execution("execute", arguments, context)
            logger.info(f"Async operation completed: {url}")
            
            # 5. 결과 반환
            return self.create_success_response({
                "status": 200,
                "data": data
            })
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout: {url}")
            return self.create_error_response(
                f"Request timeout: {url}",
                "TIMEOUT_ERROR"
            )
        
        except Exception as e:
            logger.error(f"Async tool failed: {e}", exc_info=True)
            return self.create_error_response(
                str(e),
                "EXECUTION_ERROR",
                {"url": arguments.get("url")}
            )


# 비동기 Tool 사용 예제
async def main():
    """비동기 Tool 실행 예제"""
    tool = ExampleAsyncTool()
    
    arguments = {
        "url": "https://api.example.com/data",
        "timeout": 30
    }
    
    context = {
        "user_id": "USER_001",
        "user_role": "engineer"
    }
    
    result = await tool.execute(arguments, context)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())

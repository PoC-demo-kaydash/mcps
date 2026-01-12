"""
동기 Tool 템플릿

새로운 Tool 생성 시 참고용 템플릿
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_tools.base import BaseTool, ToolMetadata
from shared.database import DatabaseManager
from shared.logging_config import get_logger

logger = get_logger(__name__)


class ExampleTool(BaseTool):
    """
    예제 Tool
    
    Tool의 주요 기능을 간단히 설명
    """
    
    def __init__(self, db: DatabaseManager = None):
        """
        Args:
            db: DatabaseManager 인스턴스 (필요 시)
        """
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        """
        Tool 메타데이터 정의
        
        Returns:
            ToolMetadata: Tool 메타데이터
        """
        return ToolMetadata(
            name="example_tool",
            description="예제 Tool (간단한 설명)",
            category="example",  # auth, document, search, version, audit, utils 등
            department="core",   # core, utils, custom 등
            version="1.0.0",
            required_permissions=["document:read"],  # 필요한 권한 목록
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "첫 번째 파라미터 설명"
                    },
                    "param2": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                        "description": "두 번째 파라미터 (옵션)"
                    }
                },
                "required": ["param1"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "count": {"type": "integer"}
                }
            },
            examples=[
                {
                    "input": {
                        "param1": "test",
                        "param2": 5
                    },
                    "output": {
                        "result": "success",
                        "count": 5
                    }
                }
            ],
            enabled=True
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """
        Tool 실행
        
        Args:
            arguments: 입력 파라미터
            context: 실행 컨텍스트 (user_id, user_role, user_team 등)
        
        Returns:
            dict: 실행 결과
                {
                    "status": "success" | "error",
                    "data": {...} | None,
                    "error": {"code": "...", "message": "..."} | None
                }
        """
        try:
            # 1. 입력 검증
            valid, error = self.validate_arguments(arguments)
            if not valid:
                return self.create_error_response(error, "INVALID_INPUT")
            
            # 2. 파라미터 추출
            param1 = arguments["param1"]
            param2 = arguments.get("param2", 10)
            
            # 3. 권한 확인 (필요 시)
            if context:
                user_role = context.get("user_role", "")
                authorized, error = self.check_permission(user_role, self.metadata.required_permissions)
                if not authorized:
                    return self.create_error_response(error, "PERMISSION_DENIED")
            
            # 4. 비즈니스 로직 실행
            # TODO: 실제 로직 구현
            result = f"Processed: {param1}"
            count = param2
            
            # 5. 로깅
            self.log_execution("execute", arguments, context)
            logger.info(f"Tool executed: {self.metadata.name}")
            
            # 6. 결과 반환
            return self.create_success_response({
                "result": result,
                "count": count
            })
        
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return self.create_error_response(
                str(e),
                "EXECUTION_ERROR",
                {"param1": arguments.get("param1")}
            )


# Tool 등록 (자동 로드 시)
if __name__ == "__main__":
    from mcp_tools.registry import register_tool
    
    tool = ExampleTool()
    register_tool(tool)
    print(f"Registered: {tool.metadata.name}")

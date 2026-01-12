"""
Tool 기본 클래스

모든 Tool은 BaseTool 또는 AsyncBaseTool을 상속받아야 함
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class ToolMetadata:
    """
    Tool 메타데이터
    
    Tool의 이름, 설명, 권한, 스키마 등을 정의
    """
    name: str
    description: str
    category: str
    department: str
    version: str
    required_permissions: List[str]
    input_schema: dict
    output_schema: dict
    examples: List[dict] = field(default_factory=list)
    enabled: bool = True


class BaseTool(ABC):
    """
    Tool 기본 클래스
    
    모든 동기 Tool은 이 클래스를 상속받아야 함
    
    Example:
        class MyTool(BaseTool):
            def _define_metadata(self) -> ToolMetadata:
                return ToolMetadata(...)
            
            def execute(self, arguments: dict, context: dict = None) -> dict:
                # 구현
                return self.create_success_response(data)
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
            ToolMetadata: Tool 메타데이터
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
                "data": {...}  # status가 success일 때
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
        schema = self.metadata.input_schema
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # 필수 필드 확인
        for field in required:
            if field not in arguments:
                return False, f"Missing required field: {field}"
        
        # 타입 확인 (간단한 버전)
        for field, value in arguments.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type:
                    if expected_type == "string" and not isinstance(value, str):
                        return False, f"Field '{field}' must be a string"
                    elif expected_type == "integer" and not isinstance(value, int):
                        return False, f"Field '{field}' must be an integer"
                    elif expected_type == "number" and not isinstance(value, (int, float)):
                        return False, f"Field '{field}' must be a number"
                    elif expected_type == "boolean" and not isinstance(value, bool):
                        return False, f"Field '{field}' must be a boolean"
                    elif expected_type == "array" and not isinstance(value, list):
                        return False, f"Field '{field}' must be an array"
                    elif expected_type == "object" and not isinstance(value, dict):
                        return False, f"Field '{field}' must be an object"
        
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
        # 권한이 필요 없는 경우
        if not required_permissions:
            return True, None
        
        # shared.permissions 사용
        try:
            from shared.permissions import PermissionEngine
            
            perm_engine = PermissionEngine()
            
            # 각 권한 확인
            for permission in required_permissions:
                if ":" in permission:
                    resource, action = permission.split(":", 1)
                    has_permission = perm_engine.can_perform_action(
                        user_role,
                        action,
                        resource
                    )
                    
                    if not has_permission:
                        return False, f"Permission denied: {user_role} lacks {permission}"
            
            return True, None
        
        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            return False, f"Permission check error: {str(e)}"
    
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
        user_id = context.get('user_id', 'unknown')
        status = result.get('status', 'unknown')
        
        self.logger.info(
            f"Tool executed: {self.metadata.name} "
            f"by {user_id} "
            f"in {execution_time_ms:.2f}ms "
            f"status={status}"
        )
        
        if status == "error":
            error = result.get("error", {})
            self.logger.warning(
                f"Tool error: {error.get('message', 'Unknown error')}"
            )


class AsyncBaseTool(BaseTool):
    """
    비동기 Tool 기본 클래스
    
    비동기 실행이 필요한 Tool은 이 클래스를 상속받아야 함
    """
    
    @abstractmethod
    async def execute(
        self,
        arguments: dict,
        context: Optional[dict] = None
    ) -> dict:
        """비동기 실행 (필수 구현)"""
        pass


def measure_execution_time(func):
    """
    실행 시간 측정 데코레이터
    
    Example:
        @measure_execution_time
        def execute(self, arguments, context):
            ...
    """
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        result = func(self, *args, **kwargs)
        execution_time = (time.time() - start_time) * 1000
        
        # context가 있으면 로그 기록
        if len(args) >= 2:
            context = args[1]
            if context:
                self.log_execution(context, args[0], result, execution_time)
        
        return result
    
    return wrapper

"""
Employee Tool - 직원 정보 관리 Tool

직원 정보 조회, 수정, 이력 관리 기능 제공
"""

from typing import Dict, Any
from mcp_tools.base import BaseTool
from shared.database import DatabaseManager
from shared.permissions import PermissionEngine
from shared.logging_config import get_logger

logger = get_logger("employee_tool")


class EmployeeTool(BaseTool):
    """
    직원 정보 관리 Tool
    
    기능:
    - 직원 정보 조회
    - 직원 정보 수정
    - 직원 이력 조회
    """
    
    def __init__(self):
        super().__init__(
            name="employee_tool",
            description="직원 정보 조회 및 관리",
            category="custom",
            department="hr"
        )
        self.db = None
        self.perm_engine = PermissionEngine()
    
    async def initialize(self, config: dict):
        """초기화"""
        self.db = DatabaseManager(config)
        logger.info("EmployeeTool initialized")
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool 실행
        
        Args:
            params: {
                "employee_id": str,  # 직원 ID
                "action": str,       # get/update/history (선택)
                "data": dict         # update 시 수정 데이터 (선택)
            }
            context: {
                "user_id": str
            }
        
        Returns:
            {
                "success": bool,
                "data": dict,
                "error": str (optional)
            }
        """
        try:
            # 1. 파라미터 검증
            if not self.validate_params(params):
                return {
                    "success": False,
                    "error": "Invalid parameters: employee_id is required"
                }
            
            # 2. 권한 체크
            user_id = context.get("user_id")
            employee_id = params["employee_id"]
            action = params.get("action", "get")
            
            if not self._check_permission(user_id, employee_id, action):
                return {
                    "success": False,
                    "error": "Permission denied"
                }
            
            # 3. 액션 실행
            if action == "get":
                result = await self._get_employee(employee_id)
            elif action == "update":
                if "data" not in params:
                    return {"success": False, "error": "data is required for update"}
                result = await self._update_employee(employee_id, params["data"])
            elif action == "history":
                result = await self._get_employee_history(employee_id)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
            
            # 4. 민감 정보 마스킹 (본인이 아닌 경우)
            if user_id != employee_id:
                result = self._mask_sensitive_data(result)
            
            return {"success": True, "data": result}
        
        except Exception as e:
            logger.error(f"EmployeeTool execute error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """파라미터 검증"""
        return "employee_id" in params
    
    def _check_permission(self, user_id: str, employee_id: str, action: str) -> bool:
        """권한 확인"""
        user_info = self.perm_engine.get_user_info(user_id)
        if not user_info:
            return False
        
        # 인사팀은 모든 직원 정보 접근 가능
        if user_info.get("department") == "hr":
            return True
        
        # 본인 정보는 조회만 가능
        if user_id == employee_id and action == "get":
            return True
        
        # manager 이상은 팀원 정보 조회 가능
        if action == "get" and user_info.get("role") in ["manager", "executive", "admin"]:
            return True
        
        return False
    
    async def _get_employee(self, employee_id: str) -> Dict[str, Any]:
        """직원 정보 조회 (예제 구현)"""
        # TODO: 실제 DB 쿼리로 대체
        # query = "SELECT * FROM employees WHERE employee_id = %s"
        # result = self.db.execute_query(query, (employee_id,))
        
        return {
            "employee_id": employee_id,
            "name": "김직원",
            "department": "IT",
            "position": "Staff",
            "email": "kim@company.com",
            "phone": "010-1234-5678",
            "hire_date": "2020-01-01",
            "status": "active",
            "ssn": "900101-1234567",  # 마스킹 대상
            "address": "서울시 강남구",
            "emergency_contact": "010-9876-5432"
        }
    
    async def _update_employee(self, employee_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """직원 정보 수정 (예제 구현)"""
        # TODO: 실제 DB 업데이트로 대체
        # allowed_fields = ["email", "phone", "address"]
        # update_data = {k: v for k, v in data.items() if k in allowed_fields}
        # query = "UPDATE employees SET ... WHERE employee_id = %s"
        
        return {
            "employee_id": employee_id,
            "updated_fields": list(data.keys()),
            "updated_at": "2026-01-12 11:40:00"
        }
    
    async def _get_employee_history(self, employee_id: str) -> Dict[str, Any]:
        """직원 이력 조회 (예제 구현)"""
        # TODO: 실제 DB 쿼리로 대체
        return {
            "employee_id": employee_id,
            "history": [
                {
                    "date": "2020-01-01",
                    "event": "입사",
                    "position": "Junior",
                    "department": "IT"
                },
                {
                    "date": "2022-01-01",
                    "event": "승진",
                    "position": "Staff",
                    "department": "IT"
                }
            ]
        }
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """민감 정보 마스킹"""
        if isinstance(data, dict):
            masked = data.copy()
            if "ssn" in masked:
                masked["ssn"] = masked["ssn"][:6] + "-*******"
            if "phone" in masked:
                masked["phone"] = masked["phone"][:9] + "****"
            if "emergency_contact" in masked:
                masked["emergency_contact"] = "***-****-****"
            if "address" in masked:
                # 주소는 시/구까지만 표시
                parts = masked["address"].split()
                masked["address"] = " ".join(parts[:2]) if len(parts) > 2 else masked["address"]
        return data
    
    async def cleanup(self):
        """리소스 정리"""
        if self.db:
            self.db.close()
        logger.info("EmployeeTool cleanup completed")

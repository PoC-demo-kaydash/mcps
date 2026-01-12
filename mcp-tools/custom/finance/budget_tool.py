"""
Budget Tool - 예산 관리 Tool

예산 조회, 집행 현황, 승인 기능 제공
"""

from typing import Dict, Any
from mcp_tools.base import BaseTool
from shared.database import DatabaseManager
from shared.permissions import PermissionEngine
from shared.logging_config import get_logger

logger = get_logger("budget_tool")


class BudgetTool(BaseTool):
    """
    예산 관리 Tool
    
    기능:
    - 예산 조회
    - 집행 현황 조회
    - 예산 승인
    """
    
    def __init__(self):
        super().__init__(
            name="budget_tool",
            description="예산 조회 및 관리",
            category="custom",
            department="finance"
        )
        self.db = None
        self.perm_engine = PermissionEngine()
    
    async def initialize(self, config: dict):
        """초기화"""
        self.db = DatabaseManager(config)
        logger.info("BudgetTool initialized")
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool 실행
        
        Args:
            params: {
                "budget_id": str,  # 예산 ID
                "year": int,       # 연도 (선택)
                "action": str      # get/approve (선택)
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
            # 1. 권한 체크
            user_id = context.get("user_id")
            if not self._check_permission(user_id):
                return {
                    "success": False,
                    "error": "Permission denied: finance department only"
                }
            
            # 2. 파라미터 검증
            if not self.validate_params(params):
                return {
                    "success": False,
                    "error": "Invalid parameters: budget_id is required"
                }
            
            # 3. 액션 실행
            action = params.get("action", "get")
            budget_id = params["budget_id"]
            
            if action == "get":
                result = await self._get_budget(budget_id)
            elif action == "approve":
                result = await self._approve_budget(budget_id, user_id)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
            
            return {"success": True, "data": result}
        
        except Exception as e:
            logger.error(f"BudgetTool execute error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """파라미터 검증"""
        return "budget_id" in params
    
    def _check_permission(self, user_id: str) -> bool:
        """권한 확인 (재무팀만 접근 가능)"""
        user_info = self.perm_engine.get_user_info(user_id)
        if not user_info:
            return False
        
        # 재무팀 또는 manager 이상
        return (
            user_info.get("department") == "finance" or
            user_info.get("role") in ["manager", "executive", "admin"]
        )
    
    async def _get_budget(self, budget_id: str) -> Dict[str, Any]:
        """예산 조회 (예제 구현)"""
        # TODO: 실제 DB 쿼리로 대체
        # query = "SELECT * FROM budgets WHERE budget_id = %s"
        # result = self.db.execute_query(query, (budget_id,))
        
        # 예제 데이터
        return {
            "budget_id": budget_id,
            "department": "IT",
            "year": 2026,
            "total_amount": 100000000,
            "spent_amount": 45000000,
            "remaining": 55000000,
            "status": "active",
            "created_at": "2026-01-01",
            "items": [
                {"item": "서버 구입", "amount": 30000000, "spent": 25000000},
                {"item": "소프트웨어 라이선스", "amount": 20000000, "spent": 15000000},
                {"item": "클라우드 비용", "amount": 50000000, "spent": 5000000}
            ]
        }
    
    async def _approve_budget(self, budget_id: str, approver_id: str) -> Dict[str, Any]:
        """예산 승인 (예제 구현)"""
        # TODO: 실제 DB 업데이트로 대체
        # query = "UPDATE budgets SET status = 'approved', approved_by = %s WHERE budget_id = %s"
        # self.db.execute_query(query, (approver_id, budget_id))
        
        return {
            "budget_id": budget_id,
            "status": "approved",
            "approved_by": approver_id,
            "approved_at": "2026-01-12 11:30:00"
        }
    
    async def cleanup(self):
        """리소스 정리"""
        if self.db:
            self.db.close()
        logger.info("BudgetTool cleanup completed")

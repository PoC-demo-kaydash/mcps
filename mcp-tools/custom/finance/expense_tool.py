"""
Expense Tool - 지출 관리 Tool

지출 내역 조회, 승인, 정산 기능 제공
"""

from typing import Dict, Any, List
from mcp_tools.base import BaseTool
from shared.database import DatabaseManager
from shared.permissions import PermissionEngine
from shared.logging_config import get_logger

logger = get_logger("expense_tool")


class ExpenseTool(BaseTool):
    """
    지출 관리 Tool
    
    기능:
    - 지출 내역 조회
    - 지출 승인/거부
    - 정산 처리
    """
    
    def __init__(self):
        super().__init__(
            name="expense_tool",
            description="지출 내역 조회 및 승인",
            category="custom",
            department="finance"
        )
        self.db = None
        self.perm_engine = PermissionEngine()
    
    async def initialize(self, config: dict):
        """초기화"""
        self.db = DatabaseManager(config)
        logger.info("ExpenseTool initialized")
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool 실행
        
        Args:
            params: {
                "expense_id": str,  # 지출 ID (선택)
                "status": str,      # pending/approved/rejected (선택)
                "action": str,      # get/approve/reject (선택)
                "page": int,        # 페이지 (선택)
                "page_size": int    # 페이지 크기 (선택)
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
            
            # 2. 액션 실행
            action = params.get("action", "get")
            
            if action == "get":
                expense_id = params.get("expense_id")
                if expense_id:
                    result = await self._get_expense(expense_id)
                else:
                    result = await self._list_expenses(params)
            elif action == "approve":
                if not self.validate_params(params):
                    return {"success": False, "error": "expense_id is required"}
                result = await self._approve_expense(params["expense_id"], user_id)
            elif action == "reject":
                if not self.validate_params(params):
                    return {"success": False, "error": "expense_id is required"}
                result = await self._reject_expense(params["expense_id"], user_id)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
            
            return {"success": True, "data": result}
        
        except Exception as e:
            logger.error(f"ExpenseTool execute error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """파라미터 검증"""
        action = params.get("action", "get")
        if action in ["approve", "reject"]:
            return "expense_id" in params
        return True
    
    def _check_permission(self, user_id: str) -> bool:
        """권한 확인 (재무팀 또는 manager 이상)"""
        user_info = self.perm_engine.get_user_info(user_id)
        if not user_info:
            return False
        
        return (
            user_info.get("department") == "finance" or
            user_info.get("role") in ["manager", "executive", "admin"]
        )
    
    async def _get_expense(self, expense_id: str) -> Dict[str, Any]:
        """지출 상세 조회 (예제 구현)"""
        # TODO: 실제 DB 쿼리로 대체
        return {
            "expense_id": expense_id,
            "budget_id": "B2026001",
            "requester_id": "U001",
            "requester_name": "김직원",
            "amount": 500000,
            "category": "여비교통비",
            "description": "출장 교통비",
            "status": "pending",
            "created_at": "2026-01-10 09:00:00",
            "receipts": [
                {"file": "receipt_001.pdf", "amount": 300000},
                {"file": "receipt_002.pdf", "amount": 200000}
            ]
        }
    
    async def _list_expenses(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """지출 목록 조회 (예제 구현)"""
        status = params.get("status", "pending")
        page = params.get("page", 1)
        page_size = params.get("page_size", 20)
        
        # TODO: 실제 DB 쿼리로 대체
        expenses = [
            {
                "expense_id": "E2026001",
                "requester": "김직원",
                "amount": 500000,
                "category": "여비교통비",
                "status": status,
                "created_at": "2026-01-10"
            },
            {
                "expense_id": "E2026002",
                "requester": "이대리",
                "amount": 300000,
                "category": "접대비",
                "status": status,
                "created_at": "2026-01-11"
            }
        ]
        
        return {
            "expenses": expenses,
            "total": len(expenses),
            "page": page,
            "page_size": page_size
        }
    
    async def _approve_expense(self, expense_id: str, approver_id: str) -> Dict[str, Any]:
        """지출 승인 (예제 구현)"""
        # TODO: 실제 DB 업데이트로 대체
        return {
            "expense_id": expense_id,
            "status": "approved",
            "approved_by": approver_id,
            "approved_at": "2026-01-12 11:35:00"
        }
    
    async def _reject_expense(self, expense_id: str, rejector_id: str) -> Dict[str, Any]:
        """지출 거부 (예제 구현)"""
        # TODO: 실제 DB 업데이트로 대체
        return {
            "expense_id": expense_id,
            "status": "rejected",
            "rejected_by": rejector_id,
            "rejected_at": "2026-01-12 11:35:00"
        }
    
    async def cleanup(self):
        """리소스 정리"""
        if self.db:
            self.db.close()
        logger.info("ExpenseTool cleanup completed")

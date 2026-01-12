"""
Attendance Tool - 근태 관리 Tool

근태 기록, 휴가 신청, 승인 기능 제공
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from mcp_tools.base import BaseTool
from shared.database import DatabaseManager
from shared.permissions import PermissionEngine
from shared.logging_config import get_logger

logger = get_logger("attendance_tool")


class AttendanceTool(BaseTool):
    """
    근태 관리 Tool
    
    기능:
    - 출퇴근 기록
    - 휴가 신청
    - 휴가 승인/거부
    - 근태 현황 조회
    """
    
    def __init__(self):
        super().__init__(
            name="attendance_tool",
            description="근태 기록 및 휴가 관리",
            category="custom",
            department="hr"
        )
        self.db = None
        self.perm_engine = PermissionEngine()
    
    async def initialize(self, config: dict):
        """초기화"""
        self.db = DatabaseManager(config)
        logger.info("AttendanceTool initialized")
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool 실행
        
        Args:
            params: {
                "employee_id": str,    # 직원 ID
                "action": str,         # check_in/check_out/request_leave/approve_leave/get_status
                "leave_type": str,     # annual/sick/personal (휴가 신청 시)
                "start_date": str,     # YYYY-MM-DD (휴가 신청 시)
                "end_date": str,       # YYYY-MM-DD (휴가 신청 시)
                "reason": str,         # 사유 (선택)
                "leave_request_id": str  # 휴가 ID (승인 시)
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
            employee_id = params.get("employee_id", user_id)
            action = params.get("action", "get_status")
            
            if not self._check_permission(user_id, employee_id, action):
                return {
                    "success": False,
                    "error": "Permission denied"
                }
            
            # 2. 액션 실행
            if action == "check_in":
                result = await self._check_in(employee_id)
            elif action == "check_out":
                result = await self._check_out(employee_id)
            elif action == "request_leave":
                if not self._validate_leave_params(params):
                    return {"success": False, "error": "Invalid leave parameters"}
                result = await self._request_leave(employee_id, params)
            elif action == "approve_leave":
                if "leave_request_id" not in params:
                    return {"success": False, "error": "leave_request_id is required"}
                result = await self._approve_leave(params["leave_request_id"], user_id)
            elif action == "reject_leave":
                if "leave_request_id" not in params:
                    return {"success": False, "error": "leave_request_id is required"}
                result = await self._reject_leave(params["leave_request_id"], user_id)
            elif action == "get_status":
                result = await self._get_attendance_status(employee_id, params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
            
            return {"success": True, "data": result}
        
        except Exception as e:
            logger.error(f"AttendanceTool execute error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """파라미터 검증"""
        action = params.get("action", "get_status")
        if action in ["approve_leave", "reject_leave"]:
            return "leave_request_id" in params
        return True
    
    def _validate_leave_params(self, params: Dict[str, Any]) -> bool:
        """휴가 신청 파라미터 검증"""
        required = ["leave_type", "start_date", "end_date"]
        return all(k in params for k in required)
    
    def _check_permission(self, user_id: str, employee_id: str, action: str) -> bool:
        """권한 확인"""
        user_info = self.perm_engine.get_user_info(user_id)
        if not user_info:
            return False
        
        # 인사팀은 모든 근태 관리 가능
        if user_info.get("department") == "hr":
            return True
        
        # 본인의 출퇴근 기록 및 휴가 신청
        if user_id == employee_id and action in ["check_in", "check_out", "request_leave", "get_status"]:
            return True
        
        # manager 이상은 팀원 휴가 승인 가능
        if action in ["approve_leave", "reject_leave"] and user_info.get("role") in ["manager", "executive", "admin"]:
            return True
        
        return False
    
    async def _check_in(self, employee_id: str) -> Dict[str, Any]:
        """출근 기록 (예제 구현)"""
        # TODO: 실제 DB INSERT로 대체
        now = datetime.now()
        return {
            "employee_id": employee_id,
            "date": now.strftime("%Y-%m-%d"),
            "check_in": now.strftime("%H:%M:%S"),
            "status": "on_time" if now.hour < 9 else "late"
        }
    
    async def _check_out(self, employee_id: str) -> Dict[str, Any]:
        """퇴근 기록 (예제 구현)"""
        # TODO: 실제 DB UPDATE로 대체
        now = datetime.now()
        return {
            "employee_id": employee_id,
            "date": now.strftime("%Y-%m-%d"),
            "check_out": now.strftime("%H:%M:%S"),
            "work_hours": 9.5  # 계산된 근무 시간
        }
    
    async def _request_leave(self, employee_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """휴가 신청 (예제 구현)"""
        # TODO: 실제 DB INSERT로 대체
        leave_type = params["leave_type"]
        start_date = params["start_date"]
        end_date = params["end_date"]
        reason = params.get("reason", "")
        
        # 휴가 일수 계산
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        
        return {
            "leave_request_id": f"L{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "employee_id": employee_id,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _approve_leave(self, leave_request_id: str, approver_id: str) -> Dict[str, Any]:
        """휴가 승인 (예제 구현)"""
        # TODO: 실제 DB UPDATE로 대체
        return {
            "leave_request_id": leave_request_id,
            "status": "approved",
            "approved_by": approver_id,
            "approved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _reject_leave(self, leave_request_id: str, rejector_id: str) -> Dict[str, Any]:
        """휴가 거부 (예제 구현)"""
        # TODO: 실제 DB UPDATE로 대체
        return {
            "leave_request_id": leave_request_id,
            "status": "rejected",
            "rejected_by": rejector_id,
            "rejected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _get_attendance_status(self, employee_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """근태 현황 조회 (예제 구현)"""
        # TODO: 실제 DB 쿼리로 대체
        year = params.get("year", datetime.now().year)
        month = params.get("month", datetime.now().month)
        
        return {
            "employee_id": employee_id,
            "year": year,
            "month": month,
            "total_days": 20,
            "work_days": 18,
            "late_days": 1,
            "absent_days": 1,
            "annual_leave_used": 5,
            "annual_leave_remaining": 10,
            "pending_leaves": [
                {
                    "leave_request_id": "L2026001",
                    "leave_type": "annual",
                    "start_date": "2026-01-20",
                    "end_date": "2026-01-21",
                    "days": 2,
                    "status": "pending"
                }
            ]
        }
    
    async def cleanup(self):
        """리소스 정리"""
        if self.db:
            self.db.close()
        logger.info("AttendanceTool cleanup completed")

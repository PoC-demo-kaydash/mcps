"""
감사 로그 및 통계 Tool

감사 로그 조회, 내 활동 조회, 시스템 통계 조회 기능 제공
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_tools.base import BaseTool, ToolMetadata
from shared.database import DatabaseManager
from shared.logging_config import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)


class GetAuditLogsTool(BaseTool):
    """감사 로그 조회 Tool"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_audit_logs",
            description="감사 로그 조회 (관리자 전용)",
            category="audit",
            department="core",
            version="1.0.0",
            required_permissions=["admin:audit"],
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "action": {"type": "string"},
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "limit": {"type": "integer", "default": 100, "maximum": 1000}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "total": {"type": "integer"},
                    "logs": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """감사 로그 조회"""
        try:
            # 권한 확인 (admin만)
            if context:
                user_role = context.get("user_role", "")
                authorized, error = self.check_permission(user_role, ["admin:audit"])
                if not authorized:
                    return self.create_error_response(error, "PERMISSION_DENIED")
            
            # 쿼리 구성
            query = """
            SELECT a.*, u.name as user_name
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE 1=1
            """
            params = []
            
            # 필터 추가
            if arguments.get("user_id"):
                query += " AND a.user_id = %s"
                params.append(arguments["user_id"])
            
            if arguments.get("action"):
                query += " AND a.action = %s"
                params.append(arguments["action"])
            
            if arguments.get("start_date"):
                query += " AND a.created_at >= %s"
                params.append(arguments["start_date"])
            
            if arguments.get("end_date"):
                query += " AND a.created_at <= %s"
                params.append(arguments["end_date"])
            
            query += " ORDER BY a.created_at DESC LIMIT %s"
            params.append(arguments.get("limit", 100))
            
            # 실행
            logs = self.db.fetch_all(query, tuple(params))
            
            # 총 개수
            count_query = query.split("ORDER BY")[0].replace(
                "SELECT a.*, u.name as user_name",
                "SELECT COUNT(*) as total"
            )
            count_result = self.db.fetch_one(count_query, tuple(params[:-1]))
            total = count_result["total"] if count_result else 0
            
            return self.create_success_response({
                "total": total,
                "logs": [
                    {
                        "id": log["id"],
                        "user_id": log["user_id"],
                        "user_name": log.get("user_name", "Unknown"),
                        "action": log["action"],
                        "resource_type": log.get("resource_type"),
                        "resource_id": log.get("resource_id"),
                        "result": log["result"],
                        "ip_address": log.get("ip_address"),
                        "created_at": log["created_at"].isoformat() if log.get("created_at") else None
                    }
                    for log in logs
                ]
            })
        
        except Exception as e:
            logger.error(f"Get audit logs failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "AUDIT_ERROR")


class GetMyActivityTool(BaseTool):
    """내 활동 로그 조회 Tool"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_my_activity",
            description="내 활동 로그 조회",
            category="audit",
            department="core",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "default": 7, "maximum": 90},
                    "limit": {"type": "integer", "default": 50, "maximum": 200}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "activities": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """내 활동 조회"""
        try:
            if not context or "user_id" not in context:
                return self.create_error_response(
                    "Authentication required",
                    "AUTH_ERROR"
                )
            
            user_id = context["user_id"]
            days = arguments.get("days", 7)
            limit = arguments.get("limit", 50)
            
            # 날짜 범위
            start_date = datetime.now() - timedelta(days=days)
            
            query = """
            SELECT * FROM audit_logs
            WHERE user_id = %s AND created_at >= %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            
            logs = self.db.fetch_all(query, (user_id, start_date, limit))
            
            return self.create_success_response({
                "activities": [
                    {
                        "action": log["action"],
                        "resource_type": log.get("resource_type"),
                        "resource_id": log.get("resource_id"),
                        "result": log["result"],
                        "created_at": log["created_at"].isoformat() if log.get("created_at") else None
                    }
                    for log in logs
                ]
            })
        
        except Exception as e:
            logger.error(f"Get my activity failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "ACTIVITY_ERROR")


class GetStatisticsTool(BaseTool):
    """통계 조회 Tool"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        super().__init__()
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_statistics",
            description="시스템 통계 조회",
            category="audit",
            department="core",
            version="1.0.0",
            required_permissions=["admin:audit"],
            input_schema={
                "type": "object",
                "properties": {
                    "period": {"type": "string", "enum": ["day", "week", "month"], "default": "week"}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "period": {"type": "string"},
                    "document_stats": {"type": "object"},
                    "user_stats": {"type": "object"},
                    "activity_stats": {"type": "object"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """통계 조회"""
        try:
            # 권한 확인
            if context:
                user_role = context.get("user_role", "")
                authorized, error = self.check_permission(user_role, ["admin:audit"])
                if not authorized:
                    return self.create_error_response(error, "PERMISSION_DENIED")
            
            period = arguments.get("period", "week")
            days = {"day": 1, "week": 7, "month": 30}[period]
            start_date = datetime.now() - timedelta(days=days)
            
            # 문서 통계
            doc_stats_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN classification = 'public' THEN 1 END) as public_count,
                COUNT(CASE WHEN classification = 'team' THEN 1 END) as team_count,
                COUNT(CASE WHEN classification = 'confidential' THEN 1 END) as confidential_count,
                COUNT(CASE WHEN created_at >= %s THEN 1 END) as recent_count
            FROM documents
            """
            doc_stats = self.db.fetch_one(doc_stats_query, (start_date,))
            
            # 사용자 통계
            user_stats_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN active = TRUE THEN 1 END) as active_count
            FROM users
            """
            user_stats = self.db.fetch_one(user_stats_query)
            
            # 활동 통계
            activity_stats_query = """
            SELECT 
                action,
                COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= %s
            GROUP BY action
            ORDER BY count DESC
            LIMIT 10
            """
            activity_stats = self.db.fetch_all(activity_stats_query, (start_date,))
            
            return self.create_success_response({
                "period": period,
                "document_stats": {
                    "total": doc_stats.get("total", 0),
                    "by_classification": {
                        "public": doc_stats.get("public_count", 0),
                        "team": doc_stats.get("team_count", 0),
                        "confidential": doc_stats.get("confidential_count", 0)
                    },
                    "recent_created": doc_stats.get("recent_count", 0)
                },
                "user_stats": {
                    "total": user_stats.get("total", 0),
                    "active": user_stats.get("active_count", 0)
                },
                "activity_stats": {
                    "top_actions": [
                        {"action": a["action"], "count": a["count"]}
                        for a in activity_stats
                    ]
                }
            })
        
        except Exception as e:
            logger.error(f"Get statistics failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "STATISTICS_ERROR")

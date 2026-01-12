"""
메트릭 수집

Server, Tool 실행 메트릭 수집
"""

from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import threading


class MetricsCollector:
    """
    메트릭 수집기
    
    Tool 실행 횟수, 실행 시간, 에러 등 통계 수집
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        
        # Tool 메트릭
        self.tool_calls: Dict[str, int] = defaultdict(int)  # tool_name -> count
        self.tool_errors: Dict[str, int] = defaultdict(int)  # tool_name -> error_count
        self.tool_total_time: Dict[str, float] = defaultdict(float)  # tool_name -> total_time
        
        # Server 메트릭
        self.server_requests: Dict[str, int] = defaultdict(int)  # server_name -> count
        self.server_errors: Dict[str, int] = defaultdict(int)  # server_name -> error_count
        
        # 세션 메트릭
        self.session_created: int = 0
        self.session_deleted: int = 0
        
        # 시작 시각
        self.start_time = datetime.utcnow()
    
    def record_tool_call(
        self,
        tool_name: str,
        server_name: str,
        execution_time: float,
        is_error: bool = False
    ):
        """
        Tool 호출 기록
        
        Args:
            tool_name: Tool 이름
            server_name: Server 이름
            execution_time: 실행 시간 (초)
            is_error: 에러 여부
        """
        with self.lock:
            self.tool_calls[tool_name] += 1
            self.tool_total_time[tool_name] += execution_time
            
            self.server_requests[server_name] += 1
            
            if is_error:
                self.tool_errors[tool_name] += 1
                self.server_errors[server_name] += 1
    
    def record_session_created(self):
        """세션 생성 기록"""
        with self.lock:
            self.session_created += 1
    
    def record_session_deleted(self):
        """세션 삭제 기록"""
        with self.lock:
            self.session_deleted += 1
    
    def get_tool_stats(self, tool_name: str) -> dict:
        """
        Tool 통계 조회
        
        Args:
            tool_name: Tool 이름
        
        Returns:
            dict: Tool 통계
        """
        with self.lock:
            calls = self.tool_calls.get(tool_name, 0)
            errors = self.tool_errors.get(tool_name, 0)
            total_time = self.tool_total_time.get(tool_name, 0.0)
            
            return {
                "tool_name": tool_name,
                "calls": calls,
                "errors": errors,
                "success_rate": (calls - errors) / calls if calls > 0 else 0.0,
                "avg_execution_time": total_time / calls if calls > 0 else 0.0,
                "total_execution_time": total_time
            }
    
    def get_server_stats(self, server_name: str) -> dict:
        """
        Server 통계 조회
        
        Args:
            server_name: Server 이름
        
        Returns:
            dict: Server 통계
        """
        with self.lock:
            requests = self.server_requests.get(server_name, 0)
            errors = self.server_errors.get(server_name, 0)
            
            return {
                "server_name": server_name,
                "requests": requests,
                "errors": errors,
                "success_rate": (requests - errors) / requests if requests > 0 else 0.0
            }
    
    def get_all_stats(self) -> dict:
        """
        전체 통계 조회
        
        Returns:
            dict: 전체 통계
        """
        with self.lock:
            # Tool 통계
            tool_stats = []
            for tool_name in self.tool_calls.keys():
                tool_stats.append(self.get_tool_stats(tool_name))
            
            # Server 통계
            server_stats = []
            for server_name in self.server_requests.keys():
                server_stats.append(self.get_server_stats(server_name))
            
            # 전체 통계
            total_calls = sum(self.tool_calls.values())
            total_errors = sum(self.tool_errors.values())
            
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            
            return {
                "uptime": uptime,
                "tools": {
                    "total_calls": total_calls,
                    "total_errors": total_errors,
                    "success_rate": (total_calls - total_errors) / total_calls if total_calls > 0 else 0.0,
                    "stats": tool_stats
                },
                "servers": {
                    "stats": server_stats
                },
                "sessions": {
                    "created": self.session_created,
                    "deleted": self.session_deleted,
                    "active": self.session_created - self.session_deleted
                }
            }
    
    def reset(self):
        """메트릭 초기화"""
        with self.lock:
            self.tool_calls.clear()
            self.tool_errors.clear()
            self.tool_total_time.clear()
            self.server_requests.clear()
            self.server_errors.clear()
            self.session_created = 0
            self.session_deleted = 0
            self.start_time = datetime.utcnow()


# 전역 메트릭 인스턴스
metrics = MetricsCollector()

__all__ = ["MetricsCollector", "metrics"]

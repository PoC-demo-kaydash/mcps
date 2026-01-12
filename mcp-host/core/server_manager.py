"""
Server 프로세스 관리

subprocess를 이용하여 MCP Server 프로세스 시작/중지/재시작
"""

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from shared.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ServerProcess:
    """Server 프로세스 정보"""
    name: str
    process: subprocess.Popen
    started_at: datetime
    restart_count: int = 0
    last_error: Optional[str] = None


class ServerManager:
    """
    MCP Server 프로세스 관리자
    
    Server 시작/중지/재시작 및 상태 관리
    """
    
    def __init__(self, config):
        """
        Args:
            config: Config 인스턴스
        """
        self.config = config
        self.processes: Dict[str, ServerProcess] = {}
        self.logger = logger
    
    def start_server(self, server_name: str) -> bool:
        """
        Server 시작
        
        Args:
            server_name: Server 이름
        
        Returns:
            bool: 성공 여부
        """
        server_config = self.config.get_server(server_name)
        if not server_config:
            self.logger.error(f"Server not found: {server_name}")
            return False
        
        if not server_config.enabled:
            self.logger.warning(f"Server disabled: {server_name}")
            return False
        
        # 이미 실행 중
        if self.is_running(server_name):
            self.logger.warning(f"Server already running: {server_name}")
            return True
        
        try:
            # Server 경로 확인
            server_path = Path(self.config.project_root) / server_config.path
            main_file = server_path / server_config.main
            
            if not main_file.exists():
                raise FileNotFoundError(f"Main file not found: {main_file}")
            
            # 환경 변수
            env = os.environ.copy()
            if server_config.env:
                env.update(server_config.env)
            
            # Server 프로세스 시작
            cmd = [server_config.python, str(main_file)]
            
            process = subprocess.Popen(
                cmd,
                cwd=str(server_path),
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0  # unbuffered
            )
            
            # 프로세스 정보 저장
            self.processes[server_name] = ServerProcess(
                name=server_name,
                process=process,
                started_at=datetime.utcnow()
            )
            
            # 시작 확인 (짧은 대기)
            time.sleep(0.5)
            if process.poll() is not None:
                # 프로세스가 즉시 종료됨
                stderr = process.stderr.read().decode() if process.stderr else ""
                raise RuntimeError(f"Server failed to start: {stderr}")
            
            self.logger.info(f"✓ Server started: {server_name} (PID: {process.pid})")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to start server {server_name}: {e}")
            if server_name in self.processes:
                self.processes[server_name].last_error = str(e)
            return False
    
    def stop_server(self, server_name: str, timeout: int = 10) -> bool:
        """
        Server 중지
        
        Args:
            server_name: Server 이름
            timeout: 종료 대기 시간 (초)
        
        Returns:
            bool: 성공 여부
        """
        if server_name not in self.processes:
            self.logger.warning(f"Server not running: {server_name}")
            return True
        
        try:
            process_info = self.processes[server_name]
            process = process_info.process
            
            # SIGTERM 전송
            if process.poll() is None:
                self.logger.info(f"Stopping server: {server_name} (PID: {process.pid})")
                process.terminate()
                
                # 종료 대기
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # 강제 종료
                    self.logger.warning(f"Force killing server: {server_name}")
                    process.kill()
                    process.wait()
            
            # 프로세스 정보 제거
            del self.processes[server_name]
            self.logger.info(f"✓ Server stopped: {server_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to stop server {server_name}: {e}")
            return False
    
    def restart_server(self, server_name: str) -> bool:
        """
        Server 재시작
        
        Args:
            server_name: Server 이름
        
        Returns:
            bool: 성공 여부
        """
        self.logger.info(f"Restarting server: {server_name}")
        
        # 중지
        if not self.stop_server(server_name):
            return False
        
        # 시작
        time.sleep(1)  # 짧은 대기
        
        if self.start_server(server_name):
            # 재시작 카운트 증가
            if server_name in self.processes:
                self.processes[server_name].restart_count += 1
            return True
        
        return False
    
    def is_running(self, server_name: str) -> bool:
        """
        Server 실행 여부 확인
        
        Args:
            server_name: Server 이름
        
        Returns:
            bool: 실행 중이면 True
        """
        if server_name not in self.processes:
            return False
        
        process = self.processes[server_name].process
        return process.poll() is None
    
    def get_server_info(self, server_name: str) -> Optional[dict]:
        """
        Server 정보 조회
        
        Args:
            server_name: Server 이름
        
        Returns:
            dict: Server 정보 또는 None
        """
        server_config = self.config.get_server(server_name)
        if not server_config:
            return None
        
        is_running = self.is_running(server_name)
        process_info = self.processes.get(server_name)
        
        info = {
            "name": server_name,
            "status": "running" if is_running else "stopped",
            "enabled": server_config.enabled,
            "auto_start": server_config.auto_start,
        }
        
        if process_info:
            info["pid"] = process_info.process.pid if is_running else None
            info["uptime"] = (datetime.utcnow() - process_info.started_at).total_seconds() if is_running else None
            info["restart_count"] = process_info.restart_count
            info["last_error"] = process_info.last_error
        
        return info
    
    def list_servers(self) -> List[dict]:
        """
        전체 Server 목록 조회
        
        Returns:
            List[dict]: Server 정보 목록
        """
        servers = []
        for server_name in self.config.list_server_names():
            info = self.get_server_info(server_name)
            if info:
                servers.append(info)
        return servers
    
    def start_all(self) -> dict:
        """
        전체 Server 시작 (auto_start=True인 것만)
        
        Returns:
            dict: 시작 결과
        """
        results = {"success": [], "failed": []}
        
        for server_name in self.config.list_server_names():
            server_config = self.config.get_server(server_name)
            if server_config and server_config.auto_start:
                if self.start_server(server_name):
                    results["success"].append(server_name)
                else:
                    results["failed"].append(server_name)
        
        self.logger.info(f"Started {len(results['success'])} servers, {len(results['failed'])} failed")
        return results
    
    def stop_all(self) -> dict:
        """
        전체 Server 중지
        
        Returns:
            dict: 중지 결과
        """
        results = {"success": [], "failed": []}
        
        for server_name in list(self.processes.keys()):
            if self.stop_server(server_name):
                results["success"].append(server_name)
            else:
                results["failed"].append(server_name)
        
        self.logger.info(f"Stopped {len(results['success'])} servers, {len(results['failed'])} failed")
        return results
    
    def health_check(self) -> dict:
        """
        헬스 체크
        
        Returns:
            dict: 헬스 체크 결과
        """
        total = len(self.config.list_server_names())
        running = sum(1 for name in self.config.list_server_names() if self.is_running(name))
        
        return {
            "total": total,
            "running": running,
            "stopped": total - running,
            "healthy": running == total
        }
    
    def cleanup(self):
        """리소스 정리"""
        self.logger.info("Cleaning up server manager...")
        self.stop_all()

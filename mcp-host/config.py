"""
MCP Host 설정

services.json과 registry.json을 로드하여 통합 설정 관리
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database 설정"""
    host: str = "localhost"
    port: int = 3306
    database: str = "mcps_db"
    user: str = "mcps_user"
    password: str = "your_password"
    charset: str = "utf8mb4"
    pool_size: Dict[str, int] = {"min": 5, "max": 20}


class ElasticsearchConfig(BaseModel):
    """Elasticsearch 설정"""
    hosts: list = ["localhost:9200"]
    timeout: int = 30


class ServerConfig(BaseModel):
    """Server 설정"""
    name: str
    path: str
    python: str = "/app/miniconda3/envs/mcp_env/bin/python"
    main: str = "main.py"
    enabled: bool = True
    auto_start: bool = True
    restart_on_failure: bool = True
    max_restarts: int = 3
    timeout: int = 30
    env: Optional[Dict[str, str]] = None
    health_check: Optional[Dict[str, Any]] = None


class HostConfig(BaseModel):
    """Host 설정"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1
    log_level: str = "INFO"
    session_timeout: int = 3600  # 세션 타임아웃 (초)


class Config:
    """
    통합 설정
    
    환경 변수 및 설정 파일에서 로드
    """
    
    def __init__(self):
        # 프로젝트 루트
        self.project_root = Path(__file__).parent.parent
        
        # Database
        self.database = DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            database=os.getenv("DB_NAME", "mcps_db"),
            user=os.getenv("DB_USER", "mcps_user"),
            password=os.getenv("DB_PASSWORD", "your_password")
        )
        
        # Elasticsearch
        self.elasticsearch = ElasticsearchConfig(
            hosts=[os.getenv("ES_HOST", "localhost:9200")],
            timeout=int(os.getenv("ES_TIMEOUT", "30"))
        )
        
        # Host
        self.host = HostConfig(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            session_timeout=int(os.getenv("SESSION_TIMEOUT", "3600"))
        )
        
        # Servers
        self.servers: Dict[str, ServerConfig] = {}
        self._load_servers()
        
        # Registry
        self.registry: dict = {}
        self._load_registry()
    
    def _load_servers(self):
        """Server 설정 로드 (services.json)"""
        services_file = self.project_root / "config" / "services.json"
        
        if not services_file.exists():
            raise FileNotFoundError(f"services.json not found: {services_file}")
        
        try:
            with open(services_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for server_data in data.get("servers", []):
                server = ServerConfig(**server_data)
                self.servers[server.name] = server
            
            print(f"✓ Loaded {len(self.servers)} servers from services.json")
        
        except Exception as e:
            raise RuntimeError(f"Failed to load services.json: {e}")
    
    def _load_registry(self):
        """Tool 레지스트리 로드 (registry.json)"""
        registry_file = self.project_root / "config" / "registry.json"
        
        if not registry_file.exists():
            raise FileNotFoundError(f"registry.json not found: {registry_file}")
        
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                self.registry = json.load(f)
            
            tool_count = len(self.registry.get("tools", []))
            print(f"✓ Loaded {tool_count} tools from registry.json")
        
        except Exception as e:
            raise RuntimeError(f"Failed to load registry.json: {e}")
    
    def get_server(self, server_name: str) -> Optional[ServerConfig]:
        """
        Server 설정 가져오기
        
        Args:
            server_name: Server 이름
        
        Returns:
            ServerConfig 또는 None
        """
        return self.servers.get(server_name)
    
    def get_tool_registry(self) -> dict:
        """
        Tool 레지스트리 가져오기
        
        Returns:
            dict: registry.json 전체 데이터
        """
        return self.registry
    
    def list_server_names(self) -> list:
        """Server 이름 목록"""
        return list(self.servers.keys())
    
    def list_enabled_servers(self) -> list:
        """활성화된 Server 목록"""
        return [
            name for name, server in self.servers.items()
            if server.enabled
        ]


# 전역 설정 인스턴스
config: Optional[Config] = None


def get_config() -> Config:
    """
    전역 설정 인스턴스 반환
    
    Returns:
        Config: 설정 인스턴스
    """
    global config
    if config is None:
        config = Config()
    return config

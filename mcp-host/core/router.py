"""
Tool 라우팅

registry.json을 이용하여 Tool → Server 매핑 및 라우팅
"""

from typing import Dict, Optional, List
from shared.logging_config import get_logger

logger = get_logger(__name__)


class Router:
    """
    Tool 라우터
    
    Tool 이름을 Server 이름으로 매핑
    """
    
    def __init__(self, config):
        """
        Args:
            config: Config 인스턴스
        """
        self.config = config
        self.logger = logger
        self.tool_map: Dict[str, str] = {}  # tool_name -> server_name
        self.tool_metadata: Dict[str, dict] = {}  # tool_name -> metadata
        
        self._build_tool_map()
    
    def _build_tool_map(self):
        """Tool → Server 매핑 구축"""
        registry = self.config.get_tool_registry()
        
        if "tools" not in registry:
            self.logger.warning("No tools found in registry")
            return
        
        for tool in registry["tools"]:
            tool_name = tool.get("name")
            server_name = tool.get("server")
            
            if not tool_name or not server_name:
                self.logger.warning(f"Invalid tool entry: {tool}")
                continue
            
            self.tool_map[tool_name] = server_name
            self.tool_metadata[tool_name] = tool
        
        self.logger.info(f"✓ Built tool map: {len(self.tool_map)} tools")
    
    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """
        Tool이 소속된 Server 찾기
        
        Args:
            tool_name: Tool 이름
        
        Returns:
            str: Server 이름 또는 None
        """
        return self.tool_map.get(tool_name)
    
    def is_tool_available(self, tool_name: str) -> bool:
        """
        Tool 사용 가능 여부
        
        Args:
            tool_name: Tool 이름
        
        Returns:
            bool: 사용 가능하면 True
        """
        return tool_name in self.tool_map
    
    def list_all_tools(self) -> List[dict]:
        """
        전체 Tool 목록
        
        Returns:
            List[dict]: Tool 메타데이터 목록
        """
        return list(self.tool_metadata.values())
    
    def get_tool_metadata(self, tool_name: str) -> Optional[dict]:
        """
        Tool 메타데이터 조회
        
        Args:
            tool_name: Tool 이름
        
        Returns:
            dict: Tool 메타데이터 또는 None
        """
        return self.tool_metadata.get(tool_name)
    
    def list_tools_by_server(self, server_name: str) -> List[dict]:
        """
        특정 Server의 Tool 목록
        
        Args:
            server_name: Server 이름
        
        Returns:
            List[dict]: Tool 메타데이터 목록
        """
        return [
            metadata for tool_name, metadata in self.tool_metadata.items()
            if self.tool_map.get(tool_name) == server_name
        ]
    
    def reload_mapping(self):
        """매핑 재로드"""
        self.logger.info("Reloading tool mapping...")
        self.tool_map.clear()
        self.tool_metadata.clear()
        
        # config 재로드
        self.config._load_registry()
        self._build_tool_map()

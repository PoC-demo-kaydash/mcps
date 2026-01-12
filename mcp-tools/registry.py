"""
Tool 레지스트리

모든 Tool을 등록하고 관리하는 전역 레지스트리
"""

from typing import Dict, List, Optional
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Tool 레지스트리
    
    모든 Tool을 등록하고 관리
    
    Example:
        registry = ToolRegistry()
        registry.register(SearchDocumentsTool())
        
        tool = registry.get_tool("search_documents")
        result = tool.execute(arguments, context)
    """
    
    def __init__(self):
        """초기화"""
        self.tools: Dict[str, Any] = {}
        self.metadata_cache: Dict[str, Any] = {}
        logger.info("ToolRegistry initialized")
    
    def register(self, tool):
        """
        Tool 등록
        
        Args:
            tool: Tool 인스턴스 (BaseTool 또는 AsyncBaseTool)
        
        Example:
            registry = ToolRegistry()
            registry.register(SearchDocumentsTool())
        """
        from .base import BaseTool
        
        if not isinstance(tool, BaseTool):
            raise TypeError(f"Tool must be an instance of BaseTool, got {type(tool)}")
        
        name = tool.metadata.name
        
        if name in self.tools:
            logger.warning(f"Tool already registered: {name}, overwriting")
        
        self.tools[name] = tool
        self.metadata_cache[name] = tool.metadata
        
        logger.info(
            f"Tool registered: {name} "
            f"(category={tool.metadata.category}, "
            f"version={tool.metadata.version})"
        )
    
    def unregister(self, name: str) -> bool:
        """
        Tool 등록 해제
        
        Args:
            name: Tool 이름
        
        Returns:
            bool: 성공 여부
        """
        if name in self.tools:
            del self.tools[name]
            del self.metadata_cache[name]
            logger.info(f"Tool unregistered: {name}")
            return True
        
        logger.warning(f"Tool not found for unregistration: {name}")
        return False
    
    def get_tool(self, name: str):
        """
        Tool 가져오기
        
        Args:
            name: Tool 이름
        
        Returns:
            Tool 인스턴스 또는 None
        """
        tool = self.tools.get(name)
        
        if tool is None:
            logger.warning(f"Tool not found: {name}")
        
        return tool
    
    def get_metadata(self, name: str):
        """
        Tool 메타데이터 가져오기
        
        Args:
            name: Tool 이름
        
        Returns:
            ToolMetadata 또는 None
        """
        return self.metadata_cache.get(name)
    
    def list_tools(
        self,
        category: Optional[str] = None,
        department: Optional[str] = None,
        enabled_only: bool = True
    ) -> List:
        """
        Tool 목록 조회
        
        Args:
            category: 카테고리 필터
            department: 부서 필터
            enabled_only: 활성화된 Tool만 반환
        
        Returns:
            List[ToolMetadata]
        """
        tools = list(self.metadata_cache.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        if department:
            tools = [t for t in tools if t.department == department]
        
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        
        return tools
    
    def exists(self, name: str) -> bool:
        """
        Tool 존재 여부
        
        Args:
            name: Tool 이름
        
        Returns:
            bool: 존재 여부
        """
        return name in self.tools
    
    def get_categories(self) -> List[str]:
        """
        카테고리 목록
        
        Returns:
            List[str]: 카테고리 목록 (정렬됨)
        """
        categories = set(t.category for t in self.metadata_cache.values())
        return sorted(categories)
    
    def get_departments(self) -> List[str]:
        """
        부서 목록
        
        Returns:
            List[str]: 부서 목록 (정렬됨)
        """
        departments = set(t.department for t in self.metadata_cache.values())
        return sorted(departments)
    
    def search_tools(self, query: str) -> List:
        """
        Tool 검색
        
        Args:
            query: 검색어 (이름 또는 설명)
        
        Returns:
            List[ToolMetadata]: 검색 결과
        """
        query_lower = query.lower()
        
        results = [
            metadata
            for metadata in self.metadata_cache.values()
            if query_lower in metadata.name.lower()
            or query_lower in metadata.description.lower()
        ]
        
        logger.info(f"Tool search '{query}': {len(results)} results")
        return results
    
    def get_stats(self) -> dict:
        """
        레지스트리 통계
        
        Returns:
            {
                "total": 10,
                "enabled": 9,
                "by_category": {"search": 2, "document": 5, ...},
                "by_department": {"core": 8, "utils": 2}
            }
        """
        categories = Counter(t.category for t in self.metadata_cache.values())
        departments = Counter(t.department for t in self.metadata_cache.values())
        enabled_count = sum(1 for t in self.metadata_cache.values() if t.enabled)
        
        return {
            "total": len(self.tools),
            "enabled": enabled_count,
            "disabled": len(self.tools) - enabled_count,
            "by_category": dict(categories),
            "by_department": dict(departments)
        }
    
    def get_tool_names(self) -> List[str]:
        """
        등록된 모든 Tool 이름 목록
        
        Returns:
            List[str]: Tool 이름 목록 (정렬됨)
        """
        return sorted(self.tools.keys())
    
    def filter_by_permissions(self, user_role: str) -> List:
        """
        사용자 역할에 따라 접근 가능한 Tool 필터링
        
        Args:
            user_role: 사용자 역할
        
        Returns:
            List[ToolMetadata]: 접근 가능한 Tool 목록
        """
        from shared.permissions import PermissionEngine
        
        perm_engine = PermissionEngine()
        accessible_tools = []
        
        for metadata in self.metadata_cache.values():
            # 권한이 필요 없거나 권한이 있는 경우
            if not metadata.required_permissions:
                accessible_tools.append(metadata)
            else:
                # 권한 확인
                has_all_permissions = True
                for permission in metadata.required_permissions:
                    if ":" in permission:
                        resource, action = permission.split(":", 1)
                        if not perm_engine.can_perform_action(user_role, action, resource):
                            has_all_permissions = False
                            break
                
                if has_all_permissions:
                    accessible_tools.append(metadata)
        
        return accessible_tools
    
    def enable_tool(self, name: str) -> bool:
        """
        Tool 활성화
        
        Args:
            name: Tool 이름
        
        Returns:
            bool: 성공 여부
        """
        if name in self.metadata_cache:
            self.metadata_cache[name].enabled = True
            logger.info(f"Tool enabled: {name}")
            return True
        
        return False
    
    def disable_tool(self, name: str) -> bool:
        """
        Tool 비활성화
        
        Args:
            name: Tool 이름
        
        Returns:
            bool: 성공 여부
        """
        if name in self.metadata_cache:
            self.metadata_cache[name].enabled = False
            logger.info(f"Tool disabled: {name}")
            return True
        
        return False
    
    def clear(self):
        """모든 Tool 제거"""
        count = len(self.tools)
        self.tools.clear()
        self.metadata_cache.clear()
        logger.info(f"Registry cleared: {count} tools removed")


# 전역 레지스트리
_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """
    전역 레지스트리 가져오기
    
    Returns:
        ToolRegistry: 전역 레지스트리 인스턴스
    """
    return _global_registry


def register_tool(tool):
    """
    Tool 등록 (편의 함수)
    
    Args:
        tool: Tool 인스턴스
    
    Example:
        from mcp_tools.registry import register_tool
        from mcp_tools.core.search_tools import SearchDocumentsTool
        
        register_tool(SearchDocumentsTool())
    """
    _global_registry.register(tool)


def get_tool(name: str):
    """
    Tool 가져오기 (편의 함수)
    
    Args:
        name: Tool 이름
    
    Returns:
        Tool 인스턴스 또는 None
    """
    return _global_registry.get_tool(name)


def list_all_tools(**filters) -> List:
    """
    Tool 목록 조회 (편의 함수)
    
    Args:
        **filters: 필터 옵션 (category, department, enabled_only)
    
    Returns:
        List[ToolMetadata]
    """
    return _global_registry.list_tools(**filters)

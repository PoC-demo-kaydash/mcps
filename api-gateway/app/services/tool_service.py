"""
Tool service for managing and executing MCP tools
"""
from typing import Dict, Any, List
from ..core.exceptions import NotFoundError, ValidationError
from .mcp_client import MCPClient


class ToolService:
    """Tool management and execution service"""
    
    def __init__(self):
        self.mcp_client = MCPClient()
    
    async def list_tools(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of available tools
        
        Args:
            session_id: Optional session ID for context
            
        Returns:
            List of tool information
        """
        try:
            headers = {}
            if session_id:
                headers["X-Session-ID"] = session_id
            
            response = await self.mcp_client.get("/api/tools/list", headers=headers)
            
            if response.get("status") != "success":
                return []
            
            tools = response.get("data", {}).get("tools", [])
            return tools
            
        except Exception as e:
            # Return empty list on error rather than raising exception
            return []
    
    async def get_tool_info(self, tool_name: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a specific tool
        
        Args:
            tool_name: Name of the tool
            session_id: Optional session ID for context
            
        Returns:
            Tool information
            
        Raises:
            NotFoundError: If tool not found
        """
        try:
            headers = {}
            if session_id:
                headers["X-Session-ID"] = session_id
            
            response = await self.mcp_client.get(f"/api/tools/{tool_name}", headers=headers)
            
            if response.get("status") != "success":
                raise NotFoundError(f"Tool '{tool_name}' not found")
            
            return response.get("data", {})
            
        except NotFoundError:
            raise
        except Exception as e:
            raise NotFoundError(f"Failed to get tool info: {str(e)}")
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Execute a tool with given arguments
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            session_id: Session ID for execution context
            
        Returns:
            Tool execution result
            
        Raises:
            ValidationError: If execution fails
            NotFoundError: If tool not found
        """
        try:
            payload = {
                "tool_name": tool_name,
                "arguments": arguments
            }
            
            headers = {
                "X-Session-ID": session_id
            }
            
            response = await self.mcp_client.post(
                "/api/tools/execute",
                json=payload,
                headers=headers
            )
            
            if response.get("status") != "success":
                error = response.get("error", {})
                error_msg = error.get("message", "Tool execution failed")
                error_code = error.get("code", "")
                
                if "not found" in error_msg.lower() or error_code == "TOOL_NOT_FOUND":
                    raise NotFoundError(f"Tool '{tool_name}' not found")
                
                raise ValidationError(error_msg)
            
            return response.get("data", {})
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            raise ValidationError(f"Failed to execute tool: {str(e)}")


from typing import Optional

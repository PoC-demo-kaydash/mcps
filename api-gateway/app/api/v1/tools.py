"""
Tool management and execution API endpoints
"""
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
from ...models.request import ExecuteToolRequest
from ...models.response import SuccessResponse, ToolListResponse, ToolInfo, ToolExecutionResponse
from ...services.tool_service import ToolService
from ...core.dependencies import get_current_user, get_tool_service

router = APIRouter(prefix="/api/v1/tools", tags=["Tools"])


@router.get("/list", response_model=SuccessResponse[ToolListResponse])
async def list_tools(
    current_user: Dict[str, Any] = Depends(get_current_user),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Get list of available tools
    
    Requires authentication.
    
    Returns:
        List of available tools with descriptions
    """
    session_id = current_user.get("session_id")
    
    # Get tools from MCP Host
    tools_data = await tool_service.list_tools(session_id=session_id)
    
    # Convert to response model
    tools = [
        ToolInfo(
            name=tool.get("name"),
            description=tool.get("description", ""),
            server=tool.get("server", "unknown"),
            parameters=tool.get("parameters", {})
        )
        for tool in tools_data
    ]
    
    response = ToolListResponse(
        tools=tools,
        total=len(tools)
    )
    
    return SuccessResponse(data=response)


@router.get("/{tool_name}", response_model=SuccessResponse[ToolInfo])
async def get_tool_info(
    tool_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Get information about a specific tool
    
    Requires authentication.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tool information including parameters schema
    """
    session_id = current_user.get("session_id")
    
    # Get tool info from MCP Host
    tool_data = await tool_service.get_tool_info(tool_name, session_id=session_id)
    
    # Convert to response model
    tool_info = ToolInfo(
        name=tool_data.get("name"),
        description=tool_data.get("description", ""),
        server=tool_data.get("server", "unknown"),
        parameters=tool_data.get("parameters", {})
    )
    
    return SuccessResponse(data=tool_info)


@router.post("/execute", response_model=SuccessResponse[ToolExecutionResponse])
async def execute_tool(
    request: ExecuteToolRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Execute a tool with given arguments
    
    Requires authentication.
    
    Args:
        request: Tool execution request with tool_name and arguments
        
    Returns:
        Tool execution result
    """
    # Use session from request or current user's session
    session_id = request.session_id or current_user.get("session_id")
    
    # Execute tool via MCP Host
    result = await tool_service.execute_tool(
        tool_name=request.tool_name,
        arguments=request.arguments,
        session_id=session_id
    )
    
    # Convert to response model
    response_data = ToolExecutionResponse(
        tool_name=request.tool_name,
        result=result.get("result"),
        execution_time=result.get("execution_time", 0.0),
        success=result.get("success", True),
        error=result.get("error")
    )
    
    return SuccessResponse(data=response_data)

"""
Admin API endpoints for system management
"""
from fastapi import APIRouter, Depends, Query, Path
from typing import Dict, Any, Optional
from ...models.request import GrantPermissionRequest, RevokePermissionRequest
from ...models.response import (
    SuccessResponse,
    SystemStatsResponse,
    AuditLogListResponse,
    AuditLogResponse,
    PermissionResponse
)
from ...services.mcp_client import MCPClient
from ...core.dependencies import get_current_user
from ...core.exceptions import AuthorizationError

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/stats", response_model=SuccessResponse[SystemStatsResponse])
async def get_system_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get system statistics
    
    Requires authentication and Admin role.
    
    Returns:
        System statistics including users, sessions, documents, etc.
    """
    # TODO: Check if current user has Admin role
    # For now, allow access (should be restricted in production)
    
    mcp_client = MCPClient()
    
    try:
        response = await mcp_client.get(
            "/api/admin/stats",
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        stats_data = response.get("data", {})
        stats = SystemStatsResponse(**stats_data)
        
        return SuccessResponse(data=stats)
        
    finally:
        await mcp_client.close()


@router.get("/audit-logs", response_model=SuccessResponse[AuditLogListResponse])
async def get_audit_logs(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Page size"),
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    action: Optional[str] = Query(default=None, description="Filter by action"),
    resource_type: Optional[str] = Query(default=None, description="Filter by resource type"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get audit logs
    
    Requires authentication and Admin role.
    
    Args:
        page: Page number
        page_size: Page size
        user_id: Filter by user ID
        action: Filter by action
        resource_type: Filter by resource type
        
    Returns:
        Paginated list of audit logs
    """
    # TODO: Check if current user has Admin role
    
    mcp_client = MCPClient()
    
    try:
        # Build query parameters
        params = {
            "page": page,
            "page_size": page_size
        }
        if user_id:
            params["user_id"] = user_id
        if action:
            params["action"] = action
        if resource_type:
            params["resource_type"] = resource_type
        
        response = await mcp_client.get(
            "/api/admin/audit-logs",
            params=params,
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        logs_data = response.get("data", {})
        
        logs = [AuditLogResponse(**log) for log in logs_data.get("logs", [])]
        
        response_data = AuditLogListResponse(
            logs=logs,
            total=logs_data.get("total", 0),
            page=page,
            page_size=page_size
        )
        
        return SuccessResponse(data=response_data)
        
    finally:
        await mcp_client.close()


@router.post("/permissions/grant", response_model=SuccessResponse[PermissionResponse])
async def grant_permission(
    request: GrantPermissionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Grant permission to a user
    
    Requires authentication and Manager role or higher.
    
    Args:
        request: Permission grant request
        
    Returns:
        Created permission
    """
    # TODO: Check if current user has Manager+ role
    
    mcp_client = MCPClient()
    
    try:
        response = await mcp_client.post(
            "/api/admin/permissions/grant",
            json=request.dict(),
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        permission_data = response.get("data", {})
        permission = PermissionResponse(**permission_data)
        
        return SuccessResponse(data=permission)
        
    finally:
        await mcp_client.close()


@router.delete("/permissions/revoke", response_model=SuccessResponse[Dict[str, str]])
async def revoke_permission(
    request: RevokePermissionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Revoke permission from a user
    
    Requires authentication and Manager role or higher.
    
    Args:
        request: Permission revoke request
        
    Returns:
        Confirmation message
    """
    # TODO: Check if current user has Manager+ role
    
    mcp_client = MCPClient()
    
    try:
        response = await mcp_client.post(
            "/api/admin/permissions/revoke",
            json=request.dict(),
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        return SuccessResponse(data={"message": "Permission revoked successfully"})
        
    finally:
        await mcp_client.close()

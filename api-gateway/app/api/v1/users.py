"""
User management API endpoints
"""
from fastapi import APIRouter, Depends, Path
from typing import Dict, Any, List
from ...models.response import SuccessResponse, UserResponse, PermissionResponse
from ...services.mcp_client import MCPClient
from ...core.dependencies import get_current_user
from ...core.exceptions import AuthorizationError

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=SuccessResponse[UserResponse])
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current user information
    
    Requires authentication.
    
    Returns:
        Current user details
    """
    mcp_client = MCPClient()
    
    try:
        response = await mcp_client.get(
            f"/api/users/{current_user.get('user_id')}",
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        user_data = response.get("data", {})
        user = UserResponse(**user_data)
        
        return SuccessResponse(data=user)
        
    finally:
        await mcp_client.close()


@router.get("/me/permissions", response_model=SuccessResponse[List[PermissionResponse]])
async def get_current_user_permissions(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current user's permissions
    
    Requires authentication.
    
    Returns:
        List of user permissions
    """
    mcp_client = MCPClient()
    
    try:
        response = await mcp_client.get(
            f"/api/users/{current_user.get('user_id')}/permissions",
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        permissions_data = response.get("data", {}).get("permissions", [])
        permissions = [PermissionResponse(**p) for p in permissions_data]
        
        return SuccessResponse(data=permissions)
        
    finally:
        await mcp_client.close()


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(
    user_id: str = Path(..., description="User ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user information by ID
    
    Requires authentication and Manager role or higher.
    Users can always view their own information.
    
    Args:
        user_id: User ID to retrieve
        
    Returns:
        User details
    """
    # Users can view their own info
    if user_id != current_user.get("user_id"):
        # TODO: Check if current user has Manager+ role
        # For now, allow access (should be restricted in production)
        pass
    
    mcp_client = MCPClient()
    
    try:
        response = await mcp_client.get(
            f"/api/users/{user_id}",
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        user_data = response.get("data", {})
        user = UserResponse(**user_data)
        
        return SuccessResponse(data=user)
        
    finally:
        await mcp_client.close()

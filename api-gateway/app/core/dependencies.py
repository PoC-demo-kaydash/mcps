"""
FastAPI dependencies for dependency injection
"""
from typing import Optional, Callable
from fastapi import Depends, Header
from .security import verify_session_token
from .exceptions import AuthenticationError, AuthorizationError


# Role hierarchy mapping
ROLE_HIERARCHY = {
    "junior": 0,
    "staff": 1,
    "manager": 2,
    "executive": 2,
    "admin": 3
}


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Get current authenticated user from JWT token
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        Dictionary with user_id and session_id
        
    Raises:
        AuthenticationError: If authentication fails
    """
    if not authorization:
        raise AuthenticationError("Missing authorization header")
    
    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format. Expected: Bearer <token>")
    
    token = parts[1]
    
    try:
        user_id, session_id = verify_session_token(token)
        return {
            "user_id": user_id,
            "session_id": session_id
        }
    except Exception as e:
        raise AuthenticationError(str(e))


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        Dictionary with user_id and session_id, or None
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except AuthenticationError:
        return None


def require_role(required_role: str) -> Callable:
    """
    Dependency factory to require specific role or higher
    
    Args:
        required_role: Minimum required role (junior, staff, manager, executive, admin)
        
    Returns:
        FastAPI dependency function
        
    Example:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        # In a real implementation, we would fetch user role from database or MCP Host
        # For now, we'll assume the role is passed in the token or needs to be fetched
        
        # TODO: Fetch user role from MCP Host using session_id
        # For now, raise an authorization error as a placeholder
        
        # This is a simplified version - in production, fetch actual role
        user_role = current_user.get("role", "junior")
        
        required_level = ROLE_HIERARCHY.get(required_role.lower(), 0)
        user_level = ROLE_HIERARCHY.get(user_role.lower(), 0)
        
        if user_level < required_level:
            raise AuthorizationError(
                f"Insufficient permissions. Required: {required_role}, Current: {user_role}"
            )
        
        return current_user
    
    return role_checker


async def get_session_service():
    """
    Get session service instance
    
    Returns:
        SessionService instance
    """
    from ..services.session_service import SessionService
    return SessionService()


async def get_cache_service():
    """
    Get cache service instance
    
    Returns:
        CacheService instance
    """
    from ..services.cache_service import CacheService
    return CacheService()


async def get_tool_service():
    """
    Get tool service instance
    
    Returns:
        ToolService instance
    """
    from ..services.tool_service import ToolService
    return ToolService()


async def get_auth_service():
    """
    Get auth service instance
    
    Returns:
        AuthService instance
    """
    from ..services.auth_service import AuthService
    return AuthService()

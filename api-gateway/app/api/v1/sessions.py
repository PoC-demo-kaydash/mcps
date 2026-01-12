"""
Session management API endpoints
"""
from fastapi import APIRouter, Depends, status
from typing import Dict, Any
from ...models.request import CreateSessionRequest
from ...models.response import SuccessResponse, SessionResponse
from ...services.session_service import SessionService
from ...services.auth_service import AuthService
from ...core.dependencies import get_current_user, get_session_service, get_auth_service
from ...core.exceptions import ValidationError

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


@router.post("", response_model=SuccessResponse[SessionResponse], status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    session_service: SessionService = Depends(get_session_service),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Create a new session
    
    This endpoint is public - no authentication required
    
    Args:
        request: Session creation request with user_id and optional password
        
    Returns:
        Created session information with JWT token
    """
    # Create session via MCP Host
    session_data = await session_service.create_session(
        user_id=request.user_id,
        password=request.password,
        metadata=request.metadata
    )
    
    # Generate JWT token for this session
    token = await auth_service.create_token(
        user_id=request.user_id,
        session_id=session_data.get("session_id")
    )
    
    # Build response
    response_data = SessionResponse(
        session_id=session_data.get("session_id"),
        user_id=request.user_id,
        token=token,
        created_at=session_data.get("created_at"),
        expires_at=session_data.get("expires_at"),
        metadata=session_data.get("metadata", {})
    )
    
    return SuccessResponse(data=response_data)


@router.get("/{session_id}", response_model=SuccessResponse[SessionResponse])
async def get_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Get session information
    
    Requires authentication. Users can only access their own sessions.
    
    Args:
        session_id: Session ID to retrieve
        
    Returns:
        Session information
    """
    # Verify user can access this session
    if current_user.get("session_id") != session_id:
        raise ValidationError("You can only access your own session")
    
    # Get session data
    session_data = await session_service.get_session(session_id)
    
    # Build response
    response_data = SessionResponse(
        session_id=session_data.get("session_id"),
        user_id=session_data.get("user_id"),
        token=None,  # Don't return token in get
        created_at=session_data.get("created_at"),
        expires_at=session_data.get("expires_at"),
        metadata=session_data.get("metadata", {})
    )
    
    return SuccessResponse(data=response_data)


@router.delete("/{session_id}", response_model=SuccessResponse[Dict[str, str]])
async def delete_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Delete (end) a session
    
    Requires authentication. Users can only delete their own sessions.
    
    Args:
        session_id: Session ID to delete
        
    Returns:
        Confirmation message
    """
    # Verify user can delete this session
    if current_user.get("session_id") != session_id:
        raise ValidationError("You can only delete your own session")
    
    # Delete session
    await session_service.delete_session(session_id)
    
    return SuccessResponse(data={"message": f"Session {session_id} deleted successfully"})

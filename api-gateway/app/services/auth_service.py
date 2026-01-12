"""
Authentication service for user authentication and token management
"""
from typing import Optional, Dict, Any
from ..core.security import verify_password, create_session_token
from ..core.exceptions import AuthenticationError
from .mcp_client import MCPClient


class AuthService:
    """Authentication service"""
    
    def __init__(self):
        self.mcp_client = MCPClient()
    
    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with username and password
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            Dictionary with user information and session
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Call MCP Host to authenticate user
            # In a real implementation, this would call /api/users/authenticate or similar
            response = await self.mcp_client.post(
                "/api/users/authenticate",
                json={"username": username, "password": password}
            )
            
            if response.get("status") != "success":
                raise AuthenticationError("Invalid username or password")
            
            user_data = response.get("data", {})
            return user_data
            
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    async def create_token(self, user_id: str, session_id: str) -> str:
        """
        Create JWT token for authenticated user
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            JWT token string
        """
        return create_session_token(user_id, session_id)
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return user info
        
        Args:
            token: JWT token
            
        Returns:
            Dictionary with user_id and session_id
            
        Raises:
            AuthenticationError: If token is invalid
        """
        from ..core.security import verify_session_token
        
        try:
            user_id, session_id = verify_session_token(token)
            
            # Optionally validate session with MCP Host
            # await self.validate_session(session_id)
            
            return {
                "user_id": user_id,
                "session_id": session_id
            }
        except Exception as e:
            raise AuthenticationError(f"Token validation failed: {str(e)}")
    
    async def validate_session(self, session_id: str) -> bool:
        """
        Validate session with MCP Host
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session is valid
            
        Raises:
            AuthenticationError: If session is invalid
        """
        try:
            response = await self.mcp_client.get(f"/api/sessions/{session_id}")
            
            if response.get("status") != "success":
                raise AuthenticationError("Invalid session")
            
            return True
            
        except Exception as e:
            raise AuthenticationError(f"Session validation failed: {str(e)}")

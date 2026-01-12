"""
Session service for managing user sessions
"""
from typing import Optional, Dict, Any
from datetime import datetime
from ..core.exceptions import NotFoundError, ValidationError
from .mcp_client import MCPClient


class SessionService:
    """Session management service"""
    
    def __init__(self):
        self.mcp_client = MCPClient()
    
    async def create_session(
        self,
        user_id: str,
        password: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new session via MCP Host
        
        Args:
            user_id: User ID
            password: User password (if required)
            metadata: Additional session metadata
            
        Returns:
            Session data including session_id
            
        Raises:
            ValidationError: If session creation fails
        """
        try:
            payload = {
                "user_id": user_id,
                "metadata": metadata or {}
            }
            
            if password:
                payload["password"] = password
            
            response = await self.mcp_client.post("/api/sessions", json=payload)
            
            if response.get("status") != "success":
                error_msg = response.get("error", {}).get("message", "Session creation failed")
                raise ValidationError(error_msg)
            
            return response.get("data", {})
            
        except Exception as e:
            raise ValidationError(f"Failed to create session: {str(e)}")
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get session information
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data
            
        Raises:
            NotFoundError: If session not found
        """
        try:
            response = await self.mcp_client.get(f"/api/sessions/{session_id}")
            
            if response.get("status") != "success":
                raise NotFoundError(f"Session {session_id} not found")
            
            return response.get("data", {})
            
        except NotFoundError:
            raise
        except Exception as e:
            raise NotFoundError(f"Failed to get session: {str(e)}")
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If session not found
        """
        try:
            response = await self.mcp_client.delete(f"/api/sessions/{session_id}")
            
            if response.get("status") != "success":
                raise NotFoundError(f"Session {session_id} not found")
            
            return True
            
        except NotFoundError:
            raise
        except Exception as e:
            raise NotFoundError(f"Failed to delete session: {str(e)}")
    
    async def validate_session(self, session_id: str) -> bool:
        """
        Validate if session exists and is active
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session is valid
        """
        try:
            session = await self.get_session(session_id)
            
            # Check if session has expired
            expires_at = session.get("expires_at")
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                
                if datetime.utcnow() > expires_at:
                    return False
            
            return True
            
        except NotFoundError:
            return False
        except Exception:
            return False

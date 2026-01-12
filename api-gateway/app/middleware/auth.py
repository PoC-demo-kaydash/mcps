"""
Authentication middleware for validating JWT tokens
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.security import verify_session_token
from ..core.exceptions import AuthenticationError
from ..utils.logger import logger


# Public paths that don't require authentication
PUBLIC_PATHS = [
    "/",
    "/health",
    "/ping",
    "/docs",
    "/redoc",
    "/openapi.json",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication"""
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no authentication required)"""
        # Exact match
        if path in PUBLIC_PATHS:
            return True
        
        # POST /api/v1/sessions is public (session creation)
        if path == "/api/v1/sessions" and hasattr(self, '_method') and self._method == "POST":
            return True
        
        # Check if path starts with any public path
        for public_path in PUBLIC_PATHS:
            if path.startswith(public_path):
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        # Store method for checking in _is_public_path
        self._method = request.method
        
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Get authorization header
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            logger.warning(f"Missing authorization header: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error": {
                        "code": "AUTHENTICATION_ERROR",
                        "message": "Missing authorization header",
                        "details": {}
                    }
                }
            )
        
        # Validate Bearer token format
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(f"Invalid authorization header format: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error": {
                        "code": "AUTHENTICATION_ERROR",
                        "message": "Invalid authorization header format. Expected: Bearer <token>",
                        "details": {}
                    }
                }
            )
        
        token = parts[1]
        
        # Verify token
        try:
            user_id, session_id = verify_session_token(token)
            
            # Add user info to request state for use in routes
            request.state.user_id = user_id
            request.state.session_id = session_id
            
            logger.debug(f"Authenticated user: {user_id}")
            
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error": {
                        "code": "AUTHENTICATION_ERROR",
                        "message": str(e),
                        "details": {}
                    }
                }
            )
        except Exception as e:
            logger.error(f"Unexpected authentication error: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error": {
                        "code": "AUTHENTICATION_ERROR",
                        "message": "Authentication failed",
                        "details": {}
                    }
                }
            )
        
        # Continue with request
        response = await call_next(request)
        return response

"""
Custom exceptions for API Gateway
"""
from typing import Optional, Dict, Any


class APIGatewayException(Exception):
    """Base exception for API Gateway"""
    
    def __init__(
        self,
        message: str,
        code: str = "API_GATEWAY_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(APIGatewayException):
    """Authentication failed (401)"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class AuthorizationError(APIGatewayException):
    """Authorization failed - insufficient permissions (403)"""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )


class ValidationError(APIGatewayException):
    """Request validation failed (400)"""
    
    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class NotFoundError(APIGatewayException):
    """Resource not found (404)"""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details
        )


class ConflictError(APIGatewayException):
    """Resource conflict (409)"""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details
        )


class RateLimitExceeded(APIGatewayException):
    """Rate limit exceeded (429)"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )


class ServiceUnavailable(APIGatewayException):
    """Service unavailable (503)"""
    
    def __init__(self, message: str = "Service temporarily unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=503,
            details=details
        )


class MCPHostError(APIGatewayException):
    """MCP Host communication error"""
    
    def __init__(self, message: str = "MCP Host error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="MCP_HOST_ERROR",
            status_code=502,
            details=details
        )

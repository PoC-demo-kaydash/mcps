"""
Global error handler middleware for catching and formatting exceptions
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.exceptions import APIGatewayException
from ..utils.logger import logger


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions and format error responses"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except APIGatewayException as e:
            # Handle custom API Gateway exceptions
            logger.warning(
                f"API Gateway Exception: {e.code} - {e.message}",
                extra={
                    "code": e.code,
                    "status_code": e.status_code,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "status": "error",
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "details": e.details
                    }
                }
            )
            
        except ValueError as e:
            # Handle validation errors
            logger.warning(f"Validation error: {str(e)}")
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(e),
                        "details": {}
                    }
                }
            )
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(
                f"Unhandled exception: {str(e)}",
                exc_info=True,
                extra={
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {}
                    }
                }
            )

"""
Rate limiting middleware using Redis
"""
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.config import settings
from ..services.cache_service import CacheService
from ..utils.logger import logger
from ..utils.metrics import record_rate_limit_exceeded


# Paths exempt from rate limiting
RATE_LIMIT_EXEMPT_PATHS = [
    "/health",
    "/ping",
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting using Redis"""
    
    def __init__(self, app):
        super().__init__(app)
        self.cache_service = CacheService()
        self.enabled = settings.rate_limit_enabled
        self.max_requests = settings.rate_limit_requests
        self.period = settings.rate_limit_period
    
    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting"""
        for exempt_path in RATE_LIMIT_EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check X-Forwarded-For header (if behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Use direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def dispatch(self, request: Request, call_next):
        # Skip if rate limiting is disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip exempt paths
        if self._is_exempt(request.url.path):
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)
        
        # Create rate limit key
        rate_limit_key = f"rate_limit:{client_ip}"
        
        try:
            # Get current request count
            current_count = await self.cache_service.get(rate_limit_key)
            
            if current_count is None:
                # First request in this period
                await self.cache_service.set(rate_limit_key, 1, ttl=self.period)
                current_count = 1
            else:
                current_count = int(current_count)
                
                # Check if limit exceeded
                if current_count >= self.max_requests:
                    logger.warning(
                        f"Rate limit exceeded for {client_ip}",
                        extra={
                            "client_ip": client_ip,
                            "path": request.url.path,
                            "count": current_count,
                            "limit": self.max_requests
                        }
                    )
                    
                    # Record metric
                    record_rate_limit_exceeded()
                    
                    # Get TTL for retry-after header
                    # Note: This is a simplified version. In production, you'd want to
                    # track the exact TTL from Redis
                    retry_after = self.period
                    
                    return JSONResponse(
                        status_code=429,
                        headers={"Retry-After": str(retry_after)},
                        content={
                            "status": "error",
                            "error": {
                                "code": "RATE_LIMIT_EXCEEDED",
                                "message": f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.period} seconds.",
                                "details": {
                                    "limit": self.max_requests,
                                    "period": self.period,
                                    "retry_after": retry_after
                                }
                            }
                        }
                    )
                
                # Increment counter
                await self.cache_service.incr(rate_limit_key)
                current_count += 1
            
            # Add rate limit headers to response
            response = await call_next(request)
            
            response.headers["X-RateLimit-Limit"] = str(self.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - current_count))
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.period)
            
            return response
            
        except Exception as e:
            # If rate limiting fails, log error but allow request to proceed
            logger.error(f"Rate limiting error: {str(e)}")
            return await call_next(request)

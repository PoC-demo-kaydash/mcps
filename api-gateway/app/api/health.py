"""
Health check endpoints
"""
from fastapi import APIRouter, Depends
from datetime import datetime
from ..models.response import HealthResponse
from ..services.mcp_client import MCPClient
from ..services.cache_service import CacheService

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns service health status including MCP Host and Redis connectivity
    """
    # Check MCP Host
    mcp_client = MCPClient()
    mcp_status = "healthy" if await mcp_client.health_check() else "unhealthy"
    await mcp_client.close()
    
    # Check Redis
    cache_service = CacheService()
    redis_status = "healthy" if await cache_service.ping() else "unhealthy"
    await cache_service.close()
    
    return HealthResponse(
        status="healthy" if mcp_status == "healthy" else "degraded",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        mcp_host_status=mcp_status,
        redis_status=redis_status
    )


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint
    
    Returns basic response to check if service is running
    """
    return {
        "status": "success",
        "data": {
            "message": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }
    }

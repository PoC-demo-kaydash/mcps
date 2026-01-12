"""
API Gateway - FastAPI Application

This is the main entry point for the API Gateway service.
It provides a unified REST API for interacting with the MCP Host.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.utils.logger import logger
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.api import health
from app.api.v1 import sessions, tools, documents, users, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting API Gateway...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"MCP Host URL: {settings.mcp_host_url}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API Gateway...")


# Create FastAPI application
app = FastAPI(
    title="MCP API Gateway",
    description="API Gateway for Model Context Protocol Host",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan
)

# CORS Middleware (must be first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error Handler Middleware
app.add_middleware(ErrorHandlerMiddleware)

# Logging Middleware
app.add_middleware(LoggingMiddleware)

# Auth Middleware
app.add_middleware(AuthMiddleware)

# Rate Limit Middleware (must be last)
app.add_middleware(RateLimitMiddleware)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - Service information
    """
    return JSONResponse(
        content={
            "status": "success",
            "data": {
                "service": "MCP API Gateway",
                "version": "1.0.0",
                "environment": settings.environment,
                "endpoints": {
                    "health": "/health",
                    "docs": "/docs" if not settings.is_production else "disabled",
                    "api": "/api/v1"
                }
            }
        }
    )


# Include routers
app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(tools.router)
app.include_router(documents.router)
app.include_router(users.router)
app.include_router(admin.router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

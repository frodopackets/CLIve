"""
FastAPI backend entry point for AI Assistant CLI
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import configuration
from backend.config import settings

# Import middleware
from backend.middleware.cors import add_cors_middleware
from backend.middleware.logging import LoggingMiddleware
from backend.middleware.error_handling import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

# Import routers
from backend.routers import health, sessions, knowledge_bases, websocket, bedrock, agent

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("ai-assistant-cli")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan event handler
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"AWS Region: {settings.aws_region}")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Backend API for web-based AI Assistant CLI with real-time communication",
    version=settings.app_version,
    debug=settings.debug,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add middleware
add_cors_middleware(app)
app.add_middleware(LoggingMiddleware)

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(knowledge_bases.router)
app.include_router(websocket.router)
app.include_router(bedrock.router)
app.include_router(agent.router)

@app.get("/")
async def root():
    """
    Root endpoint providing basic API information
    """
    return {
        "message": "AI Assistant CLI Backend is running",
        "version": settings.app_version,
        "docs_url": "/api/docs" if settings.debug else "Documentation disabled in production",
        "health_check": "/api/v1/health"
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
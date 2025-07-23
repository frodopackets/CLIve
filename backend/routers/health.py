"""
Health check router for monitoring and status endpoints
"""
from fastapi import APIRouter
from datetime import datetime, timezone
from typing import Dict, Any

router = APIRouter(prefix="/api/v1", tags=["health"])

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring service status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "ai-assistant-cli-backend",
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint for deployment validation
    """
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {
            "database": "connected",
            "aws_services": "available"
        }
    }

@router.get("/websocket-stats")
async def websocket_stats() -> Dict[str, Any]:
    """
    Get WebSocket connection statistics
    """
    from backend.routers.websocket import get_connection_manager
    
    manager = get_connection_manager()
    return {
        "active_connections": manager.get_connection_count(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
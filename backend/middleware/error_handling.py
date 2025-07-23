"""
Error handling middleware and exception handlers
"""
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger("ai-assistant-cli")

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with structured error responses
    """
    error_response = {
        "error_code": f"HTTP_{exc.status_code}",
        "error_message": exc.detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": getattr(request.state, "request_id", "unknown"),
        "path": str(request.url.path)
    }
    
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation errors
    """
    error_response = {
        "error_code": "VALIDATION_ERROR",
        "error_message": "Request validation failed",
        "details": exc.errors(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": getattr(request.state, "request_id", "unknown"),
        "path": str(request.url.path)
    }
    
    logger.error(f"Validation Error: {exc.errors()} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=422,
        content=error_response
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions with generic error response
    """
    error_response = {
        "error_code": "INTERNAL_SERVER_ERROR",
        "error_message": "An internal server error occurred",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": getattr(request.state, "request_id", "unknown"),
        "path": str(request.url.path)
    }
    
    logger.error(f"Unhandled Exception: {type(exc).__name__}: {str(exc)} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )
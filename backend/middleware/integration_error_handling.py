"""
Comprehensive error handling middleware for integration service
"""

import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from functools import wraps

from fastapi import HTTPException, status
from botocore.exceptions import ClientError, BotoCoreError


logger = logging.getLogger(__name__)


class IntegrationErrorHandler:
    """
    Centralized error handling for integration service
    Provides consistent error responses and logging across all services
    """
    
    @staticmethod
    def handle_service_error(service_name: str, error: Exception) -> Dict[str, Any]:
        """
        Handle errors from various services with appropriate error responses
        
        Args:
            service_name: Name of the service that generated the error
            error: The exception that occurred
            
        Returns:
            Dict: Standardized error response
        """
        error_response = {
            "type": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": service_name
        }
        
        if isinstance(error, HTTPException):
            # Handle FastAPI HTTP exceptions
            error_response.update({
                "content": error.detail,
                "status_code": error.status_code,
                "error_type": "http_exception"
            })
            logger.warning(f"{service_name} HTTP error {error.status_code}: {error.detail}")
            
        elif isinstance(error, ClientError):
            # Handle AWS service client errors
            error_code = error.response['Error']['Code']
            error_message = error.response['Error']['Message']
            
            error_response.update({
                "content": IntegrationErrorHandler._get_user_friendly_aws_error(error_code, error_message),
                "error_type": "aws_client_error",
                "aws_error_code": error_code
            })
            logger.error(f"{service_name} AWS ClientError {error_code}: {error_message}")
            
        elif isinstance(error, BotoCoreError):
            # Handle AWS SDK core errors
            error_response.update({
                "content": "AWS service connection error. Please try again later.",
                "error_type": "aws_connection_error"
            })
            logger.error(f"{service_name} AWS BotoCoreError: {str(error)}")
            
        elif isinstance(error, TimeoutError):
            # Handle timeout errors
            error_response.update({
                "content": f"{service_name} service timeout. Please try again.",
                "error_type": "timeout_error"
            })
            logger.error(f"{service_name} timeout error: {str(error)}")
            
        elif isinstance(error, ConnectionError):
            # Handle connection errors
            error_response.update({
                "content": f"Connection error with {service_name}. Please check your network.",
                "error_type": "connection_error"
            })
            logger.error(f"{service_name} connection error: {str(error)}")
            
        else:
            # Handle unexpected errors
            error_response.update({
                "content": f"An unexpected error occurred in {service_name}. Please try again.",
                "error_type": "unexpected_error"
            })
            logger.error(f"{service_name} unexpected error: {str(error)}\n{traceback.format_exc()}")
        
        return error_response
    
    @staticmethod
    def _get_user_friendly_aws_error(error_code: str, error_message: str) -> str:
        """
        Convert AWS error codes to user-friendly messages
        
        Args:
            error_code: AWS error code
            error_message: AWS error message
            
        Returns:
            str: User-friendly error message
        """
        error_mappings = {
            'AccessDeniedException': "You don't have permission to access this resource.",
            'ThrottlingException': "Service is busy. Please try again in a moment.",
            'ValidationException': "Invalid request parameters. Please check your input.",
            'ResourceNotFoundException': "The requested resource was not found.",
            'ServiceUnavailableException': "Service is temporarily unavailable. Please try again later.",
            'InternalServerException': "Internal service error. Please try again later.",
            'ModelNotReadyException': "AI model is not ready. Please try again in a moment.",
            'ModelTimeoutException': "AI model request timed out. Please try again.",
            'ModelErrorException': "AI model encountered an error. Please try again.",
            'ConflictException': "Request conflicts with current state. Please refresh and try again.",
            'LimitExceededException': "Request limit exceeded. Please try again later.",
            'InvalidRequestException': "Invalid request format. Please check your input."
        }
        
        return error_mappings.get(error_code, f"Service error: {error_message}")
    
    @staticmethod
    def create_error_response(message: str, error_type: str = "general_error", **kwargs) -> Dict[str, Any]:
        """
        Create a standardized error response
        
        Args:
            message: Error message for the user
            error_type: Type of error for logging/debugging
            **kwargs: Additional error context
            
        Returns:
            Dict: Standardized error response
        """
        response = {
            "type": "error",
            "content": message,
            "error_type": error_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if kwargs:
            response["metadata"] = kwargs
        
        return response


def handle_integration_errors(service_name: str):
    """
    Decorator for handling errors in integration service methods
    
    Args:
        service_name: Name of the service for error context
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Handle both sync and async functions
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                error_response = IntegrationErrorHandler.handle_service_error(service_name, e)
                
                # For async generators, yield the error
                if hasattr(func, '__annotations__') and 'AsyncGenerator' in str(func.__annotations__.get('return', '')):
                    async def error_generator():
                        yield error_response
                    return error_generator()
                else:
                    return error_response
        
        return wrapper
    return decorator


def handle_websocket_errors(func):
    """
    Decorator for handling WebSocket-specific errors
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"WebSocket error in {func.__name__}: {str(e)}")
            
            # Try to send error to WebSocket if manager is available
            try:
                from backend.routers.websocket import manager
                if len(args) > 0 and isinstance(args[0], str):  # session_id
                    session_id = args[0]
                    error_response = IntegrationErrorHandler.handle_service_error("websocket", e)
                    await manager.send_to_session(session_id, error_response)
            except Exception as send_error:
                logger.error(f"Failed to send WebSocket error response: {str(send_error)}")
            
            # Re-raise for proper error handling
            raise
    
    return wrapper


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for service resilience
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection
        """
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = datetime.now(timezone.utc) - self.last_failure_time
        return time_since_failure.total_seconds() > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


# Global circuit breakers for different services
bedrock_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
knowledge_base_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
agent_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)


def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """
    Decorator to add circuit breaker protection to service calls
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await circuit_breaker.call(func, *args, **kwargs)
                else:
                    return circuit_breaker.call(func, *args, **kwargs)
            except Exception as e:
                # Convert circuit breaker exceptions to user-friendly errors
                if "Circuit breaker is OPEN" in str(e):
                    service_name = func.__module__.split('.')[-1] if hasattr(func, '__module__') else "service"
                    return IntegrationErrorHandler.create_error_response(
                        f"{service_name.title()} is temporarily unavailable. Please try again later.",
                        "circuit_breaker_open"
                    )
                raise
        
        return wrapper
    return decorator


# Import asyncio for async function detection
import asyncio
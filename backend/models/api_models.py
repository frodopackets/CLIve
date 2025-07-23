"""
Pydantic models for API request/response validation
"""

from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .enums import MessageType, SessionStatus, AgentResponseType, KnowledgeBaseStatus


class SessionCreateRequest(BaseModel):
    """Request model for creating a new session"""
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    knowledge_base_id: Optional[str] = Field(None, description="Optional knowledge base ID to use")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v.strip():
            raise ValueError('user_id cannot be empty or whitespace')
        return v.strip()


class SessionResponse(BaseModel):
    """Response model for session data"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    knowledge_base_id: Optional[str] = Field(None, description="Active knowledge base ID")
    status: SessionStatus = Field(..., description="Session status")
    message_count: int = Field(0, description="Number of messages in conversation")
    
    model_config = ConfigDict(use_enum_values=True)


class MessageRequest(BaseModel):
    """Request model for sending a message"""
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    message_type: MessageType = Field(MessageType.USER, description="Type of message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional message metadata")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('content cannot be empty or whitespace')
        return v.strip()
    
    model_config = ConfigDict(use_enum_values=True)


class MessageResponse(BaseModel):
    """Response model for message data"""
    message_id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Session identifier")
    content: str = Field(..., description="Message content")
    message_type: MessageType = Field(..., description="Type of message")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")
    
    model_config = ConfigDict(use_enum_values=True)


class KnowledgeBaseResponse(BaseModel):
    """Response model for knowledge base data"""
    knowledge_base_id: str = Field(..., description="Unique knowledge base identifier")
    name: str = Field(..., description="Knowledge base name")
    description: str = Field(..., description="Knowledge base description")
    status: KnowledgeBaseStatus = Field(..., description="Knowledge base status")
    created_date: datetime = Field(..., description="Creation timestamp")
    updated_date: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Whether the knowledge base is active")
    display_name: str = Field(..., description="Formatted display name with status indicator")
    
    model_config = ConfigDict(use_enum_values=True)


class AgentResponseModel(BaseModel):
    """Response model for agent data"""
    agent_id: str = Field(..., description="Agent identifier")
    response_type: AgentResponseType = Field(..., description="Type of agent response")
    data: Dict[str, Any] = Field(..., description="Agent response data")
    location: str = Field("Birmingham, Alabama", description="Location for the response")
    timestamp: datetime = Field(..., description="Response timestamp")
    formatted_response: str = Field(..., description="Human-readable formatted response")
    
    model_config = ConfigDict(use_enum_values=True)


class ErrorResponse(BaseModel):
    """Response model for API errors"""
    error_code: str = Field(..., description="Error code identifier")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    
    @field_validator('error_code')
    @classmethod
    def validate_error_code(cls, v):
        if not v.strip():
            raise ValueError('error_code cannot be empty')
        return v.upper()


class WebSocketMessage(BaseModel):
    """Model for WebSocket message communication"""
    type: str = Field(..., description="Message type (command, response, error, status)")
    content: str = Field(..., description="Message content")
    session_id: str = Field(..., description="Session identifier")
    knowledge_base_id: Optional[str] = Field(None, description="Knowledge base identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed_types = ['command', 'response', 'error', 'status']
        if v not in allowed_types:
            raise ValueError(f'type must be one of: {allowed_types}')
        return v


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history"""
    session_id: str = Field(..., description="Session identifier")
    messages: List[MessageResponse] = Field(..., description="List of messages in conversation")
    total_count: int = Field(..., description="Total number of messages")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Number of messages per page")


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field("healthy", description="Service health status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Health check timestamp")
    version: str = Field("1.0.0", description="API version")
    services: Dict[str, str] = Field(default_factory=dict, description="Status of dependent services")
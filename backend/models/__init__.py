"""
Data models for AI Assistant CLI Backend
"""

from .enums import MessageType, SessionStatus, AgentResponseType, KnowledgeBaseStatus
from .session import Session
from .message import Message
from .knowledge_base import KnowledgeBase
from .agent_response import AgentResponse
from .api_models import (
    SessionCreateRequest,
    SessionResponse,
    MessageRequest,
    MessageResponse,
    KnowledgeBaseResponse,
    AgentResponseModel,
    ErrorResponse,
    WebSocketMessage,
    ConversationHistoryResponse,
    HealthCheckResponse
)

__all__ = [
    # Enums
    "MessageType",
    "SessionStatus", 
    "AgentResponseType",
    "KnowledgeBaseStatus",
    # Core Models
    "Session",
    "Message",
    "KnowledgeBase",
    "AgentResponse",
    # API Models
    "SessionCreateRequest",
    "SessionResponse",
    "MessageRequest",
    "MessageResponse",
    "KnowledgeBaseResponse",
    "AgentResponseModel",
    "ErrorResponse",
    "WebSocketMessage",
    "ConversationHistoryResponse",
    "HealthCheckResponse"
]
"""
Enums and constants for AI Assistant CLI Backend
"""

from enum import Enum


class MessageType(str, Enum):
    """Types of messages in the conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    AGENT = "agent"
    SYSTEM = "system"


class SessionStatus(str, Enum):
    """Status of a user session"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class AgentResponseType(str, Enum):
    """Types of agent responses"""
    TIME = "time"
    DATE = "date"
    WEATHER = "weather"
    COMBINED = "combined"
    ERROR = "error"


class KnowledgeBaseStatus(str, Enum):
    """Status of knowledge bases"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CREATING = "CREATING"
    DELETING = "DELETING"
    FAILED = "FAILED"
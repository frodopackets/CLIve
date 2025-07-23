"""
Message data model for AI Assistant CLI
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, Any
from uuid import uuid4

from .enums import MessageType


@dataclass
class Message:
    """
    Represents a message in the conversation
    """
    message_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = ""
    content: str = ""
    message_type: MessageType = MessageType.USER
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate message data after initialization"""
        if not self.session_id:
            raise ValueError("session_id is required")
        
        if not self.content.strip():
            raise ValueError("content cannot be empty")
        
        if self.timestamp > datetime.now(UTC):
            raise ValueError("timestamp cannot be in the future")
        
        # Validate content length
        if len(self.content) > 10000:  # 10KB limit
            raise ValueError("content exceeds maximum length of 10000 characters")
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the message"""
        if not key:
            raise ValueError("metadata key cannot be empty")
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key"""
        return self.metadata.get(key, default)
    
    def is_from_user(self) -> bool:
        """Check if message is from user"""
        return self.message_type == MessageType.USER
    
    def is_from_assistant(self) -> bool:
        """Check if message is from assistant"""
        return self.message_type == MessageType.ASSISTANT
    
    def is_from_agent(self) -> bool:
        """Check if message is from agent"""
        return self.message_type == MessageType.AGENT
    
    def is_system_message(self) -> bool:
        """Check if message is a system message"""
        return self.message_type == MessageType.SYSTEM
    
    def to_dict(self) -> dict:
        """Convert message to dictionary for storage"""
        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create message from dictionary"""
        return cls(
            message_id=data["message_id"],
            session_id=data["session_id"],
            content=data["content"],
            message_type=MessageType(data["message_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )
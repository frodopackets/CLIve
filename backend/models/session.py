"""
Session data model for AI Assistant CLI
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import List, Optional
from uuid import uuid4

from .enums import SessionStatus
from .message import Message


@dataclass
class Session:
    """
    Represents a user session with conversation history
    """
    session_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = field(default_factory=lambda: datetime.now(UTC))
    knowledge_base_id: Optional[str] = None
    conversation_history: List[Message] = field(default_factory=list)
    status: SessionStatus = SessionStatus.ACTIVE
    
    def __post_init__(self):
        """Validate session data after initialization"""
        if not self.user_id:
            raise ValueError("user_id is required")
        
        if self.created_at > datetime.now(UTC):
            raise ValueError("created_at cannot be in the future")
            
        if self.last_activity < self.created_at:
            raise ValueError("last_activity cannot be before created_at")
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation history"""
        if message.session_id != self.session_id:
            raise ValueError("Message session_id must match session session_id")
        
        self.conversation_history.append(message)
        self.last_activity = datetime.now(UTC)
    
    def is_expired(self, timeout_hours: int = 24) -> bool:
        """Check if session has expired based on last activity"""
        time_diff = datetime.now(UTC) - self.last_activity
        return time_diff.total_seconds() > (timeout_hours * 3600)
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get the most recent messages from conversation history"""
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def to_dict(self) -> dict:
        """Convert session to dictionary for storage"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "knowledge_base_id": self.knowledge_base_id,
            "conversation_history": [msg.to_dict() for msg in self.conversation_history],
            "status": self.status.value
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create session from dictionary"""
        conversation_history = [
            Message.from_dict(msg_data) 
            for msg_data in data.get("conversation_history", [])
        ]
        
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            knowledge_base_id=data.get("knowledge_base_id"),
            conversation_history=conversation_history,
            status=SessionStatus(data["status"])
        )
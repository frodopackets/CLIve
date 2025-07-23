"""
Knowledge Base data model for AI Assistant CLI
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .enums import KnowledgeBaseStatus


@dataclass
class KnowledgeBase:
    """
    Represents a Bedrock Knowledge Base
    """
    knowledge_base_id: str
    name: str
    description: str
    status: KnowledgeBaseStatus
    created_date: datetime
    updated_date: datetime
    
    def __post_init__(self):
        """Validate knowledge base data after initialization"""
        if not self.knowledge_base_id:
            raise ValueError("knowledge_base_id is required")
        
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        
        if len(self.name) > 100:
            raise ValueError("name cannot exceed 100 characters")
        
        if len(self.description) > 500:
            raise ValueError("description cannot exceed 500 characters")
        
        if self.updated_date < self.created_date:
            raise ValueError("updated_date cannot be before created_date")
    
    def is_active(self) -> bool:
        """Check if knowledge base is active and ready to use"""
        return self.status == KnowledgeBaseStatus.ACTIVE
    
    def is_available(self) -> bool:
        """Check if knowledge base is available for queries"""
        return self.status in [KnowledgeBaseStatus.ACTIVE, KnowledgeBaseStatus.INACTIVE]
    
    def get_display_name(self) -> str:
        """Get formatted display name with status"""
        status_indicator = "✅" if self.is_active() else "⚠️"
        return f"{status_indicator} {self.name}"
    
    def to_dict(self) -> dict:
        """Convert knowledge base to dictionary"""
        return {
            "knowledge_base_id": self.knowledge_base_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "created_date": self.created_date.isoformat(),
            "updated_date": self.updated_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeBase":
        """Create knowledge base from dictionary"""
        return cls(
            knowledge_base_id=data["knowledge_base_id"],
            name=data["name"],
            description=data["description"],
            status=KnowledgeBaseStatus(data["status"]),
            created_date=datetime.fromisoformat(data["created_date"]),
            updated_date=datetime.fromisoformat(data["updated_date"])
        )
    
    @classmethod
    def from_bedrock_response(cls, bedrock_data: dict) -> "KnowledgeBase":
        """Create knowledge base from Bedrock API response"""
        return cls(
            knowledge_base_id=bedrock_data["knowledgeBaseId"],
            name=bedrock_data["name"],
            description=bedrock_data.get("description", ""),
            status=KnowledgeBaseStatus(bedrock_data["status"]),
            created_date=datetime.fromisoformat(bedrock_data["createdAt"].replace("Z", "+00:00")),
            updated_date=datetime.fromisoformat(bedrock_data["updatedAt"].replace("Z", "+00:00"))
        )
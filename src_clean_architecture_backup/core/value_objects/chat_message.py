"""
Chat message value object.

Represents an immutable chat message.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(frozen=True)
class ChatMessage:
    """Immutable chat message value object."""
    
    content: str
    role: MessageRole
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def user_message(cls, content: str, metadata: Optional[Dict[str, Any]] = None) -> 'ChatMessage':
        """Create a user message."""
        return cls(
            content=content,
            role=MessageRole.USER,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
    
    @classmethod
    def assistant_message(cls, content: str, metadata: Optional[Dict[str, Any]] = None) -> 'ChatMessage':
        """Create an assistant message."""
        return cls(
            content=content,
            role=MessageRole.ASSISTANT,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
    
    @classmethod
    def system_message(cls, content: str, metadata: Optional[Dict[str, Any]] = None) -> 'ChatMessage':
        """Create a system message."""
        return cls(
            content=content,
            role=MessageRole.SYSTEM,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
    
    def is_user_message(self) -> bool:
        """Check if this is a user message."""
        return self.role == MessageRole.USER
    
    def is_assistant_message(self) -> bool:
        """Check if this is an assistant message."""
        return self.role == MessageRole.ASSISTANT
    
    def is_system_message(self) -> bool:
        """Check if this is a system message."""
        return self.role == MessageRole.SYSTEM
    
    def get_word_count(self) -> int:
        """Get word count of the message content."""
        return len(self.content.split())
    
    def get_char_count(self) -> int:
        """Get character count of the message content."""
        return len(self.content)
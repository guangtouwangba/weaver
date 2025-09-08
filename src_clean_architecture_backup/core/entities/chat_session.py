"""
Chat session entity.

Represents a chat conversation session.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from ..value_objects.chat_message import ChatMessage


@dataclass
class ChatSession:
    """Chat session entity representing a conversation."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    topic_id: Optional[int] = None
    user_id: Optional[int] = None
    
    # Session metadata
    title: Optional[str] = None
    summary: Optional[str] = None
    
    # Messages in the session
    messages: List[ChatMessage] = field(default_factory=list)
    
    # Session state
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None
    
    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the chat session."""
        self.messages.append(message)
        self.last_message_at = message.timestamp
        self.updated_at = datetime.utcnow()
    
    def get_message_count(self) -> int:
        """Get the total number of messages in the session."""
        return len(self.messages)
    
    def get_user_messages(self) -> List[ChatMessage]:
        """Get all user messages."""
        return [msg for msg in self.messages if msg.role.value == "user"]
    
    def get_assistant_messages(self) -> List[ChatMessage]:
        """Get all assistant messages."""
        return [msg for msg in self.messages if msg.role.value == "assistant"]
    
    def get_last_message(self) -> Optional[ChatMessage]:
        """Get the last message in the session."""
        return self.messages[-1] if self.messages else None
    
    def set_title(self, title: str) -> None:
        """Set session title."""
        self.title = title
        self.updated_at = datetime.utcnow()
    
    def set_summary(self, summary: str) -> None:
        """Set session summary."""
        self.summary = summary
        self.updated_at = datetime.utcnow()
    
    def end_session(self) -> None:
        """End the chat session."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def get_conversation_context(self, max_messages: int = 10) -> List[ChatMessage]:
        """Get recent conversation context."""
        return self.messages[-max_messages:] if self.messages else []
    
    def clear_messages(self) -> None:
        """Clear all messages from the session."""
        self.messages.clear()
        self.last_message_at = None
        self.updated_at = datetime.utcnow()
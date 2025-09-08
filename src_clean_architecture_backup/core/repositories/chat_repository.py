"""
Chat repository interface.

Defines the contract for chat session data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.chat_session import ChatSession
from ..value_objects.chat_message import ChatMessage


class ChatRepository(ABC):
    """Abstract repository interface for chat operations."""
    
    @abstractmethod
    async def save_session(self, session: ChatSession) -> None:
        """Save a chat session."""
        pass
    
    @abstractmethod
    async def get_session_by_id(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session by ID."""
        pass
    
    @abstractmethod
    async def list_sessions_by_topic_id(self, topic_id: int, limit: int = 100) -> List[ChatSession]:
        """List chat sessions by topic ID."""
        pass
    
    @abstractmethod
    async def list_sessions_by_user_id(self, user_id: int, limit: int = 100) -> List[ChatSession]:
        """List chat sessions by user ID."""
        pass
    
    @abstractmethod
    async def list_active_sessions(self, limit: int = 100) -> List[ChatSession]:
        """List active chat sessions."""
        pass
    
    @abstractmethod
    async def add_message_to_session(self, session_id: str, message: ChatMessage) -> bool:
        """Add a message to a chat session."""
        pass
    
    @abstractmethod
    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[ChatMessage]:
        """Get messages from a chat session."""
        pass
    
    @abstractmethod
    async def get_recent_messages(self, session_id: str, count: int = 10) -> List[ChatMessage]:
        """Get recent messages from a chat session."""
        pass
    
    @abstractmethod
    async def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title."""
        pass
    
    @abstractmethod
    async def update_session_summary(self, session_id: str, summary: str) -> bool:
        """Update session summary."""
        pass
    
    @abstractmethod
    async def end_session(self, session_id: str) -> bool:
        """End a chat session."""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session."""
        pass
    
    @abstractmethod
    async def clear_session_messages(self, session_id: str) -> bool:
        """Clear all messages from a session."""
        pass
    
    @abstractmethod
    async def count_sessions_by_topic_id(self, topic_id: int) -> int:
        """Count chat sessions by topic ID."""
        pass
    
    @abstractmethod
    async def search_sessions_by_title(self, title_pattern: str, limit: int = 10) -> List[ChatSession]:
        """Search sessions by title pattern."""
        pass
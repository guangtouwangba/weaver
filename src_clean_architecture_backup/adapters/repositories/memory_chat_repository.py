"""
Memory chat repository implementation.

Implements the ChatRepository interface using in-memory storage.
"""

from typing import List, Optional, Dict
import asyncio
from datetime import datetime

from ...core.entities.chat_session import ChatSession
from ...core.repositories.chat_repository import ChatRepository
from ...core.value_objects.chat_message import ChatMessage


class MemoryChatRepository(ChatRepository):
    """In-memory implementation of ChatRepository."""
    
    def __init__(self):
        self._sessions: Dict[str, ChatSession] = {}
        self._lock = asyncio.Lock()
    
    async def save_session(self, session: ChatSession) -> None:
        """Save a chat session."""
        async with self._lock:
            # Create a copy to avoid external modifications
            session_copy = ChatSession(
                id=session.id,
                topic_id=session.topic_id,
                user_id=session.user_id,
                title=session.title,
                summary=session.summary,
                messages=session.messages.copy(),
                is_active=session.is_active,
                created_at=session.created_at,
                updated_at=datetime.utcnow(),
                last_message_at=session.last_message_at
            )
            self._sessions[session.id] = session_copy
    
    async def get_session_by_id(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session by ID."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                return self._copy_session(session)
            return None
    
    async def list_sessions_by_topic_id(self, topic_id: int, limit: int = 100) -> List[ChatSession]:
        """List chat sessions by topic ID."""
        async with self._lock:
            results = []
            for session in self._sessions.values():
                if session.topic_id == topic_id:
                    results.append(self._copy_session(session))
                    if len(results) >= limit:
                        break
            return results
    
    async def list_sessions_by_user_id(self, user_id: int, limit: int = 100) -> List[ChatSession]:
        """List chat sessions by user ID."""
        async with self._lock:
            results = []
            for session in self._sessions.values():
                if session.user_id == user_id:
                    results.append(self._copy_session(session))
                    if len(results) >= limit:
                        break
            return results
    
    async def list_active_sessions(self, limit: int = 100) -> List[ChatSession]:
        """List active chat sessions."""
        async with self._lock:
            results = []
            for session in self._sessions.values():
                if session.is_active:
                    results.append(self._copy_session(session))
                    if len(results) >= limit:
                        break
            return results
    
    async def add_message_to_session(self, session_id: str, message: ChatMessage) -> bool:
        """Add a message to a chat session."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.messages.append(message)
                session.last_message_at = message.timestamp
                session.updated_at = datetime.utcnow()
                return True
            return False
    
    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[ChatMessage]:
        """Get messages from a chat session."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                return session.messages[-limit:] if len(session.messages) > limit else session.messages.copy()
            return []
    
    async def get_recent_messages(self, session_id: str, count: int = 10) -> List[ChatMessage]:
        """Get recent messages from a chat session."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                return session.messages[-count:] if len(session.messages) > count else session.messages.copy()
            return []
    
    async def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.title = title
                session.updated_at = datetime.utcnow()
                return True
            return False
    
    async def update_session_summary(self, session_id: str, summary: str) -> bool:
        """Update session summary."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.summary = summary
                session.updated_at = datetime.utcnow()
                return True
            return False
    
    async def end_session(self, session_id: str) -> bool:
        """End a chat session."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.is_active = False
                session.updated_at = datetime.utcnow()
                return True
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session."""
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    async def clear_session_messages(self, session_id: str) -> bool:
        """Clear all messages from a session."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.messages.clear()
                session.last_message_at = None
                session.updated_at = datetime.utcnow()
                return True
            return False
    
    async def count_sessions_by_topic_id(self, topic_id: int) -> int:
        """Count chat sessions by topic ID."""
        async with self._lock:
            count = 0
            for session in self._sessions.values():
                if session.topic_id == topic_id:
                    count += 1
            return count
    
    async def search_sessions_by_title(self, title_pattern: str, limit: int = 10) -> List[ChatSession]:
        """Search sessions by title pattern."""
        async with self._lock:
            results = []
            pattern_lower = title_pattern.lower()
            
            for session in self._sessions.values():
                if session.title and pattern_lower in session.title.lower():
                    results.append(self._copy_session(session))
                    if len(results) >= limit:
                        break
            return results
    
    def _copy_session(self, session: ChatSession) -> ChatSession:
        """Create a copy of a chat session."""
        return ChatSession(
            id=session.id,
            topic_id=session.topic_id,
            user_id=session.user_id,
            title=session.title,
            summary=session.summary,
            messages=session.messages.copy(),
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_message_at=session.last_message_at
        )
    
    # Utility methods for testing/debugging
    async def clear_all(self) -> None:
        """Clear all sessions (for testing)."""
        async with self._lock:
            self._sessions.clear()
    
    async def get_all_sessions(self) -> List[ChatSession]:
        """Get all sessions (for testing/debugging)."""
        async with self._lock:
            return [self._copy_session(session) for session in self._sessions.values()]
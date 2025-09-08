"""
Chat domain events.

Events related to chat sessions and messages.
"""

from dataclasses import dataclass
from typing import Optional

from .base_event import DomainEvent


@dataclass(frozen=True)
class ChatSessionStartedEvent(DomainEvent):
    """Event fired when a chat session is started."""
    
    topic_id: Optional[int] = None
    user_id: Optional[int] = None
    
    @classmethod
    def create(cls, session_id: str, topic_id: Optional[int] = None, 
               user_id: Optional[int] = None) -> 'ChatSessionStartedEvent':
        return super().create(
            aggregate_id=session_id,
            topic_id=topic_id,
            user_id=user_id
        )


@dataclass(frozen=True)
class MessageSentEvent(DomainEvent):
    """Event fired when a message is sent in a chat session."""
    
    session_id: str
    message_role: str  # user, assistant, system
    message_length: int
    response_time: Optional[float] = None
    
    @classmethod
    def create(cls, message_id: str, session_id: str, message_role: str, 
               message_length: int, response_time: Optional[float] = None) -> 'MessageSentEvent':
        return super().create(
            aggregate_id=message_id,
            session_id=session_id,
            message_role=message_role,
            message_length=message_length,
            response_time=response_time
        )


@dataclass(frozen=True)
class ChatSessionEndedEvent(DomainEvent):
    """Event fired when a chat session is ended."""
    
    message_count: int
    duration_minutes: float
    
    @classmethod
    def create(cls, session_id: str, message_count: int, 
               duration_minutes: float) -> 'ChatSessionEndedEvent':
        return super().create(
            aggregate_id=session_id,
            message_count=message_count,
            duration_minutes=duration_minutes
        )


@dataclass(frozen=True)
class AIResponseGeneratedEvent(DomainEvent):
    """Event fired when AI generates a response."""
    
    session_id: str
    query: str
    response_length: int
    context_chunks_used: int
    processing_time: float
    
    @classmethod
    def create(cls, response_id: str, session_id: str, query: str, 
               response_length: int, context_chunks_used: int, 
               processing_time: float) -> 'AIResponseGeneratedEvent':
        return super().create(
            aggregate_id=response_id,
            session_id=session_id,
            query=query,
            response_length=response_length,
            context_chunks_used=context_chunks_used,
            processing_time=processing_time
        )
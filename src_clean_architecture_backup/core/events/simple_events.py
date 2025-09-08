"""
Simplified event system.

A simpler implementation without complex dataclass inheritance.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4


class BaseEvent:
    """Base event class."""
    
    def __init__(self, aggregate_id: str, **kwargs):
        self.event_id = str(uuid4())
        self.occurred_at = datetime.utcnow()
        self.aggregate_id = aggregate_id
        self.event_type = self.__class__.__name__
        self.data = kwargs
    
    def __repr__(self):
        return f"{self.event_type}(id={self.event_id}, aggregate={self.aggregate_id})"


class DocumentCreatedEvent(BaseEvent):
    """Event fired when a document is created."""
    
    def __init__(self, document_id: str, title: str, content_type: str, file_id: Optional[str] = None):
        super().__init__(document_id, title=title, content_type=content_type, file_id=file_id)
        self.title = title
        self.content_type = content_type
        self.file_id = file_id


class DocumentProcessedEvent(BaseEvent):
    """Event fired when a document has been processed."""
    
    def __init__(self, document_id: str, chunks_created: int, processing_time: float):
        super().__init__(document_id, chunks_created=chunks_created, processing_time=processing_time)
        self.chunks_created = chunks_created
        self.processing_time = processing_time


class DocumentSearchedEvent(BaseEvent):
    """Event fired when documents are searched."""
    
    def __init__(self, query: str, results_count: int, search_type: str = "semantic"):
        super().__init__(f"search_{query[:50]}", query=query, results_count=results_count, search_type=search_type)
        self.query = query
        self.results_count = results_count
        self.search_type = search_type


class ChatSessionStartedEvent(BaseEvent):
    """Event fired when a chat session is started."""
    
    def __init__(self, session_id: str, topic_id: Optional[int] = None, user_id: Optional[int] = None):
        super().__init__(session_id, topic_id=topic_id, user_id=user_id)
        self.topic_id = topic_id
        self.user_id = user_id


class MessageSentEvent(BaseEvent):
    """Event fired when a message is sent."""
    
    def __init__(self, message_id: str, session_id: str, message_role: str, message_length: int):
        super().__init__(message_id, session_id=session_id, message_role=message_role, message_length=message_length)
        self.session_id = session_id
        self.message_role = message_role
        self.message_length = message_length
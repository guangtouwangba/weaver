"""
Domain events module.

Contains domain events and event handling infrastructure.
"""

from .base_event import DomainEvent
from .document_events import (
    DocumentCreatedEvent,
    DocumentProcessedEvent,
    DocumentUpdatedEvent,
    DocumentDeletedEvent
)
from .chat_events import (
    ChatSessionStartedEvent,
    MessageSentEvent,
    ChatSessionEndedEvent
)
from .topic_events import (
    TopicCreatedEvent,
    TopicUpdatedEvent,
    TopicDeletedEvent
)
from .event_dispatcher import EventDispatcher
from .event_handler import EventHandler

__all__ = [
    "DomainEvent",
    "DocumentCreatedEvent",
    "DocumentProcessedEvent", 
    "DocumentUpdatedEvent",
    "DocumentDeletedEvent",
    "ChatSessionStartedEvent",
    "MessageSentEvent",
    "ChatSessionEndedEvent",
    "TopicCreatedEvent",
    "TopicUpdatedEvent",
    "TopicDeletedEvent",
    "EventDispatcher",
    "EventHandler"
]
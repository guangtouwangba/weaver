"""
Chat event handlers.

Handles chat-related domain events.
"""

import logging
from typing import Type

from ...core.events.event_handler import EventHandler
from ...core.events.chat_events import (
    ChatSessionStartedEvent,
    MessageSentEvent
)


class ChatSessionStartedEventHandler(EventHandler[ChatSessionStartedEvent]):
    """Handles chat session started events."""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
    
    @property
    def event_type(self) -> Type[ChatSessionStartedEvent]:
        return ChatSessionStartedEvent
    
    async def handle(self, event: ChatSessionStartedEvent) -> None:
        """Handle chat session started event."""
        self._logger.info(
            f"Chat session started: {event.aggregate_id} "
            f"(topic: {event.topic_id}, user: {event.user_id})"
        )
        
        # Example actions:
        # - Initialize session context
        # - Send welcome message
        # - Update user activity
        # - Record session analytics


class MessageSentEventHandler(EventHandler[MessageSentEvent]):
    """Handles message sent events."""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
    
    @property
    def event_type(self) -> Type[MessageSentEvent]:
        return MessageSentEvent
    
    async def handle(self, event: MessageSentEvent) -> None:
        """Handle message sent event."""
        self._logger.info(
            f"Message sent in session {event.session_id}: "
            f"{event.message_role} ({event.message_length} chars)"
        )
        
        if event.response_time:
            self._logger.debug(f"Response time: {event.response_time:.2f}s")
        
        # Example actions:
        # - Update conversation analytics
        # - Track response times
        # - Monitor AI performance
        # - Update user engagement metrics
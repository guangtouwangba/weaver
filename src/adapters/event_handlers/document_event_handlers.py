"""
Document event handlers.

Handles document-related domain events.
"""

import logging
from typing import Type

from ...core.events.event_handler import EventHandler
from ...core.events.document_events import (
    DocumentCreatedEvent,
    DocumentProcessedEvent,
    DocumentSearchedEvent
)


class DocumentCreatedEventHandler(EventHandler[DocumentCreatedEvent]):
    """Handles document created events."""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
    
    @property
    def event_type(self) -> Type[DocumentCreatedEvent]:
        return DocumentCreatedEvent
    
    async def handle(self, event: DocumentCreatedEvent) -> None:
        """Handle document created event."""
        self._logger.info(
            f"Document created: {event.title} (ID: {event.aggregate_id})"
        )
        
        # Example actions:
        # - Send notification
        # - Update analytics
        # - Trigger indexing workflow
        # - Log to audit trail
        
        # For demonstration, just log
        self._logger.debug(f"Processing document created event: {event}")


class DocumentProcessedEventHandler(EventHandler[DocumentProcessedEvent]):
    """Handles document processed events."""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
    
    @property
    def event_type(self) -> Type[DocumentProcessedEvent]:
        return DocumentProcessedEvent
    
    async def handle(self, event: DocumentProcessedEvent) -> None:
        """Handle document processed event."""
        self._logger.info(
            f"Document processed: {event.aggregate_id}, "
            f"chunks: {event.chunks_created}, "
            f"time: {event.processing_time:.2f}s"
        )
        
        # Example actions:
        # - Update topic statistics
        # - Send completion notification
        # - Update search index status
        # - Record processing metrics


class DocumentSearchEventHandler(EventHandler[DocumentSearchedEvent]):
    """Handles document search events."""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
    
    @property
    def event_type(self) -> Type[DocumentSearchedEvent]:
        return DocumentSearchedEvent
    
    async def handle(self, event: DocumentSearchedEvent) -> None:
        """Handle document search event."""
        self._logger.info(
            f"Search performed: '{event.query}' -> {event.results_count} results"
        )
        
        # Example actions:
        # - Record search analytics
        # - Update popular queries
        # - Improve search suggestions
        # - Track user behavior
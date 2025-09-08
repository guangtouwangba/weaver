"""
Analytics event handler.

Handles all events for analytics and metrics collection.
"""

import logging
from typing import Type

from ...core.events.event_handler import EventHandler
from ...core.events.base_event import DomainEvent


class AnalyticsEventHandler(EventHandler[DomainEvent]):
    """Universal event handler for analytics collection."""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._metrics = {}
    
    @property
    def event_type(self) -> Type[DomainEvent]:
        return DomainEvent
    
    async def handle(self, event: DomainEvent) -> None:
        """Handle any domain event for analytics."""
        event_type = event.event_type
        
        # Count events by type
        if event_type not in self._metrics:
            self._metrics[event_type] = 0
        self._metrics[event_type] += 1
        
        self._logger.debug(f"Analytics: {event_type} (total: {self._metrics[event_type]})")
        
        # Example analytics actions:
        # - Send to analytics service
        # - Update metrics dashboard
        # - Store in time-series database
        # - Trigger alerts if needed
        
        # For demonstration, log every 10th event
        if self._metrics[event_type] % 10 == 0:
            self._logger.info(f"Analytics milestone: {event_type} reached {self._metrics[event_type]} events")
    
    def get_metrics(self) -> dict:
        """Get current metrics."""
        return self._metrics.copy()
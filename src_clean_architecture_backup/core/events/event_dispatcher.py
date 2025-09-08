"""
Event dispatcher.

Manages the dispatching of domain events to their handlers.
"""

import asyncio
from typing import Dict, List, Type
import logging

from .base_event import DomainEvent
from .event_handler import EventHandler


class EventDispatcher:
    """Dispatches domain events to registered handlers."""
    
    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}
        self._logger = logging.getLogger(__name__)
    
    def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler."""
        event_type = handler.event_type
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self._logger.info(f"Registered handler {handler.__class__.__name__} for {event_type.__name__}")
    
    def unregister_handler(self, handler: EventHandler) -> None:
        """Unregister an event handler."""
        event_type = handler.event_type
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            self._logger.info(f"Unregistered handler {handler.__class__.__name__} for {event_type.__name__}")
    
    async def dispatch(self, event: DomainEvent) -> None:
        """Dispatch an event to all registered handlers."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            self._logger.debug(f"No handlers registered for event {event_type.__name__}")
            return
        
        self._logger.info(f"Dispatching {event_type.__name__} to {len(handlers)} handler(s)")
        
        # Run all handlers concurrently
        tasks = [self._handle_event_safely(handler, event) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _handle_event_safely(self, handler: EventHandler, event: DomainEvent) -> None:
        """Handle an event with error handling."""
        try:
            await handler.handle(event)
            self._logger.debug(f"Handler {handler.__class__.__name__} processed {event.event_type}")
        except Exception as e:
            self._logger.error(
                f"Error in handler {handler.__class__.__name__} for event {event.event_type}: {str(e)}",
                exc_info=True
            )
    
    def get_registered_handlers(self, event_type: Type[DomainEvent]) -> List[EventHandler]:
        """Get all handlers registered for an event type."""
        return self._handlers.get(event_type, []).copy()
    
    def clear_handlers(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()
        self._logger.info("Cleared all event handlers")
"""
Event handler base class.

Defines the interface for domain event handlers.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from .base_event import DomainEvent

T = TypeVar('T', bound=DomainEvent)


class EventHandler(ABC, Generic[T]):
    """Base class for domain event handlers."""
    
    @abstractmethod
    async def handle(self, event: T) -> None:
        """Handle a domain event."""
        pass
    
    @property
    @abstractmethod
    def event_type(self) -> type:
        """Get the event type this handler processes."""
        pass
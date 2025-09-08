"""
Base domain event.

Defines the base class for all domain events.
"""

from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent(ABC):
    """Base class for all domain events."""
    
    event_id: str
    occurred_at: datetime
    aggregate_id: str
    event_version: int = 1
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})
    
    @classmethod
    def create(cls, aggregate_id: str, **kwargs) -> 'DomainEvent':
        """Create a new domain event."""
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.utcnow(),
            aggregate_id=aggregate_id,
            **kwargs
        )
    
    @property
    def event_type(self) -> str:
        """Get the event type name."""
        return self.__class__.__name__
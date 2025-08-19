"""
Domain shared module.

This module contains shared domain concepts like events, value objects, and base classes.
"""

# Import EventType first (no dependencies)
from .event_types import EventType, EventRegistry

# Then import DomainEvent (depends on EventType)
from .domain_event import DomainEvent

__all__ = [
    'EventType',
    'EventRegistry', 
    'DomainEvent'
]
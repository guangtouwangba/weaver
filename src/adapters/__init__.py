"""
Adapters module.

This module contains adapters that implement the interfaces defined in the core layer.
Adapters connect the application to external systems and frameworks.
"""

from . import repositories
from . import external_services
from . import storage
from . import ai

__all__ = [
    "repositories",
    "external_services",
    "storage",
    "ai"
]
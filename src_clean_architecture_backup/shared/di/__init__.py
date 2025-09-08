"""
Dependency injection module.

Contains the dependency injection container and related components.
"""

from .container import Container
from .config import DIConfig

__all__ = [
    "Container",
    "DIConfig"
]
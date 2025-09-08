"""
Common use cases module.

Contains shared use cases and base classes used across different domains.
"""

from .base_use_case import BaseUseCase
from .exceptions import UseCaseError, ValidationError, NotFoundError, ConflictError

__all__ = [
    "BaseUseCase",
    "UseCaseError",
    "ValidationError", 
    "NotFoundError",
    "ConflictError"
]
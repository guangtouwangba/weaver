"""
Core package.

Contains core functionality like dependency injection, exceptions, and configuration.
"""

from .dependencies import get_database, get_cronjob_service, get_research_service
from .exceptions import (
    DatabaseError,
    ValidationError,
    NotFoundError,
    ServiceError
)
from .config import get_settings

__all__ = [
    "get_database",
    "get_cronjob_service", 
    "get_research_service",
    "DatabaseError",
    "ValidationError",
    "NotFoundError",
    "ServiceError",
    "get_settings"
]
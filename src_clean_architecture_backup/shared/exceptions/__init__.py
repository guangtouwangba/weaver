"""
Shared exceptions module.

Contains common exception classes used throughout the application.
"""

from .base_exceptions import (
    ApplicationError,
    ValidationError,
    NotFoundError,
    ConflictError,
    PermissionError,
    BusinessRuleViolationError
)

from .infrastructure_exceptions import (
    DatabaseError,
    ExternalServiceError,
    ConfigurationError
)

__all__ = [
    "ApplicationError",
    "ValidationError",
    "NotFoundError", 
    "ConflictError",
    "PermissionError",
    "BusinessRuleViolationError",
    "DatabaseError",
    "ExternalServiceError",
    "ConfigurationError"
]
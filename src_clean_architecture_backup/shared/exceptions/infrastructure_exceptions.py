"""
Infrastructure exception classes.

Defines exceptions related to infrastructure components.
"""

from .base_exceptions import ApplicationError


class DatabaseError(ApplicationError):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, operation: str = None, details: dict = None):
        super().__init__(message, "DATABASE_ERROR", details)
        self.operation = operation


class ExternalServiceError(ApplicationError):
    """Exception raised for external service errors."""
    
    def __init__(self, message: str, service_name: str = None, status_code: int = None, details: dict = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)
        self.service_name = service_name
        self.status_code = status_code


class ConfigurationError(ApplicationError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, config_key: str = None, details: dict = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)
        self.config_key = config_key
"""
Custom exceptions for the application.
"""

class ApplicationError(Exception):
    """Base application exception"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

class DatabaseError(ApplicationError):
    """Database-related errors"""
    pass

class ValidationError(ApplicationError):
    """Validation errors"""
    pass

class NotFoundError(ApplicationError):
    """Resource not found errors"""
    pass

class ServiceError(ApplicationError):
    """Service layer errors"""
    pass

class RepositoryError(DatabaseError):
    """Repository layer errors"""
    pass

class ConfigurationError(ApplicationError):
    """Configuration-related errors"""
    pass
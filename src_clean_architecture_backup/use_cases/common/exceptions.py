"""
Use case exceptions.

Defines custom exceptions for use case operations.
"""


class UseCaseError(Exception):
    """Base exception for use case errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}


class ValidationError(UseCaseError):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class NotFoundError(UseCaseError):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource_type: str, identifier: str, details: dict = None):
        message = f"{resource_type} with identifier '{identifier}' not found"
        super().__init__(message, "NOT_FOUND", details)
        self.resource_type = resource_type
        self.identifier = identifier


class ConflictError(UseCaseError):
    """Exception raised when there's a conflict with existing data."""
    
    def __init__(self, message: str, conflicting_resource: str = None, details: dict = None):
        super().__init__(message, "CONFLICT", details)
        self.conflicting_resource = conflicting_resource


class PermissionError(UseCaseError):
    """Exception raised for permission/authorization errors."""
    
    def __init__(self, message: str, required_permission: str = None, details: dict = None):
        super().__init__(message, "PERMISSION_DENIED", details)
        self.required_permission = required_permission


class BusinessRuleViolationError(UseCaseError):
    """Exception raised when a business rule is violated."""
    
    def __init__(self, message: str, rule_name: str = None, details: dict = None):
        super().__init__(message, "BUSINESS_RULE_VIOLATION", details)
        self.rule_name = rule_name
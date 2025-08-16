"""
API exception handling and custom exceptions.

This module provides custom exception classes and handlers for the RAG API,
ensuring consistent error responses and proper logging.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class RAGAPIException(Exception):
    """Base exception for RAG API."""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "RAG_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


class TopicNotFoundError(RAGAPIException):
    """Exception raised when a topic is not found."""
    
    def __init__(self, topic_id: int):
        super().__init__(
            message=f"Topic {topic_id} not found",
            error_code="TOPIC_NOT_FOUND",
            status_code=404,
            details={"topic_id": topic_id}
        )


class ResourceNotFoundError(RAGAPIException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource_id: int):
        super().__init__(
            message=f"Resource {resource_id} not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_id": resource_id}
        )


class InvalidTopicDataError(RAGAPIException):
    """Exception raised when topic data is invalid."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="INVALID_TOPIC_DATA",
            status_code=400,
            details={"field": field} if field else {}
        )


class ResourceUploadError(RAGAPIException):
    """Exception raised when resource upload fails."""
    
    def __init__(self, message: str, filename: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="RESOURCE_UPLOAD_ERROR",
            status_code=400,
            details={"filename": filename} if filename else {}
        )


class InfrastructureError(RAGAPIException):
    """Exception raised when infrastructure services fail."""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} service error: {message}",
            error_code="INFRASTRUCTURE_ERROR",
            status_code=503,
            details={"service": service, "original_message": message}
        )


class AuthenticationError(RAGAPIException):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(RAGAPIException):
    """Exception raised when authorization fails."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403
        )


class RateLimitError(RAGAPIException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429
        )


class ValidationError(RAGAPIException):
    """Exception raised when request validation fails."""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation error for field '{field}': {message}",
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={"field": field, "validation_message": message}
        )


# Exception handlers

async def rag_api_exception_handler(request: Request, exc: RAGAPIException) -> JSONResponse:
    """Handle RAG API exceptions."""
    logger.warning(
        f"RAG API exception: {exc.error_code} - {exc.message} - "
        f"Path: {request.url.path} - Method: {request.method}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
            "method": request.method
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail} - "
        f"Path: {request.url.path} - Method: {request.method}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "path": str(request.url.path),
            "method": request.method
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation exceptions."""
    logger.warning(
        f"Validation exception: {exc} - "
        f"Path: {request.url.path} - Method: {request.method}"
    )
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"validation_errors": errors},
            "path": str(request.url.path),
            "method": request.method
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc} - "
        f"Path: {request.url.path} - Method: {request.method}",
        exc_info=True
    )
    
    # Don't expose internal errors in production
    from infrastructure import get_config
    config = get_config()
    
    if config.environment == "production":
        message = "An internal error occurred"
        details = {}
    else:
        message = str(exc)
        details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": message,
            "details": details,
            "path": str(request.url.path),
            "method": request.method
        }
    )


# Utility functions for raising common exceptions

def raise_not_found(resource_type: str, resource_id: Any) -> None:
    """Raise a not found exception for a resource."""
    if resource_type.lower() == "topic":
        raise TopicNotFoundError(resource_id)
    elif resource_type.lower() == "resource":
        raise ResourceNotFoundError(resource_id)
    else:
        raise RAGAPIException(
            message=f"{resource_type} {resource_id} not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


def raise_validation_error(field: str, message: str) -> None:
    """Raise a validation exception."""
    raise ValidationError(field, message)


def raise_infrastructure_error(service: str, original_exception: Exception) -> None:
    """Raise an infrastructure error."""
    raise InfrastructureError(service, str(original_exception))


# Error response models for OpenAPI documentation

from pydantic import BaseModel

class ErrorDetail(BaseModel):
    """Error detail model."""
    field: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    path: Optional[str] = None
    method: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response model."""
    error: str = "VALIDATION_ERROR"
    message: str = "Request validation failed"
    details: Dict[str, Any]
    path: Optional[str] = None
    method: Optional[str] = None
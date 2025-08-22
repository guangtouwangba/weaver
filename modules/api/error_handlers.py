"""
API error handlers

Custom error handlers to handle various API error scenarios, including Unicode decode errors.
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


async def unicode_decode_error_handler(request: Request, exc: UnicodeDecodeError) -> JSONResponse:
    """Handle Unicode decode errors"""
    logger.warning(f"Unicode decode error at {request.url}: {exc}")

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": "Request data encoding error",
            "error": {
                "type": "EncodingError",
                "detail": "Request contains character data that cannot be decoded, please check file encoding or data format",
                "suggestion": "Please ensure uploaded files use correct encoding format, or use proper Content-Type headers",
            },
        },
    )


async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Request validation errors, especially multipart data errors"""
    logger.warning(f"Request validation error at {request.url}: {exc}")

    # Check if it's an encoding-related error
    error_details = []
    encoding_error = False

    for error in exc.errors():
        error_dict = {
            "field": error.get("loc", [])[-1] if error.get("loc") else "unknown",
            "type": error.get("type", "unknown"),
            "message": error.get("msg", "validation error"),
        }

        # Check if it's an encoding error
        if (
            "decode" in str(error).lower()
            or "encoding" in str(error).lower()
            or "utf-8" in str(error).lower()
        ):
            encoding_error = True

        error_details.append(error_dict)

    if encoding_error:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Request data encoding error",
                "error": {
                    "type": "RequestEncodingError",
                    "detail": "Request data contains character encoding that cannot be processed",
                    "suggestion": "Please check if the request Content-Type is correct, ensure file data uses proper encoding format",
                    "errors": error_details,
                },
            },
        )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Request parameter validation failed",
            "error": {
                "type": "ValidationError",
                "detail": "Request parameters do not meet API requirements",
                "errors": error_details,
            },
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions"""
    logger.error(f"Unhandled error at {request.url}: {type(exc).__name__}: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": {
                "type": type(exc).__name__,
                "detail": "An error occurred while the server was processing the request, please try again later or contact technical support",
            },
        },
    )


def safe_encode_errors(errors: Any) -> Any:
    """
    Safely encode error information to avoid Unicode decode errors
    """
    if isinstance(errors, bytes):
        try:
            return errors.decode("utf-8", errors="replace")
        except:
            return str(errors)
    elif isinstance(errors, list):
        return [safe_encode_errors(item) for item in errors]
    elif isinstance(errors, dict):
        return {key: safe_encode_errors(value) for key, value in errors.items()}
    else:
        return errors

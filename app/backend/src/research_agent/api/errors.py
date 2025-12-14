"""Unified error handling for API."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from research_agent.shared.exceptions import (
    EmbeddingError,
    LLMError,
    NotFoundError,
    PDFProcessingError,
    ResearchAgentError,
    StorageError,
    ValidationError,
)
from research_agent.shared.utils.logger import logger


def setup_error_handlers(app: FastAPI) -> None:
    """Set up error handlers for the FastAPI app."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        logger.warning(f"NotFoundError: {exc.message} - {request.url}")
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message, "type": "not_found"},
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        logger.warning(f"ValidationError: {exc.message} - {request.url}")
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message, "type": "validation_error"},
        )

    @app.exception_handler(StorageError)
    async def storage_handler(request: Request, exc: StorageError) -> JSONResponse:
        logger.error(f"StorageError: {exc.message} - {request.url}")
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message, "type": "storage_error"},
        )

    @app.exception_handler(LLMError)
    async def llm_handler(request: Request, exc: LLMError) -> JSONResponse:
        logger.error(f"LLMError: {exc.message} - {request.url}")
        return JSONResponse(
            status_code=503,
            content={"detail": exc.message, "type": "llm_error"},
        )

    @app.exception_handler(EmbeddingError)
    async def embedding_handler(request: Request, exc: EmbeddingError) -> JSONResponse:
        logger.error(f"EmbeddingError: {exc.message} - {request.url}")
        return JSONResponse(
            status_code=503,
            content={"detail": exc.message, "type": "embedding_error"},
        )

    @app.exception_handler(PDFProcessingError)
    async def pdf_handler(request: Request, exc: PDFProcessingError) -> JSONResponse:
        logger.error(f"PDFProcessingError: {exc.message} - {request.url}")
        return JSONResponse(
            status_code=422,
            content={"detail": exc.message, "type": "pdf_processing_error"},
        )

    @app.exception_handler(ResearchAgentError)
    async def general_handler(request: Request, exc: ResearchAgentError) -> JSONResponse:
        logger.error(f"ResearchAgentError: {exc.message} - {request.url}")
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message, "type": "internal_error"},
        )
    
    # Catch-all for unhandled exceptions
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        from research_agent.config import get_settings
        settings = get_settings()
        
        error_type = type(exc).__name__
        error_message = str(exc)
        
        # Log full exception with stack trace
        logger.exception(
            f"Unhandled exception: {error_type}: {error_message} - "
            f"URL: {request.url}, "
            f"Method: {request.method}, "
            f"Path: {request.url.path}"
        )
        
        # In development, return more detailed error information
        if settings.is_development:
            detail = (
                f"Internal server error: {error_type}: {error_message}. "
                f"Check server logs for full stack trace."
            )
        else:
            detail = "Internal server error"
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": detail,
                "type": "internal_error",
                "error_type": error_type,
            },
        )


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


def setup_error_handlers(app: FastAPI) -> None:
    """Set up error handlers for the FastAPI app."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message, "type": "not_found"},
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message, "type": "validation_error"},
        )

    @app.exception_handler(StorageError)
    async def storage_handler(request: Request, exc: StorageError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message, "type": "storage_error"},
        )

    @app.exception_handler(LLMError)
    async def llm_handler(request: Request, exc: LLMError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": exc.message, "type": "llm_error"},
        )

    @app.exception_handler(EmbeddingError)
    async def embedding_handler(request: Request, exc: EmbeddingError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": exc.message, "type": "embedding_error"},
        )

    @app.exception_handler(PDFProcessingError)
    async def pdf_handler(request: Request, exc: PDFProcessingError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.message, "type": "pdf_processing_error"},
        )

    @app.exception_handler(ResearchAgentError)
    async def general_handler(request: Request, exc: ResearchAgentError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message, "type": "internal_error"},
        )


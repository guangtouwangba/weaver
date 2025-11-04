"""Application entrypoint for the minimal LangChain/LangGraph RAG service."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ingest, qa, qa_stream, search, topics, topic_contents, conversations, messages
from app.errors import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    general_exception_handler,
)


def create_app() -> FastAPI:
    """Configure FastAPI with core routers and shared metadata."""
    app = FastAPI(
        title="Knowledge Platform RAG Service",
        version="0.3.0",
        description=(
            "API surface for topic management, content management, document ingest, semantic search, and QA "
            "built on LangChain + LangGraph with PostgreSQL for knowledge management."
        ),
    )

    # Register exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server default port
            "http://localhost:5174",  # Vite alternate port
            "http://localhost:3000",  # Alternative React port
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
    )

    # Topic management
    app.include_router(topics.router, prefix="/api/v1")
    
    # Topic content management
    app.include_router(topic_contents.router, prefix="/api/v1")
    
    # Conversation and message management
    app.include_router(conversations.router, prefix="/api/v1")
    app.include_router(messages.router, prefix="/api/v1")

    # Document and RAG operations
    app.include_router(ingest.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(qa.router, prefix="/api/v1")
    app.include_router(qa_stream.router, prefix="/api/v1")  # Streaming QA endpoint

    return app


app = create_app()

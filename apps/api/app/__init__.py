"""Application entrypoint for the minimal LangChain/LangGraph RAG service."""

from fastapi import FastAPI

from app.routers import ingest, qa, search


def create_app() -> FastAPI:
    """Configure FastAPI with core routers and shared metadata."""
    app = FastAPI(
        title="Minimal RAG Service",
        version="0.1.0",
        description=(
            "API surface for document ingest, semantic search, and basic QA "
            "built on LangChain + LangGraph."
        ),
    )

    app.include_router(ingest.router)
    app.include_router(search.router)
    app.include_router(qa.router)
    return app


app = create_app()

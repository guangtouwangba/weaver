"""Shared dependency providers for FastAPI routes."""

from functools import lru_cache

from fastapi import Depends
from langchain.vectorstores.base import VectorStoreRetriever

from rag_core.chains.embeddings import build_embedding_function
from rag_core.chains.vectorstore import build_vector_store
from shared_config.settings import AppSettings


@lru_cache
def get_settings() -> AppSettings:
    """Load application settings once per process."""
    return AppSettings()  # type: ignore[arg-type]


def get_vector_retriever(
    settings: AppSettings = Depends(get_settings),
) -> VectorStoreRetriever | None:
    """Provide a LangChain retriever backed by the configured vector store."""
    vector_store = build_vector_store(settings)
    if vector_store is None:
        # No documents have been indexed yet
        return None
    return vector_store.as_retriever(search_kwargs={"k": settings.vector_top_k})

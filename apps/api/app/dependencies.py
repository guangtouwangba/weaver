"""Shared dependency providers for FastAPI routes."""

from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends, Request, HTTPException
from langchain.vectorstores.base import VectorStoreRetriever

from apps.api.app.lifecycle import ApplicationState
from rag_core.chains.embeddings import build_embedding_function
from rag_core.chains.vectorstore import build_vector_store
from shared_config.settings import AppSettings


# ========================================
# New Dependency Injection (via Lifecycle)
# ========================================

def get_app_state(request: Request) -> ApplicationState:
    """
    Get the application state from the request.
    
    The application state is managed by the lifespan context manager
    and contains all initialized components.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ApplicationState instance
    """
    return request.app.state.rag


def get_settings_from_state(
    state: Annotated[ApplicationState, Depends(get_app_state)]
) -> AppSettings:
    """
    Get application settings from the state.
    
    Args:
        state: Application state
        
    Returns:
        AppSettings instance
    """
    if not state.settings:
        raise HTTPException(status_code=500, detail="Settings not initialized")
    return state.settings


def get_vector_store_from_state(
    state: Annotated[ApplicationState, Depends(get_app_state)]
) -> Any:
    """
    Get vector store from application state.
    
    Args:
        state: Application state
        
    Returns:
        Vector store instance (FAISS)
        
    Raises:
        HTTPException: If vector store is not available
    """
    if not state.vector_store:
        raise HTTPException(
            status_code=503,
            detail="Vector store not available. Please index documents first."
        )
    return state.vector_store


def get_llm_from_state(
    state: Annotated[ApplicationState, Depends(get_app_state)]
) -> Any:
    """
    Get LLM from application state.
    
    Args:
        state: Application state
        
    Returns:
        LLM instance
        
    Raises:
        HTTPException: If LLM is not available
    """
    if not state.llm:
        raise HTTPException(status_code=503, detail="LLM not available")
    return state.llm


def get_embeddings_from_state(
    state: Annotated[ApplicationState, Depends(get_app_state)]
) -> Any:
    """
    Get embeddings from application state.
    
    Args:
        state: Application state
        
    Returns:
        Embeddings instance
        
    Raises:
        HTTPException: If embeddings are not available
    """
    if not state.embeddings:
        raise HTTPException(status_code=503, detail="Embeddings not available")
    return state.embeddings


def get_redis_client(
    state: Annotated[ApplicationState, Depends(get_app_state)]
) -> Any:
    """
    Get Redis client from application state.
    
    Args:
        state: Application state
        
    Returns:
        Redis client instance
        
    Raises:
        HTTPException: If Redis is not available or not enabled
    """
    if not state.redis_client:
        raise HTTPException(
            status_code=503,
            detail="Redis not available. Enable cache in configuration."
        )
    return state.redis_client


def get_reranker(
    state: Annotated[ApplicationState, Depends(get_app_state)]
) -> Any | None:
    """
    Get reranker from application state.
    
    Args:
        state: Application state
        
    Returns:
        Reranker instance or None if not enabled
    """
    return state.reranker


# ========================================
# Legacy Dependencies (Backward Compatible)
# ========================================

@lru_cache
def get_settings() -> AppSettings:
    """
    Load application settings once per process.
    
    Note: This is the legacy method. Prefer get_settings_from_state
    for new code as it uses the lifecycle-managed settings.
    """
    return AppSettings()  # type: ignore[arg-type]


def get_vector_retriever(
    settings: AppSettings = Depends(get_settings),
) -> VectorStoreRetriever | None:
    """
    Provide a LangChain retriever backed by the configured vector store.
    
    Note: This is the legacy method. Prefer get_vector_store_from_state
    for new code as it uses the lifecycle-managed vector store.
    """
    vector_store = build_vector_store(settings)
    if vector_store is None:
        # No documents have been indexed yet
        return None
    return vector_store.as_retriever(search_kwargs={"k": settings.vector_top_k})

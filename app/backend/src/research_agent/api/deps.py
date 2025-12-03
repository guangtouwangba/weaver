"""API dependencies for dependency injection."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.infrastructure.database.session import async_session_maker
from research_agent.infrastructure.embedding.openrouter import (
    OpenRouterEmbeddingService,
    OpenAIEmbeddingService,
)
from research_agent.infrastructure.llm.openrouter import OpenRouterLLMService
from research_agent.shared.utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_llm_service() -> OpenRouterLLMService:
    """Get LLM service instance."""
    return OpenRouterLLMService(
        api_key=settings.openrouter_api_key,
        model=settings.llm_model,
        site_name="Research Agent RAG",
    )


def get_embedding_service():
    """Get embedding service instance.
    
    OpenRouter DOES support embedding API!
    User confirmed it works with curl.
    
    Uses OpenRouter by default since it's simpler (one API key).
    Falls back to OpenAI if you prefer direct API access.
    """
    # Prefer OpenRouter (simpler, one API key)
    if settings.openrouter_api_key and settings.openrouter_api_key.strip():
        logger.info(
            f"Using OpenRouter Embedding Service (model: {settings.embedding_model})"
        )
        return OpenRouterEmbeddingService(
            api_key=settings.openrouter_api_key,
            model=settings.embedding_model,
        )
    # Fallback to OpenAI if OpenRouter key not set
    elif settings.openai_api_key and settings.openai_api_key.strip():
        logger.info(
            f"Using OpenAI Embedding Service (model: {settings.embedding_model})"
        )
        # Extract model name without provider prefix
        model_name = settings.embedding_model
        if "/" in model_name:
            model_name = model_name.split("/", 1)[1]  # Remove "openai/" prefix
        
        return OpenAIEmbeddingService(
            api_key=settings.openai_api_key,
            model=model_name,
        )
    else:
        logger.error(
            "❌ No API key set! Please set OPENROUTER_API_KEY or OPENAI_API_KEY"
        )
        raise ValueError("No embedding API key configured")


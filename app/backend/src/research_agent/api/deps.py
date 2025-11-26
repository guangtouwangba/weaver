"""API dependencies for dependency injection."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.infrastructure.database.session import async_session_maker
from research_agent.infrastructure.embedding.openrouter import OpenRouterEmbeddingService
from research_agent.infrastructure.llm.openrouter import OpenRouterLLMService

settings = get_settings()


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


def get_embedding_service() -> OpenRouterEmbeddingService:
    """Get embedding service instance."""
    return OpenRouterEmbeddingService(
        api_key=settings.openrouter_api_key,
        model=settings.embedding_model,
    )


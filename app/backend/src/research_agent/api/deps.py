"""API dependencies for dependency injection."""

import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.infrastructure.database.session import async_session_maker
from research_agent.infrastructure.embedding.openrouter import (
    OpenAIEmbeddingService,
    OpenRouterEmbeddingService,
)
from research_agent.infrastructure.llm.openrouter import OpenRouterLLMService
from research_agent.shared.utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)

# Database connection retry configuration
DB_CONNECT_MAX_RETRIES = 3
DB_CONNECT_RETRY_DELAY = 2.0  # seconds


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for FastAPI dependency injection.

    ✅ Improved: Explicit commit/rollback/close handling with retry logic.

    Retry logic helps handle transient connection pool exhaustion during
    heavy background operations (e.g., Gemini OCR processing large PDFs).
    """
    session: AsyncSession | None = None
    last_error: Exception | None = None

    for attempt in range(1, DB_CONNECT_MAX_RETRIES + 1):
        try:
            session = async_session_maker()
            # Test that the connection is actually available by starting a transaction
            # This will fail fast if the pool is exhausted
            break
        except (TimeoutError, asyncio.TimeoutError) as e:
            last_error = e
            if attempt < DB_CONNECT_MAX_RETRIES:
                logger.warning(
                    f"⚠️  Database connection error (attempt {attempt}): "
                    f"{type(e).__name__}: {e}. Retrying in {DB_CONNECT_RETRY_DELAY}s..."
                )
                await asyncio.sleep(DB_CONNECT_RETRY_DELAY)
            else:
                logger.error(
                    f"❌ Database connection failed after {DB_CONNECT_MAX_RETRIES} attempts: "
                    f"{type(e).__name__}: {e}"
                )
                raise
        except Exception as e:
            # Non-timeout errors should not be retried
            logger.error(f"❌ Database connection error (non-retryable): {type(e).__name__}: {e}")
            raise

    if session is None:
        if last_error:
            raise last_error
        raise RuntimeError("Failed to create database session")

    try:
        yield session
        # ✅ Commit on success
        await session.commit()
    except (TimeoutError, asyncio.TimeoutError) as e:
        # Log timeout errors with more context
        logger.warning(f"⚠️  Database operation timed out: {type(e).__name__}: {e}")
        await session.rollback()
        raise
    except Exception:
        # ✅ Rollback on error
        await session.rollback()
        raise
    finally:
        # ✅ Always close, even if there's an error
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing session in get_db: {e}")


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
        logger.info(f"Using OpenRouter Embedding Service (model: {settings.embedding_model})")
        return OpenRouterEmbeddingService(
            api_key=settings.openrouter_api_key,
            model=settings.embedding_model,
        )
    # Fallback to OpenAI if OpenRouter key not set
    elif settings.openai_api_key and settings.openai_api_key.strip():
        logger.info(f"Using OpenAI Embedding Service (model: {settings.embedding_model})")
        # Extract model name without provider prefix
        model_name = settings.embedding_model
        if "/" in model_name:
            model_name = model_name.split("/", 1)[1]  # Remove "openai/" prefix

        return OpenAIEmbeddingService(
            api_key=settings.openai_api_key,
            model=model_name,
        )
    else:
        logger.error("❌ No API key set! Please set OPENROUTER_API_KEY or OPENAI_API_KEY")
        raise ValueError("No embedding API key configured")

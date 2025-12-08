"""Langfuse integration for LLM observability.

Langfuse is an open-source LLM engineering platform that provides:
- LLM call tracing (inputs/outputs)
- Token usage and latency metrics
- Prompt management
- Evaluation tools

See: https://langfuse.com/docs/integrations/langchain
"""

from typing import Optional

from langchain_core.callbacks import BaseCallbackHandler

from research_agent.config import get_settings
from research_agent.shared.utils.logger import logger


def create_langfuse_callback() -> Optional[BaseCallbackHandler]:
    """
    Create a Langfuse callback handler for LangChain integration.

    Returns:
        LangfuseCallbackHandler if enabled and configured, None otherwise.

    Environment variables required:
        - LANGFUSE_ENABLED: Set to "true" to enable
        - LANGFUSE_PUBLIC_KEY: Your Langfuse public key (pk-lf-xxx)
        - LANGFUSE_SECRET_KEY: Your Langfuse secret key (sk-lf-xxx)
        - LANGFUSE_HOST: Langfuse host URL (default: https://cloud.langfuse.com)
    """
    settings = get_settings()

    if not settings.langfuse_enabled:
        logger.debug("[Langfuse] Disabled - skipping callback creation")
        return None

    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.warning(
            "[Langfuse] Enabled but missing API keys. "
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables."
        )
        return None

    try:
        # langfuse v3 uses langfuse.langchain module
        from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler

        callback = LangfuseCallbackHandler(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_host,
        )

        logger.info(f"[Langfuse] Callback handler created (host: {settings.langfuse_host})")
        return callback

    except ImportError as e:
        logger.error(f"[Langfuse] Import failed: {e}. Run: pip install langfuse")
        return None
    except Exception as e:
        logger.error(f"[Langfuse] Failed to create callback handler: {type(e).__name__}: {e}")
        return None


def get_langfuse_callbacks() -> list[BaseCallbackHandler]:
    """
    Get a list of Langfuse callbacks (empty list if disabled).

    This is a convenience function for use with LangChain's callback system.

    Example:
        ```python
        from research_agent.infrastructure.observability import get_langfuse_callbacks

        callbacks = get_langfuse_callbacks()
        chain.invoke({"question": "..."}, config={"callbacks": callbacks})
        ```
    """
    callback = create_langfuse_callback()
    return [callback] if callback else []

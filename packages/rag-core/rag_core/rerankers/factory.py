"""Factory for creating reranker instances."""

from typing import Any, Dict
import logging

from rag_core.core.exceptions import ConfigurationException
from rag_core.rerankers.base import RerankerInterface
from rag_core.rerankers.cross_encoder_reranker import CrossEncoderReranker
from shared_config.settings import AppSettings

logger = logging.getLogger(__name__)


class RerankerFactory:
    """
    Factory for creating reranker instances based on configuration.
    
    Supported reranker types:
    - "cross_encoder": Cross-encoder models from sentence-transformers
    - "llm": LLM-based reranking (TODO)
    - "cohere": Cohere rerank API (TODO)
    
    Example:
        ```python
        # Create from explicit config
        reranker = RerankerFactory.create(
            reranker_type="cross_encoder",
            config={
                "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                "top_n": 5
            }
        )
        
        # Create from settings
        settings = AppSettings()
        reranker = RerankerFactory.create_from_settings(settings)
        ```
    """
    
    @staticmethod
    async def create(
        reranker_type: str = "cross_encoder",
        config: Dict[str, Any] | None = None,
    ) -> RerankerInterface:
        """
        Create a reranker instance.
        
        Args:
            reranker_type: Type of reranker ('cross_encoder', 'llm', etc.)
            config: Configuration dictionary for the reranker
        
        Returns:
            Initialized reranker instance
        
        Raises:
            ConfigurationException: If reranker type is unknown or config is invalid
        """
        config = config or {}
        
        if reranker_type == "cross_encoder":
            logger.info(f"Creating CrossEncoderReranker with config: {config}")
            return CrossEncoderReranker(
                model_name=config.get("model", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
                top_n=config.get("top_n", 3),
                batch_size=config.get("batch_size", 32),
                device=config.get("device"),
                max_length=config.get("max_length", 512),
            )
        
        # Future reranker types:
        # elif reranker_type == "llm":
        #     return LLMReranker(llm=config.get("llm"), ...)
        # elif reranker_type == "cohere":
        #     return CohereReranker(api_key=config.get("api_key"), ...)
        
        else:
            raise ConfigurationException(
                f"Unknown reranker type: {reranker_type}",
                details={
                    "requested_type": reranker_type,
                    "supported_types": ["cross_encoder"],
                },
            )
    
    @staticmethod
    async def create_from_settings(
        settings: AppSettings | None = None,
    ) -> RerankerInterface | None:
        """
        Create a reranker from application settings.
        
        Args:
            settings: Application settings (creates new if None)
        
        Returns:
            Initialized reranker if enabled, None otherwise
        
        Raises:
            ConfigurationException: If reranker config is invalid
        """
        if settings is None:
            settings = AppSettings()
        
        # Check if reranker is enabled
        if not settings.reranker.enabled:
            logger.info("Reranker is disabled in settings")
            return None
        
        # Build config from settings
        config = {
            "model": settings.reranker.model,
            "top_n": settings.reranker.top_n,
            "batch_size": settings.reranker.batch_size,
        }
        
        logger.info(
            f"Creating reranker from settings: "
            f"type={settings.reranker.type}, model={settings.reranker.model}"
        )
        
        return await RerankerFactory.create(
            reranker_type=settings.reranker.type,
            config=config,
        )


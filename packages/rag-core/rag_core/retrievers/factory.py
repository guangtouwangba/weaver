"""Factory for creating retriever instances."""

from typing import Any
import logging

from rag_core.core.exceptions import ConfigurationException
from rag_core.core.interfaces import RetrieverInterface
from rag_core.retrievers.vector_retriever import VectorRetriever
from rag_core.retrievers.hybrid_retriever import HybridRetriever
from shared_config.settings import AppSettings

logger = logging.getLogger(__name__)


class RetrieverFactory:
    """Factory for creating retriever instances based on configuration.

    This factory provides a centralized way to create different types of
    retrievers based on configuration or explicit parameters.
    
    Supported retriever types:
    - "vector": Pure vector similarity search
    - "hybrid": BM25 + Vector hybrid search (recommended for best results)
    - "multi_query": Multi-query retrieval (TODO)
    - "ensemble": Ensemble retrieval (TODO)
    """

    @staticmethod
    def create(
        retriever_type: str = "vector",
        config: dict[str, Any] | None = None,
        vector_store: Any = None,
    ) -> RetrieverInterface:
        """Create a retriever instance.

        Args:
            retriever_type: Type of retriever to create ('vector', 'hybrid', etc.).
            config: Optional configuration dictionary. If None, uses default from settings.
            vector_store: Optional vector store instance (for vector retriever).

        Returns:
            RetrieverInterface implementation.

        Raises:
            ConfigurationException: If retriever type is unknown or configuration is invalid.
        """
        retriever_type = retriever_type.lower()

        if config is None:
            # Load default configuration from settings
            settings = AppSettings()  # type: ignore[arg-type]
            config = {
                "top_k": settings.retriever.top_k,
                "search_type": settings.retriever.search_type,
                "similarity_threshold": settings.retriever.similarity_threshold,
                "lambda_mult": settings.retriever.lambda_mult,
            }

        if retriever_type == "vector":
            logger.info(f"Creating VectorRetriever with config: {config}")
            return VectorRetriever(
                vector_store=vector_store,
                top_k=config.get("top_k", 4),
                search_type=config.get("search_type", "similarity"),
                search_kwargs={
                    "lambda_mult": config.get("lambda_mult", 0.5),
                    "similarity_threshold": config.get("similarity_threshold", 0.7),
                },
            )
        
        elif retriever_type == "hybrid":
            logger.info(f"Creating HybridRetriever with config: {config}")
            return HybridRetriever(
                vector_store=vector_store,
                vector_weight=config.get("vector_weight", 0.7),
                bm25_weight=config.get("bm25_weight", 0.3),
                top_k=config.get("top_k", 5),
                rrf_k=config.get("rrf_k", 60),
                search_kwargs=config.get("search_kwargs", {}),
            )

        # Future retriever types:
        # elif retriever_type == "multi_query":
        #     return MultiQueryRetriever(...)
        # elif retriever_type == "ensemble":
        #     return EnsembleRetriever(...)

        else:
            raise ConfigurationException(
                f"Unknown retriever type: {retriever_type}",
                details={
                    "requested_type": retriever_type,
                    "supported_types": ["vector", "hybrid"],  # Updated
                },
            )

    @staticmethod
    def create_from_settings(
        settings: AppSettings | None = None, vector_store: Any = None
    ) -> RetrieverInterface:
        """Create a retriever from application settings.

        Args:
            settings: Application settings. If None, loads default settings.
            vector_store: Optional vector store instance.

        Returns:
            RetrieverInterface implementation.
        """
        if settings is None:
            settings = AppSettings()  # type: ignore[arg-type]

        config = {
            "top_k": settings.retriever.top_k,
            "search_type": settings.retriever.search_type,
            "similarity_threshold": settings.retriever.similarity_threshold,
            "lambda_mult": settings.retriever.lambda_mult,
        }

        # For now, only vector retriever is supported
        # In the future, this could check settings.retriever.type
        return RetrieverFactory.create(
            retriever_type="vector", config=config, vector_store=vector_store
        )


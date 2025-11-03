"""Factory for creating retriever instances."""

from typing import Any

from rag_core.core.exceptions import ConfigurationException
from rag_core.core.interfaces import RetrieverInterface
from rag_core.retrievers.vector_retriever import VectorRetriever
from shared_config.settings import AppSettings


class RetrieverFactory:
    """Factory for creating retriever instances based on configuration.

    This factory provides a centralized way to create different types of
    retrievers based on configuration or explicit parameters.
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
            return VectorRetriever(
                vector_store=vector_store,
                top_k=config.get("top_k", 4),
                search_type=config.get("search_type", "similarity"),
                search_kwargs={
                    "lambda_mult": config.get("lambda_mult", 0.5),
                    "similarity_threshold": config.get("similarity_threshold", 0.7),
                },
            )

        # Future retriever types can be added here:
        # elif retriever_type == "hybrid":
        #     return HybridRetriever(...)
        # elif retriever_type == "multi_query":
        #     return MultiQueryRetriever(...)

        else:
            raise ConfigurationException(
                f"Unknown retriever type: {retriever_type}",
                details={
                    "requested_type": retriever_type,
                    "supported_types": ["vector"],  # Add more as implemented
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


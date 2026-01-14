"""
Strategy Factory.

Factory pattern for creating RAG strategy instances.
Uses a registry pattern to map strategy names to implementation classes.

This keeps the RAG graph decoupled from specific strategy implementations.
"""

from collections.abc import Callable
from typing import Any

from research_agent.domain.entities.config import RetrievalStrategyType
from research_agent.domain.strategies.base import (
    IGenerationStrategy,
    IIntentClassificationStrategy,
    IQueryTransformStrategy,
    IRetrievalStrategy,
)
from research_agent.shared.utils.logger import logger


class StrategyFactory:
    """
    Factory for creating RAG strategy instances.

    Uses a registry pattern - strategies register themselves and can be
    instantiated by name at runtime.

    Usage:
        # Register a strategy (typically done at module load)
        StrategyFactory.register_retrieval("vector", VectorRetrievalStrategy)

        # Get strategy instance
        strategy = StrategyFactory.get_retrieval_strategy("vector", **deps)

        # Or use config enum
        strategy = StrategyFactory.get_retrieval_strategy(
            RetrievalStrategyType.VECTOR, **deps
        )
    """

    # Strategy registries
    _retrieval_strategies: dict[str, type[IRetrievalStrategy]] = {}
    _generation_strategies: dict[str, type[IGenerationStrategy]] = {}
    _query_transform_strategies: dict[str, type[IQueryTransformStrategy]] = {}
    _intent_classifiers: dict[str, type[IIntentClassificationStrategy]] = {}

    # Factory functions for strategies that need complex initialization
    _retrieval_factories: dict[str, Callable[..., IRetrievalStrategy]] = {}
    _generation_factories: dict[str, Callable[..., IGenerationStrategy]] = {}

    # -----------------------------------------------------------------------------
    # Registration Methods
    # -----------------------------------------------------------------------------

    @classmethod
    def register_retrieval(
        cls,
        name: str,
        strategy_class: type[IRetrievalStrategy] | None = None,
        factory: Callable[..., IRetrievalStrategy] | None = None,
    ) -> None:
        """
        Register a retrieval strategy.

        Args:
            name: Strategy identifier (e.g., "vector", "hybrid")
            strategy_class: Strategy class to instantiate
            factory: Optional factory function for complex initialization
        """
        if strategy_class:
            cls._retrieval_strategies[name] = strategy_class
        if factory:
            cls._retrieval_factories[name] = factory
        logger.debug(f"[StrategyFactory] Registered retrieval strategy: {name}")

    @classmethod
    def register_generation(
        cls,
        name: str,
        strategy_class: type[IGenerationStrategy] | None = None,
        factory: Callable[..., IGenerationStrategy] | None = None,
    ) -> None:
        """Register a generation strategy."""
        if strategy_class:
            cls._generation_strategies[name] = strategy_class
        if factory:
            cls._generation_factories[name] = factory
        logger.debug(f"[StrategyFactory] Registered generation strategy: {name}")

    @classmethod
    def register_query_transform(
        cls,
        name: str,
        strategy_class: type[IQueryTransformStrategy],
    ) -> None:
        """Register a query transformation strategy."""
        cls._query_transform_strategies[name] = strategy_class
        logger.debug(f"[StrategyFactory] Registered query transform strategy: {name}")

    @classmethod
    def register_intent_classifier(
        cls,
        name: str,
        strategy_class: type[IIntentClassificationStrategy],
    ) -> None:
        """Register an intent classification strategy."""
        cls._intent_classifiers[name] = strategy_class
        logger.debug(f"[StrategyFactory] Registered intent classifier: {name}")

    # -----------------------------------------------------------------------------
    # Factory Methods
    # -----------------------------------------------------------------------------

    @classmethod
    def get_retrieval_strategy(
        cls,
        name: str | RetrievalStrategyType,
        **kwargs: Any,
    ) -> IRetrievalStrategy:
        """
        Get a retrieval strategy instance.

        Args:
            name: Strategy name or RetrievalStrategyType enum
            **kwargs: Dependencies to inject (e.g., embedding_service, vector_store)

        Returns:
            IRetrievalStrategy instance

        Raises:
            ValueError: If strategy is not registered
        """
        # Convert enum to string if needed
        strategy_name = name.value if isinstance(name, RetrievalStrategyType) else name

        # Try factory first (for complex initialization)
        if strategy_name in cls._retrieval_factories:
            return cls._retrieval_factories[strategy_name](**kwargs)

        # Then try class instantiation
        if strategy_name in cls._retrieval_strategies:
            return cls._retrieval_strategies[strategy_name](**kwargs)

        # Check if we have any strategies registered
        available = list(cls._retrieval_strategies.keys()) + list(cls._retrieval_factories.keys())

        if not available:
            # No strategies registered - provide helpful message
            raise ValueError(
                "No retrieval strategies registered. "
                "Call 'register_default_strategies()' or register strategies manually."
            )

        raise ValueError(f"Unknown retrieval strategy: {strategy_name}. Available: {available}")

    @classmethod
    def get_generation_strategy(
        cls,
        name: str,
        **kwargs: Any,
    ) -> IGenerationStrategy:
        """
        Get a generation strategy instance.

        Args:
            name: Strategy name (e.g., "basic", "long_context")
            **kwargs: Dependencies to inject

        Returns:
            IGenerationStrategy instance
        """
        # Try factory first
        if name in cls._generation_factories:
            return cls._generation_factories[name](**kwargs)

        # Then try class
        if name in cls._generation_strategies:
            return cls._generation_strategies[name](**kwargs)

        available = list(cls._generation_strategies.keys()) + list(cls._generation_factories.keys())

        if not available:
            raise ValueError(
                "No generation strategies registered. "
                "Call 'register_default_strategies()' or register strategies manually."
            )

        raise ValueError(f"Unknown generation strategy: {name}. Available: {available}")

    @classmethod
    def get_query_transform_strategy(
        cls,
        name: str,
        **kwargs: Any,
    ) -> IQueryTransformStrategy:
        """Get a query transformation strategy instance."""
        if name not in cls._query_transform_strategies:
            available = list(cls._query_transform_strategies.keys())
            raise ValueError(f"Unknown query transform strategy: {name}. Available: {available}")
        return cls._query_transform_strategies[name](**kwargs)

    @classmethod
    def get_intent_classifier(
        cls,
        name: str,
        **kwargs: Any,
    ) -> IIntentClassificationStrategy:
        """Get an intent classification strategy instance."""
        if name not in cls._intent_classifiers:
            available = list(cls._intent_classifiers.keys())
            raise ValueError(f"Unknown intent classifier: {name}. Available: {available}")
        return cls._intent_classifiers[name](**kwargs)

    # -----------------------------------------------------------------------------
    # Utility Methods
    # -----------------------------------------------------------------------------

    @classmethod
    def list_retrieval_strategies(cls) -> list[str]:
        """List all registered retrieval strategies."""
        return list(set(cls._retrieval_strategies.keys()) | set(cls._retrieval_factories.keys()))

    @classmethod
    def list_generation_strategies(cls) -> list[str]:
        """List all registered generation strategies."""
        return list(set(cls._generation_strategies.keys()) | set(cls._generation_factories.keys()))

    @classmethod
    def clear_all(cls) -> None:
        """Clear all registered strategies (useful for testing)."""
        cls._retrieval_strategies.clear()
        cls._generation_strategies.clear()
        cls._query_transform_strategies.clear()
        cls._intent_classifiers.clear()
        cls._retrieval_factories.clear()
        cls._generation_factories.clear()


def register_default_strategies() -> None:
    """
    Register default strategy implementations.

    Call this during application startup to register all built-in strategies.
    Strategies are lazily imported to avoid circular dependencies.
    """
    # Import and register retrieval strategies
    try:
        from research_agent.infrastructure.strategies.retrieval import (
            HybridRetrievalStrategy,
            VectorRetrievalStrategy,
        )

        StrategyFactory.register_retrieval("vector", VectorRetrievalStrategy)
        StrategyFactory.register_retrieval("hybrid", HybridRetrievalStrategy)
    except ImportError as e:
        logger.warning(f"[StrategyFactory] Could not import retrieval strategies: {e}")

    # Import and register generation strategies
    try:
        from research_agent.infrastructure.strategies.generation import (
            BasicGenerationStrategy,
            LongContextGenerationStrategy,
        )

        StrategyFactory.register_generation("basic", BasicGenerationStrategy)
        StrategyFactory.register_generation("long_context", LongContextGenerationStrategy)
    except ImportError as e:
        logger.warning(f"[StrategyFactory] Could not import generation strategies: {e}")

    # Import and register query transform strategies
    try:
        from research_agent.infrastructure.strategies.query_transform import (
            QueryRewriteStrategy,
        )

        StrategyFactory.register_query_transform("rewrite", QueryRewriteStrategy)
    except ImportError as e:
        logger.warning(f"[StrategyFactory] Could not import query transform strategies: {e}")

    # Import and register intent classifiers
    try:
        from research_agent.infrastructure.strategies.intent_classification import (
            LLMIntentClassifier,
        )

        StrategyFactory.register_intent_classifier("llm", LLMIntentClassifier)
    except ImportError as e:
        logger.warning(f"[StrategyFactory] Could not import intent classifiers: {e}")

    logger.info(
        f"[StrategyFactory] Registered strategies - "
        f"retrieval: {StrategyFactory.list_retrieval_strategies()}, "
        f"generation: {StrategyFactory.list_generation_strategies()}"
    )

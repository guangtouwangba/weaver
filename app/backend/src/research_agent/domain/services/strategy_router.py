"""Strategy Router for adaptive RAG processing.

Routes queries to appropriate processing strategies based on query classification.
Supports multiple strategy paths:
- FastPath: Direct LLM response without RAG (for simple queries)
- LiteContext: Minimal context retrieval (for moderate queries)
- FullContext: Full document context loading (for complex queries)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from research_agent.domain.services.query_classifier import (
    QueryClassification,
    QueryComplexity,
)
from research_agent.shared.utils.logger import logger


class RAGStrategyType(str, Enum):
    """Types of RAG processing strategies."""

    FAST_PATH = "fast_path"  # No RAG, direct LLM
    LITE_CONTEXT = "lite_context"  # Top-k chunks only
    FULL_CONTEXT = "full_context"  # Full long_context mode
    HYBRID = "hybrid"  # Combination of retrieval and context


@dataclass
class RAGStrategy:
    """Configuration for a RAG processing strategy."""

    strategy_type: RAGStrategyType
    max_tokens: int  # Maximum tokens to use (-1 for unlimited)
    use_retrieval: bool  # Whether to use vector retrieval
    use_long_context: bool  # Whether to load full documents
    top_k: int  # Number of chunks to retrieve (if using retrieval)
    skip_embedding: bool  # Whether to skip embedding generation
    reasoning: str  # Why this strategy was selected

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "strategy_type": self.strategy_type.value,
            "max_tokens": self.max_tokens,
            "use_retrieval": self.use_retrieval,
            "use_long_context": self.use_long_context,
            "top_k": self.top_k,
            "skip_embedding": self.skip_embedding,
            "reasoning": self.reasoning,
        }


class StrategyRouter:
    """Routes queries to appropriate RAG strategies.

    Strategy selection is based on:
    - Query classification (simple/moderate/complex)
    - Available context (token budget, document count)
    - Configuration settings
    """

    # Default configurations for each strategy type
    STRATEGY_CONFIGS = {
        RAGStrategyType.FAST_PATH: {
            "max_tokens": 0,
            "use_retrieval": False,
            "use_long_context": False,
            "top_k": 0,
            "skip_embedding": True,
        },
        RAGStrategyType.LITE_CONTEXT: {
            "max_tokens": 20000,
            "use_retrieval": True,
            "use_long_context": False,
            "top_k": 5,
            "skip_embedding": False,
        },
        RAGStrategyType.FULL_CONTEXT: {
            "max_tokens": -1,  # Unlimited
            "use_retrieval": False,
            "use_long_context": True,
            "top_k": 0,
            "skip_embedding": True,
        },
        RAGStrategyType.HYBRID: {
            "max_tokens": 50000,
            "use_retrieval": True,
            "use_long_context": True,
            "top_k": 10,
            "skip_embedding": False,
        },
    }

    def __init__(
        self,
        fast_path_enabled: bool = True,
        lite_context_max_tokens: int = 20000,
        enable_logging: bool = True,
    ):
        """Initialize the strategy router.

        Args:
            fast_path_enabled: Whether to allow fast path (no RAG) for simple queries
            lite_context_max_tokens: Token budget for lite context strategy
            enable_logging: Whether to log routing decisions
        """
        self._fast_path_enabled = fast_path_enabled
        self._lite_context_max_tokens = lite_context_max_tokens
        self._enable_logging = enable_logging

    def select_strategy(
        self,
        classification: QueryClassification,
        available_tokens: int,
        document_count: int,
        force_context: bool = False,
    ) -> RAGStrategy:
        """Select the appropriate RAG strategy for a query.

        Args:
            classification: Query classification result
            available_tokens: Maximum available tokens for context
            document_count: Number of documents in the project
            force_context: If True, always use context even for simple queries

        Returns:
            RAGStrategy configuration
        """
        complexity = classification.complexity

        # No documents available - fast path only option
        if document_count == 0:
            return self._create_strategy(
                RAGStrategyType.FAST_PATH,
                reasoning="No documents available for context",
            )

        # Simple queries - fast path if enabled
        if complexity == QueryComplexity.SIMPLE and not force_context:
            if self._fast_path_enabled and not classification.requires_context:
                return self._create_strategy(
                    RAGStrategyType.FAST_PATH,
                    reasoning=f"Simple query ({classification.reasoning}), fast path enabled",
                )
            # Simple but requires context - lite context
            return self._create_strategy(
                RAGStrategyType.LITE_CONTEXT,
                max_tokens=min(self._lite_context_max_tokens // 2, available_tokens),
                reasoning="Simple query but context required",
            )

        # Moderate queries - lite context
        if complexity == QueryComplexity.MODERATE:
            return self._create_strategy(
                RAGStrategyType.LITE_CONTEXT,
                max_tokens=min(self._lite_context_max_tokens, available_tokens),
                reasoning=f"Moderate complexity query ({classification.reasoning})",
            )

        # Complex queries - full context
        return self._create_strategy(
            RAGStrategyType.FULL_CONTEXT,
            max_tokens=available_tokens,
            reasoning=f"Complex query ({classification.reasoning})",
        )

    def _create_strategy(
        self,
        strategy_type: RAGStrategyType,
        max_tokens: Optional[int] = None,
        reasoning: str = "",
    ) -> RAGStrategy:
        """Create a strategy configuration.

        Args:
            strategy_type: Type of strategy to create
            max_tokens: Override max tokens (uses default if None)
            reasoning: Why this strategy was selected

        Returns:
            RAGStrategy configuration
        """
        config = self.STRATEGY_CONFIGS[strategy_type].copy()

        if max_tokens is not None:
            config["max_tokens"] = max_tokens

        strategy = RAGStrategy(
            strategy_type=strategy_type,
            max_tokens=config["max_tokens"],
            use_retrieval=config["use_retrieval"],
            use_long_context=config["use_long_context"],
            top_k=config["top_k"],
            skip_embedding=config["skip_embedding"],
            reasoning=reasoning,
        )

        if self._enable_logging:
            logger.info(
                f"[StrategyRouter] Selected strategy: {strategy_type.value}, "
                f"max_tokens={strategy.max_tokens}, "
                f"use_retrieval={strategy.use_retrieval}, "
                f"use_long_context={strategy.use_long_context}, "
                f"reasoning={reasoning}"
            )

        return strategy

    def should_skip_rag(self, strategy: RAGStrategy) -> bool:
        """Check if RAG should be skipped entirely.

        Args:
            strategy: The selected strategy

        Returns:
            True if RAG should be skipped
        """
        return strategy.strategy_type == RAGStrategyType.FAST_PATH


# Singleton instance
_router_instance: Optional[StrategyRouter] = None


def get_strategy_router(
    fast_path_enabled: bool = True,
    lite_context_max_tokens: int = 20000,
) -> StrategyRouter:
    """Get the strategy router instance.

    Args:
        fast_path_enabled: Whether to allow fast path
        lite_context_max_tokens: Token budget for lite context

    Returns:
        StrategyRouter instance
    """
    global _router_instance
    if _router_instance is None:
        _router_instance = StrategyRouter(
            fast_path_enabled=fast_path_enabled,
            lite_context_max_tokens=lite_context_max_tokens,
        )
    return _router_instance


def reset_strategy_router() -> None:
    """Reset the singleton router instance (for testing)."""
    global _router_instance
    _router_instance = None



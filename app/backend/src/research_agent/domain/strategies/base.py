"""
Strategy Interfaces for RAG Operations.

These abstract base classes define the contract for different RAG strategies.
Concrete implementations live in the infrastructure layer.

Design Pattern: Strategy Pattern
- Allows runtime selection of algorithms (retrieval, generation)
- Decouples the RAG graph from specific implementation details
- Enables easy addition of new strategies (HyDE, GraphRAG, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, List, Optional
from uuid import UUID

from langchain_core.documents import Document

from research_agent.domain.entities.config import (
    GenerationConfig,
    LLMConfig,
    RetrievalConfig,
)

# -----------------------------------------------------------------------------
# Result Types
# -----------------------------------------------------------------------------


@dataclass
class RetrievalResult:
    """Result from a retrieval strategy."""

    documents: List[Document]
    metadata: dict[str, Any] = field(default_factory=dict)

    # Additional context for long-context mode
    long_context_content: Optional[str] = None

    # Strategy info for debugging/logging
    strategy_name: str = "unknown"

    @property
    def document_count(self) -> int:
        return len(self.documents)

    @property
    def is_empty(self) -> bool:
        return len(self.documents) == 0


@dataclass
class GenerationResult:
    """Result from a generation strategy."""

    content: str
    citations: List[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Token usage (if available)
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

    # Strategy info
    strategy_name: str = "unknown"

    @property
    def total_tokens(self) -> Optional[int]:
        if self.prompt_tokens is not None and self.completion_tokens is not None:
            return self.prompt_tokens + self.completion_tokens
        return None


# -----------------------------------------------------------------------------
# Strategy Interfaces
# -----------------------------------------------------------------------------


class IRetrievalStrategy(ABC):
    """
    Abstract base class for retrieval strategies.

    Implementations:
    - VectorRetrievalStrategy: Standard PGVector similarity search
    - HybridRetrievalStrategy: Vector + keyword search
    - HyDERetrievalStrategy: Hypothetical Document Embedding

    Usage:
        strategy = StrategyFactory.get_retrieval_strategy("vector")
        result = await strategy.retrieve(query, project_id, config)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy identifier (e.g., 'vector', 'hybrid', 'hyde')."""
        pass

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        project_id: UUID,
        config: RetrievalConfig,
        **kwargs: Any,
    ) -> RetrievalResult:
        """
        Retrieve relevant documents for a query.

        Args:
            query: The search query (may be rewritten)
            project_id: Project scope for retrieval
            config: Retrieval configuration (top_k, min_similarity, etc.)
            **kwargs: Additional strategy-specific parameters

        Returns:
            RetrievalResult containing documents and metadata
        """
        pass

    async def rerank(
        self,
        query: str,
        documents: List[Document],
        config: RetrievalConfig,
        **kwargs: Any,
    ) -> List[Document]:
        """
        Optional: Rerank retrieved documents.

        Default implementation returns documents unchanged.
        Override for strategies that support reranking.
        """
        return documents


class IGenerationStrategy(ABC):
    """
    Abstract base class for generation strategies.

    Implementations:
    - BasicGenerationStrategy: Standard RAG generation
    - LongContextGenerationStrategy: Mega-Prompt with full documents
    - StreamingGenerationStrategy: Token-by-token streaming

    Usage:
        strategy = StrategyFactory.get_generation_strategy("basic")
        result = await strategy.generate(query, context, config)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy identifier (e.g., 'basic', 'long_context', 'streaming')."""
        pass

    @abstractmethod
    async def generate(
        self,
        query: str,
        context: str,
        config: GenerationConfig,
        llm_config: LLMConfig,
        **kwargs: Any,
    ) -> GenerationResult:
        """
        Generate an answer from query and context.

        Args:
            query: User question
            context: Retrieved context (concatenated documents or long context)
            config: Generation configuration (style, max_length, etc.)
            llm_config: LLM model configuration
            **kwargs: Additional strategy-specific parameters

        Returns:
            GenerationResult containing the answer and citations
        """
        pass

    async def stream(
        self,
        query: str,
        context: str,
        config: GenerationConfig,
        llm_config: LLMConfig,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream generation token by token.

        Default implementation yields the full response at once.
        Override for true streaming support.
        """
        result = await self.generate(query, context, config, llm_config, **kwargs)
        yield result.content


class IQueryTransformStrategy(ABC):
    """
    Abstract base class for query transformation strategies.

    Implementations:
    - QueryRewriteStrategy: Rewrite with chat history context
    - HyDEQueryStrategy: Generate hypothetical document for query

    Usage:
        strategy = StrategyFactory.get_query_transform_strategy("rewrite")
        transformed = await strategy.transform(query, chat_history, config)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy identifier (e.g., 'rewrite', 'hyde')."""
        pass

    @abstractmethod
    async def transform(
        self,
        query: str,
        chat_history: Optional[List[tuple[str, str]]] = None,
        llm_config: Optional[LLMConfig] = None,
        **kwargs: Any,
    ) -> str:
        """
        Transform the query for better retrieval.

        Args:
            query: Original user query
            chat_history: Optional conversation history
            llm_config: LLM configuration for transformation
            **kwargs: Additional parameters

        Returns:
            Transformed query string
        """
        pass


class IIntentClassificationStrategy(ABC):
    """
    Abstract base class for intent classification strategies.

    Implementations:
    - LLMIntentClassifier: Use LLM to classify intent
    - RuleBasedIntentClassifier: Pattern matching rules

    Usage:
        strategy = StrategyFactory.get_intent_classifier("llm")
        intent, confidence = await strategy.classify(query, config)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy identifier (e.g., 'llm', 'rule_based')."""
        pass

    @abstractmethod
    async def classify(
        self,
        query: str,
        llm_config: Optional[LLMConfig] = None,
        **kwargs: Any,
    ) -> tuple[str, float]:
        """
        Classify the intent of a query.

        Args:
            query: User query to classify
            llm_config: LLM configuration (for LLM-based classifiers)
            **kwargs: Additional parameters

        Returns:
            Tuple of (intent_type, confidence_score)
        """
        pass

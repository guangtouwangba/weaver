"""Strategy interfaces for RAG operations."""

from research_agent.domain.strategies.base import (
    GenerationResult,
    IGenerationStrategy,
    IRetrievalStrategy,
    RetrievalResult,
)

__all__ = [
    "IRetrievalStrategy",
    "IGenerationStrategy",
    "RetrievalResult",
    "GenerationResult",
]

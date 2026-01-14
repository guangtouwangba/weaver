"""Embedding service abstract interface."""

from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    """Abstract embedding service interface."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Get embedding for a single text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for multiple texts."""
        pass


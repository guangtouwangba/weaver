"""Embedding service abstract interface."""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingService(ABC):
    """Abstract embedding service interface."""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        pass


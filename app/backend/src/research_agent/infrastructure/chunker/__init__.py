"""Chunker module.

Provides extensible text chunking using the Registry pattern.
"""

from research_agent.infrastructure.chunker.base import (
    Chunker,
    ChunkResult,
)
from research_agent.infrastructure.chunker.factory import (
    ChunkerFactory,
)

__all__ = [
    "Chunker",
    "ChunkResult",
    "ChunkerFactory",
]

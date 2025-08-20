"""
Document Processor Module

Responsible for processing documents - parsing, cleaning, and chunking.
Provides intelligent document segmentation strategies.

Key Features:
- Multiple chunking strategies (fixed size, sentence-based, semantic)
- Content preprocessing and cleaning
- Metadata preservation
- Configurable chunk sizes and overlaps
"""

from .interface import IDocumentProcessor
from .text_processor import TextProcessor
from .chunking_processor import ChunkingProcessor

__all__ = [
    "IDocumentProcessor",
    "TextProcessor",
    "ChunkingProcessor",
]
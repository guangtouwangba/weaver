"""
File Loader Module

Responsible for loading and parsing documents from various sources and formats.
Provides a unified interface for file loading operations.

Key Features:
- Multi-format support (PDF, Word, Text, Markdown, etc.)
- Metadata extraction
- Error handling and validation
- Async batch processing
"""

from .interface import IFileLoader
from .text_loader import TextFileLoader
from .pdf_loader import PDFFileLoader
from .multi_format_loader import MultiFormatLoader

__all__ = [
    "IFileLoader",
    "TextFileLoader", 
    "PDFFileLoader",
    "MultiFormatLoader",
]
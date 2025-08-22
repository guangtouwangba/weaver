"""
File loader module

Responsible for loading document content from various sources.
Provides unified interface and multiple loading strategies.
"""

# Ensure loaders are registered to factory - trigger decorators by importing them
from . import pdf_loader  # Trigger pdf_loader decorator registration
from . import text_loader  # Trigger text_loader decorator registration
from .base import FileLoaderError, IFileLoader
from .factory import (  # Convenience functions for easier usage
    FileLoaderFactory,
    detect_content_type,
    get_supported_types,
    is_supported,
    load_document,
    register_file_loader,
    register_multi_type_file_loader,
)
from .pdf_loader import PDFFileLoader
from .text_loader import TextFileLoader

__all__ = [
    "IFileLoader",
    "FileLoaderError",
    "TextFileLoader",
    "PDFFileLoader",
    "FileLoaderFactory",
    "register_file_loader",
    "register_multi_type_file_loader",
    # Convenience functions
    "load_document",
    "detect_content_type",
    "get_supported_types",
    "is_supported",
]

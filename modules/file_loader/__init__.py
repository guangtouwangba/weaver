"""
File loader module

Responsible for loading document content from various sources.
Provides unified interface and multiple loading strategies.
"""

from .base import IFileLoader, FileLoaderError
from .text_loader import TextFileLoader
from .pdf_loader import PDFFileLoader
from .factory import (
    FileLoaderFactory, 
    register_file_loader, 
    register_multi_type_file_loader,
    # Convenience functions for easier usage
    load_document,
    detect_content_type,
    get_supported_types,
    is_supported
)

# Ensure loaders are registered to factory - trigger decorators by importing them
from . import text_loader  # Trigger text_loader decorator registration
from . import pdf_loader   # Trigger pdf_loader decorator registration

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
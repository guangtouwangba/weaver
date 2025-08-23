"""
File loader module

Responsible for loading document content from various sources.
Provides unified interface and multiple loading strategies.
"""

# Ensure loaders are registered to factory - trigger decorators by importing them
from modules.file_loader.pdf import (
  PDFFileLoader,
)
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

__all__ = [
    "IFileLoader",
    "PDFFileLoader",
    "FileLoaderError",
    "FileLoaderFactory",
    "register_file_loader",
    "register_multi_type_file_loader",
    # Convenience functions
    "load_document",
    "detect_content_type",
    "get_supported_types",
    "is_supported",
]

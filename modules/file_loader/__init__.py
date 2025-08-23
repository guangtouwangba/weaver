"""
File loader module

Responsible for loading document content from various sources.
Provides unified interface and multiple loading strategies.
"""

from modules.file_loader.base import FileLoaderError, IFileLoader
from modules.file_loader.factory import (  # Convenience functions for easier usage
    FileLoaderFactory,
    detect_content_type,
    get_supported_types,
    is_supported,
    load_document,
    register_file_loader,
    register_multi_type_file_loader,
)

# Ensure loaders are registered to factory - trigger decorators by importing them
from modules.file_loader.pdf import (
    PDFFileLoader,
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

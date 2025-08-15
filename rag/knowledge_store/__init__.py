"""
Knowledge Store Module
Provides document metadata and knowledge information management functionality
"""

# Base interface
from .base import BaseKnowledgeStore

# Exception classes - only import the ones that exist
try:
    from .exceptions import (
        KnowledgeStoreError,
        DocumentNotFoundError,
        DocumentAlreadyExistsError,
        InvalidDocumentError,
        StorageConnectionError,
        StorageOperationError,
        ConfigurationError
    )
except ImportError:
    # If exceptions module doesn't exist, define basic exceptions
    class KnowledgeStoreError(Exception):
        """Base knowledge store exception."""
        pass
    
    class DocumentNotFoundError(KnowledgeStoreError):
        """Document not found exception."""
        pass

# Version information
__version__ = "0.1.0"

# Main exports
__all__ = [
    # Base interface
    "BaseKnowledgeStore",
    
    # Exception classes
    "KnowledgeStoreError",
    "DocumentNotFoundError", 
]
"""
Router Module

Orchestrates interactions between different modules and provides
high-level workflows for document processing and retrieval.

Key Features:
- Document ingestion workflows
- Search and retrieval orchestration
- Module coordination
- Error handling and recovery
"""

from .base import IRouter
from .document_router import DocumentRouter

__all__ = [
    "IRouter",
    "DocumentRouter",
]

"""
Simple Modular RAG Architecture

This package provides a clean, modular architecture for RAG (Retrieval-Augmented Generation)
system with clear responsibilities and interfaces between modules.

Core Modules:
- file_loader: File loading and parsing
- document_processor: Document processing and chunking
- vector_store: Vector storage and similarity search
- knowledge_store: Knowledge metadata management
- retriever: Multi-strategy information retrieval
- router: Request routing and orchestration
- index: Index building and management

Each module has:
1. Clear responsibility scope
2. Well-defined interfaces
3. Minimal dependencies
4. Easy testability
"""

__version__ = "0.1.0"

# Module exports - lazy loading to avoid circular imports
__all__ = [
    "file_loader",
    "document_processor", 
    "vector_store",
    "knowledge_store",
    "retriever",
    "router",
    "index",
]
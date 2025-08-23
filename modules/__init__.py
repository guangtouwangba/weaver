"""
RAG Knowledge Management System Modules

This package contains all the core modules for the RAG system following DDD architecture:
- API layer: REST endpoints and request handling
- Service layer: Business logic orchestration
- Repository layer: Data access abstraction
- Schema layer: Data models and validation
"""

from .database import DatabaseConnection
from .repository import (
    DocumentRepository,
    FileRepository,
    TopicRepository,
)
from .schemas import (
    APIResponse,
    ChunkingStrategy,
    ContentType,
    Document,
    DocumentSchema,
    FileSchema,
    HealthCheckResponse,
    ProcessingStatus,
    TopicSchema,
)
from .services import (
    DocumentService,
    FileService,
    TopicService,
)

__version__ = "0.1.0"

__all__ = [
    # Database
    "DatabaseConnection",
    # Schemas
    "APIResponse",
    "HealthCheckResponse",
    "TopicSchema",
    "FileSchema",
    "DocumentSchema",
    "ContentType",
    "ChunkingStrategy",
    "ProcessingStatus",
    # Services
    "TopicService",
    "FileService",
    "DocumentService",
    # Repositories
    "TopicRepository",
    "FileRepository",
    "DocumentRepository",
]

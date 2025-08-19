"""
Simplified FastAPI Dependency Injection System

This module demonstrates how to replace the custom dependency injection
system with FastAPI's built-in dependency injection capabilities.
"""

from functools import lru_cache
from typing import AsyncGenerator
import logging

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# Infrastructure imports
from infrastructure.database import get_async_database_session
from infrastructure.storage.factory import create_storage_from_env
from infrastructure.storage.interfaces import IObjectStorage
from infrastructure.messaging.redis_broker import RedisMessageBroker
from infrastructure.messaging.interfaces import IMessageBroker
from application.event.event_bus import EventBus

logger = logging.getLogger(__name__)


# =============================================================================
# Core Infrastructure Dependencies
# =============================================================================

async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency with proper cleanup.
    
    This replaces the scoped session management from the custom DI system.
    """
    async with get_async_database_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


@lru_cache()
def get_object_storage() -> IObjectStorage:
    """
    Object storage dependency - singleton pattern.
    
    Uses lru_cache for singleton behavior, replacing the custom singleton
    management in the DI registry.
    """
    try:
        return create_storage_from_env()
    except Exception as e:
        logger.error(f"Failed to create storage service: {e}")
        raise HTTPException(
            status_code=500,
            detail="Storage service configuration error"
        )


@lru_cache()
def get_event_bus() -> EventBus:
    """
    Event bus dependency - singleton pattern.
    
    Simple singleton using lru_cache, much cleaner than custom DI.
    """
    return EventBus()


async def get_message_broker() -> AsyncGenerator[IMessageBroker, None]:
    """
    Message broker dependency with connection management.
    
    Handles connection lifecycle automatically.
    """
    broker = None
    try:
        # This could be made configurable or conditional
        broker = RedisMessageBroker()
        await broker.connect()
        yield broker
    except Exception as e:
        logger.warning(f"Message broker unavailable: {e}")
        # Yield None or a NullBroker for graceful degradation
        yield None
    finally:
        if broker:
            try:
                await broker.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting message broker: {e}")


# =============================================================================
# Repository Dependencies
# =============================================================================

def get_topic_repository(
    session: AsyncSession = Depends(get_database_session)
):
    """Topic repository dependency."""
    from infrastructure.database.repositories.topic import TopicRepository
    return TopicRepository(session)


def get_tag_repository(
    session: AsyncSession = Depends(get_database_session)
):
    """Tag repository dependency."""
    from infrastructure.database.repositories.topic import TagRepository
    return TagRepository(session)


def get_resource_repository(
    session: AsyncSession = Depends(get_database_session)
):
    """Resource repository dependency."""
    from infrastructure.database.repositories.topic import TopicResourceRepository
    return TopicResourceRepository(session)


# =============================================================================
# Application Service Dependencies
# =============================================================================

def get_topic_service(
    topic_repo=Depends(get_topic_repository),
    tag_repo=Depends(get_tag_repository),
    resource_repo=Depends(get_resource_repository),
    storage: IObjectStorage = Depends(get_object_storage),
    event_bus: EventBus = Depends(get_event_bus),
    message_broker: IMessageBroker = Depends(get_message_broker)
):
    """
    Topic service dependency with all required dependencies injected.
    
    This replaces the complex dependency resolution in the custom DI system
    with FastAPI's simple and transparent approach.
    """
    from application.services.topic_service import TopicService
    
    return TopicService(
        topic_repo=topic_repo,
        tag_repo=tag_repo, 
        resource_repo=resource_repo,
        storage=storage,
        event_bus=event_bus,
        message_broker=message_broker
    )


def get_document_service(
    storage: IObjectStorage = Depends(get_object_storage),
    event_bus: EventBus = Depends(get_event_bus)
):
    """Document service dependency."""
    from application.services.document_service import DocumentService
    
    return DocumentService(
        storage=storage,
        event_bus=event_bus
    )


# =============================================================================
# RAG Service Dependencies  
# =============================================================================

def get_rag_document_loader():
    """RAG document loader dependency."""
    from infrastructure.rag.loaders import UnifiedDocumentLoader
    return UnifiedDocumentLoader()


def get_rag_processor():
    """RAG document processor dependency."""  
    from infrastructure.rag.processors import DocumentProcessor
    return DocumentProcessor()


def get_vector_store():
    """Vector store dependency."""
    from infrastructure.rag.vector_stores import WeaviateVectorStore
    return WeaviateVectorStore()


def get_embedding_service():
    """Embedding service dependency."""
    from infrastructure.rag.embeddings import HuggingFaceEmbeddingService
    return HuggingFaceEmbeddingService()


def get_rag_service(
    loader=Depends(get_rag_document_loader),
    processor=Depends(get_rag_processor),
    vector_store=Depends(get_vector_store),
    embedding_service=Depends(get_embedding_service),
    event_bus: EventBus = Depends(get_event_bus)
):
    """
    RAG service dependency with all RAG components injected.
    
    This demonstrates how to wire up complex dependencies in a clean,
    testable way without custom DI complexity.
    """
    from application.services.rag_service import RAGService
    
    return RAGService(
        loader=loader,
        processor=processor,
        vector_store=vector_store,
        embedding_service=embedding_service,
        event_bus=event_bus
    )


# =============================================================================
# Health Check Dependencies
# =============================================================================

async def get_system_health():
    """
    System health dependency that checks all major components.
    
    This can be used in health check endpoints to verify system status.
    """
    health_status = {
        "database": False,
        "storage": False,
        "message_broker": False,
        "embedding_service": False,
        "vector_store": False
    }
    
    try:
        # Check database
        async with get_async_database_session() as session:
            await session.execute("SELECT 1")
            health_status["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    try:
        # Check storage
        storage = get_object_storage()
        await storage.health_check()  # Assuming this method exists
        health_status["storage"] = True
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
    
    try:
        # Check embedding service
        embedding_service = get_embedding_service()
        await embedding_service.health_check()  # Assuming this method exists
        health_status["embedding_service"] = True  
    except Exception as e:
        logger.error(f"Embedding service health check failed: {e}")
    
    try:
        # Check vector store
        vector_store = get_vector_store()
        await vector_store.health_check()  # Assuming this method exists
        health_status["vector_store"] = True
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
    
    # Check message broker
    async with get_message_broker() as broker:
        if broker:
            health_status["message_broker"] = True
    
    return health_status


# =============================================================================
# Testing Utilities
# =============================================================================

class MockDependencies:
    """
    Mock dependencies for testing.
    
    This demonstrates how easy it is to override dependencies for testing
    with FastAPI's system vs the custom DI approach.
    """
    
    @staticmethod
    def mock_storage():
        """Mock storage for testing."""
        from unittest.mock import Mock
        return Mock(spec=IObjectStorage)
    
    @staticmethod
    def mock_database_session():
        """Mock database session for testing."""
        from unittest.mock import AsyncMock
        return AsyncMock(spec=AsyncSession)
    
    @staticmethod
    def mock_event_bus():
        """Mock event bus for testing."""
        from unittest.mock import Mock
        return Mock(spec=EventBus)


def override_dependencies_for_testing(app):
    """
    Override dependencies for testing.
    
    Usage in tests:
    
    def test_something():
        with TestClient(app) as client:
            app.dependency_overrides[get_object_storage] = MockDependencies.mock_storage
            response = client.get("/api/topics")
            assert response.status_code == 200
    """
    app.dependency_overrides[get_object_storage] = MockDependencies.mock_storage
    app.dependency_overrides[get_database_session] = MockDependencies.mock_database_session  
    app.dependency_overrides[get_event_bus] = MockDependencies.mock_event_bus


# =============================================================================
# Usage Examples
# =============================================================================

"""
Usage in API routes:

# api/topic_routes.py
from fastapi import APIRouter, Depends
from .dependencies import get_topic_service

router = APIRouter()

@router.post("/topics/")
async def create_topic(
    request: CreateTopicRequest,
    topic_service: TopicService = Depends(get_topic_service)
):
    return await topic_service.create_topic(request)

@router.get("/topics/{topic_id}")
async def get_topic(
    topic_id: int,
    topic_service: TopicService = Depends(get_topic_service)
):
    return await topic_service.get_topic(topic_id)


# Benefits of this approach:

1. **Simplicity**: No custom DI registry, just standard FastAPI patterns
2. **Transparency**: Dependencies are explicit and easy to understand
3. **Testability**: Easy to mock dependencies for testing
4. **Performance**: FastAPI's DI is optimized and battle-tested
5. **IDE Support**: Full type hints and autocomplete support
6. **Debugging**: Clear dependency resolution, easy to debug
7. **Standards**: Uses established patterns familiar to FastAPI developers
"""
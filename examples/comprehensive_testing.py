"""
Comprehensive Testing Strategy Example

This demonstrates how to implement a proper testing infrastructure
for the RAG system with unit, integration, and API tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

# Application imports (these would be actual imports in the real implementation)
from examples.simplified_config import get_settings_for_testing
from examples.consolidated_services import TopicService, CreateTopicRequest


# =============================================================================
# Test Configuration and Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings with isolated configuration."""
    return get_settings_for_testing()


@pytest.fixture
async def test_db_engine(test_settings):
    """Test database engine with in-memory SQLite."""
    # Use in-memory SQLite for fast tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create all tables
    from infrastructure.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Test database session with transaction rollback."""
    async with AsyncSession(test_db_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_storage():
    """Mock storage service for testing."""
    storage = AsyncMock()
    storage.create_folder.return_value = None
    storage.delete_folder.return_value = None
    storage.health_check.return_value = True
    return storage


@pytest.fixture
def mock_event_bus():
    """Mock event bus for testing."""
    event_bus = AsyncMock()
    event_bus.publish.return_value = None
    return event_bus


@pytest.fixture
def mock_message_broker():
    """Mock message broker for testing."""
    broker = AsyncMock()
    broker.publish.return_value = None
    return broker


# =============================================================================
# Test Data Factories
# =============================================================================

class TopicFactory:
    """Factory for creating test topic data."""
    
    @staticmethod
    def create_topic_request(**overrides) -> CreateTopicRequest:
        """Create a test topic creation request."""
        defaults = {
            "name": "Test Topic",
            "description": "A test topic for testing",
            "category": "test",
            "tags": ["test", "example"],
            "settings": {"test": True}
        }
        defaults.update(overrides)
        return CreateTopicRequest(**defaults)
    
    @staticmethod
    def create_topic_entity(**overrides):
        """Create a test topic database entity."""
        from datetime import datetime
        
        defaults = {
            "id": 1,
            "name": "Test Topic",
            "description": "A test topic for testing",
            "category": "test",
            "status": "active",
            "total_resources": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "tags": []
        }
        defaults.update(overrides)
        
        # Create a mock entity with the specified attributes
        entity = Mock()
        for key, value in defaults.items():
            setattr(entity, key, value)
        
        return entity


# =============================================================================
# Unit Tests
# =============================================================================

class TestTopicService:
    """Unit tests for TopicService."""
    
    @pytest.fixture
    def topic_service(self, test_db_session, mock_storage, mock_event_bus, mock_message_broker):
        """Create TopicService instance for testing."""
        return TopicService(
            session=test_db_session,
            storage=mock_storage,
            event_bus=mock_event_bus,
            message_broker=mock_message_broker
        )
    
    @pytest.fixture
    def mock_topic_repo(self):
        """Mock topic repository."""
        repo = AsyncMock()
        return repo
    
    async def test_create_topic_success(self, topic_service, mock_topic_repo):
        """Test successful topic creation."""
        # Arrange
        request = TopicFactory.create_topic_request()
        expected_entity = TopicFactory.create_topic_entity()
        
        # Mock the repository
        with patch.object(topic_service, 'topic_repo', mock_topic_repo):
            mock_topic_repo.create.return_value = expected_entity
            mock_topic_repo.get_all.return_value = []  # No duplicates
            
            # Mock session commit
            topic_service.session.commit = AsyncMock()
            
            # Act
            result = await topic_service.create_topic(request)
            
            # Assert
            assert result.name == request.name
            assert result.description == request.description
            assert result.category == request.category
            
            # Verify repository was called correctly
            mock_topic_repo.create.assert_called_once()
            create_args = mock_topic_repo.create.call_args[0][0]
            assert create_args["name"] == request.name
            assert create_args["status"] == "active"
            
            # Verify storage was initialized
            topic_service.storage.create_folder.assert_called_once_with("topics/1")
            
            # Verify event was published
            topic_service.event_bus.publish.assert_called_once()
            event_args = topic_service.event_bus.publish.call_args
            assert event_args[0][0] == "topic.created"
            assert event_args[0][1]["topic_id"] == 1
    
    async def test_create_topic_duplicate_name(self, topic_service, mock_topic_repo):
        """Test topic creation with duplicate name."""
        # Arrange
        request = TopicFactory.create_topic_request()
        existing_entity = TopicFactory.create_topic_entity()
        
        with patch.object(topic_service, 'topic_repo', mock_topic_repo):
            mock_topic_repo.get_all.return_value = [existing_entity]  # Duplicate exists
            
            # Act & Assert
            with pytest.raises(ValueError, match="already exists"):
                await topic_service.create_topic(request)
    
    async def test_get_topic_success(self, topic_service, mock_topic_repo):
        """Test successful topic retrieval."""
        # Arrange
        topic_id = 1
        expected_entity = TopicFactory.create_topic_entity(id=topic_id)
        
        with patch.object(topic_service, 'topic_repo', mock_topic_repo):
            mock_topic_repo.get_by_id.return_value = expected_entity
            mock_topic_repo.update.return_value = expected_entity
            topic_service.session.commit = AsyncMock()
            
            # Act
            result = await topic_service.get_topic(topic_id)
            
            # Assert
            assert result is not None
            assert result.id == topic_id
            assert result.name == expected_entity.name
            
            # Verify last accessed was updated
            mock_topic_repo.update.assert_called_once_with(topic_id, {"last_accessed_at": pytest.mock.ANY})
    
    async def test_get_topic_not_found(self, topic_service, mock_topic_repo):
        """Test topic retrieval when topic doesn't exist."""
        # Arrange
        topic_id = 999
        
        with patch.object(topic_service, 'topic_repo', mock_topic_repo):
            mock_topic_repo.get_by_id.return_value = None
            
            # Act
            result = await topic_service.get_topic(topic_id)
            
            # Assert
            assert result is None
    
    async def test_delete_topic_success(self, topic_service, mock_topic_repo):
        """Test successful topic deletion."""
        # Arrange
        topic_id = 1
        
        with patch.object(topic_service, 'topic_repo', mock_topic_repo):
            mock_topic_repo.delete.return_value = True
            topic_service.session.commit = AsyncMock()
            
            # Act
            result = await topic_service.delete_topic(topic_id, hard_delete=False)
            
            # Assert
            assert result is True
            mock_topic_repo.delete.assert_called_once_with(topic_id, soft_delete=True)
            topic_service.event_bus.publish.assert_called_once()
    
    async def test_delete_topic_hard_delete(self, topic_service, mock_topic_repo):
        """Test hard topic deletion with storage cleanup."""
        # Arrange
        topic_id = 1
        
        with patch.object(topic_service, 'topic_repo', mock_topic_repo):
            mock_topic_repo.delete.return_value = True
            topic_service.session.commit = AsyncMock()
            
            # Act
            result = await topic_service.delete_topic(topic_id, hard_delete=True)
            
            # Assert
            assert result is True
            mock_topic_repo.delete.assert_called_once_with(topic_id, soft_delete=False)
            topic_service.storage.delete_folder.assert_called_once_with("topics/1")


# =============================================================================
# Integration Tests
# =============================================================================

class TestTopicServiceIntegration:
    """Integration tests with real database."""
    
    @pytest.fixture
    async def topic_service_integration(self, test_db_session, mock_storage, mock_event_bus):
        """Create TopicService with real database session."""
        return TopicService(
            session=test_db_session,
            storage=mock_storage,
            event_bus=mock_event_bus,
            message_broker=None
        )
    
    async def test_full_topic_lifecycle(self, topic_service_integration):
        """Test complete topic lifecycle with database."""
        service = topic_service_integration
        
        # Create topic
        create_request = TopicFactory.create_topic_request(name="Integration Test Topic")
        
        with patch.object(service, '_validate_topic_creation'):  # Skip validation for test
            created_topic = await service.create_topic(create_request)
        
        assert created_topic.name == "Integration Test Topic"
        topic_id = created_topic.id
        
        # Retrieve topic
        retrieved_topic = await service.get_topic(topic_id)
        assert retrieved_topic is not None
        assert retrieved_topic.name == "Integration Test Topic"
        
        # Update topic
        update_request = TopicFactory.create_topic_request(
            name="Updated Integration Topic",
            description="Updated description"
        )
        
        with patch.object(service, '_validate_topic_update'):  # Skip validation
            updated_topic = await service.update_topic(topic_id, update_request)
        
        assert updated_topic is not None
        assert updated_topic.name == "Updated Integration Topic"
        assert updated_topic.description == "Updated description"
        
        # Delete topic
        with patch.object(service, '_validate_topic_deletion'):  # Skip validation
            deleted = await service.delete_topic(topic_id)
        
        assert deleted is True
        
        # Verify topic is gone
        deleted_topic = await service.get_topic(topic_id)
        assert deleted_topic is None  # Assuming soft delete makes it invisible


# =============================================================================
# API Tests
# =============================================================================

@pytest.fixture
def test_app():
    """Create test FastAPI application."""
    from fastapi import FastAPI, Depends
    from examples.simplified_dependencies import get_topic_service
    
    app = FastAPI()
    
    # Override dependencies for testing
    def override_topic_service():
        # Return a mock or test service
        return AsyncMock()
    
    app.dependency_overrides[get_topic_service] = override_topic_service
    
    # Add routes (simplified for testing)
    from fastapi import APIRouter
    router = APIRouter(prefix="/api/v1/topics")
    
    @router.post("/")
    async def create_topic(request: dict, service=Depends(get_topic_service)):
        return await service.create_topic(request)
    
    @router.get("/{topic_id}")
    async def get_topic(topic_id: int, service=Depends(get_topic_service)):
        return await service.get_topic(topic_id)
    
    app.include_router(router)
    
    return app


class TestTopicAPI:
    """API endpoint tests."""
    
    def test_create_topic_api(self, test_app):
        """Test topic creation via API."""
        with TestClient(test_app) as client:
            # Arrange
            topic_data = {
                "name": "API Test Topic",
                "description": "Created via API",
                "category": "test",
                "tags": ["api", "test"]
            }
            
            # Act
            response = client.post("/api/v1/topics/", json=topic_data)
            
            # Assert
            assert response.status_code == 200
            # Additional assertions would depend on the actual service response
    
    def test_get_topic_api(self, test_app):
        """Test topic retrieval via API."""
        with TestClient(test_app) as client:
            # Act
            response = client.get("/api/v1/topics/1")
            
            # Assert
            assert response.status_code == 200
    
    async def test_create_topic_async_api(self, test_app):
        """Test topic creation with async client."""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            topic_data = {
                "name": "Async API Test Topic",
                "description": "Created via async API",
                "category": "test"
            }
            
            response = await client.post("/api/v1/topics/", json=topic_data)
            assert response.status_code == 200


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Performance and load tests."""
    
    @pytest.mark.slow
    async def test_concurrent_topic_creation(self, topic_service):
        """Test concurrent topic creation performance."""
        import asyncio
        
        async def create_topic(index):
            request = TopicFactory.create_topic_request(name=f"Concurrent Topic {index}")
            return await topic_service.create_topic(request)
        
        # Create 10 topics concurrently
        start_time = asyncio.get_event_loop().time()
        tasks = [create_topic(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()
        
        # Verify results
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) == 10
        
        # Performance assertion (adjust threshold as needed)
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete in under 5 seconds


# =============================================================================
# Test Utilities
# =============================================================================

class TestHelpers:
    """Utility functions for testing."""
    
    @staticmethod
    def assert_topic_response(response, expected_name: str, expected_category: str = None):
        """Helper to assert topic response structure."""
        assert hasattr(response, 'id')
        assert hasattr(response, 'name')
        assert hasattr(response, 'created_at')
        assert response.name == expected_name
        if expected_category:
            assert response.category == expected_category
    
    @staticmethod
    async def create_test_topic(service, name: str = "Test Topic"):
        """Helper to create a test topic."""
        request = TopicFactory.create_topic_request(name=name)
        return await service.create_topic(request)


# =============================================================================
# Pytest Configuration
# =============================================================================

"""
# conftest.py content for global test configuration

import pytest
import asyncio
from pathlib import Path


def pytest_configure(config):
    # Configure test markers
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    # Set up test environment
    import os
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE__NAME"] = "test_rag_db"
    
    yield
    
    # Cleanup after all tests


# pytest.ini content:
# [tool:pytest]
# testpaths = tests
# python_files = test_*.py *_test.py
# python_classes = Test* *Tests
# python_functions = test_*
# asyncio_mode = auto
# markers =
#     slow: marks tests as slow (deselect with '-m "not slow"')
#     integration: marks tests as integration tests
#     unit: marks tests as unit tests
#     api: marks tests as API tests
# addopts = 
#     --strict-markers
#     --strict-config
#     --cov=application
#     --cov=infrastructure
#     --cov-report=term-missing
#     --cov-report=html:htmlcov
"""


# =============================================================================
# Running Tests
# =============================================================================

"""
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests with coverage
pytest --cov=application --cov=infrastructure --cov-report=html

# Run tests in parallel
pytest -n auto

# Run specific test file
pytest tests/unit/test_topic_service.py

# Run specific test
pytest tests/unit/test_topic_service.py::TestTopicService::test_create_topic_success

# Run tests with verbose output
pytest -v

# Skip slow tests
pytest -m "not slow"
"""


# =============================================================================
# Benefits of This Testing Strategy
# =============================================================================

"""
This comprehensive testing strategy provides:

1. **Unit Tests**: Fast, isolated tests for business logic
2. **Integration Tests**: Tests with real database and external services
3. **API Tests**: End-to-end testing of HTTP endpoints
4. **Performance Tests**: Load and concurrency testing
5. **Test Fixtures**: Reusable test setup and teardown
6. **Factory Pattern**: Consistent test data generation
7. **Mocking**: Isolated testing without external dependencies
8. **Async Support**: Proper async/await testing patterns
9. **Database Testing**: In-memory database for fast tests
10. **Coverage Reports**: Comprehensive test coverage tracking

Key improvements over the current architecture:
- Clear test organization by test type
- Consistent mocking and fixture patterns
- Performance testing capabilities
- Easy test data creation with factories
- Proper async test support
- Integration with CI/CD pipelines
"""
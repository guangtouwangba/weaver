"""
Test configuration and fixtures for all test types.

Provides comprehensive test fixtures for unit, integration, and end-to-end tests.
"""
import os
import asyncio
from typing import AsyncGenerator, Generator
import pytest

# Import test utilities
from tests.utils import TestDataFactory, TestAssertions, TestHelpers

# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "database: mark test as database integration test")
    config.addinivalue_line("markers", "api: mark test as API integration test")
    config.addinivalue_line("markers", "fullstack: mark test as full stack integration test")
    config.addinivalue_line("markers", "load_test: mark test as load/stress test")

def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their location or name."""
    for item in items:
        # Mark unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark e2e tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)  # E2E tests are typically slow
        
        # Mark database tests
        if "database" in str(item.fspath) or "database" in item.name:
            item.add_marker(pytest.mark.database)
        
        # Mark API tests
        if "_api.py" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        
        # Mark performance tests
        if "performance" in str(item.fspath) or "performance" in item.name:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        # Mark full stack tests
        if "full_stack" in str(item.fspath) or "fullstack" in item.name:
            item.add_marker(pytest.mark.fullstack)
            item.add_marker(pytest.mark.slow)

def pytest_runtest_setup(item):
    """Setup function run before each test."""
    # Skip integration tests if running in unit test mode
    if item.get_closest_marker("integration"):
        if item.config.getoption("-m") == "unit":
            pytest.skip("Skipping integration test in unit test mode")
    
    # Skip e2e tests if running in unit test mode
    if item.get_closest_marker("e2e"):
        if item.config.getoption("-m") in ["unit", "integration"]:
            pytest.skip("Skipping e2e test in unit/integration test mode")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_topic_data():
    """Sample topic data for testing."""
    return TestDataFactory.create_topic_data(
        title="测试主题",
        description="这是一个测试主题的描述",
        tags=["测试", "RAG", "知识管理"],
        is_public=True
    )

@pytest.fixture
def sample_file_data():
    """Sample file data for testing."""
    return TestDataFactory.create_file_data(
        filename="test_document.pdf", 
        content_type="application/pdf"
    )

@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "title": "测试文档",
        "content": TestDataFactory.create_document_content(
            content_type="article",
            word_count=300,
            include_keywords=["测试", "文档", "RAG"]
        ),
        "content_type": "text/plain",
        "metadata": {
            "source": "integration_test",
            "category": "test"
        }
    }

@pytest.fixture
def bulk_test_data():
    """Bulk test data for performance testing."""
    return TestDataFactory.create_bulk_test_data(
        topic_count=5,
        files_per_topic=3,
        content_type="mixed"
    )

@pytest.fixture
def test_assertions():
    """Test assertion utilities."""
    return TestAssertions

@pytest.fixture
def test_helpers():
    """Test helper utilities."""
    return TestHelpers


# Database and HTTP client fixtures (for integration/e2e tests)
# These will only be set up when the required modules are available

DATABASE_AVAILABLE = False
try:
    from httpx import AsyncClient, ASGITransport
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    
    # Try to import application modules
    import sys
    project_root = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, project_root)
    
    from main import app
    from modules.database.connection import Base
    from modules.database import get_db_session
    
    # Test database configuration
    TEST_DATABASE_URL = "postgresql+asyncpg://rag_user:rag_password@localhost:5432/rag_test_db"
    
    # Create test engine
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        connect_args={"command_timeout": 60}
    )
    
    # Create test session factory
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    DATABASE_AVAILABLE = True
    
    async def get_test_db_session() -> AsyncGenerator[AsyncSession, None]:
        """Override database session for tests."""
        async with test_session_factory() as session:
            yield session

    @pytest.fixture(scope="function")
    async def db_session() -> AsyncGenerator[AsyncSession, None]:
        """Provide a database session for each test."""
        if not DATABASE_AVAILABLE:
            pytest.skip("Database not available")
        
        async with test_session_factory() as session:
            yield session

    @pytest.fixture(scope="function", autouse=True)
    async def setup_database():
        """Setup and teardown test database for each test."""
        if not DATABASE_AVAILABLE:
            pytest.skip("Database not available")
        
        # Create tables
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        yield
        
        # Clean up after test
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @pytest.fixture(scope="function")
    async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
        """Create HTTP client for testing."""
        if not DATABASE_AVAILABLE:
            pytest.skip("Database not available")
        
        # Override the database dependency
        app.dependency_overrides[get_db_session] = get_test_db_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
        
        # Clear overrides after test
        app.dependency_overrides.clear()

except ImportError:
    # Database modules not available - create dummy fixtures that skip tests
    @pytest.fixture
    def db_session():
        pytest.skip("Database modules not available")
    
    @pytest.fixture
    def client():
        pytest.skip("Database modules not available")
    
    @pytest.fixture
    def setup_database():
        pytest.skip("Database modules not available")
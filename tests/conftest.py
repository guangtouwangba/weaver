"""
Test configuration and fixtures for integration tests.
"""
import os
import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Import the main application
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from main import app
from modules.database import Base, get_db_session

# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://rag_user:rag_password@localhost:5432/rag_test_db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # Disable connection pooling for tests
)

test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

async def get_test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Override database session for tests."""
    async with test_session_factory() as session:
        yield session

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for each test."""
    async with test_session_factory() as session:
        yield session

@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Setup and teardown test database for each test."""
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
    # Override the database dependency
    app.dependency_overrides[get_db_session] = get_test_db_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Clear overrides after test
    app.dependency_overrides.clear()

@pytest.fixture
def sample_topic_data():
    """Sample topic data for testing."""
    return {
        "title": "测试主题",
        "description": "这是一个测试主题的描述",
        "tags": ["测试", "RAG", "知识管理"],
        "is_public": True
    }

@pytest.fixture
def sample_file_data():
    """Sample file data for testing."""
    return {
        "filename": "test_document.pdf", 
        "content_type": "application/pdf",
        "file_size": 1024,
        "topic_id": None  # Will be set by tests
    }

@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "title": "测试文档",
        "content": "这是一个测试文档的内容，用于验证系统功能。",
        "content_type": "text/plain",
        "metadata": {
            "source": "integration_test",
            "category": "test"
        }
    }
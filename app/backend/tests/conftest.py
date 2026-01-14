"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from research_agent.api.deps import get_db
from research_agent.infrastructure.database.models import Base
from research_agent.infrastructure.database.session import get_session
from research_agent.main import app

# ==============================================================================
# SQLite Compatibility Layer for PostgreSQL Types
# ==============================================================================

# Use explicit compilation hooks which are stronger than colspecs
@compiles(Vector, "sqlite")
def compile_vector(type_, compiler, **kw):
    return "TEXT"

@compiles(JSONB, "sqlite")
def compile_jsonb(type_, compiler, **kw):
    return "JSON"

@compiles(PG_UUID, "sqlite")
def compile_uuid(type_, compiler, **kw):
    return "VARCHAR(36)"

@compiles(TSVECTOR, "sqlite")
def compile_tsvector(type_, compiler, **kw):
    return "TEXT"

@compiles(ARRAY, "sqlite")
def compile_array(type_, compiler, **kw):
    return "JSON"


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict("os.environ", {
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "OPENROUTER_API_KEY": "sk-mock-key",
        "SUPABASE_URL": "https://mock.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "mock-key",
        "ENVIRONMENT": "test"
    }):
        yield


# Mock app startup to prevent connecting to real DB
@pytest.fixture(scope="session", autouse=True)
def mock_app_startup(mock_env_vars):
    """Mock application startup components."""
    with patch("research_agent.main.init_db", new_callable=AsyncMock), \
         patch("research_agent.main.close_db", new_callable=AsyncMock), \
         patch("research_agent.main.BackgroundWorker") as mock_worker_cls:

        # Mock background worker instance
        mock_worker = MagicMock()
        mock_worker.start = AsyncMock()
        mock_worker.stop = AsyncMock()
        mock_worker_cls.return_value = mock_worker

        yield


@pytest.fixture(scope="session")
async def db_engine(mock_env_vars):
    """Create async database engine using SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # Enable foreign keys in SQLite
    async with engine.connect() as conn:
        await conn.exec_driver_sql("PRAGMA foreign_keys = ON")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession]:
    """Create a new database session for a test function."""
    connection = await db_engine.connect()
    transaction = await connection.begin()

    session = AsyncSession(bind=connection, expire_on_commit=False)

    # Override the get_db/get_session dependency for the app
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_db] = override_get_session

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Create a test client with overridden dependencies."""
    if not hasattr(app, "state"):
        app.state = MagicMock()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for unit tests",
    }


@pytest.fixture
def sample_canvas_data():
    """Sample canvas data for testing."""
    return {
        "nodes": [
            {
                "id": "node-1",
                "type": "card",
                "title": "Test Card",
                "content": "Test content",
                "x": 100,
                "y": 200,
            }
        ],
        "edges": [],
        "viewport": {"x": 0, "y": 0, "scale": 1},
    }

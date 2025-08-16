"""
Database configuration and connection management.

Provides both synchronous and asynchronous database connections
with proper connection pooling and environment-based configuration.
"""

import os
from typing import Optional, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')
load_dotenv('.env.middleware')


class DatabaseConfig:
    """Database configuration class with environment-based settings."""
    
    def __init__(self):
        """Initialize database configuration from environment variables."""
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = int(os.getenv('POSTGRES_PORT', 5432))
        self.database = os.getenv('POSTGRES_DB', 'rag_db')
        self.username = os.getenv('POSTGRES_USER', 'rag_user')
        self.password = os.getenv('POSTGRES_PASSWORD', 'rag_password')
        
        # Connection settings
        self.echo = os.getenv('SQL_ECHO', 'false').lower() == 'true'
        self.pool_size = int(os.getenv('DB_POOL_SIZE', 10))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', 20))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', 3600))
        
        # SSL settings
        self.ssl_mode = os.getenv('POSTGRES_SSL_MODE', 'prefer')
    
    @property
    def sync_url(self) -> str:
        """Synchronous database connection URL."""
        base_url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        if self.ssl_mode != 'prefer':
            base_url += f"?sslmode={self.ssl_mode}"
        return base_url
    
    @property
    def async_url(self) -> str:
        """Asynchronous database connection URL."""
        base_url = f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        if self.ssl_mode != 'prefer':
            base_url += f"?ssl={self.ssl_mode}"
        return base_url
    
    @property
    def alembic_url(self) -> str:
        """Alembic migration database connection URL."""
        return self.sync_url
    
    def get_test_config(self) -> 'DatabaseConfig':
        """Get a test database configuration."""
        test_config = DatabaseConfig()
        test_config.database = f"{self.database}_test"
        return test_config


# Global configuration instance
db_config = DatabaseConfig()


def create_sync_engine(config: Optional[DatabaseConfig] = None) -> Engine:
    """Create a synchronous SQLAlchemy engine."""
    config = config or db_config
    
    return create_engine(
        config.sync_url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_pre_ping=True,
        pool_recycle=config.pool_recycle,
        # Connection arguments for better error handling
        connect_args={
            "connect_timeout": 30,
        }
    )


def create_async_engine_instance(config: Optional[DatabaseConfig] = None) -> AsyncEngine:
    """Create an asynchronous SQLAlchemy engine."""
    config = config or db_config
    
    return create_async_engine(
        config.async_url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_pre_ping=True,
        pool_recycle=config.pool_recycle,
        # Connection arguments for better error handling
        connect_args={
            "server_settings": {
                "application_name": "research-agent-rag",
            },
        }
    )


# Global engine instances
sync_engine = create_sync_engine()
async_engine = create_async_engine_instance()

# Session factories
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
    expire_on_commit=False  # Prevent lazy loading issues
)

AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    expire_on_commit=False
)


def get_database_session() -> Session:
    """Get a synchronous database session."""
    return SyncSessionLocal()


async def get_async_database_session() -> AsyncSession:
    """Get an asynchronous database session."""
    return AsyncSessionLocal()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic cleanup."""
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Dependency injection functions (for FastAPI, etc.)
def get_db_dependency():
    """Database session dependency for FastAPI."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db_dependency():
    """Async database session dependency for FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Health check function
def check_database_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        from sqlalchemy import text
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def check_async_database_connection() -> bool:
    """Check if async database connection is healthy."""
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


# Convenience functions for backward compatibility
def get_database_config() -> DatabaseConfig:
    """Get the global database configuration."""
    return db_config


def get_sync_session() -> Session:
    """Get a synchronous database session (backward compatibility)."""
    return get_database_session()


async def get_async_session() -> AsyncSession:
    """Get an asynchronous database session (backward compatibility)."""
    return await get_async_database_session()
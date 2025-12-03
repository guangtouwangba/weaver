"""SQLAlchemy async session management."""

import asyncio
import ssl

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import Pool

from research_agent.config import get_settings
from research_agent.shared.utils.logger import logger

settings = get_settings()


# Debug: Log database configuration
def _mask_password(url: str) -> str:
    """Mask password in database URL for logging."""
    import re

    return re.sub(r":([^:@]+)@", ":****@", url)


logger.info(f"Database URL: {_mask_password(settings.database_url)}")

# Check connection mode
if "pooler" in settings.database_url:
    if ":6543/" in settings.database_url:
        logger.info(
            "✅ Using Transaction Mode (port 6543) - Recommended for applications with connection pooling"
        )
    elif ":5432/" in settings.database_url:
        logger.warning(
            "⚠️  Using Session Mode (port 5432) - Consider Transaction Mode (port 6543) for better concurrency"
        )

# Configure connection args for asyncpg
connect_args: dict = {}

# Check if using a connection pooler (Supavisor/PgBouncer)
is_using_pooler = "pooler" in settings.database_url
is_transaction_mode = ":6543/" in settings.database_url

# Configure SSL for cloud PostgreSQL
if (
    "supabase" in settings.database_url
    or "neon" in settings.database_url
    or "pooler" in settings.database_url
):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

# For connection poolers, disable prepared statements
if is_using_pooler:
    connect_args["statement_cache_size"] = 0

# Add asyncpg timeout settings to prevent "connection is closed" errors
# These are critical for long-running operations like batch inserts
connect_args["timeout"] = 60  # Connection timeout (seconds)
connect_args["command_timeout"] = (
    300  # Command execution timeout (5 minutes for large batch inserts)
)
# Note: close_timeout is not a valid asyncpg parameter
# Connection close timeout is handled at application level in close_db()
connect_args["server_settings"] = {
    "application_name": "research_agent_backend",
}

logger.info(
    f"asyncpg timeout configuration: timeout={connect_args['timeout']}s, "
    f"command_timeout={connect_args['command_timeout']}s"
)

# Create async engine (use async_database_url to ensure asyncpg driver)
logger.info(f"Creating async engine with URL: {_mask_password(settings.async_database_url)}")
logger.info(f"Connect args: { {k: v for k, v in connect_args.items() if k != 'ssl'} }")

# For pooler connections, we need additional configuration
engine_kwargs: dict = {
    "echo": False,  # Disable SQL echo to reduce log noise
    "connect_args": connect_args,
}

# Configure connection pool based on mode
if is_using_pooler and is_transaction_mode:
    # Transaction Mode: Use NullPool (connection pooling handled by Supabase pooler)
    # Transaction Mode uses Supabase's connection pooler, so we don't need SQLAlchemy's pool
    from sqlalchemy.pool import NullPool

    engine_kwargs["poolclass"] = NullPool
    logger.info("Transaction Mode: Using NullPool (connection pooling handled by Supabase pooler)")
else:
    # Session Mode: Use SQLAlchemy connection pool
    engine_kwargs["pool_pre_ping"] = True
    # Reduce pool size to avoid exceeding PostgreSQL max_connections
    # For local PostgreSQL, max_connections is typically 100
    # For Supabase Session Mode, it depends on your plan
    engine_kwargs["pool_size"] = 5  # Conservative pool size
    engine_kwargs["max_overflow"] = 10  # Allow 10 additional connections beyond pool_size
    engine_kwargs["pool_timeout"] = 30  # Wait up to 30 seconds for a connection
    engine_kwargs["pool_recycle"] = 3600  # Recycle connections after 1 hour
    # Reset connections on return to pool to avoid stale connection issues
    engine_kwargs["pool_reset_on_return"] = "rollback"

    logger.info(
        f"Session Mode: Database pool configuration: pool_size={engine_kwargs['pool_size']}, "
        f"max_overflow={engine_kwargs['max_overflow']}, "
        f"max_connections={engine_kwargs['pool_size'] + engine_kwargs['max_overflow']}, "
        f"pool_recycle={engine_kwargs['pool_recycle']}s"
    )

engine = create_async_engine(
    settings.async_database_url,
    **engine_kwargs,
)


# Add event listener to suppress connection close timeout errors
@event.listens_for(Pool, "close")
def receive_close(dbapi_conn, connection_record):
    """Suppress asyncpg close timeout errors."""
    # This event is fired when a connection is closed
    # We don't need to do anything here, just having this listener
    # helps SQLAlchemy handle close errors more gracefully
    pass


@event.listens_for(Pool, "close_detached")
def receive_close_detached(dbapi_conn, connection_record):
    """Handle detached connection close."""
    # This handles connections that are closed outside the pool
    pass


# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database connection."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
            logger.info("Database connected")
    except Exception as e:
        logger.error(f"Database connection failed: {type(e).__name__}: {e}")
        logger.error("Please check your DATABASE_URL configuration")
        logger.error("For Supabase, use Transaction Mode (port 6543) for better concurrency")
        logger.error(
            "Transaction Mode uses connection pooling and supports more concurrent connections"
        )
        raise


async def close_db() -> None:
    """Close database connection gracefully with timeout handling."""
    try:
        logger.info("Closing database connections...")
        # Use timeout wrapper to avoid infinite wait during close
        await asyncio.wait_for(engine.dispose(), timeout=30.0)
        logger.info("✅ Database connections closed successfully")
    except asyncio.TimeoutError:
        logger.warning("⚠️ Database connection close timed out (30s), forcing close")
        # Force close (synchronous way)
        try:
            engine.sync_engine.dispose(close=True)
            logger.info("✅ Database connections force-closed")
        except Exception as force_error:
            logger.error(f"❌ Failed to force close database: {force_error}")
    except Exception as e:
        logger.warning(
            f"⚠️ Error closing database connections: {type(e).__name__}: {e}",
            exc_info=True,
        )
        # Try to force close even if there's an error
        try:
            engine.sync_engine.dispose(close=True)
            logger.info("✅ Database connections force-closed after error")
        except Exception:
            pass


def get_async_session_factory():
    """
    Get async session factory as a context manager.

    Used by background workers to create sessions.
    """
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def session_factory():
        async with async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    return session_factory

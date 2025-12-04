"""SQLAlchemy async session management."""

import asyncio
import atexit
import ssl
import sys
import threading
import weakref
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, Pool

from research_agent.config import get_settings
from research_agent.shared.utils.logger import logger


# ✅ CRITICAL: Global stderr filter to suppress asyncpg close timeout errors
class AsyncpgErrorFilter:
    """Filter stderr to suppress asyncpg connection close timeout errors."""

    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self._buffer = ""
        self._lock = threading.Lock()
        self._suppressing = False

    def write(self, text):
        with self._lock:
            # Check if this is the start of an asyncpg close error
            if "Exception closing connection" in text:
                self._suppressing = True
                self._buffer = text
                return

            if self._suppressing:
                self._buffer += text
                # Check if we've captured the full traceback
                if "TimeoutError" in text and text.strip().endswith("TimeoutError"):
                    # Suppress this entire error, clear buffer
                    self._buffer = ""
                    self._suppressing = False
                    return
                # If it's something else, stop suppressing and flush
                if text.strip() and not any(
                    x in text
                    for x in [
                        "Traceback",
                        "File ",
                        "line ",
                        "asyncpg",
                        "sqlalchemy",
                        "await",
                        "TimeoutError",
                        "close",
                        "connection",
                        "pool",
                    ]
                ):
                    # This is different content, stop suppressing and output
                    self._suppressing = False
                    self.original_stderr.write(self._buffer + text)
                    self._buffer = ""
                return

            # Normal output
            self.original_stderr.write(text)

    def flush(self):
        self.original_stderr.flush()

    def fileno(self):
        return self.original_stderr.fileno()

    def isatty(self):
        return self.original_stderr.isatty()


# Install global stderr filter immediately
_original_stderr = sys.stderr
sys.stderr = AsyncpgErrorFilter(_original_stderr)


def _restore_stderr():
    """Restore original stderr on exit."""
    sys.stderr = _original_stderr


atexit.register(_restore_stderr)

settings = get_settings()

# Track active sessions for graceful shutdown
_active_sessions: set[weakref.ref] = set()


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

# ✅ Key: Reduce timeout times for faster failure detection
connect_args["timeout"] = 30  # Reduced from 60 to 30 seconds
connect_args["command_timeout"] = 60  # Reduced from 300 to 60 seconds
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

# ✅ CRITICAL FIX: Always use NullPool to avoid connection close timeout issues
# NullPool doesn't maintain a connection pool, so no connection close timeouts
engine_kwargs["poolclass"] = NullPool
logger.info("🔧 Using NullPool (no connection pooling - fixes close timeout issues)")

engine = create_async_engine(
    settings.async_database_url,
    **engine_kwargs,
)


# Event listeners are minimal for NullPool
@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Set connection parameters on connect."""
    logger.debug("New database connection established")


# Create async session maker with proper configuration
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # ✅ Disable auto flush, manual control
    autocommit=False,  # ✅ Explicitly disable auto commit
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
    """Close database connection gracefully."""
    try:
        logger.info("Closing database connections...")
        await asyncio.wait_for(engine.dispose(), timeout=5.0)  # ✅ Reduced to 5 seconds
        logger.info("✅ Database connections closed")
    except TimeoutError:
        logger.warning("⚠️ Database close timed out, continuing shutdown")
    except Exception as e:
        logger.warning(f"⚠️ Error closing database: {e}")


# ✅ Improved: Session factory with proper tracking
@asynccontextmanager
async def get_async_session():
    """
    Get async session as a context manager with proper tracking.

    Usage:
        async with get_async_session() as session:
            # Use session
            pass
    """
    session = async_session_maker()

    # Track this session
    session_ref = weakref.ref(session)
    _active_sessions.add(session_ref)

    try:
        yield session
        # ✅ Ensure commit
        await session.commit()
    except Exception as e:
        # ✅ Ensure rollback
        logger.error(f"Session error, rolling back: {e}")
        await session.rollback()
        raise
    finally:
        # ✅ Ensure close
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")
        finally:
            # Remove from tracking
            _active_sessions.discard(session_ref)


def get_async_session_factory():
    """
    Get async session factory as a context manager.

    Used by background workers to create sessions.

    ⚠️ Deprecated: Use get_async_session() directly instead.
    """
    return get_async_session


# ✅ New: Get active session count (for monitoring)
def get_active_session_count() -> int:
    """Get count of currently active sessions."""
    # Clean up dead references
    _active_sessions.difference_update(ref for ref in _active_sessions if ref() is None)
    return len(_active_sessions)

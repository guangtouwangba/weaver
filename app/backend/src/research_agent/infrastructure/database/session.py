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
from sqlalchemy.pool import AsyncAdaptedQueuePool, Pool

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

# ✅ Key: Connection timeout configuration
# Adjusted for cloud databases with potential network latency (e.g., Supabase from China)
connect_args["timeout"] = 30  # Connection timeout: 30 seconds (increased for high latency networks)
connect_args["command_timeout"] = 60  # Command execution timeout: 60 seconds
connect_args["server_settings"] = {
    "application_name": "research_agent_backend",
    "statement_timeout": "60000",  # 60 second statement timeout at PostgreSQL level
}

logger.info(
    f"asyncpg timeout configuration: timeout={connect_args['timeout']}s, "
    f"command_timeout={connect_args['command_timeout']}s, statement_timeout=60s"
)

# Create async engine (use async_database_url to ensure asyncpg driver)
logger.info(f"Creating async engine with URL: {_mask_password(settings.async_database_url)}")
logger.info(f"Connect args: { {k: v for k, v in connect_args.items() if k != 'ssl'} }")

# For pooler connections, we need additional configuration
engine_kwargs: dict = {
    "echo": False,  # Disable SQL echo to reduce log noise
    "connect_args": connect_args,
}

# ✅ FIXED: Use AsyncAdaptedQueuePool with appropriate settings for concurrent operations
# NullPool was causing TimeoutError during heavy concurrent operations (like Gemini OCR)
# because every request created a new connection, overwhelming the system.
# Note: For async engines, we must use AsyncAdaptedQueuePool, not QueuePool
engine_kwargs["poolclass"] = AsyncAdaptedQueuePool
engine_kwargs["pool_size"] = 20  # Base number of persistent connections (increased for OCR + API)
engine_kwargs["max_overflow"] = 25  # Allow up to 45 total connections (20 + 25)
engine_kwargs["pool_timeout"] = 45  # Wait up to 45s to get a connection from pool (increased)
engine_kwargs["pool_recycle"] = (
    120  # Recycle connections after 2 minutes (more lenient for high latency)
)
engine_kwargs["pool_pre_ping"] = True  # Verify connections before use (handles stale connections)
engine_kwargs["pool_reset_on_return"] = "rollback"  # Ensure clean state on return to pool
engine_kwargs["pool_use_lifo"] = (
    True  # Use LIFO to prefer recently used connections (less likely to be stale)
)
logger.info(
    f"🔧 Using AsyncAdaptedQueuePool (pool_size={engine_kwargs['pool_size']}, "
    f"max_overflow={engine_kwargs['max_overflow']}, pool_pre_ping=True, "
    f"pool_recycle=120s, pool_timeout=45s, pool_use_lifo=True) [v7-high-concurrency]"
)

engine = create_async_engine(
    settings.async_database_url,
    **engine_kwargs,
)


# ============================================================================
# Connection Pool Monitoring
# ============================================================================

# Pool warning threshold (80% usage triggers warning)
POOL_WARNING_THRESHOLD = 0.8


def get_pool_status() -> dict:
    """
    Get current connection pool status.

    Returns:
        dict with pool statistics:
        - size: Current pool size (connections in pool)
        - checkedin: Available connections in pool
        - checkedout: Connections currently in use
        - overflow: Current overflow connections
        - max_overflow: Maximum allowed overflow
        - total_max: Maximum total connections (pool_size + max_overflow)
        - usage_ratio: Current usage as a ratio (0.0 - 1.0+)
    """
    pool = engine.pool
    pool_size = engine_kwargs["pool_size"]
    max_overflow = engine_kwargs["max_overflow"]
    total_max = pool_size + max_overflow

    checkedout = pool.checkedout()
    checkedin = pool.checkedin()
    overflow = pool.overflow()

    return {
        "size": pool.size(),
        "checkedin": checkedin,
        "checkedout": checkedout,
        "overflow": overflow,
        "max_overflow": max_overflow,
        "total_max": total_max,
        "usage_ratio": checkedout / total_max if total_max > 0 else 0,
    }


async def log_pool_status_periodically(interval: int = 60) -> None:
    """
    Log connection pool status periodically.

    This can be started as a background task for monitoring.

    Args:
        interval: Seconds between status logs (default: 60)
    """
    while True:
        try:
            status = get_pool_status()
            usage_pct = status["usage_ratio"] * 100
            logger.info(
                f"📊 Pool status: checkedout={status['checkedout']}/{status['total_max']} "
                f"({usage_pct:.1f}%), checkedin={status['checkedin']}, overflow={status['overflow']}"
            )
        except Exception as e:
            logger.warning(f"Failed to get pool status: {e}")
        await asyncio.sleep(interval)


# Event listeners for connection pool management
@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Set connection parameters on connect."""
    logger.debug("New database connection established")


@event.listens_for(Pool, "invalidate")
def receive_invalidate(dbapi_conn, connection_record, exception):
    """Log when a connection is invalidated."""
    if exception:
        logger.warning(
            f"⚠️ Database connection invalidated due to: {type(exception).__name__}: {exception}"
        )
    else:
        logger.debug("Database connection invalidated (no exception)")


@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool and warn if usage is high."""
    try:
        status = get_pool_status()
        usage_ratio = status["usage_ratio"]

        if usage_ratio >= POOL_WARNING_THRESHOLD:
            logger.warning(
                f"⚠️ Connection pool usage high: {usage_ratio:.1%} "
                f"({status['checkedout']}/{status['total_max']}), "
                f"overflow={status['overflow']}/{status['max_overflow']}"
            )
        else:
            logger.debug(
                f"Connection checked out from pool "
                f"({status['checkedout']}/{status['total_max']} in use)"
            )
    except Exception as e:
        logger.debug(f"Connection checked out from pool (status check failed: {e})")


# Create async session maker with proper configuration
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # ✅ Disable auto flush, manual control
    autocommit=False,  # ✅ Explicitly disable auto commit
)


async def init_db() -> None:
    """Initialize database connection with retry logic."""
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempting database connection (attempt {attempt}/{max_retries})...")
            async with asyncio.timeout(10):  # 10 second timeout for init check
                async with engine.begin() as conn:
                    await conn.run_sync(lambda _: None)
            logger.info("✅ Database connected successfully")
            return
        except asyncio.TimeoutError:
            logger.error(f"❌ Database connection timeout on attempt {attempt}/{max_retries}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Database connection failed after all retries")
                logger.error("Please check:")
                logger.error("  1. Database server is running")
                logger.error("  2. DATABASE_URL is correct")
                logger.error("  3. Network connectivity to database")
                logger.error(
                    "For Supabase, use Transaction Mode (port 6543) for better concurrency"
                )
                raise
        except Exception as e:
            logger.error(
                f"❌ Database connection error on attempt {attempt}/{max_retries}: {type(e).__name__}: {e}"
            )
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Database connection failed after all retries")
                logger.error("Please check your DATABASE_URL configuration")
                logger.error(
                    "For Supabase, use Transaction Mode (port 6543) for better concurrency"
                )
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
# Note: Connection validation is handled by pool_pre_ping=True at the pool level,
# so we don't need to test connections here (which would start unwanted transactions)
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


# ✅ FastAPI dependency for session injection
# Note: Connection validation is handled by pool_pre_ping=True at the pool level
async def get_session():
    """
    FastAPI dependency that yields a database session.

    Usage:
        @router.get("/example")
        async def example(session: AsyncSession = Depends(get_session)):
            # Use session
            pass
    """
    session = async_session_maker()

    # Track this session
    session_ref = weakref.ref(session)
    _active_sessions.add(session_ref)

    try:
        yield session
        await session.commit()
    except Exception as e:
        # Log connection errors with more detail for debugging
        error_str = str(e)
        if "ConnectionDoesNotExistError" in error_str or "connection was closed" in error_str:
            logger.error(f"⚠️ Database connection error (stale connection): {e}")
            # Try to invalidate the bad connection so pool_pre_ping can detect it next time
            try:
                conn = await session.connection()
                conn.invalidate()
            except Exception:
                pass  # Connection might already be invalid
        else:
            logger.error(f"Session error, rolling back: {e}")
        await session.rollback()
        raise
    finally:
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")
        finally:
            _active_sessions.discard(session_ref)

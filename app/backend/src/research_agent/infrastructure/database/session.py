"""SQLAlchemy async session management."""

import asyncio
import atexit
import ssl
import sys
import threading
import weakref
from contextlib import asynccontextmanager

from sqlalchemy import event, text
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
# IMPORTANT: Large PDF processing (OCR) can take 5-15 minutes, so timeouts must be generous
connect_args["timeout"] = 60  # Connection timeout: 60 seconds (for high latency networks)
connect_args["command_timeout"] = 300  # Command execution timeout: 5 minutes (for long queries)
connect_args["server_settings"] = {
    "application_name": "research_agent_backend",
    "statement_timeout": "300000",  # 5 minute statement timeout at PostgreSQL level
}

logger.info(
    f"asyncpg timeout configuration: timeout={connect_args['timeout']}s, "
    f"command_timeout={connect_args['command_timeout']}s, statement_timeout=300s"
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
engine_kwargs["pool_size"] = 10  # Base number of persistent connections
engine_kwargs["max_overflow"] = 20  # Allow up to 30 total connections (10 + 20)
engine_kwargs["pool_timeout"] = 60  # Wait up to 60s to get a connection from pool
engine_kwargs["pool_recycle"] = (
    300  # Recycle connections after 5 minutes (reduced to prevent stale connections)
)
engine_kwargs["pool_pre_ping"] = True  # Verify connections before use (handles stale connections)
engine_kwargs["pool_reset_on_return"] = "rollback"  # Ensure clean state on return to pool
engine_kwargs["pool_use_lifo"] = (
    True  # Use LIFO to prefer recently used connections (less likely to be stale)
)
logger.info(
    f"🔧 Using AsyncAdaptedQueuePool (pool_size={engine_kwargs['pool_size']}, "
    f"max_overflow={engine_kwargs['max_overflow']}, pool_pre_ping=True, "
    f"pool_recycle=300s, pool_timeout=60s, pool_use_lifo=True) [v9-connection-retry]"
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
    """
    Log when a connection is invalidated.
    
    Note: This is NORMAL behavior when pool_pre_ping=True detects a dead connection.
    The pool will automatically create a new connection. Only log as warning if
    it happens frequently or with specific error types.
    """
    if exception:
        error_type = type(exception).__name__
        error_msg = str(exception)
        
        # InvalidatePoolError is normal - connection was detected as dead by pre_ping
        # and will be replaced automatically. Only log at debug level.
        if "InvalidatePoolError" in error_type or "InvalidatePoolError" in error_msg:
            logger.debug(
                f"Connection invalidated (normal recovery): {error_type}. "
                f"Pool will create new connection automatically."
            )
        else:
            # Other errors might be more serious
            logger.warning(
                f"⚠️ Database connection invalidated due to: {error_type}: {error_msg}"
            )
    else:
        logger.debug("Database connection invalidated (no exception - normal pool maintenance)")


@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool and warn if usage is high."""
    # ✅ Reduced logging: Only log warnings, not every checkout (too noisy)
    try:
        status = get_pool_status()
        usage_ratio = status["usage_ratio"]

        if usage_ratio >= POOL_WARNING_THRESHOLD:
            logger.warning(
                f"⚠️ Connection pool usage high: {usage_ratio:.1%} "
                f"({status['checkedout']}/{status['total_max']}), "
                f"overflow={status['overflow']}/{status['max_overflow']}"
            )
        # Removed debug logging for normal checkouts to reduce log noise
    except Exception:
        # Silently ignore status check failures
        pass


# Create async session maker with proper configuration
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # ✅ Disable auto flush, manual control
    autocommit=False,  # ✅ Explicitly disable auto commit
)


async def init_db() -> None:
    """
    Initialize database connection with retry logic.
    
    Note: This function will NOT raise exceptions on failure.
    The application will start even if the database is temporarily unavailable.
    Individual requests will fail gracefully until the database is available.
    """
    max_retries = 3
    retry_delay = 3  # seconds
    connection_timeout = 30  # seconds - increased for slow cloud DB connections

    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"Attempting database connection (attempt {attempt}/{max_retries})...")
            async with asyncio.timeout(connection_timeout):
                async with engine.begin() as conn:
                    await conn.run_sync(lambda _: None)
            logger.debug("✅ Database connected successfully")
            return
        except asyncio.TimeoutError:
            logger.warning(f"⚠️  Database connection timeout on attempt {attempt}/{max_retries}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.warning("⚠️  Database connection failed after all retries")
                logger.warning("   Application will start anyway - requests will retry connection")
                logger.warning("   Please check:")
                logger.warning("     1. Database server is running")
                logger.warning("     2. DATABASE_URL is correct")
                logger.warning("     3. Network connectivity to database")
                logger.warning(
                    "   For Supabase, use Transaction Mode (port 6543) for better concurrency"
                )
                # Don't raise - let app start anyway
                return
        except asyncio.CancelledError:
            # Handle cancellation gracefully (e.g., during shutdown)
            logger.warning("⚠️  Database connection cancelled")
            return
        except Exception as e:
            logger.warning(
                f"⚠️  Database connection error on attempt {attempt}/{max_retries}: {type(e).__name__}: {e}"
            )
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.warning("⚠️  Database connection failed after all retries")
                logger.warning("   Application will start anyway - requests will retry connection")
                logger.warning("   Please check your DATABASE_URL configuration")
                logger.warning(
                    "   For Supabase, use Transaction Mode (port 6543) for better concurrency"
                )
                # Don't raise - let app start anyway
                return


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


# ✅ Improved: Session factory with proper tracking and retry logic
# Note: Connection validation is handled by pool_pre_ping=True at the pool level,
# but we add retry logic for connection errors that occur during operations
@asynccontextmanager
async def get_async_session(max_retries: int = 3):
    """
    Get async session as a context manager with proper tracking and retry logic.

    This function automatically retries on connection errors, which is critical
    for long-running operations (OCR, embedding generation) that may experience
    connection timeouts.

    Usage:
        async with get_async_session() as session:
            # Use session
            pass

    Args:
        max_retries: Maximum number of retries for connection errors (default: 3)
    """
    session = None
    last_error = None
    
    # Retry logic for session creation
    for attempt in range(1, max_retries + 1):
        try:
            session = async_session_maker()
            
            # Test connection with a simple query
            # This ensures the connection is alive before we yield it
            try:
                await session.execute(text("SELECT 1"))
            except Exception as conn_test_error:
                # Connection test failed, close and retry
                try:
                    await session.close()
                except Exception:
                    pass
                session = None
                
                # Check if this is a connection error that we should retry
                error_str = str(conn_test_error)
                if any(keyword in error_str for keyword in [
                    "ConnectionDoesNotExistError",
                    "connection was closed",
                    "connection closed",
                    "server closed the connection",
                    "connection timeout",
                ]):
                    if attempt < max_retries:
                        logger.warning(
                            f"⚠️ Connection test failed (attempt {attempt}/{max_retries}): "
                            f"{type(conn_test_error).__name__}. Retrying..."
                        )
                        await asyncio.sleep(0.5 * attempt)  # Exponential backoff
                        continue
                    else:
                        last_error = conn_test_error
                        break
                else:
                    # Non-connection error, don't retry
                    raise conn_test_error
            
            # Connection is good, break out of retry loop
            break
            
        except Exception as e:
            if session:
                try:
                    await session.close()
                except Exception:
                    pass
                session = None
            
            error_str = str(e)
            if any(keyword in error_str for keyword in [
                "ConnectionDoesNotExistError",
                "connection was closed",
                "connection closed",
                "server closed the connection",
            ]):
                if attempt < max_retries:
                    logger.warning(
                        f"⚠️ Session creation failed (attempt {attempt}/{max_retries}): "
                        f"{type(e).__name__}. Retrying..."
                    )
                    await asyncio.sleep(0.5 * attempt)  # Exponential backoff
                    last_error = e
                    continue
                else:
                    last_error = e
                    break
            else:
                # Non-connection error, don't retry
                raise
    
    if session is None:
        if last_error:
            logger.error(f"❌ Failed to create database session after {max_retries} attempts: {last_error}")
            raise last_error
        raise RuntimeError("Failed to create database session")

    # Track this session
    session_ref = weakref.ref(session)
    _active_sessions.add(session_ref)

    try:
        yield session
        # ✅ Ensure commit
        try:
            await session.commit()
        except Exception as commit_error:
            # Retry commit on connection errors
            error_str = str(commit_error)
            if any(keyword in error_str for keyword in [
                "ConnectionDoesNotExistError",
                "connection was closed",
                "connection closed",
            ]):
                logger.warning(f"⚠️ Commit failed due to connection error, retrying commit...")
                # Invalidate the connection and try again with a fresh session
                try:
                    conn = await session.connection()
                    conn.invalidate()
                except Exception:
                    pass
                # Retry commit (this will get a new connection from pool)
                await asyncio.sleep(0.1)
                await session.commit()
            else:
                raise
    except Exception as e:
        # ✅ Ensure rollback
        error_str = str(e)
        if any(keyword in error_str for keyword in [
            "ConnectionDoesNotExistError",
            "connection was closed",
            "connection closed",
        ]):
            logger.error(f"⚠️ Database connection error during operation: {type(e).__name__}")
            # Try to invalidate the bad connection
            try:
                conn = await session.connection()
                conn.invalidate()
            except Exception:
                pass
        else:
            logger.error(f"Session error, rolling back: {e}")
        
        try:
            await session.rollback()
        except Exception as rollback_error:
            logger.warning(f"Error during rollback: {rollback_error}")
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


# ✅ FastAPI dependency for session injection with retry logic
# Note: Connection validation is handled by pool_pre_ping=True at the pool level,
# but we add retry logic for connection errors
async def get_session():
    """
    FastAPI dependency that yields a database session with automatic retry on connection errors.

    Usage:
        @router.get("/example")
        async def example(session: AsyncSession = Depends(get_session)):
            # Use session
            pass
    """
    session = None
    last_error = None
    max_retries = 3
    
    # Retry logic for session creation
    for attempt in range(1, max_retries + 1):
        try:
            session = async_session_maker()
            
            # Test connection with a simple query
            try:
                await session.execute(text("SELECT 1"))
            except Exception as conn_test_error:
                try:
                    await session.close()
                except Exception:
                    pass
                session = None
                
                error_str = str(conn_test_error)
                if any(keyword in error_str for keyword in [
                    "ConnectionDoesNotExistError",
                    "connection was closed",
                    "connection closed",
                    "server closed the connection",
                ]):
                    if attempt < max_retries:
                        logger.warning(
                            f"⚠️ Connection test failed (attempt {attempt}/{max_retries}). Retrying..."
                        )
                        await asyncio.sleep(0.5 * attempt)
                        continue
                    else:
                        last_error = conn_test_error
                        break
                else:
                    raise conn_test_error
            
            break
            
        except Exception as e:
            if session:
                try:
                    await session.close()
                except Exception:
                    pass
                session = None
            
            error_str = str(e)
            if any(keyword in error_str for keyword in [
                "ConnectionDoesNotExistError",
                "connection was closed",
                "connection closed",
            ]):
                if attempt < max_retries:
                    logger.warning(
                        f"⚠️ Session creation failed (attempt {attempt}/{max_retries}). Retrying..."
                    )
                    await asyncio.sleep(0.5 * attempt)
                    last_error = e
                    continue
                else:
                    last_error = e
                    break
            else:
                raise
    
    if session is None:
        if last_error:
            logger.error(f"❌ Failed to create database session after {max_retries} attempts: {last_error}")
            raise last_error
        raise RuntimeError("Failed to create database session")

    # Track this session
    session_ref = weakref.ref(session)
    _active_sessions.add(session_ref)

    try:
        yield session
        try:
            await session.commit()
        except Exception as commit_error:
            error_str = str(commit_error)
            if any(keyword in error_str for keyword in [
                "ConnectionDoesNotExistError",
                "connection was closed",
                "connection closed",
            ]):
                logger.warning(f"⚠️ Commit failed due to connection error, retrying...")
                try:
                    conn = await session.connection()
                    conn.invalidate()
                except Exception:
                    pass
                await asyncio.sleep(0.1)
                await session.commit()
            else:
                raise
    except Exception as e:
        error_str = str(e)
        if any(keyword in error_str for keyword in [
            "ConnectionDoesNotExistError",
            "connection was closed",
            "connection closed",
        ]):
            logger.error(f"⚠️ Database connection error during operation: {type(e).__name__}")
            try:
                conn = await session.connection()
                conn.invalidate()
            except Exception:
                pass
        else:
            logger.error(f"Session error, rolling back: {e}")
        
        try:
            await session.rollback()
        except Exception as rollback_error:
            logger.warning(f"Error during rollback: {rollback_error}")
        raise
    finally:
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")
        finally:
            _active_sessions.discard(session_ref)

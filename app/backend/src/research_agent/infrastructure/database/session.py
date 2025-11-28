"""SQLAlchemy async session management."""

import ssl
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from research_agent.config import get_settings
from research_agent.shared.utils.logger import logger

settings = get_settings()


# Debug: Log database configuration
def _mask_password(url: str) -> str:
    """Mask password in database URL for logging."""
    import re
    return re.sub(r':([^:@]+)@', ':****@', url)


logger.info("=" * 60)
logger.info("DATABASE CONFIGURATION DEBUG")
logger.info("=" * 60)
raw_url = os.environ.get('DATABASE_URL', 'NOT SET')
logger.info(f"Raw DATABASE_URL env: {_mask_password(raw_url)}")
logger.info(f"Settings database_url: {_mask_password(settings.database_url)}")
logger.info(f"Settings async_database_url: {_mask_password(settings.async_database_url)}")
logger.info(f"Contains 'supabase': {'supabase' in settings.database_url}")
logger.info(f"Contains 'pooler': {'pooler' in settings.database_url}")

# Check connection mode
if 'pooler' in settings.database_url:
    if ':6543/' in settings.database_url:
        logger.warning("Using Transaction Mode (port 6543) - may have issues with prepared statements!")
        logger.warning("Consider using Session Mode (port 5432) for better SQLAlchemy compatibility")
    elif ':5432/' in settings.database_url:
        logger.info("Using Session Mode (port 5432) - recommended for persistent backends")
logger.info("=" * 60)

# Configure connection args for asyncpg
connect_args: dict = {}

# Check if using a connection pooler (Supavisor/PgBouncer)
is_using_pooler = "pooler" in settings.database_url
is_transaction_mode = ":6543/" in settings.database_url

# Configure SSL for Supabase/cloud PostgreSQL
# asyncpg requires ssl context, not sslmode parameter
if "supabase" in settings.database_url or "neon" in settings.database_url or "pooler" in settings.database_url:
    # Create SSL context for cloud databases
    logger.info("Configuring SSL for cloud database connection")
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context
else:
    logger.info("No SSL configured (local database)")

# For connection poolers (PgBouncer/Supavisor), disable prepared statements
# This must be done at the asyncpg connection level
if is_using_pooler:
    logger.info("Detected connection pooler - disabling prepared statement cache")
    # asyncpg's statement_cache_size controls prepared statement caching
    connect_args["statement_cache_size"] = 0

# Create async engine (use async_database_url to ensure asyncpg driver)
logger.info(f"Creating async engine with URL: {_mask_password(settings.async_database_url)}")
logger.info(f"Connect args: { {k: v for k, v in connect_args.items() if k != 'ssl'} }")

# For pooler connections, we need additional configuration
engine_kwargs: dict = {
    "echo": settings.is_development,
    "connect_args": connect_args,
}

# Disable pool_pre_ping for transaction mode as it can cause prepared statement issues
if is_using_pooler and is_transaction_mode:
    logger.info("Transaction mode detected - using NullPool to avoid connection reuse issues")
    from sqlalchemy.pool import NullPool

    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(
    settings.async_database_url,
    **engine_kwargs,
)

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database connection."""
    try:
        # Test connection
        logger.info("Attempting to connect to database...")
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
            logger.info("Database connection test successful!")
    except Exception as e:
        logger.error(f"Database connection failed: {type(e).__name__}: {e}")
        logger.error("Please check your DATABASE_URL configuration")
        logger.error("For Supabase, use Session Mode (port 5432) instead of Transaction Mode (port 6543)")
        raise


async def close_db() -> None:
    """Close database connection."""
    await engine.dispose()

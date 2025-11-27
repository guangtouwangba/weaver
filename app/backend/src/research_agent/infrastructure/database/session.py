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
logger.info(f"Raw DATABASE_URL env: {_mask_password(os.environ.get('DATABASE_URL', 'NOT SET'))}")
logger.info(f"Settings database_url: {_mask_password(settings.database_url)}")
logger.info(f"Settings async_database_url: {_mask_password(settings.async_database_url)}")
logger.info(f"Contains 'supabase': {'supabase' in settings.database_url}")
logger.info(f"Contains 'pooler': {'pooler' in settings.database_url}")
logger.info("=" * 60)

# Configure SSL for Supabase/cloud PostgreSQL
# asyncpg requires ssl context, not sslmode parameter
connect_args = {}
if "supabase" in settings.database_url or "neon" in settings.database_url or "pooler" in settings.database_url:
    # Create SSL context for cloud databases
    logger.info("Configuring SSL for cloud database connection")
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context
else:
    logger.info("No SSL configured (local database)")

# Create async engine (use async_database_url to ensure asyncpg driver)
logger.info(f"Creating async engine with URL: {_mask_password(settings.async_database_url)}")
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database connection."""
    # Test connection
    async with engine.begin() as conn:
        await conn.run_sync(lambda _: None)


async def close_db() -> None:
    """Close database connection."""
    await engine.dispose()


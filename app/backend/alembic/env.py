"""Alembic environment configuration."""

import asyncio
import ssl
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from research_agent.config import get_settings
from research_agent.infrastructure.database.models import Base

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Get database URL from settings (use async_database_url for proper driver)
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.async_database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # 重要：设置较短的超时，避免在 Transaction Mode 下长时间等待
        transaction_per_migration=True,  # 每个迁移一个事务
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    # Configure connection args for asyncpg
    connect_args = {}

    # Check if using Transaction Mode (port 6543) or connection pooler
    database_url = settings.database_url
    is_using_pooler = "pooler" in database_url
    is_transaction_mode = ":6543/" in database_url

    # Always disable prepared statements for asyncpg to be compatible with
    # pgbouncer, supabase pooler, and other connection poolers
    connect_args["statement_cache_size"] = 0
    connect_args["prepared_statement_cache_size"] = 0
    
    # ✅ Increased timeouts for cloud databases (Zeabur internal DB may have latency)
    connect_args["timeout"] = 60  # Connection timeout: 60 seconds
    connect_args["command_timeout"] = 120  # Command timeout: 2 minutes (for large migrations)

    # Configure SSL for cloud PostgreSQL
    if "supabase" in database_url or "neon" in database_url or "pooler" in database_url:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_context

    # 配置引擎参数
    engine_config = config.get_section(config.config_ini_section, {})

    # ✅ Increased pool timeout for cloud databases
    if is_transaction_mode:
        engine_config["pool_timeout"] = "60"  # 60 秒连接超时（增加以应对网络延迟）
        engine_config["pool_recycle"] = "600"  # 10 分钟回收连接

    # Retry logic for connection failures
    max_retries = 3
    retry_delay = 3  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            connectable = async_engine_from_config(
                engine_config,
                prefix="sqlalchemy.",
                poolclass=pool.NullPool,
                connect_args=connect_args,
            )

            async with connectable.connect() as connection:
                await connection.run_sync(do_run_migrations)

            await connectable.dispose()
            return  # Success, exit retry loop
            
        except (TimeoutError, asyncio.TimeoutError) as e:
            if attempt < max_retries:
                print(f"⚠️  Migration connection timeout (attempt {attempt}/{max_retries}): {e}")
                print(f"   Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"❌ Migration failed after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            # Non-timeout errors should not be retried
            print(f"❌ Migration error: {e}")
            raise


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

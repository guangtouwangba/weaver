"""Factory for creating database client instances."""

from typing import Optional

from research_agent.config import get_settings
from research_agent.infrastructure.database.client.base import DatabaseClient
from research_agent.infrastructure.database.client.postgres_client import (
    PostgresDatabaseClient,
)
from research_agent.infrastructure.database.client.supabase_client import (
    SupabaseDatabaseClient,
)
from research_agent.shared.utils.logger import setup_logger

logger = setup_logger(__name__)

# Singleton instance
_database_client_instance: Optional[DatabaseClient] = None


def get_database_client() -> DatabaseClient:
    """
    Get database client instance based on configuration.

    Defaults to 'postgres' for local development.
    Use 'supabase' for production/cloud deployment.

    Returns:
        DatabaseClient instance

    Raises:
        ValueError: If configuration is invalid or missing
    """
    global _database_client_instance

    if _database_client_instance is not None:
        return _database_client_instance

    settings = get_settings()
    db_type = settings.database_client_type or "postgres"  # Default to postgres

    logger.info(f"Initializing database client: type={db_type}")

    if db_type == "supabase":
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError(
                "Supabase configuration missing (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)"
            )
        _database_client_instance = SupabaseDatabaseClient(
            url=settings.supabase_url, key=settings.supabase_service_role_key
        )
        logger.info("Created Supabase database client")
    elif db_type == "postgres":
        # Use existing DATABASE_URL from settings
        _database_client_instance = PostgresDatabaseClient(database_url=settings.database_url)
        logger.info("Created PostgreSQL database client")
    elif db_type == "sqlalchemy":
        # For backward compatibility - SQLAlchemy wrapper can be added later
        raise NotImplementedError(
            "SQLAlchemy wrapper client not yet implemented. Use 'postgres' or 'supabase' instead."
        )
    else:
        raise ValueError(f"Unknown database_client_type: {db_type}")

    return _database_client_instance


async def reset_database_client() -> None:
    """Reset the singleton database client instance (useful for testing)."""
    global _database_client_instance
    if _database_client_instance:
        # Close existing client if it has a close method
        if hasattr(_database_client_instance, "close"):
            try:
                await _database_client_instance.close()
            except Exception as e:
                logger.warning(f"Error closing database client: {e}")

    _database_client_instance = None









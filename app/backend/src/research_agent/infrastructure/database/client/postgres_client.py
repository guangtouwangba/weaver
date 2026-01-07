"""PostgreSQL direct database client implementation using asyncpg."""

import asyncio
from typing import Dict, List, Optional
from urllib.parse import urlparse

import asyncpg
from asyncpg import Pool

from research_agent.infrastructure.database.client.base import DatabaseClient
from research_agent.shared.utils.logger import setup_logger

logger = setup_logger(__name__)


def parse_database_url(url: str) -> Dict[str, str]:
    """
    Parse database URL into connection parameters.

    Supports formats:
    - postgresql+asyncpg://user:pass@host:port/dbname
    - postgresql://user:pass@host:port/dbname
    - postgres://user:pass@host:port/dbname
    """
    # Remove driver prefix if present
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgres://", "postgresql://")

    parsed = urlparse(url)

    # Extract database name from path (remove leading slash)
    database = parsed.path.lstrip("/") if parsed.path else "postgres"
    # Remove query parameters if present
    if "?" in database:
        database = database.split("?")[0]

    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": database,
    }


class PostgresDatabaseClient(DatabaseClient):
    """PostgreSQL database client using asyncpg."""

    def __init__(self, database_url: str, min_size: int = 2, max_size: int = 10):
        """
        Initialize PostgreSQL client.

        Args:
            database_url: PostgreSQL connection URL
            min_size: Minimum pool size
            max_size: Maximum pool size
        """
        self.database_url = database_url
        self.conn_params = parse_database_url(database_url)
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Optional[Pool] = None

    async def _get_pool(self) -> Pool:
        """Get or create connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.conn_params["host"],
                port=self.conn_params["port"],
                user=self.conn_params["user"],
                password=self.conn_params["password"],
                database=self.conn_params["database"],
                min_size=self.min_size,
                max_size=self.max_size,
            )
            logger.info(
                f"Created PostgreSQL connection pool: "
                f"{self.conn_params['host']}:{self.conn_params['port']}/{self.conn_params['database']}"
            )
        return self._pool

    def _build_where_clause(self, filters: Optional[Dict]) -> tuple[str, List]:
        """Build WHERE clause and parameters from filters."""
        if not filters:
            return "", []

        conditions = []
        values = []
        param_index = 1

        for column, value in filters.items():
            conditions.append(f"{column} = ${param_index}")
            values.append(value)
            param_index += 1

        where_clause = "WHERE " + " AND ".join(conditions)
        return where_clause, values

    async def select(
        self, table: str, filters: Optional[Dict] = None, limit: Optional[int] = None
    ) -> List[Dict]:
        """Select rows from table."""
        pool = await self._get_pool()

        where_clause, values = self._build_where_clause(filters)
        limit_clause = f"LIMIT {limit}" if limit else ""

        query = f"SELECT * FROM {table} {where_clause} {limit_clause}".strip()

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *values)
            return [dict(row) for row in rows]

    async def select_one(self, table: str, filters: Optional[Dict] = None) -> Optional[Dict]:
        """Select a single row from table."""
        results = await self.select(table, filters, limit=1)
        return results[0] if results else None

    async def insert(self, table: str, data: Dict) -> Dict:
        """Insert a row into table."""
        pool = await self._get_pool()

        columns = list(data.keys())
        placeholders = [f"${i + 1}" for i in range(len(columns))]
        values = list(data.values())

        query = f"""
            INSERT INTO {table} ({", ".join(columns)})
            VALUES ({", ".join(placeholders)})
            RETURNING *
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)
            return dict(row) if row else {}

    async def update(self, table: str, filters: Dict, data: Dict) -> Optional[Dict]:
        """Update rows in table."""
        pool = await self._get_pool()

        # Build SET clause
        set_clauses = []
        set_values = []
        param_index = 1

        for column, value in data.items():
            set_clauses.append(f"{column} = ${param_index}")
            set_values.append(value)
            param_index += 1

        # Build WHERE clause
        where_clause, where_values = self._build_where_clause(filters)

        # Combine all values
        all_values = set_values + where_values

        query = f"""
            UPDATE {table}
            SET {", ".join(set_clauses)}
            {where_clause}
            RETURNING *
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *all_values)
            return dict(row) if row else None

    async def upsert(
        self,
        table: str,
        data: Dict,
        conflict_target: Optional[str] = None,
    ) -> Dict:
        """
        Insert or update a row.

        Args:
            table: Table name
            data: Dictionary of column: value pairs
            conflict_target: Column name(s) for conflict resolution (defaults to 'id')
        """
        pool = await self._get_pool()

        if conflict_target is None:
            conflict_target = "id"

        columns = list(data.keys())
        placeholders = [f"${i + 1}" for i in range(len(columns))]
        values = list(data.values())

        # Build UPDATE clause for ON CONFLICT
        update_clauses = [f"{col} = EXCLUDED.{col}" for col in columns if col != conflict_target]

        query = f"""
            INSERT INTO {table} ({", ".join(columns)})
            VALUES ({", ".join(placeholders)})
            ON CONFLICT ({conflict_target}) DO UPDATE
            SET {", ".join(update_clauses) if update_clauses else f"{conflict_target} = EXCLUDED.{conflict_target}"}
            RETURNING *
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)
            return dict(row) if row else {}

    async def delete(self, table: str, filters: Dict) -> bool:
        """Delete rows from table."""
        pool = await self._get_pool()

        where_clause, values = self._build_where_clause(filters)

        query = f"DELETE FROM {table} {where_clause}"

        async with pool.acquire() as conn:
            result = await conn.execute(query, *values)
            # result is a string like "DELETE 1", extract the number
            deleted_count = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
            return deleted_count > 0

    async def close(self) -> None:
        """Close the database client and release resources."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Closed PostgreSQL connection pool")














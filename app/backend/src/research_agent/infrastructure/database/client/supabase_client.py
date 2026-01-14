"""Supabase database client implementation using Supabase Python SDK."""

import asyncio

from supabase import Client, create_client

from research_agent.infrastructure.database.client.base import DatabaseClient
from research_agent.shared.utils.logger import setup_logger

logger = setup_logger(__name__)


class SupabaseDatabaseClient(DatabaseClient):
    """Supabase database client using Supabase Python SDK."""

    def __init__(self, url: str, key: str):
        """
        Initialize Supabase client.

        Args:
            url: Supabase project URL
            key: Supabase service role key or anon key
        """
        self.url = url
        self.key = key
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            self._client = create_client(self.url, self.key)
            logger.info(f"Created Supabase client for {self.url}")
        return self._client

    def _convert_filters_to_supabase_query(self, query, filters: dict | None):
        """Apply filters to Supabase query builder."""
        if not filters:
            return query

        for column, value in filters.items():
            query = query.eq(column, value)

        return query

    async def select(
        self, table: str, filters: dict | None = None, limit: int | None = None
    ) -> list[dict]:
        """Select rows from table."""
        query = self.client.table(table).select("*")

        query = self._convert_filters_to_supabase_query(query, filters)

        if limit:
            query = query.limit(limit)

        # Supabase SDK is synchronous, wrap in thread pool
        def _execute():
            response = query.execute()
            return response.data if response.data else []

        data = await asyncio.to_thread(_execute)
        return data

    async def select_one(self, table: str, filters: dict | None = None) -> dict | None:
        """Select a single row from table."""
        results = await self.select(table, filters, limit=1)
        return results[0] if results else None

    async def insert(self, table: str, data: dict) -> dict:
        """Insert a row into table."""
        query = self.client.table(table).insert(data)

        def _execute():
            response = query.execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return {}

        result = await asyncio.to_thread(_execute)
        return result

    async def update(self, table: str, filters: dict, data: dict) -> dict | None:
        """Update rows in table."""
        query = self.client.table(table).update(data)
        query = self._convert_filters_to_supabase_query(query, filters)

        def _execute():
            response = query.execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        result = await asyncio.to_thread(_execute)
        return result

    async def upsert(
        self,
        table: str,
        data: dict,
        conflict_target: str | None = None,
    ) -> dict:
        """
        Insert or update a row.

        Args:
            table: Table name
            data: Dictionary of column: value pairs
            conflict_target: Column name(s) for conflict resolution
        """
        # Supabase uses upsert() method
        query = self.client.table(table).upsert(data)

        if conflict_target:
            # Note: Supabase upsert uses the primary key by default
            # If conflict_target is specified, we might need to handle it differently
            pass

        def _execute():
            response = query.execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return {}

        result = await asyncio.to_thread(_execute)
        return result

    async def delete(self, table: str, filters: dict) -> bool:
        """Delete rows from table."""
        query = self.client.table(table).delete()
        query = self._convert_filters_to_supabase_query(query, filters)

        def _execute():
            response = query.execute()
            # Supabase returns data array, check if any rows were affected
            return response.data is not None and len(response.data) > 0

        result = await asyncio.to_thread(_execute)
        return result

    async def close(self) -> None:
        """Close the database client and release resources."""
        # Supabase client doesn't require explicit cleanup
        # But we can clear the reference
        self._client = None
        logger.info("Closed Supabase client")















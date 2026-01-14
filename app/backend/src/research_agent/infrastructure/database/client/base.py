"""Database client abstract interface."""

from abc import ABC, abstractmethod


class DatabaseClient(ABC):
    """Abstract database client interface."""

    @abstractmethod
    async def select(
        self, table: str, filters: dict | None = None, limit: int | None = None
    ) -> list[dict]:
        """
        Select rows from table.

        Args:
            table: Table name
            filters: Optional dictionary of column: value filters
            limit: Optional limit on number of rows to return

        Returns:
            List of row dictionaries
        """
        pass

    @abstractmethod
    async def select_one(self, table: str, filters: dict | None = None) -> dict | None:
        """
        Select a single row from table.

        Args:
            table: Table name
            filters: Optional dictionary of column: value filters

        Returns:
            Single row dictionary or None if not found
        """
        pass

    @abstractmethod
    async def insert(self, table: str, data: dict) -> dict:
        """
        Insert a row into table.

        Args:
            table: Table name
            data: Dictionary of column: value pairs

        Returns:
            Inserted row dictionary
        """
        pass

    @abstractmethod
    async def update(self, table: str, filters: dict, data: dict) -> dict | None:
        """
        Update rows in table.

        Args:
            table: Table name
            filters: Dictionary of column: value filters to identify rows
            data: Dictionary of column: value pairs to update

        Returns:
            Updated row dictionary (if single row updated) or None
        """
        pass

    @abstractmethod
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
            conflict_target: Optional column name(s) for conflict resolution

        Returns:
            Upserted row dictionary
        """
        pass

    @abstractmethod
    async def delete(self, table: str, filters: dict) -> bool:
        """
        Delete rows from table.

        Args:
            table: Table name
            filters: Dictionary of column: value filters to identify rows

        Returns:
            True if rows were deleted, False otherwise
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the database client and release resources."""
        pass















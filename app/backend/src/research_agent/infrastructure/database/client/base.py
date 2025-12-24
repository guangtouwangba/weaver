"""Database client abstract interface."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class DatabaseClient(ABC):
    """Abstract database client interface."""

    @abstractmethod
    async def select(
        self, table: str, filters: Optional[Dict] = None, limit: Optional[int] = None
    ) -> List[Dict]:
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
    async def select_one(self, table: str, filters: Optional[Dict] = None) -> Optional[Dict]:
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
    async def insert(self, table: str, data: Dict) -> Dict:
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
    async def update(self, table: str, filters: Dict, data: Dict) -> Optional[Dict]:
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
        data: Dict,
        conflict_target: Optional[str] = None,
    ) -> Dict:
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
    async def delete(self, table: str, filters: Dict) -> bool:
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








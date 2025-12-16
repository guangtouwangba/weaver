"""Project repository implementation using DatabaseClient interface."""

from typing import List, Optional
from uuid import UUID

from research_agent.domain.entities.project import Project
from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.infrastructure.database.client.base import DatabaseClient


class DatabaseClientProjectRepository(ProjectRepository):
    """Project repository using DatabaseClient interface (works with Postgres or Supabase)."""

    def __init__(self, client: DatabaseClient):
        """
        Initialize repository with database client.

        Args:
            client: DatabaseClient instance (PostgresDatabaseClient or SupabaseDatabaseClient)
        """
        self._client = client

    async def save(self, project: Project) -> Project:
        """Save a project."""
        # Check if exists
        existing = await self._client.select_one("projects", {"id": str(project.id)})

        # Convert datetime to ISO format for compatibility with both asyncpg and Supabase
        # asyncpg can handle datetime objects, but ISO strings work universally
        def to_iso(dt):
            if dt is None:
                return None
            return dt.isoformat() if hasattr(dt, "isoformat") else dt

        if existing:
            # Update existing
            data = {
                "name": project.name,
                "description": project.description,
                "updated_at": to_iso(project.updated_at),
            }
            await self._client.update("projects", {"id": str(project.id)}, data)
        else:
            # Create new
            data = {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "created_at": to_iso(project.created_at),
                "updated_at": to_iso(project.updated_at),
            }
            await self._client.insert("projects", data)

        return project

    async def find_by_id(self, project_id: UUID) -> Optional[Project]:
        """Find project by ID."""
        row = await self._client.select_one("projects", {"id": str(project_id)})
        return self._to_entity(row) if row else None

    async def find_all(self) -> List[Project]:
        """Find all projects."""
        rows = await self._client.select("projects")
        # Sort by updated_at descending (most recent first)
        rows.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return [self._to_entity(row) for row in rows]

    async def delete(self, project_id: UUID) -> bool:
        """Delete a project."""
        return await self._client.delete("projects", {"id": str(project_id)})

    def _to_entity(self, row: dict) -> Project:
        """Convert database row to entity."""
        from datetime import datetime

        # Handle UUID conversion
        project_id = UUID(row["id"]) if isinstance(row["id"], str) else row["id"]

        # Handle datetime conversion
        # asyncpg returns datetime objects directly, Supabase returns ISO strings
        def parse_datetime(value):
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                # Handle ISO format with or without timezone
                if value.endswith("Z"):
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                elif "+" in value or value.count("-") > 2:  # Has timezone
                    return datetime.fromisoformat(value)
                else:
                    # No timezone, assume UTC
                    return datetime.fromisoformat(value + "+00:00")
            return value

        created_at = parse_datetime(row["created_at"])
        updated_at = parse_datetime(row["updated_at"])

        return Project(
            id=project_id,
            name=row["name"],
            description=row.get("description"),
            created_at=created_at,
            updated_at=updated_at,
        )

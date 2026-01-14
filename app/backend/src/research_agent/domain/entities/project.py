"""Project domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Project:
    """Project entity - represents a research project."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str | None = None
    user_id: str | None = None  # Owner user ID for multi-tenant isolation
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update(self, name: str | None = None, description: str | None = None) -> None:
        """Update project fields."""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        self.updated_at = datetime.utcnow()

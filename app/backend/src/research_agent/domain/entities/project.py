"""Project domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Project:
    """Project entity - represents a research project."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update(self, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """Update project fields."""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        self.updated_at = datetime.utcnow()


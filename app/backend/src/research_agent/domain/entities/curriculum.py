"""Curriculum domain entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID


@dataclass
class CurriculumStep:
    """A single step in a learning curriculum."""
    
    id: str
    title: str
    source: str
    source_type: str  # 'document' | 'video'
    page_range: Optional[str] = None
    duration: int = 10  # in minutes


@dataclass
class Curriculum:
    """Learning curriculum for a project."""
    
    id: UUID
    project_id: UUID
    steps: List[CurriculumStep]
    total_duration: int
    created_at: datetime
    updated_at: datetime


"""Save curriculum use case."""

from dataclasses import dataclass
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from research_agent.domain.entities.curriculum import Curriculum, CurriculumStep
from research_agent.domain.repositories.curriculum_repo import CurriculumRepository
from research_agent.shared.utils.logger import logger


@dataclass
class SaveCurriculumInput:
    """Input for save curriculum use case."""
    
    project_id: UUID
    steps: List[CurriculumStep]


@dataclass
class SaveCurriculumOutput:
    """Output for save curriculum use case."""
    
    curriculum: Curriculum


class SaveCurriculumUseCase:
    """Use case for saving a curriculum to the database."""

    def __init__(self, curriculum_repo: CurriculumRepository):
        self._curriculum_repo = curriculum_repo

    async def execute(self, input_data: SaveCurriculumInput) -> SaveCurriculumOutput:
        """Save curriculum for a project."""
        logger.info(f"Saving curriculum for project {input_data.project_id}")
        
        # Calculate total duration
        total_duration = sum(step.duration for step in input_data.steps)
        
        # Create or update curriculum entity
        curriculum = Curriculum(
            id=uuid4(),  # Will be updated if exists
            project_id=input_data.project_id,
            steps=input_data.steps,
            total_duration=total_duration,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Save to repository
        saved = await self._curriculum_repo.save(curriculum)
        
        logger.info(f"Saved curriculum {saved.id} with {len(saved.steps)} steps")
        
        return SaveCurriculumOutput(curriculum=saved)


"""Get curriculum use case."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from research_agent.domain.entities.curriculum import Curriculum
from research_agent.domain.repositories.curriculum_repo import CurriculumRepository
from research_agent.shared.exceptions import NotFoundError
from research_agent.shared.utils.logger import logger


@dataclass
class GetCurriculumInput:
    """Input for get curriculum use case."""
    
    project_id: UUID


@dataclass
class GetCurriculumOutput:
    """Output for get curriculum use case."""
    
    curriculum: Curriculum


class GetCurriculumUseCase:
    """Use case for retrieving a curriculum from the database."""

    def __init__(self, curriculum_repo: CurriculumRepository):
        self._curriculum_repo = curriculum_repo

    async def execute(self, input_data: GetCurriculumInput) -> GetCurriculumOutput:
        """Get curriculum for a project."""
        logger.info(f"Fetching curriculum for project {input_data.project_id}")
        
        curriculum = await self._curriculum_repo.find_by_project(input_data.project_id)
        
        if not curriculum:
            raise NotFoundError(f"Curriculum not found for project {input_data.project_id}")
        
        logger.info(f"Found curriculum {curriculum.id} with {len(curriculum.steps)} steps")
        
        return GetCurriculumOutput(curriculum=curriculum)


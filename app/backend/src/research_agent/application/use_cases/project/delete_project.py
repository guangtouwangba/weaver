"""Delete project use case."""

import logging
from dataclasses import dataclass
from uuid import UUID

from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.infrastructure.storage.base import StorageService
from research_agent.shared.exceptions import NotFoundError

logger = logging.getLogger(__name__)


@dataclass
class DeleteProjectInput:
    """Input for delete project use case."""

    project_id: UUID


@dataclass
class DeleteProjectOutput:
    """Output for delete project use case."""

    success: bool


class DeleteProjectUseCase:
    """Use case for deleting a project."""

    def __init__(
        self,
        project_repo: ProjectRepository,
        storage_service: StorageService | None = None,
        supabase_storage_service: object | None = None,
    ):
        self._project_repo = project_repo
        self._storage_service = storage_service
        self._supabase_storage_service = supabase_storage_service

    async def execute(self, input: DeleteProjectInput) -> DeleteProjectOutput:
        """Execute the use case."""
        # Check if project exists
        project = await self._project_repo.find_by_id(input.project_id)
        if not project:
            raise NotFoundError("Project", str(input.project_id))

        # Delete project from database (cascade will handle related data)
        deleted = await self._project_repo.delete(input.project_id)

        if deleted:
            # Delete project files from local storage
            if self._storage_service:
                try:
                    project_path = f"projects/{input.project_id}"
                    await self._storage_service.delete_directory(project_path)
                    logger.info(f"Deleted local files for project {input.project_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete local files for project {input.project_id}: {e}")

            # Delete project files from Supabase storage
            if self._supabase_storage_service:
                try:
                    project_path = f"projects/{input.project_id}"
                    await self._supabase_storage_service.delete_directory(project_path)
                    logger.info(f"Deleted Supabase storage files for project {input.project_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete Supabase storage files for project {input.project_id}: {e}")

        return DeleteProjectOutput(success=deleted)


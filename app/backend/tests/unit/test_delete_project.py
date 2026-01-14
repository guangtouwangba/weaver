"""Unit tests for delete project use case."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from research_agent.application.use_cases.project.delete_project import (
    DeleteProjectInput,
    DeleteProjectUseCase,
)
from research_agent.domain.entities.project import Project
from research_agent.shared.exceptions import NotFoundError


@pytest.fixture
def mock_project_repo():
    """Create a mock project repository."""
    return MagicMock()


@pytest.fixture
def mock_storage_service():
    """Create a mock storage service."""
    return AsyncMock()


@pytest.fixture
def mock_supabase_storage():
    """Create a mock Supabase storage service."""
    return AsyncMock()


@pytest.fixture
def sample_project():
    """Create a sample project."""
    return Project(
        id=uuid4(),
        name="Test Project",
        description="A test project",
    )


@pytest.mark.asyncio
async def test_delete_project_success(
    mock_project_repo,
    mock_storage_service,
    mock_supabase_storage,
    sample_project,
):
    """Test successful project deletion."""
    # Setup
    mock_project_repo.find_by_id = AsyncMock(return_value=sample_project)
    mock_project_repo.delete = AsyncMock(return_value=True)
    mock_storage_service.delete_directory = AsyncMock(return_value=True)
    mock_supabase_storage.delete_directory = AsyncMock(return_value=True)

    use_case = DeleteProjectUseCase(
        mock_project_repo,
        storage_service=mock_storage_service,
        supabase_storage_service=mock_supabase_storage,
    )

    # Execute
    input_data = DeleteProjectInput(project_id=sample_project.id)
    result = await use_case.execute(input_data)

    # Assert
    assert result.success is True
    mock_project_repo.find_by_id.assert_called_once_with(sample_project.id)
    mock_project_repo.delete.assert_called_once_with(sample_project.id)
    mock_storage_service.delete_directory.assert_called_once_with(
        f"projects/{sample_project.id}"
    )
    mock_supabase_storage.delete_directory.assert_called_once_with(
        f"projects/{sample_project.id}"
    )


@pytest.mark.asyncio
async def test_delete_project_not_found(mock_project_repo):
    """Test deletion of non-existent project."""
    # Setup
    project_id = uuid4()
    mock_project_repo.find_by_id = AsyncMock(return_value=None)

    use_case = DeleteProjectUseCase(mock_project_repo)

    # Execute and Assert
    input_data = DeleteProjectInput(project_id=project_id)
    with pytest.raises(NotFoundError) as exc_info:
        await use_case.execute(input_data)

    assert "Project" in str(exc_info.value)
    assert str(project_id) in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_project_without_storage_services(
    mock_project_repo,
    sample_project,
):
    """Test deletion without storage services (database only)."""
    # Setup
    mock_project_repo.find_by_id = AsyncMock(return_value=sample_project)
    mock_project_repo.delete = AsyncMock(return_value=True)

    use_case = DeleteProjectUseCase(mock_project_repo)

    # Execute
    input_data = DeleteProjectInput(project_id=sample_project.id)
    result = await use_case.execute(input_data)

    # Assert
    assert result.success is True
    mock_project_repo.delete.assert_called_once_with(sample_project.id)


@pytest.mark.asyncio
async def test_delete_project_storage_failure(
    mock_project_repo,
    mock_storage_service,
    sample_project,
):
    """Test that project deletion continues even if storage deletion fails."""
    # Setup
    mock_project_repo.find_by_id = AsyncMock(return_value=sample_project)
    mock_project_repo.delete = AsyncMock(return_value=True)
    mock_storage_service.delete_directory = AsyncMock(
        side_effect=Exception("Storage error")
    )

    use_case = DeleteProjectUseCase(
        mock_project_repo,
        storage_service=mock_storage_service,
    )

    # Execute - should not raise exception
    input_data = DeleteProjectInput(project_id=sample_project.id)
    result = await use_case.execute(input_data)

    # Assert - deletion should still succeed
    assert result.success is True
    mock_project_repo.delete.assert_called_once_with(sample_project.id)


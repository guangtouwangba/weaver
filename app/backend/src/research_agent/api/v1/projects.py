"""Projects API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db
from research_agent.application.dto.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
)
from research_agent.application.use_cases.project.create_project import (
    CreateProjectInput,
    CreateProjectUseCase,
)
from research_agent.application.use_cases.project.delete_project import (
    DeleteProjectInput,
    DeleteProjectUseCase,
)
from research_agent.application.use_cases.project.get_project import (
    GetProjectInput,
    GetProjectUseCase,
)
from research_agent.application.use_cases.project.list_projects import ListProjectsUseCase
from research_agent.infrastructure.database.repositories.sqlalchemy_project_repo import (
    SQLAlchemyProjectRepository,
)
from research_agent.shared.exceptions import NotFoundError

router = APIRouter()


def get_project_repo(session: AsyncSession = Depends(get_db)) -> SQLAlchemyProjectRepository:
    """Get project repository."""
    return SQLAlchemyProjectRepository(session)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    repo: SQLAlchemyProjectRepository = Depends(get_project_repo),
) -> ProjectListResponse:
    """List all projects."""
    use_case = ListProjectsUseCase(repo)
    result = await use_case.execute()

    return ProjectListResponse(
        items=[
            ProjectResponse(
                id=item.id,
                name=item.name,
                description=item.description,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in result.items
        ],
        total=result.total,
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    repo: SQLAlchemyProjectRepository = Depends(get_project_repo),
) -> ProjectResponse:
    """Create a new project."""
    use_case = CreateProjectUseCase(repo)
    result = await use_case.execute(
        CreateProjectInput(
            name=data.name,
            description=data.description,
        )
    )

    # Fetch the full project to get timestamps
    get_use_case = GetProjectUseCase(repo)
    project = await get_use_case.execute(GetProjectInput(project_id=result.id))

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    repo: SQLAlchemyProjectRepository = Depends(get_project_repo),
) -> ProjectResponse:
    """Get a project by ID."""
    use_case = GetProjectUseCase(repo)

    try:
        result = await use_case.execute(GetProjectInput(project_id=project_id))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

    return ProjectResponse(
        id=result.id,
        name=result.name,
        description=result.description,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    repo: SQLAlchemyProjectRepository = Depends(get_project_repo),
) -> None:
    """Delete a project."""
    use_case = DeleteProjectUseCase(repo)

    try:
        await use_case.execute(DeleteProjectInput(project_id=project_id))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

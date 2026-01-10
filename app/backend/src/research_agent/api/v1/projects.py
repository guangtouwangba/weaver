"""Projects API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.auth.supabase import UserContext, get_current_user, get_optional_user
from research_agent.api.deps import get_db
from research_agent.application.dto.auth import MigrateDataRequest
from research_agent.application.dto.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
)
from research_agent.config import get_settings
from research_agent.domain.entities.project import Project
from research_agent.infrastructure.database.repositories.sqlalchemy_project_repo import (
    SQLAlchemyProjectRepository,
)
from research_agent.infrastructure.storage.local import LocalStorageService
from research_agent.infrastructure.storage.supabase_storage import SupabaseStorageService

router = APIRouter()
settings = get_settings()


def get_project_repo(session: AsyncSession = Depends(get_db)) -> SQLAlchemyProjectRepository:
    """Get project repository."""
    return SQLAlchemyProjectRepository(session)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    repo: SQLAlchemyProjectRepository = Depends(get_project_repo),
    user: UserContext = Depends(get_optional_user),
) -> ProjectListResponse:
    """List all projects for the current user."""
    # Filter by user_id (authenticated or anonymous)
    projects = await repo.find_all(user_id=user.user_id)

    return ProjectListResponse(
        items=[
            ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
            for project in projects
        ],
        total=len(projects),
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    repo: SQLAlchemyProjectRepository = Depends(get_project_repo),
    user: UserContext = Depends(get_optional_user),
) -> ProjectResponse:
    """Create a new project owned by the current user."""
    # Create project entity with user ownership
    project = Project(
        name=data.name,
        description=data.description,
        user_id=user.user_id,
    )

    # Save to repository
    saved_project = await repo.save(project)

    return ProjectResponse(
        id=saved_project.id,
        name=saved_project.name,
        description=saved_project.description,
        created_at=saved_project.created_at,
        updated_at=saved_project.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    repo: SQLAlchemyProjectRepository = Depends(get_project_repo),
    user: UserContext = Depends(get_optional_user),
) -> ProjectResponse:
    """Get a project by ID (must be owned by current user)."""
    project = await repo.find_by_id(project_id, user_id=user.user_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    repo: SQLAlchemyProjectRepository = Depends(get_project_repo),
    user: UserContext = Depends(get_optional_user),
) -> None:
    """Delete a project and all associated files (must be owned by current user)."""
    # Verify ownership first
    project = await repo.find_by_id(project_id, user_id=user.user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create storage services
    local_storage = LocalStorageService(settings.upload_dir)

    supabase_storage = None
    if settings.supabase_url and settings.supabase_service_role_key:
        supabase_storage = SupabaseStorageService(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
            bucket_name=settings.storage_bucket,
        )

    try:
        # Delete project files from storage
        if supabase_storage:
            try:
                await supabase_storage.delete_project_files(
                    user_id=user.user_id, project_id=str(project_id)
                )
            except Exception:
                pass  # Non-critical if file cleanup fails

        # Delete project from database
        deleted = await repo.delete(project_id, user_id=user.user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Project not found")

    finally:
        # Close Supabase storage client if created
        if supabase_storage:
            await supabase_storage.close()


@router.post("/migrate", status_code=204)
async def migrate_projects(
    data: MigrateDataRequest,
    repo: SQLAlchemyProjectRepository = Depends(get_project_repo),
    user: UserContext = Depends(get_current_user),
) -> None:
    """Migrate projects from anonymous session to authenticated user."""
    # Construct the anonymous user ID from the session ID
    anon_user_id = f"anon-{data.anonymous_session_id}"

    # Perform migration
    migrated_count = await repo.migrate_user_data(anon_user_id, user)

    # We could log this or return the count if needed
    print(f"Migrated {migrated_count} projects from {anon_user_id} to {user}")

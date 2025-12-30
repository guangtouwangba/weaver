from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db
from research_agent.application.dto.tag import TagCreate, TagListResponse, TagResponse
from research_agent.infrastructure.database.models import TagModel
from research_agent.infrastructure.database.repositories.sqlalchemy_tag_repo import (
    SQLAlchemyTagRepository,
)

router = APIRouter()


def get_repo(session: AsyncSession = Depends(get_db)) -> SQLAlchemyTagRepository:
    return SQLAlchemyTagRepository(session)


@router.get("", response_model=TagListResponse)
async def list_tags(
    repo: SQLAlchemyTagRepository = Depends(get_repo),
):
    """List all tags."""
    items = await repo.list_all()
    return TagListResponse(items=items)


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(
    data: TagCreate,
    repo: SQLAlchemyTagRepository = Depends(get_repo),
):
    """Create a new tag."""
    # Check if exists
    existing = await repo.get_by_name(data.name)
    if existing:
        return existing

    tag = TagModel(name=data.name, color=data.color)
    created = await repo.create(tag)
    return created


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: UUID,
    repo: SQLAlchemyTagRepository = Depends(get_repo),
):
    """Delete a tag."""
    await repo.delete(tag_id)

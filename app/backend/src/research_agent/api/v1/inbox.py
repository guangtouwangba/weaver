from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.auth import get_api_key
from research_agent.api.deps import get_db
from research_agent.application.dto.inbox import (
    InboxItemCreate,
    InboxItemListResponse,
    InboxItemResponse,
    InboxItemUpdate,
)
from research_agent.infrastructure.database.models import InboxItemModel, ProjectModel, TagModel
from research_agent.infrastructure.database.repositories.sqlalchemy_inbox_repo import (
    SQLAlchemyInboxRepository,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_tag_repo import (
    SQLAlchemyTagRepository,
)

router = APIRouter()


def get_repo(session: AsyncSession = Depends(get_db)) -> SQLAlchemyInboxRepository:
    return SQLAlchemyInboxRepository(session)


@router.get("/items", response_model=InboxItemListResponse)
async def list_inbox_items(
    skip: int = 0,
    limit: int = 50,
    is_processed: Optional[bool] = None,
    type: Optional[str] = None,
    tag_id: Optional[UUID] = None,
    q: Optional[str] = None,
    repo: SQLAlchemyInboxRepository = Depends(get_repo),
):
    """List inbox items with filtering."""
    items = await repo.list_items(
        skip=skip,
        limit=limit,
        is_processed=is_processed,
        item_type=type,
        tag_id=tag_id,
        search_query=q,
    )
    # Total count would require a separate query, for now just returning list length
    # In a real app we'd implementing count() in repo
    return InboxItemListResponse(items=items, total=len(items))


@router.get("/items/{item_id}", response_model=InboxItemResponse)
async def get_inbox_item(
    item_id: UUID,
    repo: SQLAlchemyInboxRepository = Depends(get_repo),
):
    """Get a single inbox item."""
    item = await repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/items/{item_id}", status_code=204)
async def delete_inbox_item(
    item_id: UUID,
    repo: SQLAlchemyInboxRepository = Depends(get_repo),
):
    """Delete an inbox item."""
    await repo.delete(item_id)


@router.post("/items/{item_id}/assign/{project_id}", status_code=204)
async def assign_item_to_project(
    item_id: UUID,
    project_id: UUID,
    repo: SQLAlchemyInboxRepository = Depends(get_repo),
    session: AsyncSession = Depends(get_db),
):
    """
    Assign an item to a project.
    This effectively "processes" the item and might trigger ingestion.
    For now, we just mark it as processed and maybe move content.
    """
    item = await repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # In a full implementation, this would:
    # 1. Create a DocumentModel in the project from this item
    # 2. Trigger processing pipeline
    # 3. Mark inbox item as processed or delete it

    # Simple flow: Mark processed
    item.is_processed = True
    # item.project_id = project_id # If we had a direct link, or we define it now

    # We can also create a new DocumentModel here
    # from research_agent.infrastructure.database.models import DocumentModel
    # doc = DocumentModel(project_id=project_id, title=item.title, ...)
    # session.add(doc)

    await repo.update(item)
    await session.commit()


# =============================================================================
# Collection Endpoints (External Access)
# =============================================================================


@router.post("/collect", response_model=InboxItemResponse, status_code=201)
async def collect_item(
    payload: InboxItemCreate,
    api_key=Depends(get_api_key),  # Require API Key
    repo: SQLAlchemyInboxRepository = Depends(get_repo),
    session: AsyncSession = Depends(get_db),
):
    """Collect a new item via external API (e.g. Chrome Extension)."""
    # Create tags if needed
    tag_models = []
    if payload.tag_ids:
        tag_repo = SQLAlchemyTagRepository(session)
        for tag_id in payload.tag_ids:
            tag = await tag_repo.get_by_id(tag_id)
            if tag:
                tag_models.append(tag)

    item = InboxItemModel(
        title=payload.title,
        type=payload.type,
        source_url=payload.source_url,
        content=payload.content,
        thumbnail_url=payload.thumbnail_url,
        source_type=payload.source_type,
        meta_data=payload.meta_data,
        is_read=payload.is_read,
        is_processed=payload.is_processed,
        tags=tag_models,
    )

    created_item = await repo.create(item)
    return created_item


@router.post("/collect/batch", response_model=List[InboxItemResponse], status_code=201)
async def batch_collect_items(
    payloads: List[InboxItemCreate],
    api_key=Depends(get_api_key),
    repo: SQLAlchemyInboxRepository = Depends(get_repo),
    session: AsyncSession = Depends(get_db),
):
    """Batch collect items."""
    created_items = []
    tag_repo = SQLAlchemyTagRepository(session)

    for p in payloads:
        tag_models = []
        if p.tag_ids:
            for tag_id in p.tag_ids:
                tag = await tag_repo.get_by_id(tag_id)
                if tag:
                    tag_models.append(tag)

        item = InboxItemModel(
            title=p.title,
            type=p.type,
            source_url=p.source_url,
            content=p.content,
            thumbnail_url=p.thumbnail_url,
            source_type=p.source_type,
            meta_data=p.meta_data,
            is_read=p.is_read,
            is_processed=p.is_processed,
            tags=tag_models,
        )
        created = await repo.create(item)
        created_items.append(created)

    return created_items

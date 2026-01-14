from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from research_agent.application.dto.tag import TagResponse


class InboxItemBase(BaseModel):
    title: str | None = None
    type: str  # link, pdf, note, video, article
    source_url: str | None = None
    content: str | None = None
    thumbnail_url: str | None = None
    source_type: str  # extension, manual, upload
    meta_data: dict[str, Any] = {}
    is_read: bool = False
    is_processed: bool = False


class InboxItemCreate(InboxItemBase):
    tag_ids: list[UUID] = []


class InboxItemUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    is_read: bool | None = None
    is_processed: bool | None = None
    tag_ids: list[UUID] | None = None


class InboxItemResponse(InboxItemBase):
    id: UUID
    collected_at: datetime
    tags: list[TagResponse] = []

    class Config:
        from_attributes = True


class InboxItemListResponse(BaseModel):
    items: list[InboxItemResponse]
    total: int

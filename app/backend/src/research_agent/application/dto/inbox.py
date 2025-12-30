from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl

from research_agent.application.dto.tag import TagResponse


class InboxItemBase(BaseModel):
    title: Optional[str] = None
    type: str  # link, pdf, note, video, article
    source_url: Optional[str] = None
    content: Optional[str] = None
    thumbnail_url: Optional[str] = None
    source_type: str  # extension, manual, upload
    meta_data: Dict[str, Any] = {}
    is_read: bool = False
    is_processed: bool = False


class InboxItemCreate(InboxItemBase):
    tag_ids: List[UUID] = []


class InboxItemUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_read: Optional[bool] = None
    is_processed: Optional[bool] = None
    tag_ids: Optional[List[UUID]] = None


class InboxItemResponse(InboxItemBase):
    id: UUID
    collected_at: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True


class InboxItemListResponse(BaseModel):
    items: List[InboxItemResponse]
    total: int

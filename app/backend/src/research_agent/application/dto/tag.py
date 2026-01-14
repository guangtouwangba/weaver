from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TagBase(BaseModel):
    name: str
    color: str = "blue"


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TagListResponse(BaseModel):
    items: list[TagResponse]

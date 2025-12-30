from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApiKeyGeneratedResponse(ApiKeyResponse):
    full_key: str  # Only returned once upon creation


class ApiKeyListResponse(BaseModel):
    items: List[ApiKeyResponse]

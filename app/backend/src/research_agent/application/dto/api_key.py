from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None

    class Config:
        from_attributes = True


class ApiKeyGeneratedResponse(ApiKeyResponse):
    full_key: str  # Only returned once upon creation


class ApiKeyListResponse(BaseModel):
    items: list[ApiKeyResponse]

import hashlib
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db
from research_agent.application.dto.api_key import (
    ApiKeyCreate,
    ApiKeyGeneratedResponse,
    ApiKeyListResponse,
)
from research_agent.infrastructure.database.models import ApiKeyModel
from research_agent.infrastructure.database.repositories.sqlalchemy_api_key_repo import (
    SQLAlchemyApiKeyRepository,
)

router = APIRouter()


def get_repo(session: AsyncSession = Depends(get_db)) -> SQLAlchemyApiKeyRepository:
    return SQLAlchemyApiKeyRepository(session)


@router.get("", response_model=ApiKeyListResponse)
async def list_api_keys(
    # In a real app, strict user auth here
    user_id: str = "default_user",
    repo: SQLAlchemyApiKeyRepository = Depends(get_repo),
):
    """List API keys."""
    items = await repo.list_by_user(user_id)
    return ApiKeyListResponse(items=items)


@router.post("", response_model=ApiKeyGeneratedResponse, status_code=201)
async def generate_api_key(
    data: ApiKeyCreate,
    user_id: str = "default_user",
    repo: SQLAlchemyApiKeyRepository = Depends(get_repo),
):
    """Generate a new API key."""
    # Generate random key: sk_xxxx...
    prefix = "sk"
    entropy = secrets.token_urlsafe(32)
    full_key = f"{prefix}_{entropy}"

    # Hash it
    hashed = hashlib.sha256(full_key.encode()).hexdigest()

    model = ApiKeyModel(name=data.name, key_prefix=prefix, key_hash=hashed, user_id=user_id)

    created = await repo.create(model)

    return ApiKeyGeneratedResponse(
        id=created.id,
        name=created.name,
        key_prefix=created.key_prefix,
        created_at=created.created_at,
        full_key=full_key,  # Valid only now
    )


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: UUID,
    repo: SQLAlchemyApiKeyRepository = Depends(get_repo),
):
    """Revoke an API key."""
    await repo.revoke(key_id)

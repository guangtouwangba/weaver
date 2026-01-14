"""API Key authentication dependency for external API access."""

import hashlib

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db
from research_agent.infrastructure.database.repositories.sqlalchemy_api_key_repo import (
    SQLAlchemyApiKeyRepository,
)


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(key.encode()).hexdigest()


async def get_api_key(
    x_api_key: str = Header(..., description="API key for authentication"),
    session: AsyncSession = Depends(get_db),
):
    """
    FastAPI dependency to validate API key from X-API-Key header.
    Returns the ApiKeyModel if valid, raises HTTPException otherwise.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    # Hash the provided key
    key_hash = hash_api_key(x_api_key)

    # Look up in database
    repo = SQLAlchemyApiKeyRepository(session)
    api_key_model = await repo.get_by_hash(key_hash)

    if not api_key_model:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if api_key_model.revoked_at:
        raise HTTPException(status_code=401, detail="API key has been revoked")

    # Update last_used_at
    await repo.update_last_used(api_key_model.id)
    await session.commit()

    return api_key_model

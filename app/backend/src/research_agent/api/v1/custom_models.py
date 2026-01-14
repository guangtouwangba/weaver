"""
Custom Models API Endpoints.

CRUD operations for user-defined custom models.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.auth.supabase import get_current_user
from research_agent.domain.repositories.custom_model_repo import CustomModelDTO
from research_agent.domain.services.custom_model_service import CustomModelService
from research_agent.infrastructure.database.repositories.sqlalchemy_custom_model_repo import (
    SQLAlchemyCustomModelRepository,
)
from research_agent.infrastructure.database.session import get_session

router = APIRouter(prefix="/settings/custom-models", tags=["custom-models"])


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------


class CustomModelCreate(BaseModel):
    """Request model for creating a custom model."""

    model_id: str = Field(..., description="Model identifier string (e.g. provider/model-name)")
    label: str = Field(..., description="Display label")
    description: Optional[str] = Field(None, description="Optional description")
    provider: str = Field("openrouter", description="Model provider")
    context_window: Optional[int] = Field(None, description="Context window size in tokens")


class CustomModelUpdate(BaseModel):
    """Request model for updating a custom model."""

    label: Optional[str] = Field(None, description="Display label")
    description: Optional[str] = Field(None, description="Optional description")
    is_active: Optional[bool] = Field(None, description="Whether the model is active")
    context_window: Optional[int] = Field(None, description="Context window size in tokens")


# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------


async def get_custom_model_service(
    session: AsyncSession = Depends(get_session),
) -> CustomModelService:
    """Get custom model service with repository."""
    repo = SQLAlchemyCustomModelRepository(session)
    return CustomModelService(repo)


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------


@router.get("", response_model=List[CustomModelDTO])
async def get_custom_models(
    user_id: str = Depends(get_current_user),
    service: CustomModelService = Depends(get_custom_model_service),
):
    """Get all custom models for the current user."""
    return await service.get_user_custom_models(user_id)


@router.post("", response_model=CustomModelDTO, status_code=status.HTTP_201_CREATED)
async def create_custom_model(
    model: CustomModelCreate,
    user_id: str = Depends(get_current_user),
    service: CustomModelService = Depends(get_custom_model_service),
):
    """Create a new custom model."""
    try:
        return await service.create_custom_model(
            user_id=user_id,
            model_id=model.model_id,
            label=model.label,
            description=model.description,
            provider=model.provider,
            context_window=model.context_window,
        )
    except Exception as e:
        # TODO: Handle unique constraint violation gracefully
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create custom model: {str(e)}",
        )


@router.put("/{model_id}", response_model=CustomModelDTO)
async def update_custom_model(
    model_id: UUID,
    update: CustomModelUpdate,
    user_id: str = Depends(get_current_user),
    service: CustomModelService = Depends(get_custom_model_service),
):
    """Update a custom model."""
    # Verify ownership first
    existing = await service.get_custom_model(model_id)
    if not existing or existing.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom model not found")

    updated = await service.update_custom_model(
        id=model_id,
        label=update.label,
        description=update.description,
        is_active=update.is_active,
        context_window=update.context_window,
    )

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom model not found")

    return updated


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_model(
    model_id: UUID,
    user_id: str = Depends(get_current_user),
    service: CustomModelService = Depends(get_custom_model_service),
):
    """Delete a custom model."""
    # Verify ownership first
    existing = await service.get_custom_model(model_id)
    if not existing or existing.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom model not found")

    deleted = await service.delete_custom_model(model_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom model not found")

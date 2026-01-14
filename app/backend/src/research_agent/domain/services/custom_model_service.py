"""
Custom Model Service.

Handles business logic for custom models.
"""

from typing import List, Optional
from uuid import UUID

from research_agent.domain.repositories.custom_model_repo import (
    CustomModelDTO,
    ICustomModelRepository,
)
from research_agent.shared.utils.logger import logger


class CustomModelService:
    """Service for managing custom models."""

    def __init__(self, custom_model_repo: ICustomModelRepository):
        """
        Initialize service with repository.

        Args:
            custom_model_repo: Custom model repository instance
        """
        self._repo = custom_model_repo

    async def get_user_custom_models(self, user_id: str) -> List[CustomModelDTO]:
        """Get all custom models for a user."""
        return await self._repo.get_user_custom_models(user_id)

    async def get_custom_model(self, id: UUID) -> Optional[CustomModelDTO]:
        """Get a custom model by ID."""
        return await self._repo.get_custom_model(id)

    async def create_custom_model(
        self,
        user_id: str,
        model_id: str,
        label: str,
        description: Optional[str] = None,
        provider: str = "openrouter",
        context_window: Optional[int] = None,
    ) -> CustomModelDTO:
        """Create a new custom model."""
        # TODO: Add validation if needed (e.g. check if model_id is valid format)
        return await self._repo.create_custom_model(
            user_id=user_id,
            model_id=model_id,
            label=label,
            description=description,
            provider=provider,
            context_window=context_window,
            is_active=True,
        )

    async def update_custom_model(
        self,
        id: UUID,
        label: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        context_window: Optional[int] = None,
    ) -> Optional[CustomModelDTO]:
        """Update a custom model."""
        kwargs = {}
        if label is not None:
            kwargs["label"] = label
        if description is not None:
            kwargs["description"] = description
        if is_active is not None:
            kwargs["is_active"] = is_active
        if context_window is not None:
            kwargs["context_window"] = context_window

        return await self._repo.update_custom_model(id, **kwargs)

    async def delete_custom_model(self, id: UUID) -> bool:
        """Delete a custom model."""
        return await self._repo.delete_custom_model(id)

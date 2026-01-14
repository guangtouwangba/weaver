"""
Custom Model Repository Interface.

Defines the contract for custom model persistence operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class CustomModelDTO(BaseModel):
    """Data Transfer Object for custom models."""

    id: UUID
    user_id: str
    model_id: str
    label: str
    description: Optional[str] = None
    provider: str = "openrouter"
    context_window: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ICustomModelRepository(ABC):
    """
    Abstract interface for custom model repository.
    """

    @abstractmethod
    async def get_custom_model(self, id: UUID) -> Optional[CustomModelDTO]:
        """
        Get a custom model by ID.

        Args:
            id: Custom model UUID

        Returns:
            CustomModelDTO if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_user_custom_models(self, user_id: str) -> List[CustomModelDTO]:
        """
        Get all custom models for a user.

        Args:
            user_id: User identifier

        Returns:
            List of CustomModelDTO
        """
        pass

    @abstractmethod
    async def create_custom_model(
        self,
        user_id: str,
        model_id: str,
        label: str,
        description: Optional[str] = None,
        provider: str = "openrouter",
        context_window: Optional[int] = None,
        is_active: bool = True,
    ) -> CustomModelDTO:
        """
        Create a new custom model.
        """
        pass

    @abstractmethod
    async def update_custom_model(self, id: UUID, **kwargs) -> Optional[CustomModelDTO]:
        """
        Update a custom model.

        Args:
            id: Custom model UUID
            **kwargs: Fields to update

        Returns:
            Updated CustomModelDTO if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete_custom_model(self, id: UUID) -> bool:
        """
        Delete a custom model.

        Args:
            id: Custom model UUID

        Returns:
            True if deleted, False if not found
        """
        pass

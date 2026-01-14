"""
SQLAlchemy Custom Model Repository Implementation.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.repositories.custom_model_repo import (
    CustomModelDTO,
    ICustomModelRepository,
)
from research_agent.infrastructure.database.models import CustomModelModel
from research_agent.shared.utils.logger import logger


class SQLAlchemyCustomModelRepository(ICustomModelRepository):
    """SQLAlchemy implementation of custom model repository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def get_custom_model(self, id: UUID) -> Optional[CustomModelDTO]:
        """Get a custom model by ID."""
        stmt = select(CustomModelModel).where(CustomModelModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._model_to_dto(model)
        return None

    async def get_user_custom_models(self, user_id: str) -> List[CustomModelDTO]:
        """Get all custom models for a user."""
        stmt = select(CustomModelModel).where(CustomModelModel.user_id == user_id)
        stmt = stmt.order_by(CustomModelModel.created_at.desc())

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_dto(m) for m in models]

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
        """Create a new custom model."""
        # Check if already exists (although DB has constraint, we might want manual check
        # or just let DB error handle it. Here we trust DB constraint or handle it gracefully)

        model = CustomModelModel(
            user_id=user_id,
            model_id=model_id,
            label=label,
            description=description,
            provider=provider,
            context_window=context_window,
            is_active=is_active,
        )
        self._session.add(model)
        await self._session.flush()  # To get ID
        await self._session.commit()
        await self._session.refresh(model)  # To get created_at etc

        logger.info(f"[CustomModelRepo] Created custom model: {model.id} for user {user_id}")
        return self._model_to_dto(model)

    async def update_custom_model(self, id: UUID, **kwargs) -> Optional[CustomModelDTO]:
        """Update a custom model."""
        stmt = select(CustomModelModel).where(CustomModelModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        # Update fields
        for key, value in kwargs.items():
            if hasattr(model, key):
                setattr(model, key, value)

        await self._session.commit()
        await self._session.refresh(model)

        return self._model_to_dto(model)

    async def delete_custom_model(self, id: UUID) -> bool:
        """Delete a custom model."""
        stmt = delete(CustomModelModel).where(CustomModelModel.id == id)
        result = await self._session.execute(stmt)
        await self._session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"[CustomModelRepo] Deleted custom model: {id}")
        return deleted

    @staticmethod
    def _model_to_dto(model: CustomModelModel) -> CustomModelDTO:
        """Convert CustomModelModel to CustomModelDTO."""
        return CustomModelDTO(
            id=model.id,
            user_id=model.user_id,
            model_id=model.model_id,
            label=model.label,
            description=model.description,
            provider=model.provider,
            context_window=model.context_window,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

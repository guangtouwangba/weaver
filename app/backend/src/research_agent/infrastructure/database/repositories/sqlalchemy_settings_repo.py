"""
SQLAlchemy Settings Repository Implementation.

Provides persistence for global and project-level settings.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.repositories.settings_repo import ISettingsRepository, SettingDTO
from research_agent.infrastructure.database.models import (
    GlobalSettingModel,
    ProjectSettingModel,
    UserSettingModel,
)
from research_agent.shared.utils.logger import logger


class SQLAlchemySettingsRepository(ISettingsRepository):
    """SQLAlchemy implementation of settings repository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    # -------------------------------------------------------------------------
    # Global Settings
    # -------------------------------------------------------------------------

    async def get_global_setting(self, key: str) -> SettingDTO | None:
        """Get a global setting by key."""
        stmt = select(GlobalSettingModel).where(GlobalSettingModel.key == key)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._global_model_to_dto(model)
        return None

    async def get_all_global_settings(self, category: str | None = None) -> list[SettingDTO]:
        """Get all global settings, optionally filtered by category."""
        stmt = select(GlobalSettingModel)
        if category:
            stmt = stmt.where(GlobalSettingModel.category == category)
        stmt = stmt.order_by(GlobalSettingModel.key)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._global_model_to_dto(m) for m in models]

    async def create_or_update_global_setting(
        self,
        key: str,
        value: Any,
        category: str,
        description: str | None = None,
        is_encrypted: bool = False,
    ) -> SettingDTO:
        """Create or update a global setting using upsert."""
        # Use PostgreSQL INSERT ... ON CONFLICT for upsert
        stmt = insert(GlobalSettingModel).values(
            key=key,
            value=value,
            category=category,
            description=description,
            is_encrypted=is_encrypted,
        )

        # On conflict, update the value and metadata
        stmt = stmt.on_conflict_do_update(
            index_elements=["key"],
            set_={
                "value": value,
                "category": category,
                "description": description,
                "is_encrypted": is_encrypted,
            },
        )

        await self._session.execute(stmt)
        await self._session.commit()

        logger.info(f"[SettingsRepo] Upserted global setting: {key}")

        # Return the updated setting
        return await self.get_global_setting(key)  # type: ignore

    async def delete_global_setting(self, key: str) -> bool:
        """Delete a global setting."""
        stmt = delete(GlobalSettingModel).where(GlobalSettingModel.key == key)
        result = await self._session.execute(stmt)
        await self._session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"[SettingsRepo] Deleted global setting: {key}")
        return deleted

    # -------------------------------------------------------------------------
    # Project Settings
    # -------------------------------------------------------------------------

    async def get_project_setting(self, project_id: UUID, key: str) -> SettingDTO | None:
        """Get a project setting by project ID and key."""
        stmt = select(ProjectSettingModel).where(
            ProjectSettingModel.project_id == project_id,
            ProjectSettingModel.key == key,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._project_model_to_dto(model)
        return None

    async def get_all_project_settings(
        self, project_id: UUID, category: str | None = None
    ) -> list[SettingDTO]:
        """Get all settings for a project, optionally filtered by category."""
        stmt = select(ProjectSettingModel).where(ProjectSettingModel.project_id == project_id)
        if category:
            stmt = stmt.where(ProjectSettingModel.category == category)
        stmt = stmt.order_by(ProjectSettingModel.key)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._project_model_to_dto(m) for m in models]

    async def create_or_update_project_setting(
        self,
        project_id: UUID,
        key: str,
        value: Any,
        category: str,
        description: str | None = None,
        is_encrypted: bool = False,
    ) -> SettingDTO:
        """Create or update a project setting using upsert."""
        stmt = insert(ProjectSettingModel).values(
            project_id=project_id,
            key=key,
            value=value,
            category=category,
            description=description,
            is_encrypted=is_encrypted,
        )

        # On conflict (project_id, key), update the value
        stmt = stmt.on_conflict_do_update(
            constraint="uq_project_settings_project_key",
            set_={
                "value": value,
                "category": category,
                "description": description,
                "is_encrypted": is_encrypted,
            },
        )

        await self._session.execute(stmt)
        await self._session.commit()

        logger.info(f"[SettingsRepo] Upserted project setting: {project_id}/{key}")

        return await self.get_project_setting(project_id, key)  # type: ignore

    async def delete_project_setting(self, project_id: UUID, key: str) -> bool:
        """Delete a project setting (reverts to global setting)."""
        stmt = delete(ProjectSettingModel).where(
            ProjectSettingModel.project_id == project_id,
            ProjectSettingModel.key == key,
        )
        result = await self._session.execute(stmt)
        await self._session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"[SettingsRepo] Deleted project setting: {project_id}/{key}")
        return deleted

    # -------------------------------------------------------------------------
    # Merged Settings (with priority)
    # -------------------------------------------------------------------------

    async def get_effective_setting(
        self, key: str, project_id: UUID | None = None
    ) -> SettingDTO | None:
        """
        Get the effective setting value with priority resolution.

        Priority: Project > Global
        """
        # Try project setting first if project_id is provided
        if project_id:
            project_setting = await self.get_project_setting(project_id, key)
            if project_setting:
                return project_setting

        # Fall back to global setting
        return await self.get_global_setting(key)

    async def get_all_effective_settings(
        self, project_id: UUID | None = None, category: str | None = None
    ) -> list[SettingDTO]:
        """
        Get all effective settings with priority resolution.

        Project settings override global settings with the same key.
        """
        # Get all global settings
        global_settings = await self.get_all_global_settings(category)
        settings_dict: dict[str, SettingDTO] = {s.key: s for s in global_settings}

        # Overlay project settings if project_id is provided
        if project_id:
            project_settings = await self.get_all_project_settings(project_id, category)
            for ps in project_settings:
                settings_dict[ps.key] = ps

        return list(settings_dict.values())

    # -------------------------------------------------------------------------
    # User Settings
    # -------------------------------------------------------------------------

    async def get_user_setting(self, user_id: UUID, key: str) -> SettingDTO | None:
        """Get a user setting by user ID and key."""
        stmt = select(UserSettingModel).where(
            UserSettingModel.user_id == user_id,
            UserSettingModel.key == key,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._user_model_to_dto(model)
        return None

    async def get_all_user_settings(
        self, user_id: UUID, category: str | None = None
    ) -> list[SettingDTO]:
        """Get all settings for a user, optionally filtered by category."""
        stmt = select(UserSettingModel).where(UserSettingModel.user_id == user_id)
        if category:
            stmt = stmt.where(UserSettingModel.category == category)
        stmt = stmt.order_by(UserSettingModel.key)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._user_model_to_dto(m) for m in models]

    async def create_or_update_user_setting(
        self,
        user_id: UUID,
        key: str,
        value: Any,
        category: str,
        description: str | None = None,
        is_encrypted: bool = False,
    ) -> SettingDTO:
        """Create or update a user setting using upsert."""
        stmt = insert(UserSettingModel).values(
            user_id=user_id,
            key=key,
            value=value,
            category=category,
            description=description,
            is_encrypted=is_encrypted,
        )

        # On conflict (user_id, key), update the value
        stmt = stmt.on_conflict_do_update(
            constraint="uq_user_settings_user_key",
            set_={
                "value": value,
                "category": category,
                "description": description,
                "is_encrypted": is_encrypted,
            },
        )

        await self._session.execute(stmt)
        await self._session.commit()

        logger.info(f"[SettingsRepo] Upserted user setting: {user_id}/{key}")

        return await self.get_user_setting(user_id, key)  # type: ignore

    async def delete_user_setting(self, user_id: UUID, key: str) -> bool:
        """Delete a user setting."""
        stmt = delete(UserSettingModel).where(
            UserSettingModel.user_id == user_id,
            UserSettingModel.key == key,
        )
        result = await self._session.execute(stmt)
        await self._session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"[SettingsRepo] Deleted user setting: {user_id}/{key}")
        return deleted

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def _global_model_to_dto(model: GlobalSettingModel) -> SettingDTO:
        """Convert GlobalSettingModel to SettingDTO."""
        return SettingDTO(
            key=model.key,
            value=model.value,
            category=model.category,
            description=model.description,
            is_encrypted=model.is_encrypted,
            project_id=None,
        )

    @staticmethod
    def _project_model_to_dto(model: ProjectSettingModel) -> SettingDTO:
        """Convert ProjectSettingModel to SettingDTO."""
        return SettingDTO(
            key=model.key,
            value=model.value,
            category=model.category,
            description=model.description,
            is_encrypted=model.is_encrypted,
            project_id=model.project_id,
        )

    @staticmethod
    def _user_model_to_dto(model: UserSettingModel) -> SettingDTO:
        """Convert UserSettingModel to SettingDTO."""
        return SettingDTO(
            key=model.key,
            value=model.value,
            category=model.category,
            description=model.description,
            is_encrypted=model.is_encrypted,
            user_id=model.user_id,
        )

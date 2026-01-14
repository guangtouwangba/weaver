"""
Settings Repository Interface.

Defines the contract for settings persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class SettingDTO:
    """Data Transfer Object for settings."""

    def __init__(
        self,
        key: str,
        value: Any,
        category: str,
        description: str | None = None,
        is_encrypted: bool = False,
        project_id: UUID | None = None,
        user_id: UUID | None = None,
    ):
        self.key = key
        self.value = value
        self.category = category
        self.description = description
        self.is_encrypted = is_encrypted
        self.project_id = project_id
        self.user_id = user_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "description": self.description,
            "is_encrypted": self.is_encrypted,
            "project_id": str(self.project_id) if self.project_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
        }


class ISettingsRepository(ABC):
    """
    Abstract interface for settings repository.

    Implementations should handle persistence of global and project-level settings.
    """

    # -------------------------------------------------------------------------
    # Global Settings
    # -------------------------------------------------------------------------

    @abstractmethod
    async def get_global_setting(self, key: str) -> SettingDTO | None:
        """
        Get a global setting by key.

        Args:
            key: Setting key

        Returns:
            SettingDTO if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all_global_settings(self, category: str | None = None) -> list[SettingDTO]:
        """
        Get all global settings, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of SettingDTO
        """
        pass

    @abstractmethod
    async def create_or_update_global_setting(
        self,
        key: str,
        value: Any,
        category: str,
        description: str | None = None,
        is_encrypted: bool = False,
    ) -> SettingDTO:
        """
        Create or update a global setting.

        Args:
            key: Setting key
            value: Setting value (will be stored as JSON)
            category: Setting category
            description: Optional description
            is_encrypted: Whether the value is encrypted

        Returns:
            Created or updated SettingDTO
        """
        pass

    @abstractmethod
    async def delete_global_setting(self, key: str) -> bool:
        """
        Delete a global setting.

        Args:
            key: Setting key

        Returns:
            True if deleted, False if not found
        """
        pass

    # -------------------------------------------------------------------------
    # Project Settings
    # -------------------------------------------------------------------------

    @abstractmethod
    async def get_project_setting(self, project_id: UUID, key: str) -> SettingDTO | None:
        """
        Get a project setting by project ID and key.

        Args:
            project_id: Project UUID
            key: Setting key

        Returns:
            SettingDTO if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all_project_settings(
        self, project_id: UUID, category: str | None = None
    ) -> list[SettingDTO]:
        """
        Get all settings for a project, optionally filtered by category.

        Args:
            project_id: Project UUID
            category: Optional category filter

        Returns:
            List of SettingDTO
        """
        pass

    @abstractmethod
    async def create_or_update_project_setting(
        self,
        project_id: UUID,
        key: str,
        value: Any,
        category: str,
        description: str | None = None,
        is_encrypted: bool = False,
    ) -> SettingDTO:
        """
        Create or update a project setting.

        Args:
            project_id: Project UUID
            key: Setting key
            value: Setting value
            category: Setting category
            description: Optional description
            is_encrypted: Whether the value is encrypted

        Returns:
            Created or updated SettingDTO
        """
        pass

    @abstractmethod
    async def delete_project_setting(self, project_id: UUID, key: str) -> bool:
        """
        Delete a project setting (reverts to global setting).

        Args:
            project_id: Project UUID
            key: Setting key

        Returns:
            True if deleted, False if not found
        """
        pass

    # -------------------------------------------------------------------------
    # Merged Settings (with priority)
    # -------------------------------------------------------------------------

    @abstractmethod
    async def get_effective_setting(
        self, key: str, project_id: UUID | None = None
    ) -> SettingDTO | None:
        """
        Get the effective setting value with priority resolution.

        Priority: Project > Global

        Args:
            key: Setting key
            project_id: Optional project UUID

        Returns:
            SettingDTO with highest priority, None if not found
        """
        pass

    @abstractmethod
    async def get_all_effective_settings(
        self, project_id: UUID | None = None, category: str | None = None
    ) -> list[SettingDTO]:
        """
        Get all effective settings with priority resolution.

        Args:
            project_id: Optional project UUID
            category: Optional category filter

        Returns:
            List of SettingDTO with project overrides applied
        """
        pass

    # -------------------------------------------------------------------------
    # User Settings
    # -------------------------------------------------------------------------

    @abstractmethod
    async def get_user_setting(self, user_id: UUID, key: str) -> SettingDTO | None:
        """
        Get a user setting by user ID and key.

        Args:
            user_id: User UUID
            key: Setting key

        Returns:
            SettingDTO if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all_user_settings(
        self, user_id: UUID, category: str | None = None
    ) -> list[SettingDTO]:
        """
        Get all settings for a user, optionally filtered by category.

        Args:
            user_id: User UUID
            category: Optional category filter

        Returns:
            List of SettingDTO
        """
        pass

    @abstractmethod
    async def create_or_update_user_setting(
        self,
        user_id: UUID,
        key: str,
        value: Any,
        category: str,
        description: str | None = None,
        is_encrypted: bool = False,
    ) -> SettingDTO:
        """
        Create or update a user setting.

        Args:
            user_id: User UUID
            key: Setting key
            value: Setting value
            category: Setting category
            description: Optional description
            is_encrypted: Whether the value is encrypted

        Returns:
            Created or updated SettingDTO
        """
        pass

    @abstractmethod
    async def delete_user_setting(self, user_id: UUID, key: str) -> bool:
        """
        Delete a user setting.

        Args:
            user_id: User UUID
            key: Setting key

        Returns:
            True if deleted, False if not found
        """
        pass

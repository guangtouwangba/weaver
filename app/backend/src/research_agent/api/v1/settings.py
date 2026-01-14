"""
Settings API Endpoints.

Provides REST API for managing global and project-level configuration.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.repositories.settings_repo import SettingDTO
from research_agent.domain.services.settings_service import SETTING_METADATA, SettingsService
from research_agent.infrastructure.database.repositories.sqlalchemy_settings_repo import (
    SQLAlchemySettingsRepository,
)
from research_agent.infrastructure.database.session import get_session
from research_agent.shared.utils.logger import logger

router = APIRouter(prefix="/settings", tags=["settings"])


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------


class SettingValue(BaseModel):
    """Setting value for create/update."""

    value: Any = Field(..., description="Setting value (JSON compatible)")
    description: Optional[str] = Field(None, description="Optional description")


class SettingResponse(BaseModel):
    """Setting response model."""

    key: str
    value: Any
    category: str
    description: Optional[str] = None
    is_encrypted: bool = False
    is_project_override: bool = False
    is_user_override: bool = False


class AllSettingsResponse(BaseModel):
    """Response for all settings."""

    settings: Dict[str, Any]
    metadata: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Setting metadata (types, defaults, etc.)"
    )


class ApiKeyValidationRequest(BaseModel):
    """Request for API key validation."""

    api_key: str = Field(..., description="API key to validate")
    provider: str = Field(default="openrouter", description="Provider: openrouter or openai")


class ApiKeyValidationResponse(BaseModel):
    """Response for API key validation."""

    valid: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------


async def get_settings_service(
    session: AsyncSession = Depends(get_session),
) -> SettingsService:
    """Get settings service with repository."""
    repo = SQLAlchemySettingsRepository(session)
    # Create custom model service for integration
    from research_agent.domain.services.custom_model_service import CustomModelService
    from research_agent.infrastructure.database.repositories.sqlalchemy_custom_model_repo import (
        SQLAlchemyCustomModelRepository,
    )

    custom_repo = SQLAlchemyCustomModelRepository(session)
    custom_service = CustomModelService(custom_repo)

    return SettingsService(repo, custom_model_service=custom_service)


# -----------------------------------------------------------------------------
# Global Settings Endpoints
# -----------------------------------------------------------------------------


@router.get("/global", response_model=AllSettingsResponse)
async def get_all_global_settings(
    category: Optional[str] = None,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Get all global settings.

    Args:
        category: Optional filter by category (model, api_key, rag_strategy, advanced)
    """
    settings = await service.get_all_settings(
        project_id=None,
        category=category,
        include_encrypted=True,  # Include masked API keys
    )

    return AllSettingsResponse(
        settings=settings,
        metadata=SETTING_METADATA,
    )


@router.get("/global/{key}", response_model=SettingResponse)
async def get_global_setting(
    key: str,
    service: SettingsService = Depends(get_settings_service),
):
    """Get a specific global setting."""
    value = await service.get_global_setting(key, decrypt=False)

    if value is None:
        # Check if it's a known key with default
        metadata = SETTING_METADATA.get(key)
        if metadata and "default" in metadata:
            return SettingResponse(
                key=key,
                value=metadata["default"],
                category=metadata.get("category", "advanced"),
                description=metadata.get("description"),
                is_encrypted=metadata.get("encrypted", False),
            )
        raise HTTPException(status_code=404, detail=f"Setting not found: {key}")

    metadata = SETTING_METADATA.get(key, {})
    return SettingResponse(
        key=key,
        value=value,
        category=metadata.get("category", "advanced"),
        description=metadata.get("description"),
        is_encrypted=metadata.get("encrypted", False),
    )


@router.put("/global/{key}", response_model=SettingResponse)
async def update_global_setting(
    key: str,
    setting: SettingValue,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Create or update a global setting.

    Note: API keys will be encrypted before storage.
    """
    try:
        result = await service.set_global_setting(
            key=key,
            value=setting.value,
            description=setting.description,
        )

        metadata = SETTING_METADATA.get(key, {})
        return SettingResponse(
            key=result.key,
            value=result.value if not result.is_encrypted else "********",
            category=result.category,
            description=result.description,
            is_encrypted=result.is_encrypted,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/global/{key}")
async def delete_global_setting(
    key: str,
    service: SettingsService = Depends(get_settings_service),
):
    """Delete a global setting."""
    deleted = await service.delete_global_setting(key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Setting not found: {key}")

    return {"message": f"Setting '{key}' deleted"}


# -----------------------------------------------------------------------------
# Project Settings Endpoints
# -----------------------------------------------------------------------------


@router.get("/projects/{project_id}", response_model=AllSettingsResponse)
async def get_all_project_settings(
    project_id: UUID,
    category: Optional[str] = None,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Get all effective settings for a project.

    Returns merged settings with project overrides applied.
    """
    settings = await service.get_all_settings(
        project_id=project_id,
        category=category,
        include_encrypted=True,
    )

    return AllSettingsResponse(
        settings=settings,
        metadata=SETTING_METADATA,
    )


@router.get("/projects/{project_id}/{key}", response_model=SettingResponse)
async def get_project_setting(
    project_id: UUID,
    key: str,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Get a specific setting for a project.

    Returns project override if exists, otherwise global setting.
    """
    # Check if project has override
    project_value = await service.get_project_setting(project_id, key, decrypt=False)
    is_override = project_value is not None

    # Get effective value
    value = await service.get_setting(key, user_id=None, project_id=project_id, decrypt=False)

    if value is None:
        metadata = SETTING_METADATA.get(key)
        if metadata and "default" in metadata:
            return SettingResponse(
                key=key,
                value=metadata["default"],
                category=metadata.get("category", "advanced"),
                description=metadata.get("description"),
                is_encrypted=metadata.get("encrypted", False),
                is_project_override=False,
            )
        raise HTTPException(status_code=404, detail=f"Setting not found: {key}")

    metadata = SETTING_METADATA.get(key, {})
    return SettingResponse(
        key=key,
        value=value,
        category=metadata.get("category", "advanced"),
        description=metadata.get("description"),
        is_encrypted=metadata.get("encrypted", False),
        is_project_override=is_override,
    )


@router.put("/projects/{project_id}/{key}", response_model=SettingResponse)
async def update_project_setting(
    project_id: UUID,
    key: str,
    setting: SettingValue,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Create or update a project-specific setting.

    This creates an override for the project that takes precedence over global settings.
    """
    try:
        result = await service.set_project_setting(
            project_id=project_id,
            key=key,
            value=setting.value,
            description=setting.description,
        )

        metadata = SETTING_METADATA.get(key, {})
        return SettingResponse(
            key=result.key,
            value=result.value if not result.is_encrypted else "********",
            category=result.category,
            description=result.description,
            is_encrypted=result.is_encrypted,
            is_project_override=True,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/projects/{project_id}/{key}")
async def delete_project_setting(
    project_id: UUID,
    key: str,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Delete a project setting (reverts to global setting).
    """
    deleted = await service.delete_project_setting(project_id, key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Project setting not found: {key}")

    return {"message": f"Project setting '{key}' deleted, reverted to global"}


# -----------------------------------------------------------------------------
# User Settings Endpoints
# -----------------------------------------------------------------------------


@router.get("/users/{user_id}", response_model=AllSettingsResponse)
async def get_all_user_settings(
    user_id: UUID,
    category: Optional[str] = None,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Get all settings for a user.

    Returns user-specific settings with defaults for unset values.
    """
    settings = await service.get_all_user_settings(
        user_id=user_id,
        category=category,
        include_encrypted=True,
    )

    return AllSettingsResponse(
        settings=settings,
        metadata=SETTING_METADATA,
    )


@router.get("/users/{user_id}/{key}", response_model=SettingResponse)
async def get_user_setting(
    user_id: UUID,
    key: str,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Get a specific setting for a user.

    Returns user override if exists, otherwise default.
    """
    # Check if user has override
    user_value = await service.get_user_setting(user_id, key, decrypt=False)
    is_override = user_value is not None

    # Get effective value (user > default)
    value = await service.get_setting(key, user_id=user_id, decrypt=False)

    if value is None:
        metadata = SETTING_METADATA.get(key)
        if metadata and "default" in metadata:
            return SettingResponse(
                key=key,
                value=metadata["default"],
                category=metadata.get("category", "advanced"),
                description=metadata.get("description"),
                is_encrypted=metadata.get("encrypted", False),
                is_user_override=False,
            )
        raise HTTPException(status_code=404, detail=f"Setting not found: {key}")

    metadata = SETTING_METADATA.get(key, {})
    return SettingResponse(
        key=key,
        value=value,
        category=metadata.get("category", "advanced"),
        description=metadata.get("description"),
        is_encrypted=metadata.get("encrypted", False),
        is_user_override=is_override,
    )


@router.put("/users/{user_id}/{key}", response_model=SettingResponse)
async def update_user_setting(
    user_id: UUID,
    key: str,
    setting: SettingValue,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Create or update a user-specific setting.

    This creates an override for the user that takes precedence over global settings.
    """
    try:
        result = await service.set_user_setting(
            user_id=user_id,
            key=key,
            value=setting.value,
            description=setting.description,
        )

        return SettingResponse(
            key=result.key,
            value=result.value if not result.is_encrypted else "********",
            category=result.category,
            description=result.description,
            is_encrypted=result.is_encrypted,
            is_user_override=True,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/users/{user_id}/{key}")
async def delete_user_setting(
    user_id: UUID,
    key: str,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Delete a user setting (reverts to global/default).
    """
    deleted = await service.delete_user_setting(user_id, key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"User setting not found: {key}")

    return {"message": f"User setting '{key}' deleted, reverted to default"}


# -----------------------------------------------------------------------------
# Utility Endpoints
# -----------------------------------------------------------------------------


@router.post("/validate-api-key", response_model=ApiKeyValidationResponse)
async def validate_api_key(
    request: ApiKeyValidationRequest,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Validate an API key by making a test request to the provider.

    Supports openrouter and openai providers.
    """
    result = await service.validate_api_key(request.api_key, request.provider)

    return ApiKeyValidationResponse(
        valid=result["valid"],
        message=result["message"],
        data=result.get("data"),
    )


# Redefine with proper signature
@router.get("/metadata")
async def get_settings_metadata_endpoint(
    request: Request,
    service: SettingsService = Depends(get_settings_service),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    from research_agent.api.auth.supabase import get_optional_user

    user = await get_optional_user(request, authorization)
    user_id = None
    if user and not user.is_anonymous:
        try:
            user_id = UUID(user.user_id)
        except (ValueError, TypeError):
            pass

    # Get dynamic metadata
    return {"settings": await service.get_settings_metadata(user_id)}

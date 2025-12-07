"""
Settings Service.

Business logic for managing application settings.
Handles encryption, validation, and priority resolution.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

from research_agent.domain.repositories.settings_repo import ISettingsRepository, SettingDTO
from research_agent.infrastructure.security.encryption import (
    EncryptionService,
    get_encryption_service,
)
from research_agent.shared.utils.logger import logger


class SettingCategory(str, Enum):
    """Setting categories."""

    MODEL = "model"
    API_KEY = "api_key"
    RAG_STRATEGY = "rag_strategy"
    ADVANCED = "advanced"


# Keys that should be encrypted
ENCRYPTED_KEYS = {
    "openrouter_api_key",
    "openai_api_key",
}

# Known setting keys with their metadata
SETTING_METADATA = {
    # Model settings
    "llm_model": {
        "category": SettingCategory.MODEL,
        "description": "LLM model for RAG queries",
        "default": "openai/gpt-4o-mini",
        "options": [
            {
                "value": "openai/gpt-4o-mini",
                "label": "GPT-4o Mini",
                "description": "Fast and cost-effective for most tasks",
                "cost": "low",
                "performance": "fast",
                "best_for": "Quick Q&A, general queries",
            },
            {
                "value": "openai/gpt-4o",
                "label": "GPT-4o",
                "description": "Most capable model, best for complex reasoning",
                "cost": "high",
                "performance": "medium",
                "best_for": "Complex analysis, detailed reports",
            },
            {
                "value": "anthropic/claude-3.5-sonnet",
                "label": "Claude 3.5 Sonnet",
                "description": "Excellent for long documents and nuanced understanding",
                "cost": "medium",
                "performance": "medium",
                "best_for": "Long-form content, detailed explanations",
            },
            {
                "value": "google/gemini-pro-1.5",
                "label": "Gemini Pro 1.5",
                "description": "Large context window (1M tokens), good for full documents",
                "cost": "medium",
                "performance": "medium",
                "best_for": "Very long documents, multi-document analysis",
            },
            {
                "value": "google/gemini-2.5-pro",
                "label": "Gemini 2.5 Pro",
                "description": "Latest Gemini model with enhanced reasoning and 1M context",
                "cost": "medium",
                "performance": "medium",
                "best_for": "Complex reasoning, code generation, multimodal tasks",
            },
            {
                "value": "google/gemini-3-pro-preview",
                "label": "Gemini 3 Pro Preview",
                "description": "Google's flagship frontier model with 1M context, best multimodal reasoning",
                "cost": "medium",
                "performance": "medium",
                "best_for": "Advanced reasoning, agentic workflows, multimodal analysis, long context",
            },
            {
                "value": "anthropic/claude-sonnet-4",
                "label": "Claude Sonnet 4",
                "description": "Latest Claude model, excellent balance of speed and capability",
                "cost": "medium",
                "performance": "fast",
                "best_for": "General tasks, coding, analysis",
            },
            {
                "value": "anthropic/claude-opus-4",
                "label": "Claude Opus 4",
                "description": "Most capable Claude model for complex tasks",
                "cost": "high",
                "performance": "medium",
                "best_for": "Complex research, detailed analysis, creative writing",
            },
            {
                "value": "openai/gpt-4.1",
                "label": "GPT-4.1",
                "description": "Enhanced GPT-4 with improved reasoning and coding",
                "cost": "high",
                "performance": "medium",
                "best_for": "Complex reasoning, code generation",
            },
            {
                "value": "openai/o3-mini",
                "label": "OpenAI o3-mini",
                "description": "Reasoning model optimized for complex problems",
                "cost": "medium",
                "performance": "slow",
                "best_for": "Math, logic, complex reasoning tasks",
            },
        ],
    },
    "embedding_model": {
        "category": SettingCategory.MODEL,
        "description": "Embedding model for document vectorization",
        "default": "openai/text-embedding-3-small",
        "options": [
            {
                "value": "openai/text-embedding-3-small",
                "label": "OpenAI Small",
                "description": "Cost-effective, 1536 dimensions",
                "cost": "low",
                "performance": "fast",
                "best_for": "Most use cases",
            },
            {
                "value": "openai/text-embedding-3-large",
                "label": "OpenAI Large",
                "description": "Higher quality, 3072 dimensions",
                "cost": "medium",
                "performance": "medium",
                "best_for": "High-precision retrieval",
            },
        ],
    },
    # API Keys
    "openrouter_api_key": {
        "category": SettingCategory.API_KEY,
        "description": "OpenRouter API key",
        "encrypted": True,
    },
    "openai_api_key": {
        "category": SettingCategory.API_KEY,
        "description": "OpenAI API key (optional fallback)",
        "encrypted": True,
    },
    # RAG Strategy
    "rag_mode": {
        "category": SettingCategory.RAG_STRATEGY,
        "description": "RAG operation mode",
        "default": "traditional",
        "allowed_values": ["traditional", "long_context", "auto"],
        "options": [
            {
                "value": "traditional",
                "label": "Traditional (Chunk-based)",
                "description": "Retrieves relevant chunks from documents using vector search",
                "cost": "low",
                "performance": "fast",
                "best_for": "Large document collections, quick queries",
            },
            {
                "value": "long_context",
                "label": "Long Context (Mega-Prompt)",
                "description": "Includes full document content in the prompt for deep analysis",
                "cost": "high",
                "performance": "slow",
                "best_for": "Deep analysis, precise citations, small documents",
            },
            {
                "value": "auto",
                "label": "Auto",
                "description": "Automatically selects mode based on document size and query type",
                "cost": "variable",
                "performance": "variable",
                "best_for": "Mixed workloads, adaptive requirements",
            },
        ],
    },
    "long_context_safety_ratio": {
        "category": SettingCategory.RAG_STRATEGY,
        "description": "Percentage of model context window to use for long context mode (higher = more content but risk of truncation)",
        "default": 0.55,
        "min": 0.3,
        "max": 0.9,
        "step": 0.05,
        "type": "slider",
        "options": [
            {
                "value": 0.4,
                "label": "40% (Conservative)",
                "description": "Safe for complex prompts with many system instructions",
            },
            {
                "value": 0.55,
                "label": "55% (Balanced)",
                "description": "Default balance between content and response space",
            },
            {
                "value": 0.7,
                "label": "70% (Aggressive)",
                "description": "More document content, less response space",
            },
            {
                "value": 0.85,
                "label": "85% (Maximum)",
                "description": "Maximum content, minimal response space",
            },
        ],
    },
    "fast_upload_mode": {
        "category": SettingCategory.RAG_STRATEGY,
        "description": "Skip summary generation and embeddings to speed up document processing in long context mode",
        "default": True,
    },
    "retrieval_strategy": {
        "category": SettingCategory.RAG_STRATEGY,
        "description": "Document retrieval strategy",
        "default": "vector",
        "allowed_values": ["vector", "hybrid", "hyde"],
        "options": [
            {
                "value": "vector",
                "label": "Vector Search",
                "description": "Semantic similarity search using embeddings",
                "cost": "low",
                "performance": "fast",
                "best_for": "Conceptual questions, semantic understanding",
            },
            {
                "value": "hybrid",
                "label": "Hybrid Search",
                "description": "Combines vector similarity with keyword matching (BM25)",
                "cost": "medium",
                "performance": "medium",
                "best_for": "Factual queries, specific terms, technical content",
            },
            {
                "value": "hyde",
                "label": "HyDE",
                "description": "Hypothetical Document Embedding - generates ideal answer first",
                "cost": "high",
                "performance": "slow",
                "best_for": "Complex questions, when direct matching fails",
            },
        ],
    },
    "retrieval_top_k": {
        "category": SettingCategory.RAG_STRATEGY,
        "description": "Number of documents to retrieve",
        "default": 5,
        "min": 1,
        "max": 50,
    },
    "retrieval_min_similarity": {
        "category": SettingCategory.RAG_STRATEGY,
        "description": "Minimum similarity threshold",
        "default": 0.0,
        "min": 0.0,
        "max": 1.0,
    },
    "use_hybrid_search": {
        "category": SettingCategory.RAG_STRATEGY,
        "description": "Enable hybrid (vector + keyword) search",
        "default": False,
    },
    "citation_format": {
        "category": SettingCategory.RAG_STRATEGY,
        "description": "Citation format in responses",
        "default": "both",
        "allowed_values": ["inline", "structured", "both"],
        "options": [
            {
                "value": "inline",
                "label": "Inline",
                "description": "Simple [doc_01] style citations in text",
                "cost": "low",
                "performance": "fast",
                "best_for": "Quick reading, simple documents",
            },
            {
                "value": "structured",
                "label": "Structured",
                "description": "XML-style citations with precise location data",
                "cost": "low",
                "performance": "fast",
                "best_for": "Academic use, precise verification",
            },
            {
                "value": "both",
                "label": "Both",
                "description": "Supports both citation formats for flexibility",
                "cost": "low",
                "performance": "fast",
                "best_for": "General use, maximum compatibility",
            },
        ],
    },
    # Advanced
    "intent_classification_enabled": {
        "category": SettingCategory.ADVANCED,
        "description": "Enable intent-based adaptive RAG",
        "default": True,
    },
    "intent_cache_enabled": {
        "category": SettingCategory.ADVANCED,
        "description": "Cache intent classification results",
        "default": True,
    },
}


class SettingsService:
    """
    Service for managing application settings.

    Handles:
    - CRUD operations for global and project settings
    - Encryption/decryption of sensitive values
    - Validation of setting values
    - API key verification
    """

    def __init__(
        self,
        repository: ISettingsRepository,
        encryption_service: Optional[EncryptionService] = None,
    ):
        """
        Initialize settings service.

        Args:
            repository: Settings repository implementation
            encryption_service: Optional encryption service (uses default if not provided)
        """
        self._repo = repository
        self._encryption = encryption_service or get_encryption_service()

    # -------------------------------------------------------------------------
    # Get Settings
    # -------------------------------------------------------------------------

    async def get_setting(
        self,
        key: str,
        user_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        decrypt: bool = True,
    ) -> Optional[Any]:
        """
        Get a setting value with priority resolution.

        Priority: User > Project > Global > Default

        Args:
            key: Setting key
            user_id: Optional user for user-specific settings
            project_id: Optional project for project-specific settings
            decrypt: Whether to decrypt encrypted values

        Returns:
            Setting value or None if not found
        """
        # Try user setting first if user_id is provided
        if user_id:
            user_setting = await self._repo.get_user_setting(user_id, key)
            if user_setting:
                value = user_setting.value
                if decrypt and user_setting.is_encrypted:
                    try:
                        value = self._encryption.decrypt(value)
                    except ValueError:
                        logger.warning(f"[SettingsService] Failed to decrypt {key}")
                        value = None
                return value

        # Fall back to project/global
        setting = await self._repo.get_effective_setting(key, project_id)

        if setting:
            value = setting.value
            if decrypt and setting.is_encrypted:
                try:
                    value = self._encryption.decrypt(value)
                except ValueError:
                    logger.warning(f"[SettingsService] Failed to decrypt {key}")
                    value = None
            return value

        # Return default if defined
        metadata = SETTING_METADATA.get(key)
        if metadata and "default" in metadata:
            return metadata["default"]

        return None

    async def get_all_settings(
        self,
        project_id: Optional[UUID] = None,
        category: Optional[str] = None,
        include_encrypted: bool = False,
    ) -> Dict[str, Any]:
        """
        Get all effective settings as a dictionary.

        Args:
            project_id: Optional project for project-specific settings
            category: Optional category filter
            include_encrypted: Whether to include (masked) encrypted values

        Returns:
            Dictionary of key -> value
        """
        settings = await self._repo.get_all_effective_settings(project_id, category)

        result = {}
        for s in settings:
            if s.is_encrypted:
                if include_encrypted:
                    # Return masked value
                    result[s.key] = self._encryption.mask_value(s.value)
                # Skip encrypted values if not included
            else:
                result[s.key] = s.value

        # Add defaults for missing settings
        for key, metadata in SETTING_METADATA.items():
            if key not in result and "default" in metadata:
                if category is None or metadata.get("category") == category:
                    result[key] = metadata["default"]

        return result

    async def get_global_setting(self, key: str, decrypt: bool = True) -> Optional[Any]:
        """Get a global setting value."""
        setting = await self._repo.get_global_setting(key)
        if setting:
            value = setting.value
            if decrypt and setting.is_encrypted:
                try:
                    value = self._encryption.decrypt(value)
                except ValueError:
                    return None
            return value
        return None

    async def get_project_setting(
        self,
        project_id: UUID,
        key: str,
        decrypt: bool = True,
    ) -> Optional[Any]:
        """Get a project-specific setting value."""
        setting = await self._repo.get_project_setting(project_id, key)
        if setting:
            value = setting.value
            if decrypt and setting.is_encrypted:
                try:
                    value = self._encryption.decrypt(value)
                except ValueError:
                    return None
            return value
        return None

    async def get_user_setting(
        self,
        user_id: UUID,
        key: str,
        decrypt: bool = True,
    ) -> Optional[Any]:
        """Get a user-specific setting value."""
        setting = await self._repo.get_user_setting(user_id, key)
        if setting:
            value = setting.value
            if decrypt and setting.is_encrypted:
                try:
                    value = self._encryption.decrypt(value)
                except ValueError:
                    return None
            return value
        return None

    async def get_all_user_settings(
        self,
        user_id: UUID,
        category: Optional[str] = None,
        include_encrypted: bool = False,
    ) -> Dict[str, Any]:
        """
        Get all settings for a user as a dictionary.

        Args:
            user_id: User UUID
            category: Optional category filter
            include_encrypted: Whether to include (masked) encrypted values

        Returns:
            Dictionary of key -> value
        """
        settings = await self._repo.get_all_user_settings(user_id, category)

        result = {}
        for s in settings:
            if s.is_encrypted:
                if include_encrypted:
                    result[s.key] = self._encryption.mask_value(s.value)
            else:
                result[s.key] = s.value

        # Add defaults for missing settings
        for key, metadata in SETTING_METADATA.items():
            if key not in result and "default" in metadata:
                if category is None or metadata.get("category") == category:
                    result[key] = metadata["default"]

        return result

    # -------------------------------------------------------------------------
    # Set Settings
    # -------------------------------------------------------------------------

    async def set_global_setting(
        self,
        key: str,
        value: Any,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SettingDTO:
        """
        Set a global setting.

        Args:
            key: Setting key
            value: Setting value
            category: Optional category (inferred from key if not provided)
            description: Optional description

        Returns:
            Created/updated SettingDTO
        """
        # Validate
        self._validate_setting(key, value)

        # Determine category
        metadata = SETTING_METADATA.get(key, {})
        cat = category or metadata.get("category", SettingCategory.ADVANCED)
        desc = description or metadata.get("description")

        # Encrypt if needed
        is_encrypted = key in ENCRYPTED_KEYS
        if is_encrypted and value:
            value = self._encryption.encrypt(str(value))

        return await self._repo.create_or_update_global_setting(
            key=key,
            value=value,
            category=cat,
            description=desc,
            is_encrypted=is_encrypted,
        )

    async def set_project_setting(
        self,
        project_id: UUID,
        key: str,
        value: Any,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SettingDTO:
        """
        Set a project-specific setting.

        Args:
            project_id: Project UUID
            key: Setting key
            value: Setting value
            category: Optional category
            description: Optional description

        Returns:
            Created/updated SettingDTO
        """
        # Validate
        self._validate_setting(key, value)

        # Determine category
        metadata = SETTING_METADATA.get(key, {})
        cat = category or metadata.get("category", SettingCategory.ADVANCED)
        desc = description or metadata.get("description")

        # Encrypt if needed
        is_encrypted = key in ENCRYPTED_KEYS
        if is_encrypted and value:
            value = self._encryption.encrypt(str(value))

        return await self._repo.create_or_update_project_setting(
            project_id=project_id,
            key=key,
            value=value,
            category=cat,
            description=desc,
            is_encrypted=is_encrypted,
        )

    async def set_user_setting(
        self,
        user_id: UUID,
        key: str,
        value: Any,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SettingDTO:
        """
        Set a user-specific setting.

        Args:
            user_id: User UUID
            key: Setting key
            value: Setting value
            category: Optional category
            description: Optional description

        Returns:
            Created/updated SettingDTO
        """
        # Validate
        self._validate_setting(key, value)

        # Determine category
        metadata = SETTING_METADATA.get(key, {})
        cat = category or metadata.get("category", SettingCategory.ADVANCED)
        desc = description or metadata.get("description")

        # Encrypt if needed
        is_encrypted = key in ENCRYPTED_KEYS
        if is_encrypted and value:
            value = self._encryption.encrypt(str(value))

        return await self._repo.create_or_update_user_setting(
            user_id=user_id,
            key=key,
            value=value,
            category=cat,
            description=desc,
            is_encrypted=is_encrypted,
        )

    # -------------------------------------------------------------------------
    # Delete Settings
    # -------------------------------------------------------------------------

    async def delete_global_setting(self, key: str) -> bool:
        """Delete a global setting."""
        return await self._repo.delete_global_setting(key)

    async def delete_project_setting(self, project_id: UUID, key: str) -> bool:
        """Delete a project setting (reverts to global)."""
        return await self._repo.delete_project_setting(project_id, key)

    async def delete_user_setting(self, user_id: UUID, key: str) -> bool:
        """Delete a user setting (reverts to project/global)."""
        return await self._repo.delete_user_setting(user_id, key)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def _validate_setting(self, key: str, value: Any) -> None:
        """
        Validate a setting value.

        Raises:
            ValueError: If validation fails
        """
        metadata = SETTING_METADATA.get(key)
        if not metadata:
            # Unknown key - allow any value
            return

        # Check allowed values
        allowed = metadata.get("allowed_values")
        if allowed and value not in allowed:
            raise ValueError(f"Invalid value for {key}. Allowed: {allowed}")

        # Check numeric range
        min_val = metadata.get("min")
        max_val = metadata.get("max")

        if min_val is not None and value < min_val:
            raise ValueError(f"Value for {key} must be >= {min_val}")

        if max_val is not None and value > max_val:
            raise ValueError(f"Value for {key} must be <= {max_val}")

    # -------------------------------------------------------------------------
    # API Key Validation
    # -------------------------------------------------------------------------

    async def validate_api_key(self, api_key: str, provider: str = "openrouter") -> Dict[str, Any]:
        """
        Validate an API key by making a test request.

        Args:
            api_key: API key to validate
            provider: Provider name (openrouter or openai)

        Returns:
            Validation result with status and message
        """
        if provider == "openrouter":
            return await self._validate_openrouter_key(api_key)
        elif provider == "openai":
            return await self._validate_openai_key(api_key)
        else:
            return {"valid": False, "message": f"Unknown provider: {provider}"}

    async def _validate_openrouter_key(self, api_key: str) -> Dict[str, Any]:
        """Validate OpenRouter API key."""
        # Check format
        if not api_key.startswith("sk-or-"):
            return {
                "valid": False,
                "message": "Invalid OpenRouter key format (should start with sk-or-)",
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/auth/key",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "valid": True,
                        "message": "API key is valid",
                        "data": {
                            "usage": data.get("data", {}).get("usage"),
                            "limit": data.get("data", {}).get("limit"),
                        },
                    }
                else:
                    return {
                        "valid": False,
                        "message": f"Invalid API key (status {response.status_code})",
                    }

        except httpx.TimeoutException:
            return {"valid": False, "message": "Validation timed out"}
        except Exception as e:
            logger.error(f"[SettingsService] API key validation error: {e}")
            return {"valid": False, "message": f"Validation error: {str(e)}"}

    async def _validate_openai_key(self, api_key: str) -> Dict[str, Any]:
        """Validate OpenAI API key."""
        # Check format
        if not api_key.startswith("sk-"):
            return {"valid": False, "message": "Invalid OpenAI key format (should start with sk-)"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return {"valid": True, "message": "API key is valid"}
                else:
                    return {
                        "valid": False,
                        "message": f"Invalid API key (status {response.status_code})",
                    }

        except httpx.TimeoutException:
            return {"valid": False, "message": "Validation timed out"}
        except Exception as e:
            logger.error(f"[SettingsService] API key validation error: {e}")
            return {"valid": False, "message": f"Validation error: {str(e)}"}

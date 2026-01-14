"""
Configuration Service.

Responsible for resolving configuration from multiple sources:
1. Environment variables (system defaults)
2. Database (global and project settings)
3. Request-level overrides

Priority: Request > Project DB > Global DB > Environment Variables
"""

from typing import Any, Dict, Optional
from uuid import UUID

from research_agent.domain.entities.config import (
    CitationFormat,
    EmbeddingConfig,
    GenerationConfig,
    IntentClassificationConfig,
    IntentType,
    LLMConfig,
    LongContextConfig,
    RAGConfig,
    RAGMode,
    RetrievalConfig,
    RetrievalStrategyType,
)
from research_agent.shared.utils.logger import logger


class ConfigurationService:
    """
    Service for resolving RAG configuration.

    Provides synchronous configuration resolution from environment variables.
    For async database configuration, use AsyncConfigurationService.

    Usage:
        config_service = ConfigurationService()
        config = config_service.get_config(project_id=uuid)

        # Or with intent-based tuning
        config = config_service.get_config_for_intent(IntentType.FACTUAL, project_id=uuid)
    """

    def __init__(self):
        """Initialize with environment-based settings."""
        # Lazy import to avoid circular dependency
        from research_agent.config import get_settings

        self._settings = get_settings()

    def get_config(
        self,
        project_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        overrides: Optional[dict] = None,
    ) -> RAGConfig:
        """
        Get resolved RAG configuration (sync - env only).

        For database config, use AsyncConfigurationService.get_config_async().

        Args:
            project_id: Project ID (ignored in sync mode)
            user_id: User ID (ignored in sync mode)
            overrides: Request-level configuration overrides

        Returns:
            Resolved RAGConfig
        """
        # Load from environment
        base_config = self._load_from_env()

        # Apply request-level overrides
        if overrides:
            base_config = self._apply_overrides(base_config, overrides)

        logger.debug(
            f"[ConfigService] Resolved config: mode={base_config.mode}, "
            f"retrieval_strategy={base_config.retrieval.strategy_type}"
        )
        return base_config

    def get_config_for_intent(
        self,
        intent_type: IntentType,
        project_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> RAGConfig:
        """
        Get configuration optimized for a specific intent type.

        Args:
            intent_type: The classified intent type
            project_id: Optional project scope
            user_id: Optional user scope

        Returns:
            RAGConfig tuned for the intent
        """
        # Get base config first
        base_config = self.get_config(project_id=project_id, user_id=user_id)

        # Apply intent-specific optimizations
        optimized = RAGConfig.from_intent(intent_type, base_config)

        logger.info(
            f"[ConfigService] Intent-optimized config: intent={intent_type}, "
            f"top_k={optimized.retrieval.top_k}"
        )
        return optimized

    def _load_from_env(self) -> RAGConfig:
        """Load configuration from environment variables."""
        settings = self._settings

        # Map RAG mode
        rag_mode_map = {
            "traditional": RAGMode.TRADITIONAL,
            "long_context": RAGMode.LONG_CONTEXT,
            "auto": RAGMode.AUTO,
        }
        rag_mode = rag_mode_map.get(settings.rag_mode, RAGMode.TRADITIONAL)

        # Map citation format
        citation_format_map = {
            "inline": CitationFormat.INLINE,
            "structured": CitationFormat.STRUCTURED,
            "both": CitationFormat.BOTH,
        }
        citation_format = citation_format_map.get(settings.citation_format, CitationFormat.BOTH)

        return RAGConfig(
            mode=rag_mode,
            llm=LLMConfig(
                model_name=settings.llm_model,
                api_key=settings.openrouter_api_key or settings.openai_api_key or None,
            ),
            embedding=EmbeddingConfig(
                model_name=settings.embedding_model,
                api_key=settings.openrouter_api_key or settings.openai_api_key or None,
            ),
            retrieval=RetrievalConfig(
                strategy_type=RetrievalStrategyType.VECTOR,
                top_k=settings.retrieval_top_k,
                min_similarity=settings.retrieval_min_similarity,
                use_hybrid_search=False,
            ),
            generation=GenerationConfig(
                citation_format=citation_format,
            ),
            intent_classification=IntentClassificationConfig(
                enabled=settings.intent_classification_enabled,
                cache_enabled=settings.intent_cache_enabled,
            ),
            long_context=LongContextConfig(
                safety_ratio=settings.long_context_safety_ratio,
                min_tokens=settings.long_context_min_tokens,
                enable_citation_grounding=settings.enable_citation_grounding,
            ),
        )

    def _apply_overrides(self, config: RAGConfig, overrides: dict) -> RAGConfig:
        """Apply request-level overrides to config."""
        return self._merge_configs(config, overrides)

    def _merge_configs(self, base: RAGConfig, override: dict) -> RAGConfig:
        """Merge a configuration override into base config."""
        base_dict = base.model_dump()
        merged = self._deep_merge(base_dict, override)
        return RAGConfig(**merged)

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigurationService._deep_merge(result[key], value)
            else:
                result[key] = value

        return result


class AsyncConfigurationService:
    """
    Async configuration service with database support.

    Resolves configuration from both environment and database.
    Priority: Request > User DB > Project DB > Global DB > Environment Variables

    Usage:
        async with get_session() as session:
            service = AsyncConfigurationService(session)
            config = await service.get_config_async(user_id=uuid, project_id=uuid)
    """

    def __init__(self, session):
        """
        Initialize with database session.

        Args:
            session: SQLAlchemy AsyncSession
        """
        from research_agent.config import get_settings
        from research_agent.domain.services.settings_service import SettingsService
        from research_agent.infrastructure.database.repositories.sqlalchemy_settings_repo import (
            SQLAlchemySettingsRepository,
        )

        self._settings = get_settings()
        self._session = session
        self._repo = SQLAlchemySettingsRepository(session)
        self._settings_service = SettingsService(self._repo)

    async def get_config_async(
        self,
        user_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        overrides: Optional[dict] = None,
    ) -> RAGConfig:
        """
        Get resolved RAG configuration from database and environment.

        Priority: Request > User DB > Project DB > Global DB > Environment Variables

        Args:
            user_id: User ID for user-specific config
            project_id: Project ID for project-specific config
            overrides: Request-level configuration overrides

        Returns:
            Resolved RAGConfig
        """
        # Step 1: Load defaults from environment
        base_config = self._load_from_env()

        # Step 2: Load and merge database settings (Global -> Project -> User)
        db_overrides = await self._load_from_db(user_id=user_id, project_id=project_id)
        if db_overrides:
            base_config = self._merge_configs(base_config, db_overrides)

        # Step 3: Apply request-level overrides
        if overrides:
            base_config = self._merge_configs(base_config, overrides)

        logger.debug(
            f"[AsyncConfigService] Resolved config: mode={base_config.mode}, "
            f"retrieval_strategy={base_config.retrieval.strategy_type}"
        )
        return base_config

    async def get_config_for_intent_async(
        self,
        intent_type: IntentType,
        user_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> RAGConfig:
        """
        Get configuration optimized for a specific intent type.

        Args:
            intent_type: The classified intent type
            user_id: Optional user scope
            project_id: Optional project scope

        Returns:
            RAGConfig tuned for the intent
        """
        base_config = await self.get_config_async(user_id=user_id, project_id=project_id)
        optimized = RAGConfig.from_intent(intent_type, base_config)

        logger.info(
            f"[AsyncConfigService] Intent-optimized config: intent={intent_type}, "
            f"top_k={optimized.retrieval.top_k}"
        )
        return optimized

    def _load_from_env(self) -> RAGConfig:
        """Load configuration from environment variables."""
        settings = self._settings

        rag_mode_map = {
            "traditional": RAGMode.TRADITIONAL,
            "long_context": RAGMode.LONG_CONTEXT,
            "auto": RAGMode.AUTO,
        }
        rag_mode = rag_mode_map.get(settings.rag_mode, RAGMode.TRADITIONAL)

        citation_format_map = {
            "inline": CitationFormat.INLINE,
            "structured": CitationFormat.STRUCTURED,
            "both": CitationFormat.BOTH,
        }
        citation_format = citation_format_map.get(settings.citation_format, CitationFormat.BOTH)

        return RAGConfig(
            mode=rag_mode,
            llm=LLMConfig(
                model_name=settings.llm_model,
                api_key=settings.openrouter_api_key or settings.openai_api_key or None,
            ),
            embedding=EmbeddingConfig(
                model_name=settings.embedding_model,
                api_key=settings.openrouter_api_key or settings.openai_api_key or None,
            ),
            retrieval=RetrievalConfig(
                strategy_type=RetrievalStrategyType.VECTOR,
                top_k=settings.retrieval_top_k,
                min_similarity=settings.retrieval_min_similarity,
                use_hybrid_search=False,
            ),
            generation=GenerationConfig(
                citation_format=citation_format,
            ),
            intent_classification=IntentClassificationConfig(
                enabled=settings.intent_classification_enabled,
                cache_enabled=settings.intent_cache_enabled,
            ),
            long_context=LongContextConfig(
                safety_ratio=settings.long_context_safety_ratio,
                min_tokens=settings.long_context_min_tokens,
                enable_citation_grounding=settings.enable_citation_grounding,
            ),
        )

    async def _load_from_db(
        self,
        user_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Load configuration overrides from database.

        Priority: User > Project > Global
        Maps database settings to RAGConfig structure.
        """
        try:
            # Get all effective settings (global + project)
            # NOTE: include_defaults=False to avoid overriding env config with SETTING_METADATA defaults
            settings = await self._settings_service.get_all_settings(
                project_id=project_id,
                include_encrypted=False,  # Don't include masked API keys
                include_defaults=False,  # Don't include SETTING_METADATA defaults
            )

            # Overlay user settings if user_id is provided
            if user_id:
                user_settings = await self._settings_service.get_all_user_settings(
                    user_id=user_id,
                    include_encrypted=False,
                    include_defaults=False,  # Don't include SETTING_METADATA defaults
                )
                settings.update(user_settings)

            # Fetch API keys separately (need decryption)
            # Priority: User > Project > Global > Env
            api_key = await self._settings_service.get_setting(
                "openrouter_api_key",
                user_id=user_id,
                project_id=project_id,
                decrypt=True,
            )

            if not settings and not api_key:
                return None

            # Map flat settings to nested RAGConfig structure
            overrides: Dict[str, Any] = {}

            # LLM config
            if "llm_model" in settings:
                overrides.setdefault("llm", {})["model_name"] = settings["llm_model"]

            # Add API key to LLM config if available from DB
            if api_key:
                overrides.setdefault("llm", {})["api_key"] = api_key
                overrides.setdefault("embedding", {})["api_key"] = (
                    api_key  # Use same key for embedding
                )

            # Embedding config
            if "embedding_model" in settings:
                overrides.setdefault("embedding", {})["model_name"] = settings["embedding_model"]

            # RAG mode
            if "rag_mode" in settings:
                mode_map = {
                    "traditional": RAGMode.TRADITIONAL,
                    "long_context": RAGMode.LONG_CONTEXT,
                    "auto": RAGMode.AUTO,
                }
                overrides["mode"] = mode_map.get(settings["rag_mode"], RAGMode.TRADITIONAL)

            # Retrieval config
            retrieval = {}
            if "retrieval_top_k" in settings:
                retrieval["top_k"] = settings["retrieval_top_k"]
            if "retrieval_min_similarity" in settings:
                retrieval["min_similarity"] = settings["retrieval_min_similarity"]
            if "retrieval_strategy" in settings:
                strategy_map = {
                    "vector": RetrievalStrategyType.VECTOR,
                    "hybrid": RetrievalStrategyType.HYBRID,
                    "hyde": RetrievalStrategyType.HYDE,
                }
                retrieval["strategy_type"] = strategy_map.get(
                    settings["retrieval_strategy"], RetrievalStrategyType.VECTOR
                )
            if "use_hybrid_search" in settings:
                retrieval["use_hybrid_search"] = settings["use_hybrid_search"]
                # Legacy: use_hybrid_search overrides strategy_type to HYBRID
                if settings["use_hybrid_search"] and "strategy_type" not in retrieval:
                    retrieval["strategy_type"] = RetrievalStrategyType.HYBRID
            if retrieval:
                overrides["retrieval"] = retrieval

            # Generation config
            generation = {}
            if "citation_format" in settings:
                format_map = {
                    "inline": CitationFormat.INLINE,
                    "structured": CitationFormat.STRUCTURED,
                    "both": CitationFormat.BOTH,
                }
                generation["citation_format"] = format_map.get(
                    settings["citation_format"], CitationFormat.BOTH
                )
            if generation:
                overrides["generation"] = generation

            # Intent classification
            intent = {}
            if "intent_classification_enabled" in settings:
                intent["enabled"] = settings["intent_classification_enabled"]
            if "intent_cache_enabled" in settings:
                intent["cache_enabled"] = settings["intent_cache_enabled"]
            if intent:
                overrides["intent_classification"] = intent

            return overrides if overrides else None

        except Exception as e:
            logger.warning(f"[AsyncConfigService] Failed to load DB config: {e}")
            return None

    def _merge_configs(self, base: RAGConfig, override: dict) -> RAGConfig:
        """Merge a configuration override into base config."""
        base_dict = base.model_dump()
        merged = self._deep_merge(base_dict, override)
        return RAGConfig(**merged)

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = AsyncConfigurationService._deep_merge(result[key], value)
            else:
                result[key] = value

        return result


# Singleton instance for sync access (env only)
_config_service: Optional[ConfigurationService] = None


def get_config_service() -> ConfigurationService:
    """Get singleton ConfigurationService instance (sync, env only)."""
    global _config_service
    if _config_service is None:
        _config_service = ConfigurationService()
    return _config_service


def get_async_config_service(session) -> AsyncConfigurationService:
    """
    Create AsyncConfigurationService with database session.

    Args:
        session: SQLAlchemy AsyncSession

    Returns:
        AsyncConfigurationService instance
    """
    return AsyncConfigurationService(session)

"""Domain services."""

from research_agent.domain.services.config_service import (
    AsyncConfigurationService,
    ConfigurationService,
    get_async_config_service,
    get_config_service,
)
from research_agent.domain.services.settings_service import (
    SETTING_METADATA,
    SettingCategory,
    SettingsService,
)
from research_agent.domain.services.strategy_factory import (
    StrategyFactory,
    register_default_strategies,
)

__all__ = [
    # Configuration
    "ConfigurationService",
    "AsyncConfigurationService",
    "get_config_service",
    "get_async_config_service",
    # Settings
    "SettingsService",
    "SettingCategory",
    "SETTING_METADATA",
    # Strategy
    "StrategyFactory",
    "register_default_strategies",
]

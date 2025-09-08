"""
Configuration manager.

Loads and manages application configuration from various sources.
"""

import os
import yaml
from typing import Optional, Dict, Any
from pathlib import Path

from .config_models import (
    ApplicationConfig,
    DatabaseConfig,
    AIConfig,
    StorageConfig,
    CacheConfig,
    VectorStoreConfig
)
from ...shared.exceptions.infrastructure_exceptions import ConfigurationError


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, environment: str = None):
        self._environment = environment or os.getenv("ENVIRONMENT", "development")
        self._config: Optional[ApplicationConfig] = None
        self._config_cache: Dict[str, Any] = {}
    
    def load_config(self, config_path: Optional[str] = None) -> ApplicationConfig:
        """Load configuration from file and environment variables."""
        if self._config:
            return self._config
        
        # Default config file paths
        if not config_path:
            config_dir = Path(__file__).parent.parent.parent.parent / "config"
            config_path = config_dir / f"{self._environment}.yaml"
            
            # Fallback to default config if environment-specific doesn't exist
            if not config_path.exists():
                config_path = config_dir / "default.yaml"
        
        # Load from YAML file
        config_data = self._load_from_file(config_path)
        
        # Override with environment variables
        config_data = self._load_from_env(config_data)
        
        # Create configuration objects
        self._config = self._create_config_objects(config_data)
        
        return self._config
    
    def get_config(self) -> ApplicationConfig:
        """Get the current configuration."""
        if not self._config:
            self.load_config()
        return self._config
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        return self.get_config().database
    
    def get_ai_config(self) -> AIConfig:
        """Get AI service configuration."""
        return self.get_config().ai
    
    def get_storage_config(self) -> StorageConfig:
        """Get storage configuration."""
        return self.get_config().storage
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration."""
        return self.get_config().cache
    
    def get_vector_store_config(self) -> VectorStoreConfig:
        """Get vector store configuration."""
        return self.get_config().vector_store
    
    def _load_from_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not config_path.exists():
            # Return minimal default configuration
            return self._get_default_config()
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to load config from {config_path}: {str(e)}")
    
    def _load_from_env(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration with environment variables."""
        env_mappings = {
            "DATABASE_URL": ("database", "url"),
            "OPENAI_API_KEY": ("ai", "api_key"),
            "AI_CHAT_MODEL": ("ai", "chat_model"),
            "AI_EMBEDDING_MODEL": ("ai", "embedding_model"),
            "STORAGE_TYPE": ("storage", "type"),
            "STORAGE_BASE_PATH": ("storage", "base_path"),
            "CACHE_TYPE": ("cache", "type"),
            "CACHE_URL": ("cache", "url"),
            "VECTOR_STORE_TYPE": ("vector_store", "type"),
            "VECTOR_STORE_URL": ("vector_store", "url"),
            "LOG_LEVEL": ("log_level",),
            "DEBUG": ("debug",),
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                self._set_nested_value(config_data, config_path, env_value)
        
        return config_data
    
    def _set_nested_value(self, data: Dict[str, Any], path: tuple, value: str):
        """Set a nested dictionary value using a tuple path."""
        current = data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert string values to appropriate types
        final_key = path[-1]
        if final_key in ["debug"]:
            current[final_key] = value.lower() in ("true", "1", "yes")
        elif final_key in ["pool_size", "max_overflow", "pool_timeout", "pool_recycle", "max_tokens", "timeout", "ttl", "max_size", "dimension"]:
            current[final_key] = int(value)
        elif final_key in ["temperature"]:
            current[final_key] = float(value)
        else:
            current[final_key] = value
    
    def _create_config_objects(self, config_data: Dict[str, Any]) -> ApplicationConfig:
        """Create configuration objects from dictionary data."""
        try:
            # Database config
            db_data = config_data.get("database", {})
            database_config = DatabaseConfig(
                url=db_data.get("url", "sqlite:///./app.db"),
                echo=db_data.get("echo", False),
                pool_size=db_data.get("pool_size", 10),
                max_overflow=db_data.get("max_overflow", 20),
                pool_timeout=db_data.get("pool_timeout", 30),
                pool_recycle=db_data.get("pool_recycle", 3600)
            )
            
            # AI config
            ai_data = config_data.get("ai", {})
            ai_config = AIConfig(
                provider=ai_data.get("provider", "openai"),
                api_key=ai_data.get("api_key"),
                chat_model=ai_data.get("chat_model", "gpt-3.5-turbo"),
                embedding_model=ai_data.get("embedding_model", "text-embedding-ada-002"),
                max_tokens=ai_data.get("max_tokens", 1000),
                temperature=ai_data.get("temperature", 0.7),
                timeout=ai_data.get("timeout", 30)
            )
            
            # Storage config
            storage_data = config_data.get("storage", {})
            storage_config = StorageConfig(
                type=storage_data.get("type", "local"),
                base_path=storage_data.get("base_path"),
                bucket=storage_data.get("bucket"),
                endpoint=storage_data.get("endpoint"),
                access_key=storage_data.get("access_key"),
                secret_key=storage_data.get("secret_key"),
                secure=storage_data.get("secure", True)
            )
            
            # Cache config
            cache_data = config_data.get("cache", {})
            cache_config = CacheConfig(
                type=cache_data.get("type", "memory"),
                url=cache_data.get("url"),
                ttl=cache_data.get("ttl", 3600),
                max_size=cache_data.get("max_size", 1000)
            )
            
            # Vector store config
            vector_data = config_data.get("vector_store", {})
            vector_config = VectorStoreConfig(
                type=vector_data.get("type", "memory"),
                url=vector_data.get("url"),
                api_key=vector_data.get("api_key"),
                collection_name=vector_data.get("collection_name", "documents"),
                dimension=vector_data.get("dimension", 1536)
            )
            
            # Main application config
            return ApplicationConfig(
                environment=config_data.get("environment", self._environment),
                debug=config_data.get("debug", False),
                log_level=config_data.get("log_level", "INFO"),
                database=database_config,
                ai=ai_config,
                storage=storage_config,
                cache=cache_config,
                vector_store=vector_config,
                settings=config_data.get("settings", {})
            )
            
        except Exception as e:
            raise ConfigurationError(f"Failed to create configuration objects: {str(e)}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for development."""
        return {
            "environment": self._environment,
            "debug": True if self._environment == "development" else False,
            "log_level": "DEBUG" if self._environment == "development" else "INFO",
            "database": {
                "url": "sqlite:///./app.db"
            },
            "ai": {
                "provider": "openai",
                "chat_model": "gpt-3.5-turbo",
                "embedding_model": "text-embedding-ada-002"
            },
            "storage": {
                "type": "local",
                "base_path": "./storage"
            },
            "cache": {
                "type": "memory"
            },
            "vector_store": {
                "type": "memory"
            }
        }


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> ApplicationConfig:
    """Get the current application configuration."""
    return get_config_manager().get_config()
"""
Storage configuration management for multi-cloud support.

This module provides configuration utilities for setting up
different storage providers and managing storage policies.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from .interfaces import StorageProvider, ProviderConfig, StorageCredentials
from .factory import StorageFactory, MultiStorageManager

logger = logging.getLogger(__name__)


@dataclass
class StoragePolicy:
    """Storage policy configuration."""
    primary_provider: str
    fallback_providers: List[str] = None
    replication_enabled: bool = False
    backup_enabled: bool = False
    auto_failover: bool = True
    health_check_interval: int = 300  # seconds
    retention_days: int = 30


class StorageConfigManager:
    """
    Manager for storage configuration and provider setup.
    
    Handles loading configuration from various sources and
    setting up storage instances with proper policies.
    """
    
    def __init__(self):
        self.storage_manager = MultiStorageManager()
        self.policies = {}
        self._configs = {}
    
    def load_from_dict(self, config: Dict[str, Any]) -> MultiStorageManager:
        """
        Load storage configuration from dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configured storage manager
        """
        # Load individual provider configurations
        providers = config.get('providers', {})
        
        for name, provider_config in providers.items():
            try:
                storage = StorageFactory.create_from_dict(provider_config)
                is_primary = provider_config.get('is_primary', False)
                self.storage_manager.add_storage(name, storage, is_primary)
                self._configs[name] = provider_config
                logger.info(f"Loaded storage provider: {name} (primary: {is_primary})")
            except Exception as e:
                logger.error(f"Failed to load storage provider {name}: {e}")
                continue
        
        # Load policies
        policy_config = config.get('policy', {})
        if policy_config:
            self.policies['default'] = StoragePolicy(**policy_config)
            
            # Set fallback order if specified
            if policy_config.get('fallback_providers'):
                self.storage_manager.set_fallback_order(policy_config['fallback_providers'])
        
        return self.storage_manager
    
    def load_from_file(self, config_file: str) -> MultiStorageManager:
        """
        Load storage configuration from file.
        
        Args:
            config_file: Path to configuration file (JSON or YAML)
            
        Returns:
            Configured storage manager
        """
        import json
        import yaml
        from pathlib import Path
        
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            return self.load_from_dict(config)
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
            raise
    
    def load_from_env(self) -> MultiStorageManager:
        """
        Load storage configuration from environment variables.
        
        Environment variable patterns:
        - STORAGE_PROVIDER: Default provider (minio, aws_s3, etc.)
        - STORAGE_{PROVIDER}_ENDPOINT: Provider endpoint
        - STORAGE_{PROVIDER}_ACCESS_KEY: Provider access key
        - STORAGE_{PROVIDER}_SECRET_KEY: Provider secret key
        - STORAGE_{PROVIDER}_REGION: Provider region
        - STORAGE_{PROVIDER}_BUCKET: Default bucket
        - STORAGE_PRIMARY: Primary provider name
        - STORAGE_FALLBACK: Comma-separated fallback provider names
        
        Also supports legacy MINIO_* environment variables for compatibility:
        - MINIO_ENDPOINT: MinIO server endpoint (automatically adds http:// if missing)
        - MINIO_ACCESS_KEY: MinIO access key
        - MINIO_SECRET_KEY: MinIO secret key
        - MINIO_REGION: MinIO region
        - MINIO_BUCKET: Default MinIO bucket
        - MINIO_SECURE: Whether to use HTTPS (true/false)
        
        Returns:
            Configured storage manager
        """
        # Get primary provider
        primary_provider = os.getenv('STORAGE_PRIMARY', os.getenv('STORAGE_PROVIDER', 'minio'))
        
        # Define provider configurations from env
        provider_configs = {}
        
        # MinIO configuration with enhanced fallback support
        if os.getenv('STORAGE_MINIO_ENDPOINT') or os.getenv('MINIO_ENDPOINT') or primary_provider == 'minio':
            # Build endpoint URL with proper protocol handling
            endpoint = (
                os.getenv('STORAGE_MINIO_ENDPOINT') or 
                os.getenv('STORAGE_ENDPOINT') or 
                os.getenv('MINIO_ENDPOINT') or 
                'localhost:9000'
            )
            
            # Ensure endpoint has protocol
            if not endpoint.startswith(('http://', 'https://')):
                # Determine if we should use HTTPS
                is_secure = (
                    os.getenv('STORAGE_MINIO_SECURE', '').lower() == 'true' or
                    os.getenv('MINIO_SECURE', 'false').lower() == 'true' or
                    endpoint.startswith('minio.') or  # Assume cloud MinIO uses HTTPS
                    ':443' in endpoint  # Standard HTTPS port
                )
                protocol = 'https' if is_secure else 'http'
                endpoint = f"{protocol}://{endpoint}"
            
            provider_configs['minio'] = {
                'provider': 'minio',
                'credentials': {
                    'access_key': (
                        os.getenv('STORAGE_MINIO_ACCESS_KEY') or 
                        os.getenv('STORAGE_ACCESS_KEY') or 
                        os.getenv('MINIO_ACCESS_KEY') or 
                        'minioadmin'
                    ),
                    'secret_key': (
                        os.getenv('STORAGE_MINIO_SECRET_KEY') or 
                        os.getenv('STORAGE_SECRET_KEY') or 
                        os.getenv('MINIO_SECRET_KEY') or 
                        'minioadmin'
                    ),
                    'endpoint_url': endpoint,
                    'region': (
                        os.getenv('STORAGE_MINIO_REGION') or 
                        os.getenv('STORAGE_REGION') or 
                        os.getenv('MINIO_REGION') or 
                        'us-east-1'
                    )
                },
                'default_bucket': (
                    os.getenv('STORAGE_MINIO_BUCKET') or 
                    os.getenv('STORAGE_BUCKET') or 
                    os.getenv('MINIO_BUCKET') or 
                    'uploads'
                ),
                'is_primary': primary_provider == 'minio',
                'minio_settings': {
                    'secure': endpoint.startswith('https://')
                }
            }
        
        # AWS S3 configuration
        if os.getenv('STORAGE_AWS_ACCESS_KEY') or primary_provider == 'aws_s3':
            provider_configs['aws_s3'] = {
                'provider': 'aws_s3',
                'credentials': {
                    'access_key': os.getenv('STORAGE_AWS_ACCESS_KEY'),
                    'secret_key': os.getenv('STORAGE_AWS_SECRET_KEY'),
                    'region': os.getenv('STORAGE_AWS_REGION', 'us-east-1')
                },
                'default_bucket': os.getenv('STORAGE_AWS_BUCKET', 'default'),
                'is_primary': primary_provider == 'aws_s3',
                'encryption_enabled': os.getenv('STORAGE_AWS_ENCRYPTION', 'false').lower() == 'true',
                'versioning_enabled': os.getenv('STORAGE_AWS_VERSIONING', 'false').lower() == 'true'
            }
        
        # Google Cloud Storage configuration
        if os.getenv('STORAGE_GCP_KEY_FILE') or primary_provider == 'google_cloud':
            provider_configs['google_cloud'] = {
                'provider': 'google_cloud',
                'credentials': {
                    'key_file_path': os.getenv('STORAGE_GCP_KEY_FILE')
                },
                'default_bucket': os.getenv('STORAGE_GCP_BUCKET', 'default'),
                'is_primary': primary_provider == 'google_cloud'
            }
        
        # Alibaba OSS configuration
        if os.getenv('STORAGE_OSS_ACCESS_KEY') or primary_provider == 'alibaba_oss':
            provider_configs['alibaba_oss'] = {
                'provider': 'alibaba_oss',
                'credentials': {
                    'access_key': os.getenv('STORAGE_OSS_ACCESS_KEY'),
                    'secret_key': os.getenv('STORAGE_OSS_SECRET_KEY'),
                    'region': os.getenv('STORAGE_OSS_REGION', 'oss-cn-hangzhou'),
                    'endpoint_url': os.getenv('STORAGE_OSS_ENDPOINT')
                },
                'default_bucket': os.getenv('STORAGE_OSS_BUCKET', 'default'),
                'is_primary': primary_provider == 'alibaba_oss'
            }
        
        # Create configuration
        config = {
            'providers': provider_configs,
            'policy': {
                'primary_provider': primary_provider,
                'fallback_providers': os.getenv('STORAGE_FALLBACK', '').split(',') if os.getenv('STORAGE_FALLBACK') else [],
                'auto_failover': os.getenv('STORAGE_AUTO_FAILOVER', 'true').lower() == 'true',
                'replication_enabled': os.getenv('STORAGE_REPLICATION', 'false').lower() == 'true'
            }
        }
        
        return self.load_from_dict(config)
    
    def create_config_template(self) -> Dict[str, Any]:
        """
        Create a configuration template with all supported providers.
        
        Returns:
            Configuration template dictionary
        """
        return {
            "providers": {
                "minio": {
                    "provider": "minio",
                    "credentials": {
                        "access_key": "minioadmin",
                        "secret_key": "minioadmin",
                        "endpoint_url": "http://localhost:9000",
                        "region": "us-east-1"
                    },
                    "default_bucket": "uploads",
                    "is_primary": True,
                    "encryption_enabled": False,
                    "versioning_enabled": False,
                    "minio_settings": {
                        "secure": False
                    }
                },
                "aws_s3": {
                    "provider": "aws_s3",
                    "credentials": {
                        "access_key": "your-aws-access-key",
                        "secret_key": "your-aws-secret-key",
                        "region": "us-east-1"
                    },
                    "default_bucket": "your-s3-bucket",
                    "is_primary": False,
                    "encryption_enabled": True,
                    "versioning_enabled": True,
                    "aws_settings": {
                        "storage_class": "STANDARD_IA"
                    }
                },
                "google_cloud": {
                    "provider": "google_cloud",
                    "credentials": {
                        "key_file_path": "/path/to/service-account.json"
                    },
                    "default_bucket": "your-gcs-bucket",
                    "is_primary": False,
                    "encryption_enabled": True,
                    "gcp_settings": {
                        "kms_key_name": "projects/your-project/locations/global/keyRings/your-ring/cryptoKeys/your-key"
                    }
                },
                "alibaba_oss": {
                    "provider": "alibaba_oss",
                    "credentials": {
                        "access_key": "your-oss-access-key",
                        "secret_key": "your-oss-secret-key",
                        "region": "oss-cn-hangzhou",
                        "endpoint_url": "https://oss-cn-hangzhou.aliyuncs.com"
                    },
                    "default_bucket": "your-oss-bucket",
                    "is_primary": False,
                    "alibaba_settings": {
                        "storage_class": "IA"
                    }
                }
            },
            "policy": {
                "primary_provider": "minio",
                "fallback_providers": ["aws_s3", "google_cloud"],
                "auto_failover": True,
                "replication_enabled": False,
                "backup_enabled": True,
                "health_check_interval": 300,
                "retention_days": 30
            }
        }
    
    def save_config_template(self, output_file: str, format_type: str = 'yaml'):
        """
        Save configuration template to file.
        
        Args:
            output_file: Output file path
            format_type: File format ('yaml' or 'json')
        """
        template = self.create_config_template()
        
        with open(output_file, 'w') as f:
            if format_type.lower() == 'yaml':
                import yaml
                yaml.dump(template, f, default_flow_style=False, indent=2)
            else:
                import json
                json.dump(template, f, indent=2)
        
        logger.info(f"Configuration template saved to: {output_file}")
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate storage configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check providers section
        if 'providers' not in config:
            errors.append("Missing 'providers' section")
            return errors
        
        providers = config['providers']
        if not providers:
            errors.append("No providers configured")
            return errors
        
        # Check each provider
        primary_count = 0
        for name, provider_config in providers.items():
            if 'provider' not in provider_config:
                errors.append(f"Provider '{name}' missing 'provider' field")
                continue
            
            try:
                provider_type = StorageProvider(provider_config['provider'])
            except ValueError:
                errors.append(f"Invalid provider type for '{name}': {provider_config['provider']}")
                continue
            
            if provider_config.get('is_primary', False):
                primary_count += 1
            
            # Check credentials
            credentials = provider_config.get('credentials', {})
            if provider_type in [StorageProvider.MINIO, StorageProvider.AWS_S3, StorageProvider.ALIBABA_OSS]:
                if not credentials.get('access_key'):
                    errors.append(f"Provider '{name}' missing access_key")
                if not credentials.get('secret_key'):
                    errors.append(f"Provider '{name}' missing secret_key")
            elif provider_type == StorageProvider.GOOGLE_CLOUD:
                if not credentials.get('key_file_path'):
                    errors.append(f"Provider '{name}' missing key_file_path")
        
        # Check primary provider count
        if primary_count == 0:
            errors.append("No primary provider configured")
        elif primary_count > 1:
            errors.append("Multiple primary providers configured")
        
        return errors


def get_storage_manager() -> MultiStorageManager:
    """
    Get a configured storage manager instance.
    
    Tries to load configuration from various sources in order:
    1. Environment variables (both STORAGE_* and legacy MINIO_* variables)
    2. Configuration file (storage.yaml or storage.json)
    3. Default MinIO configuration with environment fallbacks
    
    Returns:
        Configured storage manager
    """
    config_manager = StorageConfigManager()
    
    # Try environment variables first
    try:
        storage_manager = config_manager.load_from_env()
        logger.info("Successfully loaded storage configuration from environment variables")
        return storage_manager
    except Exception as e:
        logger.warning(f"Failed to load from environment: {e}")
    
    # Try configuration files
    for config_file in ['storage.yaml', 'storage.yml', 'storage.json']:
        try:
            storage_manager = config_manager.load_from_file(config_file)
            logger.info(f"Successfully loaded storage configuration from {config_file}")
            return storage_manager
        except FileNotFoundError:
            logger.debug(f"Configuration file not found: {config_file}")
            continue
        except Exception as e:
            logger.warning(f"Failed to load from {config_file}: {e}")
            continue
    
    # Fall back to default MinIO configuration
    logger.info("Using default MinIO storage configuration")
    
    # Try to detect existing MinIO configuration from legacy env vars
    endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    if not endpoint.startswith(('http://', 'https://')):
        endpoint = f"http://{endpoint}"
    
    default_config = {
        'providers': {
            'minio': {
                'provider': 'minio',
                'credentials': {
                    'access_key': os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
                    'secret_key': os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
                    'endpoint_url': endpoint,
                    'region': os.getenv('MINIO_REGION', 'us-east-1')
                },
                'default_bucket': os.getenv('MINIO_BUCKET', 'uploads'),
                'is_primary': True,
                'minio_settings': {'secure': endpoint.startswith('https://')}
            }
        }
    }
    
    try:
        storage_manager = config_manager.load_from_dict(default_config)
        logger.info(f"Successfully created default storage configuration with endpoint: {endpoint}")
        return storage_manager
    except Exception as e:
        logger.error(f"Failed to create default storage configuration: {e}")
        raise RuntimeError(f"Unable to initialize storage: {e}")
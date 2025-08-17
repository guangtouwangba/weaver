"""
Storage provider factory and management.

This module provides factory methods to create storage providers
based on configuration and manages multiple storage instances.
"""

import logging
from typing import Dict, Any, Optional, Type
from enum import Enum

from .interfaces import IObjectStorage, StorageProvider, ProviderConfig, StorageCredentials
from .providers.minio import MinIOStorage
from .providers.aws_s3 import AWSS3Storage
from .providers.alibaba_oss import AlibabaOSSStorage  
from .providers.google_cloud import GoogleCloudStorage

logger = logging.getLogger(__name__)


class StorageFactory:
    """
    Factory for creating storage provider instances.
    
    Supports multiple cloud providers and local storage options.
    """
    
    # Registry of available storage providers
    _providers: Dict[StorageProvider, Type[IObjectStorage]] = {
        StorageProvider.MINIO: MinIOStorage,
        StorageProvider.AWS_S3: AWSS3Storage,
        StorageProvider.ALIBABA_OSS: AlibabaOSSStorage,
        StorageProvider.GOOGLE_CLOUD: GoogleCloudStorage,
    }
    
    @classmethod
    def create_storage(cls, config: ProviderConfig) -> IObjectStorage:
        """
        Create a storage provider instance based on configuration.
        
        Args:
            config: Provider configuration
            
        Returns:
            Storage provider instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider_class = cls._providers.get(config.provider)
        if not provider_class:
            raise ValueError(f"Unsupported storage provider: {config.provider}")
        
        try:
            storage = provider_class(config)
            logger.info(f"Created {config.provider.value} storage instance")
            return storage
        except Exception as e:
            logger.error(f"Failed to create {config.provider.value} storage: {e}")
            raise
    
    @classmethod
    def create_from_dict(cls, config_dict: Dict[str, Any]) -> IObjectStorage:
        """
        Create storage provider from dictionary configuration.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Storage provider instance
        """
        # Parse provider
        provider_str = config_dict.get('provider')
        if not provider_str:
            raise ValueError("Storage provider not specified")
        
        try:
            provider = StorageProvider(provider_str)
        except ValueError:
            raise ValueError(f"Unknown storage provider: {provider_str}")
        
        # Parse credentials
        creds_dict = config_dict.get('credentials', {})
        credentials = StorageCredentials(
            provider=provider,
            access_key=creds_dict.get('access_key'),
            secret_key=creds_dict.get('secret_key'),
            region=creds_dict.get('region'),
            endpoint_url=creds_dict.get('endpoint_url'),
            token=creds_dict.get('token'),
            key_file_path=creds_dict.get('key_file_path'),
            bucket_name=creds_dict.get('bucket_name'),
            additional_config=creds_dict.get('additional_config', {})
        )
        
        # Create provider config
        config = ProviderConfig(
            provider=provider,
            credentials=credentials,
            default_bucket=config_dict.get('default_bucket', 'default'),
            region=config_dict.get('region'),
            encryption_enabled=config_dict.get('encryption_enabled', False),
            versioning_enabled=config_dict.get('versioning_enabled', False),
            multipart_threshold=config_dict.get('multipart_threshold', 64 * 1024 * 1024),
            max_concurrency=config_dict.get('max_concurrency', 10),
            connect_timeout=config_dict.get('connect_timeout', 60),
            read_timeout=config_dict.get('read_timeout', 300),
            retry_attempts=config_dict.get('retry_attempts', 3),
            aws_settings=config_dict.get('aws_settings', {}),
            gcp_settings=config_dict.get('gcp_settings', {}),
            alibaba_settings=config_dict.get('alibaba_settings', {}),
            azure_settings=config_dict.get('azure_settings', {}),
            minio_settings=config_dict.get('minio_settings', {})
        )
        
        return cls.create_storage(config)
    
    @classmethod
    def register_provider(cls, provider: StorageProvider, provider_class: Type[IObjectStorage]):
        """
        Register a new storage provider.
        
        Args:
            provider: Provider enum value
            provider_class: Provider implementation class
        """
        cls._providers[provider] = provider_class
        logger.info(f"Registered storage provider: {provider.value}")
    
    @classmethod
    def get_supported_providers(cls) -> list[StorageProvider]:
        """Get list of supported storage providers."""
        return list(cls._providers.keys())


class MultiStorageManager:
    """
    Manager for handling multiple storage providers.
    
    Supports primary/secondary storage configurations, load balancing,
    and failover scenarios.
    """
    
    def __init__(self):
        self._storage_instances: Dict[str, IObjectStorage] = {}
        self._primary_storage: Optional[str] = None
        self._fallback_order: list[str] = []
    
    def add_storage(self, name: str, storage: IObjectStorage, is_primary: bool = False):
        """
        Add a storage provider instance.
        
        Args:
            name: Unique name for the storage instance
            storage: Storage provider instance
            is_primary: Whether this is the primary storage
        """
        self._storage_instances[name] = storage
        
        if is_primary:
            self._primary_storage = name
        
        logger.info(f"Added storage instance: {name} (primary: {is_primary})")
    
    def add_storage_from_config(self, name: str, config: ProviderConfig, is_primary: bool = False):
        """
        Add storage from configuration.
        
        Args:
            name: Unique name for the storage instance
            config: Provider configuration
            is_primary: Whether this is the primary storage
        """
        storage = StorageFactory.create_storage(config)
        self.add_storage(name, storage, is_primary)
    
    def set_fallback_order(self, order: list[str]):
        """
        Set the fallback order for storage instances.
        
        Args:
            order: List of storage names in fallback order
        """
        # Validate all names exist
        for name in order:
            if name not in self._storage_instances:
                raise ValueError(f"Storage instance '{name}' not found")
        
        self._fallback_order = order
        logger.info(f"Set fallback order: {order}")
    
    def get_storage(self, name: Optional[str] = None) -> Optional[IObjectStorage]:
        """
        Get a storage instance by name.
        
        Args:
            name: Storage instance name (uses primary if None)
            
        Returns:
            Storage instance or None if not found
        """
        if name is None:
            name = self._primary_storage
        
        return self._storage_instances.get(name)
    
    def get_primary_storage(self) -> Optional[IObjectStorage]:
        """Get the primary storage instance."""
        if self._primary_storage:
            return self._storage_instances.get(self._primary_storage)
        return None
    
    async def upload_with_fallback(self, bucket: str, key: str, data, options=None) -> tuple[IObjectStorage, Any]:
        """
        Upload to storage with automatic fallback.
        
        Args:
            bucket: Bucket name
            key: Object key
            data: Data to upload
            options: Upload options
            
        Returns:
            Tuple of (successful_storage, result)
            
        Raises:
            Exception: If all storage instances fail
        """
        storage_order = self._get_storage_order()
        last_error = None
        
        for storage_name in storage_order:
            storage = self._storage_instances[storage_name]
            try:
                result = await storage.upload_object(bucket, key, data, options)
                logger.info(f"Successfully uploaded {key} to {storage_name}")
                return storage, result
            except Exception as e:
                logger.warning(f"Upload failed for {storage_name}: {e}")
                last_error = e
                continue
        
        # All storages failed
        raise Exception(f"Upload failed for all storage instances. Last error: {last_error}")
    
    async def download_with_fallback(self, bucket: str, key: str, options=None) -> tuple[IObjectStorage, Any]:
        """
        Download from storage with automatic fallback.
        
        Args:
            bucket: Bucket name
            key: Object key
            options: Download options
            
        Returns:
            Tuple of (successful_storage, result)
            
        Raises:
            Exception: If all storage instances fail
        """
        storage_order = self._get_storage_order()
        last_error = None
        
        for storage_name in storage_order:
            storage = self._storage_instances[storage_name]
            try:
                result = await storage.download_object(bucket, key, options)
                if result is not None:  # Success
                    logger.info(f"Successfully downloaded {key} from {storage_name}")
                    return storage, result
            except Exception as e:
                logger.warning(f"Download failed for {storage_name}: {e}")
                last_error = e
                continue
        
        # All storages failed
        raise Exception(f"Download failed for all storage instances. Last error: {last_error}")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all storage instances.
        
        Returns:
            Dictionary mapping storage names to health status
        """
        results = {}
        
        for name, storage in self._storage_instances.items():
            try:
                is_healthy = await storage.health_check()
                results[name] = is_healthy
                logger.debug(f"Health check for {name}: {'OK' if is_healthy else 'FAILED'}")
            except Exception as e:
                logger.error(f"Health check error for {name}: {e}")
                results[name] = False
        
        return results
    
    def _get_storage_order(self) -> list[str]:
        """Get the order of storage instances to try."""
        if self._fallback_order:
            return self._fallback_order
        elif self._primary_storage:
            return [self._primary_storage] + [
                name for name in self._storage_instances.keys()
                if name != self._primary_storage
            ]
        else:
            return list(self._storage_instances.keys())
    
    def list_storages(self) -> Dict[str, str]:
        """
        List all configured storage instances.
        
        Returns:
            Dictionary mapping storage names to provider types
        """
        return {
            name: storage.provider.value
            for name, storage in self._storage_instances.items()
        }
    
    def remove_storage(self, name: str) -> bool:
        """
        Remove a storage instance.
        
        Args:
            name: Storage instance name
            
        Returns:
            True if removed, False if not found
        """
        if name in self._storage_instances:
            del self._storage_instances[name]
            
            # Update primary if it was removed
            if self._primary_storage == name:
                self._primary_storage = None
            
            # Remove from fallback order
            if name in self._fallback_order:
                self._fallback_order.remove(name)
            
            logger.info(f"Removed storage instance: {name}")
            return True
        
        return False


def create_storage_from_env() -> IObjectStorage:
    """
    Create storage instance from environment variables.
    
    Environment variables (priority order):
    - STORAGE_PROVIDER: Provider type (minio, aws_s3, google_cloud, alibaba_oss)
    - STORAGE_ENDPOINT: Endpoint URL (for MinIO/S3-compatible)
    - STORAGE_ACCESS_KEY: Access key
    - STORAGE_SECRET_KEY: Secret key
    - STORAGE_REGION: Region
    - STORAGE_BUCKET: Default bucket
    - STORAGE_SECURE: Use HTTPS (true/false)
    
    Legacy MinIO environment variables (fallback):
    - MINIO_ENDPOINT: MinIO server endpoint
    - MINIO_ACCESS_KEY: MinIO access key
    - MINIO_SECRET_KEY: MinIO secret key
    - MINIO_REGION: MinIO region
    - MINIO_BUCKET: Default MinIO bucket
    - MINIO_SECURE: Whether to use HTTPS
    
    Returns:
        Storage provider instance
    """
    import os
    
    provider_str = os.getenv('STORAGE_PROVIDER', 'minio')
    try:
        provider = StorageProvider(provider_str)
    except ValueError:
        raise ValueError(f"Invalid storage provider in environment: {provider_str}")
    
    # Enhanced environment variable fallback for MinIO
    if provider == StorageProvider.MINIO:
        # Build endpoint URL with proper protocol handling
        endpoint = (
            os.getenv('STORAGE_ENDPOINT') or 
            os.getenv('MINIO_ENDPOINT') or 
            'localhost:9000'
        )
        
        # Ensure endpoint has protocol
        if not endpoint.startswith(('http://', 'https://')):
            # Determine if we should use HTTPS
            is_secure = (
                os.getenv('STORAGE_SECURE', '').lower() == 'true' or
                os.getenv('MINIO_SECURE', 'false').lower() == 'true' or
                endpoint.startswith('minio.') or  # Assume cloud MinIO uses HTTPS
                ':443' in endpoint  # Standard HTTPS port
            )
            protocol = 'https' if is_secure else 'http'
            endpoint = f"{protocol}://{endpoint}"
        
        credentials = StorageCredentials(
            provider=provider,
            access_key=(
                os.getenv('STORAGE_ACCESS_KEY') or 
                os.getenv('MINIO_ACCESS_KEY') or 
                'minioadmin'
            ),
            secret_key=(
                os.getenv('STORAGE_SECRET_KEY') or 
                os.getenv('MINIO_SECRET_KEY') or 
                'minioadmin'
            ),
            region=(
                os.getenv('STORAGE_REGION') or 
                os.getenv('MINIO_REGION') or 
                'us-east-1'
            ),
            endpoint_url=endpoint,
            token=os.getenv('STORAGE_TOKEN'),
            key_file_path=os.getenv('STORAGE_KEY_FILE')
        )
        
        minio_settings = {
            'secure': endpoint.startswith('https://')
        }
    else:
        # Non-MinIO providers use standard env vars
        credentials = StorageCredentials(
            provider=provider,
            access_key=os.getenv('STORAGE_ACCESS_KEY'),
            secret_key=os.getenv('STORAGE_SECRET_KEY'),
            region=os.getenv('STORAGE_REGION'),
            endpoint_url=os.getenv('STORAGE_ENDPOINT'),
            token=os.getenv('STORAGE_TOKEN'),
            key_file_path=os.getenv('STORAGE_KEY_FILE')
        )
        minio_settings = {}
    
    config = ProviderConfig(
        provider=provider,
        credentials=credentials,
        default_bucket=(
            os.getenv('STORAGE_BUCKET') or 
            os.getenv('MINIO_BUCKET') or 
            'uploads'
        ),
        region=credentials.region,
        encryption_enabled=os.getenv('STORAGE_ENCRYPTION', 'false').lower() == 'true',
        versioning_enabled=os.getenv('STORAGE_VERSIONING', 'false').lower() == 'true',
        minio_settings=minio_settings
    )
    
    return StorageFactory.create_storage(config)


def get_primary_storage() -> IObjectStorage:
    """
    Get the primary storage instance using configuration manager.
    
    Returns:
        Primary storage provider instance
    """
    from .storage_config import get_storage_manager
    
    storage_manager = get_storage_manager()
    primary = storage_manager.get_primary_storage()
    
    if not primary:
        # Fallback to environment-based storage
        return create_storage_from_env()
    
    return primary


# Pre-configured storage instances for common scenarios
def create_minio_storage(
    endpoint: str = "localhost:9000",
    access_key: str = "minioadmin",
    secret_key: str = "minioadmin",
    secure: bool = False,
    bucket: str = "default"
) -> IObjectStorage:
    """Create a MinIO storage instance with default configuration."""
    credentials = StorageCredentials(
        provider=StorageProvider.MINIO,
        access_key=access_key,
        secret_key=secret_key,
        endpoint_url=f"{'https' if secure else 'http'}://{endpoint}"
    )
    
    config = ProviderConfig(
        provider=StorageProvider.MINIO,
        credentials=credentials,
        default_bucket=bucket,
        minio_settings={'secure': secure}
    )
    
    return StorageFactory.create_storage(config)


def create_aws_s3_storage(
    access_key: str,
    secret_key: str,
    region: str = "us-east-1",
    bucket: str = "default"
) -> IObjectStorage:
    """Create an AWS S3 storage instance."""
    credentials = StorageCredentials(
        provider=StorageProvider.AWS_S3,
        access_key=access_key,
        secret_key=secret_key,
        region=region
    )
    
    config = ProviderConfig(
        provider=StorageProvider.AWS_S3,
        credentials=credentials,
        default_bucket=bucket,
        region=region
    )
    
    return StorageFactory.create_storage(config)


def create_alibaba_oss_storage(
    access_key: str,
    secret_key: str,
    region: str = "oss-cn-hangzhou",
    bucket: str = "default"
) -> IObjectStorage:
    """Create an Alibaba Cloud OSS storage instance."""
    credentials = StorageCredentials(
        provider=StorageProvider.ALIBABA_OSS,
        access_key=access_key,
        secret_key=secret_key,
        region=region
    )
    
    config = ProviderConfig(
        provider=StorageProvider.ALIBABA_OSS,
        credentials=credentials,
        default_bucket=bucket,
        region=region
    )
    
    return StorageFactory.create_storage(config)


def create_google_cloud_storage(
    key_file_path: str,
    bucket: str = "default"
) -> IObjectStorage:
    """Create a Google Cloud Storage instance."""
    credentials = StorageCredentials(
        provider=StorageProvider.GOOGLE_CLOUD,
        key_file_path=key_file_path
    )
    
    config = ProviderConfig(
        provider=StorageProvider.GOOGLE_CLOUD,
        credentials=credentials,
        default_bucket=bucket
    )
    
    return StorageFactory.create_storage(config)
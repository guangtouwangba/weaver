"""
MinIO storage provider implementation.

This module provides integration with MinIO object storage,
supporting S3-compatible operations through the unified storage interface.
"""

import logging
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
from minio import Minio
from minio.error import S3Error, InvalidResponseError
import io

from ..interfaces import (
    IObjectStorage, StorageProvider, StorageObject, StorageMetadata,
    UploadOptions, DownloadOptions, ListOptions, AccessLevel,
    detect_content_type, ProviderConfig
)

logger = logging.getLogger(__name__)


class MinIOStorage(IObjectStorage):
    """
    MinIO implementation of the object storage interface.
    
    Provides full S3-compatible object storage capabilities with
    MinIO-specific optimizations and features.
    """
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize MinIO storage client.
        
        Args:
            config: Provider configuration with MinIO credentials and settings
        """
        if config.provider != StorageProvider.MINIO:
            raise ValueError(f"Invalid provider: {config.provider}. Expected MINIO")
        
        self.config = config
        self.client = None
        self._initialized = False
        
    async def _ensure_initialized(self):
        """Ensure the MinIO client is initialized."""
        if not self._initialized:
            await self._initialize_client()
    
    async def _initialize_client(self):
        """Initialize the MinIO client."""
        try:
            # Extract connection details
            endpoint = self.config.credentials.endpoint_url
            if not endpoint:
                raise ValueError(
                    "MinIO endpoint URL is required. Please set one of:\n"
                    "- MINIO_ENDPOINT (e.g., 'localhost:9000')\n"
                    "- STORAGE_ENDPOINT (e.g., 'http://localhost:9000')\n"
                    "- STORAGE_MINIO_ENDPOINT\n"
                    "- Or configure via storage.yaml file"
                )
            
            # Validate access credentials
            if not self.config.credentials.access_key:
                raise ValueError(
                    "MinIO access key is required. Please set one of:\n"
                    "- MINIO_ACCESS_KEY\n"
                    "- STORAGE_ACCESS_KEY\n"
                    "- STORAGE_MINIO_ACCESS_KEY"
                )
            
            if not self.config.credentials.secret_key:
                raise ValueError(
                    "MinIO secret key is required. Please set one of:\n"
                    "- MINIO_SECRET_KEY\n"
                    "- STORAGE_SECRET_KEY\n"
                    "- STORAGE_MINIO_SECRET_KEY"
                )
            
            # Remove protocol from endpoint if present
            if endpoint.startswith('http://'):
                endpoint = endpoint[7:]
                secure = False
            elif endpoint.startswith('https://'):
                endpoint = endpoint[8:]
                secure = True
            else:
                secure = self.config.minio_settings.get('secure', False)
            
            # Create MinIO client
            self.client = Minio(
                endpoint=endpoint,
                access_key=self.config.credentials.access_key,
                secret_key=self.config.credentials.secret_key,
                secure=secure,
                region=self.config.credentials.region or 'us-east-1',
                session_token=self.config.credentials.token
            )
            
            self._initialized = True
            
            logger.info(f"MinIO client initialized successfully for endpoint: {endpoint} (secure: {secure})")
            
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise
    
    def _run_sync(self, func, *args, **kwargs):
        """Run synchronous MinIO operations in async context."""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, func, *args, **kwargs)
    
    @property
    def provider(self) -> StorageProvider:
        """Get the storage provider type."""
        return StorageProvider.MINIO
    
    async def create_bucket(
        self,
        bucket_name: str,
        region: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Create a new MinIO bucket."""
        await self._ensure_initialized()
        
        try:
            target_region = region or self.config.region or 'us-east-1'
            
            await self._run_sync(
                self.client.make_bucket,
                bucket_name,
                location=target_region
            )
            
            # Configure bucket versioning if enabled
            if self.config.versioning_enabled:
                # MinIO versioning configuration would go here
                # This is a placeholder as MinIO versioning API may differ
                pass
            
            logger.info(f"Created MinIO bucket: {bucket_name} in region: {target_region}")
            return True
            
        except S3Error as e:
            if e.code in ['BucketAlreadyOwnedByYou', 'BucketAlreadyExists']:
                logger.warning(f"Bucket {bucket_name} already exists")
                return True
            else:
                logger.error(f"Failed to create bucket {bucket_name}: {e}")
                raise
    
    async def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete a MinIO bucket."""
        await self._ensure_initialized()
        
        try:
            if force:
                # Delete all objects first
                objects = await self.list_objects(bucket_name)
                for obj in objects:
                    await self.delete_object(bucket_name, obj.key)
            
            await self._run_sync(self.client.remove_bucket, bucket_name)
            logger.info(f"Deleted MinIO bucket: {bucket_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to delete bucket {bucket_name}: {e}")
            return False
    
    async def bucket_exists(self, bucket_name: str) -> bool:
        """Check if MinIO bucket exists."""
        await self._ensure_initialized()
        
        try:
            return await self._run_sync(self.client.bucket_exists, bucket_name)
        except Exception:
            return False
    
    async def list_buckets(self) -> List[str]:
        """List all MinIO buckets."""
        await self._ensure_initialized()
        
        try:
            buckets = await self._run_sync(self.client.list_buckets)
            return [bucket.name for bucket in buckets]
        except Exception as e:
            logger.error(f"Failed to list buckets: {e}")
            return []
    
    async def upload_object(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO, str, Path],
        options: Optional[UploadOptions] = None
    ) -> StorageObject:
        """Upload an object to MinIO."""
        await self._ensure_initialized()
        
        options = options or UploadOptions()
        
        try:
            # Ensure bucket exists
            if not await self.bucket_exists(bucket):
                await self.create_bucket(bucket)
            
            # Handle different data types
            if isinstance(data, (str, Path)):
                # File path
                file_path = Path(data)
                if not options.content_type:
                    options.content_type = detect_content_type(str(file_path))
                
                # Prepare metadata
                metadata = options.metadata or {}
                if options.tags:
                    # MinIO doesn't have built-in tags, use metadata
                    metadata.update({f"tag_{k}": v for k, v in options.tags.items()})
                
                # Upload from file
                result = await self._run_sync(
                    self.client.fput_object,
                    bucket,
                    key,
                    str(file_path),
                    content_type=options.content_type,
                    metadata=metadata
                )
                
                file_size = file_path.stat().st_size
                
            else:
                # Handle bytes or file-like objects
                if isinstance(data, bytes):
                    data_stream = io.BytesIO(data)
                    data_length = len(data)
                elif hasattr(data, 'read'):
                    data_stream = data
                    # Try to get length
                    try:
                        current_pos = data_stream.tell()
                        data_stream.seek(0, 2)
                        data_length = data_stream.tell()
                        data_stream.seek(current_pos)
                    except:
                        data_length = -1
                else:
                    raise ValueError(f"Unsupported data type: {type(data)}")
                
                # Set content type
                if not options.content_type:
                    options.content_type = detect_content_type(key)
                
                # Prepare metadata
                metadata = options.metadata or {}
                if options.tags:
                    metadata.update({f"tag_{k}": v for k, v in options.tags.items()})
                
                # Upload from stream
                result = await self._run_sync(
                    self.client.put_object,
                    bucket,
                    key,
                    data_stream,
                    length=data_length,
                    content_type=options.content_type,
                    metadata=metadata
                )
                
                file_size = data_length if data_length > 0 else 0
            
            # Get object metadata
            metadata_obj = await self.get_object_metadata(bucket, key)
            
            return StorageObject(
                key=key,
                bucket=bucket,
                metadata=metadata_obj or StorageMetadata(
                    size=file_size,
                    content_type=options.content_type or 'application/octet-stream',
                    etag=result.etag,
                    version=result.version_id,
                    custom_metadata=metadata
                ),
                access_level=options.access_level
            )
            
        except Exception as e:
            logger.error(f"Failed to upload object {key} to bucket {bucket}: {e}")
            raise
    
    async def download_object(
        self,
        bucket: str,
        key: str,
        options: Optional[DownloadOptions] = None
    ) -> StorageObject:
        """Download an object from MinIO."""
        await self._ensure_initialized()
        
        options = options or DownloadOptions()
        
        try:
            # Get object data
            response = await self._run_sync(self.client.get_object, bucket, key)
            content = response.read()
            response.close()
            response.release_conn()
            
            # Get object metadata
            metadata = await self.get_object_metadata(bucket, key)
            
            return StorageObject(
                key=key,
                bucket=bucket,
                metadata=metadata or StorageMetadata(size=len(content)),
                content=content
            )
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                logger.warning(f"Object {key} not found in bucket {bucket}")
                return None
            else:
                logger.error(f"Failed to download object {key} from bucket {bucket}: {e}")
                raise
    
    async def download_object_to_file(
        self,
        bucket: str,
        key: str,
        file_path: Union[str, Path],
        options: Optional[DownloadOptions] = None
    ) -> bool:
        """Download an object directly to a file."""
        await self._ensure_initialized()
        
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            await self._run_sync(
                self.client.fget_object,
                bucket,
                key,
                str(file_path)
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to download object {key} to file {file_path}: {e}")
            return False
    
    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete an object from MinIO."""
        await self._ensure_initialized()
        
        try:
            await self._run_sync(self.client.remove_object, bucket, key)
            logger.debug(f"Deleted object {key} from bucket {bucket}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete object {key} from bucket {bucket}: {e}")
            return False
    
    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists in MinIO."""
        await self._ensure_initialized()
        
        try:
            await self._run_sync(self.client.stat_object, bucket, key)
            return True
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            raise
        except Exception:
            return False
    
    async def get_object_metadata(self, bucket: str, key: str) -> Optional[StorageMetadata]:
        """Get metadata for a MinIO object."""
        await self._ensure_initialized()
        
        try:
            stat_result = await self._run_sync(self.client.stat_object, bucket, key)
            
            return StorageMetadata(
                size=stat_result.size,
                content_type=stat_result.content_type or 'application/octet-stream',
                created_at=stat_result.last_modified,
                modified_at=stat_result.last_modified,
                etag=stat_result.etag.strip('"') if stat_result.etag else '',
                version=stat_result.version_id,
                custom_metadata=stat_result.metadata or {}
            )
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to get metadata for object {key}: {e}")
            return None
    
    async def update_object_metadata(
        self,
        bucket: str,
        key: str,
        metadata: Dict[str, str]
    ) -> bool:
        """Update metadata for an existing MinIO object."""
        await self._ensure_initialized()
        
        try:
            # MinIO requires copying the object to update metadata
            from minio.commonconfig import CopySource
            
            copy_source = CopySource(bucket, key)
            
            await self._run_sync(
                self.client.copy_object,
                bucket,
                key,
                copy_source,
                metadata=metadata,
                metadata_directive="REPLACE"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update metadata for object {key}: {e}")
            return False
    
    async def list_objects(
        self,
        bucket: str,
        options: Optional[ListOptions] = None
    ) -> List[StorageObject]:
        """List objects in a MinIO bucket."""
        await self._ensure_initialized()
        
        options = options or ListOptions()
        objects = []
        
        try:
            # List objects
            object_list = await self._run_sync(
                self.client.list_objects,
                bucket,
                prefix=options.prefix,
                recursive=options.recursive
            )
            
            count = 0
            for obj in object_list:
                if count >= options.max_keys:
                    break
                
                # Filter by suffix if specified
                if options.suffix and not obj.object_name.endswith(options.suffix):
                    continue
                
                metadata = StorageMetadata(
                    size=obj.size,
                    created_at=obj.last_modified,
                    modified_at=obj.last_modified,
                    etag=obj.etag.strip('"') if obj.etag else ''
                )
                
                # Get detailed metadata if requested
                if options.include_metadata:
                    detailed_metadata = await self.get_object_metadata(bucket, obj.object_name)
                    if detailed_metadata:
                        metadata = detailed_metadata
                
                objects.append(StorageObject(
                    key=obj.object_name,
                    bucket=bucket,
                    metadata=metadata
                ))
                count += 1
            
            return objects
            
        except Exception as e:
            logger.error(f"Failed to list objects in bucket {bucket}: {e}")
            return []
    
    async def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """Copy an object within or between MinIO buckets."""
        await self._ensure_initialized()
        
        try:
            from minio.commonconfig import CopySource
            
            # Ensure destination bucket exists
            if not await self.bucket_exists(dest_bucket):
                await self.create_bucket(dest_bucket)
            
            copy_source = CopySource(source_bucket, source_key)
            
            copy_kwargs = {}
            if metadata:
                copy_kwargs['metadata'] = metadata
                copy_kwargs['metadata_directive'] = "REPLACE"
            
            await self._run_sync(
                self.client.copy_object,
                dest_bucket,
                dest_key,
                copy_source,
                **copy_kwargs
            )
            
            logger.debug(f"Copied object from {source_bucket}/{source_key} to {dest_bucket}/{dest_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy object: {e}")
            return False
    
    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration: timedelta = timedelta(hours=1),
        method: str = "GET"
    ) -> str:
        """Generate a presigned URL for MinIO object access."""
        await self._ensure_initialized()
        
        try:
            # Use partial to properly handle the expires parameter
            from functools import partial
            presigned_func = partial(
                self.client.get_presigned_url,
                method.upper(),
                bucket,
                key,
                expires=expiration
            )
            url = await self._run_sync(presigned_func)
            
            logger.debug(f"Generated presigned URL for {bucket}/{key}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {bucket}/{key}: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if MinIO is healthy."""
        await self._ensure_initialized()
        
        try:
            # Try to list buckets as a health check
            await self._run_sync(self.client.list_buckets)
            return True
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return False
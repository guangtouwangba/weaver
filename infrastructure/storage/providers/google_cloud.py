"""
Google Cloud Storage provider implementation.

This module provides integration with Google Cloud Storage,
supporting standard GCS operations through the unified storage interface.
"""

import logging
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
from google.cloud import storage as gcs
from google.cloud.exceptions import NotFound, Forbidden
from google.api_core import exceptions as gcs_exceptions
import io

from ..interfaces import (
    IObjectStorage, StorageProvider, StorageObject, StorageMetadata,
    UploadOptions, DownloadOptions, ListOptions, AccessLevel,
    detect_content_type, ProviderConfig
)

logger = logging.getLogger(__name__)


class GoogleCloudStorage(IObjectStorage):
    """
    Google Cloud Storage implementation of the object storage interface.
    
    Provides full GCS compatibility including resumable uploads,
    signed URLs, and IAM-based access control.
    """
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize Google Cloud Storage client.
        
        Args:
            config: Provider configuration with GCP credentials and settings
        """
        if config.provider != StorageProvider.GOOGLE_CLOUD:
            raise ValueError(f"Invalid provider: {config.provider}. Expected GOOGLE_CLOUD")
        
        self.config = config
        self.client = None
        self._initialized = False
        
    async def _ensure_initialized(self):
        """Ensure the GCS client is initialized."""
        if not self._initialized:
            await self._initialize_client()
    
    async def _initialize_client(self):
        """Initialize the Google Cloud Storage client."""
        try:
            # Initialize GCS client
            if self.config.credentials.key_file_path:
                # Use service account key file
                self.client = gcs.Client.from_service_account_json(
                    self.config.credentials.key_file_path
                )
            elif self.config.credentials.token:
                # Use token-based authentication
                credentials = self.config.credentials.additional_config.get('credentials')
                self.client = gcs.Client(credentials=credentials)
            else:
                # Use default credentials (environment variables, metadata service, etc.)
                self.client = gcs.Client()
            
            self._initialized = True
            
            logger.info(f"Google Cloud Storage client initialized for project: {self.client.project}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Storage client: {e}")
            raise
    
    @property
    def provider(self) -> StorageProvider:
        """Get the storage provider type."""
        return StorageProvider.GOOGLE_CLOUD
    
    async def create_bucket(
        self,
        bucket_name: str,
        region: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Create a new GCS bucket."""
        await self._ensure_initialized()
        
        try:
            # Create bucket
            bucket = self.client.bucket(bucket_name)
            
            # Set location (region)
            location = region or self.config.region or 'US'
            
            # Create bucket with configuration
            new_bucket = await asyncio.get_event_loop().run_in_executor(
                None, self.client.create_bucket, bucket, location=location
            )
            
            # Configure bucket settings
            if self.config.versioning_enabled:
                new_bucket.versioning_enabled = True
                await asyncio.get_event_loop().run_in_executor(
                    None, new_bucket.patch
                )
            
            # Set default encryption if enabled
            if self.config.encryption_enabled:
                # GCS automatically encrypts all data, but we can set customer-managed keys
                gcp_settings = self.config.gcp_settings
                if 'kms_key_name' in gcp_settings:
                    new_bucket.default_kms_key_name = gcp_settings['kms_key_name']
                    await asyncio.get_event_loop().run_in_executor(
                        None, new_bucket.patch
                    )
            
            logger.info(f"Created GCS bucket: {bucket_name} in location: {location}")
            return True
            
        except gcs_exceptions.Conflict:
            logger.warning(f"Bucket {bucket_name} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            raise
    
    async def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete a GCS bucket."""
        await self._ensure_initialized()
        
        try:
            bucket = self.client.bucket(bucket_name)
            
            if force:
                # Delete all objects first
                blobs = await asyncio.get_event_loop().run_in_executor(
                    None, list, bucket.list_blobs()
                )
                
                for blob in blobs:
                    await asyncio.get_event_loop().run_in_executor(
                        None, blob.delete
                    )
            
            await asyncio.get_event_loop().run_in_executor(
                None, bucket.delete
            )
            
            logger.info(f"Deleted GCS bucket: {bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete bucket {bucket_name}: {e}")
            return False
    
    async def bucket_exists(self, bucket_name: str) -> bool:
        """Check if GCS bucket exists."""
        await self._ensure_initialized()
        
        try:
            bucket = self.client.bucket(bucket_name)
            await asyncio.get_event_loop().run_in_executor(
                None, bucket.exists
            )
            return True
        except Exception:
            return False
    
    async def list_buckets(self) -> List[str]:
        """List all GCS buckets."""
        await self._ensure_initialized()
        
        try:
            buckets = await asyncio.get_event_loop().run_in_executor(
                None, list, self.client.list_buckets()
            )
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
        """Upload an object to GCS."""
        await self._ensure_initialized()
        
        options = options or UploadOptions()
        bucket_obj = self.client.bucket(bucket)
        blob = bucket_obj.blob(key)
        
        try:
            # Handle different data types
            if isinstance(data, (str, Path)):
                # File path
                file_path = Path(data)
                if not options.content_type:
                    options.content_type = detect_content_type(str(file_path))
                
                # Set blob properties
                if options.content_type:
                    blob.content_type = options.content_type
                
                # Set metadata
                if options.metadata:
                    blob.metadata = options.metadata
                
                # Set custom properties
                if options.tags:
                    # GCS doesn't have tags like S3, but we can use custom metadata
                    blob.metadata = blob.metadata or {}
                    blob.metadata.update({f"tag_{k}": v for k, v in options.tags.items()})
                
                # Upload file
                if file_path.stat().st_size > self.config.multipart_threshold:
                    # Use resumable upload for large files
                    await self._resumable_upload_file(blob, str(file_path))
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        None, blob.upload_from_filename, str(file_path)
                    )
                
            else:
                # Handle bytes or file-like objects
                if isinstance(data, bytes):
                    body = data
                elif hasattr(data, 'read'):
                    body = data.read()
                    if hasattr(data, 'name') and not options.content_type:
                        options.content_type = detect_content_type(data.name)
                else:
                    raise ValueError(f"Unsupported data type: {type(data)}")
                
                # Set blob properties
                if options.content_type:
                    blob.content_type = options.content_type
                
                if options.metadata:
                    blob.metadata = options.metadata
                
                if options.tags:
                    blob.metadata = blob.metadata or {}
                    blob.metadata.update({f"tag_{k}": v for k, v in options.tags.items()})
                
                # Upload data
                if len(body) > self.config.multipart_threshold:
                    await self._resumable_upload_data(blob, body)
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        None, blob.upload_from_string, body
                    )
            
            # Set access control
            if options.access_level == AccessLevel.PUBLIC_READ:
                await asyncio.get_event_loop().run_in_executor(
                    None, blob.make_public
                )
            
            # Reload blob to get updated metadata
            await asyncio.get_event_loop().run_in_executor(
                None, blob.reload
            )
            
            # Get object metadata
            metadata = await self.get_object_metadata(bucket, key)
            
            return StorageObject(
                key=key,
                bucket=bucket,
                metadata=metadata,
                access_level=options.access_level
            )
            
        except Exception as e:
            logger.error(f"Failed to upload object {key} to bucket {bucket}: {e}")
            raise
    
    async def _resumable_upload_file(self, blob: gcs.Blob, file_path: str):
        """Perform resumable upload for large files."""
        def _upload():
            with open(file_path, 'rb') as f:
                blob.upload_from_file(f, checksum=None)  # Disable checksum for better performance
        
        await asyncio.get_event_loop().run_in_executor(None, _upload)
    
    async def _resumable_upload_data(self, blob: gcs.Blob, data: bytes):
        """Perform resumable upload for large data."""
        def _upload():
            blob.upload_from_string(data, checksum=None)
        
        await asyncio.get_event_loop().run_in_executor(None, _upload)
    
    async def download_object(
        self,
        bucket: str,
        key: str,
        options: Optional[DownloadOptions] = None
    ) -> StorageObject:
        """Download an object from GCS."""
        await self._ensure_initialized()
        
        options = options or DownloadOptions()
        bucket_obj = self.client.bucket(bucket)
        blob = bucket_obj.blob(key)
        
        try:
            # Check if blob exists
            exists = await asyncio.get_event_loop().run_in_executor(
                None, blob.exists
            )
            if not exists:
                logger.warning(f"Object {key} not found in bucket {bucket}")
                return None
            
            # Set download parameters
            start = options.range_start
            end = options.range_end
            
            # Download content
            if start is not None or end is not None:
                content = await asyncio.get_event_loop().run_in_executor(
                    None, blob.download_as_bytes, start, end
                )
            else:
                content = await asyncio.get_event_loop().run_in_executor(
                    None, blob.download_as_bytes
                )
            
            # Reload blob to get fresh metadata
            await asyncio.get_event_loop().run_in_executor(
                None, blob.reload
            )
            
            # Create metadata
            metadata = StorageMetadata(
                size=blob.size or len(content),
                content_type=blob.content_type or 'application/octet-stream',
                created_at=blob.time_created or datetime.utcnow(),
                modified_at=blob.updated or datetime.utcnow(),
                etag=blob.etag.strip('"') if blob.etag else '',
                version=blob.generation,
                custom_metadata=blob.metadata or {}
            )
            
            return StorageObject(
                key=key,
                bucket=bucket,
                metadata=metadata,
                content=content
            )
            
        except NotFound:
            logger.warning(f"Object {key} not found in bucket {bucket}")
            return None
        except Exception as e:
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
            bucket_obj = self.client.bucket(bucket)
            blob = bucket_obj.blob(key)
            
            await asyncio.get_event_loop().run_in_executor(
                None, blob.download_to_filename, str(file_path)
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to download object {key} to file {file_path}: {e}")
            return False
    
    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete an object from GCS."""
        await self._ensure_initialized()
        
        try:
            bucket_obj = self.client.bucket(bucket)
            blob = bucket_obj.blob(key)
            
            await asyncio.get_event_loop().run_in_executor(
                None, blob.delete
            )
            
            logger.debug(f"Deleted object {key} from bucket {bucket}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete object {key} from bucket {bucket}: {e}")
            return False
    
    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists in GCS."""
        await self._ensure_initialized()
        
        try:
            bucket_obj = self.client.bucket(bucket)
            blob = bucket_obj.blob(key)
            
            return await asyncio.get_event_loop().run_in_executor(
                None, blob.exists
            )
        except Exception:
            return False
    
    async def get_object_metadata(self, bucket: str, key: str) -> Optional[StorageMetadata]:
        """Get metadata for a GCS object."""
        await self._ensure_initialized()
        
        try:
            bucket_obj = self.client.bucket(bucket)
            blob = bucket_obj.blob(key)
            
            await asyncio.get_event_loop().run_in_executor(
                None, blob.reload
            )
            
            return StorageMetadata(
                size=blob.size or 0,
                content_type=blob.content_type or 'application/octet-stream',
                created_at=blob.time_created or datetime.utcnow(),
                modified_at=blob.updated or datetime.utcnow(),
                etag=blob.etag.strip('"') if blob.etag else '',
                version=str(blob.generation) if blob.generation else None,
                custom_metadata=blob.metadata or {}
            )
        except Exception:
            return None
    
    async def update_object_metadata(
        self,
        bucket: str,
        key: str,
        metadata: Dict[str, str]
    ) -> bool:
        """Update metadata for an existing GCS object."""
        await self._ensure_initialized()
        
        try:
            bucket_obj = self.client.bucket(bucket)
            blob = bucket_obj.blob(key)
            
            # Update metadata
            blob.metadata = metadata
            
            await asyncio.get_event_loop().run_in_executor(
                None, blob.patch
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
        """List objects in a GCS bucket."""
        await self._ensure_initialized()
        
        options = options or ListOptions()
        bucket_obj = self.client.bucket(bucket)
        objects = []
        
        try:
            # Set up list parameters
            list_kwargs = {}
            if options.prefix:
                list_kwargs['prefix'] = options.prefix
            if options.max_keys:
                list_kwargs['max_results'] = min(options.max_keys, 1000)  # GCS limit
            
            # List blobs
            blobs = await asyncio.get_event_loop().run_in_executor(
                None, bucket_obj.list_blobs, **list_kwargs
            )
            
            for blob in blobs:
                key = blob.name
                
                # Apply suffix filter if specified
                if options.suffix and not key.endswith(options.suffix):
                    continue
                
                metadata = StorageMetadata(
                    size=blob.size or 0,
                    created_at=blob.time_created or datetime.utcnow(),
                    modified_at=blob.updated or datetime.utcnow(),
                    etag=blob.etag.strip('"') if blob.etag else '',
                    content_type=blob.content_type
                )
                
                # Include detailed metadata if requested
                if options.include_metadata:
                    metadata.custom_metadata = blob.metadata or {}
                
                objects.append(StorageObject(
                    key=key,
                    bucket=bucket,
                    metadata=metadata
                ))
                
                # Respect max_keys limit
                if len(objects) >= options.max_keys:
                    break
            
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
        """Copy an object within or between GCS buckets."""
        await self._ensure_initialized()
        
        try:
            source_bucket_obj = self.client.bucket(source_bucket)
            source_blob = source_bucket_obj.blob(source_key)
            
            dest_bucket_obj = self.client.bucket(dest_bucket)
            
            # Copy the blob
            new_blob = await asyncio.get_event_loop().run_in_executor(
                None, source_bucket_obj.copy_blob, source_blob, dest_bucket_obj, dest_key
            )
            
            # Update metadata if provided
            if metadata:
                new_blob.metadata = metadata
                await asyncio.get_event_loop().run_in_executor(
                    None, new_blob.patch
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
        """Generate a signed URL for GCS object access."""
        await self._ensure_initialized()
        
        try:
            bucket_obj = self.client.bucket(bucket)
            blob = bucket_obj.blob(key)
            
            expires_at = datetime.utcnow() + expiration
            
            url = await asyncio.get_event_loop().run_in_executor(
                None, blob.generate_signed_url, expires_at, method=method.upper()
            )
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {bucket}/{key}: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the GCS service is healthy."""
        await self._ensure_initialized()
        
        try:
            # Try to list buckets as a health check
            await asyncio.get_event_loop().run_in_executor(
                None, list, self.client.list_buckets(max_results=1)
            )
            return True
        except Exception as e:
            logger.error(f"GCS health check failed: {e}")
            return False
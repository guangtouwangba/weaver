"""
Alibaba Cloud OSS storage provider implementation.

This module provides integration with Alibaba Cloud Object Storage Service (OSS),
supporting standard OSS operations through the unified storage interface.
"""

import logging
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import oss2
from oss2.exceptions import OssError, NoSuchBucket, NoSuchKey
import io

from ..interfaces import (
    IObjectStorage, StorageProvider, StorageObject, StorageMetadata,
    UploadOptions, DownloadOptions, ListOptions, AccessLevel,
    detect_content_type, ProviderConfig
)

logger = logging.getLogger(__name__)


class AlibabaOSSStorage(IObjectStorage):
    """
    Alibaba Cloud OSS implementation of the object storage interface.
    
    Provides full OSS compatibility including multipart uploads,
    presigned URLs, and cross-region operations.
    """
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize Alibaba OSS storage client.
        
        Args:
            config: Provider configuration with Alibaba credentials and settings
        """
        if config.provider != StorageProvider.ALIBABA_OSS:
            raise ValueError(f"Invalid provider: {config.provider}. Expected ALIBABA_OSS")
        
        self.config = config
        self.auth = None
        self.service = None
        self._bucket_cache = {}
        self._initialized = False
        
    async def _ensure_initialized(self):
        """Ensure the OSS client is initialized."""
        if not self._initialized:
            await self._initialize_client()
    
    async def _initialize_client(self):
        """Initialize the OSS client."""
        try:
            # Create OSS auth
            self.auth = oss2.Auth(
                self.config.credentials.access_key,
                self.config.credentials.secret_key
            )
            
            # Create OSS service for bucket operations
            endpoint = self.config.credentials.endpoint_url
            if not endpoint:
                # Default endpoint based on region
                region = self.config.credentials.region or 'oss-cn-hangzhou'
                endpoint = f'https://{region}.aliyuncs.com'
            
            self.service = oss2.Service(self.auth, endpoint)
            self._initialized = True
            
            logger.info(f"Alibaba OSS client initialized with endpoint: {endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Alibaba OSS client: {e}")
            raise
    
    def _get_bucket(self, bucket_name: str) -> oss2.Bucket:
        """Get or create a bucket client."""
        if bucket_name not in self._bucket_cache:
            endpoint = self.config.credentials.endpoint_url
            if not endpoint:
                region = self.config.credentials.region or 'oss-cn-hangzhou'
                endpoint = f'https://{region}.aliyuncs.com'
            
            self._bucket_cache[bucket_name] = oss2.Bucket(
                self.auth, endpoint, bucket_name
            )
        
        return self._bucket_cache[bucket_name]
    
    @property
    def provider(self) -> StorageProvider:
        """Get the storage provider type."""
        return StorageProvider.ALIBABA_OSS
    
    async def create_bucket(
        self,
        bucket_name: str,
        region: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Create a new OSS bucket."""
        await self._ensure_initialized()
        
        try:
            # Use default region if not specified
            target_region = region or self.config.region or 'oss-cn-hangzhou'
            
            # Create bucket with region-specific endpoint
            endpoint = f'https://{target_region}.aliyuncs.com'
            bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
            
            # Create bucket
            create_config = oss2.models.BucketCreateConfig()
            if self.config.alibaba_settings.get('storage_class'):
                create_config.storage_class = self.config.alibaba_settings['storage_class']
            
            await asyncio.get_event_loop().run_in_executor(
                None, bucket.create_bucket, create_config
            )
            
            # Configure bucket settings
            if self.config.versioning_enabled:
                versioning_config = oss2.models.BucketVersioningConfig(
                    status=oss2.models.BUCKET_VERSIONING_ENABLE
                )
                await asyncio.get_event_loop().run_in_executor(
                    None, bucket.put_bucket_versioning, versioning_config
                )
            
            if self.config.encryption_enabled:
                encryption_config = oss2.models.ServerSideEncryptionRule()
                encryption_config.sse_algorithm = 'AES256'
                await asyncio.get_event_loop().run_in_executor(
                    None, bucket.put_bucket_encryption, encryption_config
                )
            
            logger.info(f"Created OSS bucket: {bucket_name} in region: {target_region}")
            return True
            
        except OssError as e:
            if e.code == 'BucketAlreadyExists':
                logger.warning(f"Bucket {bucket_name} already exists")
                return False
            else:
                logger.error(f"Failed to create bucket {bucket_name}: {e}")
                raise
    
    async def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete an OSS bucket."""
        await self._ensure_initialized()
        
        try:
            bucket = self._get_bucket(bucket_name)
            
            if force:
                # Delete all objects first
                for obj in oss2.ObjectIterator(bucket):
                    await asyncio.get_event_loop().run_in_executor(
                        None, bucket.delete_object, obj.key
                    )
            
            await asyncio.get_event_loop().run_in_executor(
                None, bucket.delete_bucket
            )
            
            # Remove from cache
            if bucket_name in self._bucket_cache:
                del self._bucket_cache[bucket_name]
            
            logger.info(f"Deleted OSS bucket: {bucket_name}")
            return True
            
        except OssError as e:
            logger.error(f"Failed to delete bucket {bucket_name}: {e}")
            return False
    
    async def bucket_exists(self, bucket_name: str) -> bool:
        """Check if OSS bucket exists."""
        await self._ensure_initialized()
        
        try:
            bucket = self._get_bucket(bucket_name)
            await asyncio.get_event_loop().run_in_executor(
                None, bucket.get_bucket_info
            )
            return True
        except (OssError, NoSuchBucket):
            return False
    
    async def list_buckets(self) -> List[str]:
        """List all OSS buckets."""
        await self._ensure_initialized()
        
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.service.list_buckets
            )
            return [bucket.name for bucket in result.buckets]
        except OssError as e:
            logger.error(f"Failed to list buckets: {e}")
            return []
    
    async def upload_object(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO, str, Path],
        options: Optional[UploadOptions] = None
    ) -> StorageObject:
        """Upload an object to OSS."""
        await self._ensure_initialized()
        
        options = options or UploadOptions()
        bucket_client = self._get_bucket(bucket)
        
        try:
            # Handle different data types
            if isinstance(data, (str, Path)):
                # File path
                file_path = Path(data)
                if not options.content_type:
                    options.content_type = detect_content_type(str(file_path))
                
                # Use file upload for better performance
                headers = {}
                if options.content_type:
                    headers['Content-Type'] = options.content_type
                
                # Add metadata to headers
                if options.metadata:
                    for k, v in options.metadata.items():
                        headers[f'x-oss-meta-{k}'] = str(v)
                
                # Set tags
                if options.tags:
                    tag_str = '&'.join([f"{k}={v}" for k, v in options.tags.items()])
                    headers['x-oss-tagging'] = tag_str
                
                # Set ACL based on access level
                if options.access_level == AccessLevel.PUBLIC_READ:
                    headers['x-oss-object-acl'] = 'public-read'
                elif options.access_level == AccessLevel.PUBLIC_READ_WRITE:
                    headers['x-oss-object-acl'] = 'public-read-write'
                
                # Determine if we should use multipart upload
                file_size = file_path.stat().st_size
                if file_size > self.config.multipart_threshold:
                    await self._multipart_upload_file(bucket_client, key, str(file_path), headers)
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        None, bucket_client.put_object_from_file, key, str(file_path), headers
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
                
                headers = {}
                if options.content_type:
                    headers['Content-Type'] = options.content_type
                
                # Add metadata
                if options.metadata:
                    for k, v in options.metadata.items():
                        headers[f'x-oss-meta-{k}'] = str(v)
                
                # Set tags
                if options.tags:
                    tag_str = '&'.join([f"{k}={v}" for k, v in options.tags.items()])
                    headers['x-oss-tagging'] = tag_str
                
                # Set ACL
                if options.access_level == AccessLevel.PUBLIC_READ:
                    headers['x-oss-object-acl'] = 'public-read'
                elif options.access_level == AccessLevel.PUBLIC_READ_WRITE:
                    headers['x-oss-object-acl'] = 'public-read-write'
                
                # Upload
                if len(body) > self.config.multipart_threshold:
                    await self._multipart_upload_data(bucket_client, key, body, headers)
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        None, bucket_client.put_object, key, body, headers
                    )
            
            # Get object metadata
            metadata = await self.get_object_metadata(bucket, key)
            
            return StorageObject(
                key=key,
                bucket=bucket,
                metadata=metadata,
                access_level=options.access_level
            )
            
        except OssError as e:
            logger.error(f"Failed to upload object {key} to bucket {bucket}: {e}")
            raise
    
    async def _multipart_upload_file(self, bucket_client: oss2.Bucket, key: str, file_path: str, headers: Dict[str, str]):
        """Perform multipart upload for large files."""
        # Calculate part size
        file_size = Path(file_path).stat().st_size
        part_size = max(self.config.multipart_threshold // 10, 100 * 1024)  # Min 100KB
        
        # Initiate multipart upload
        upload_id = await asyncio.get_event_loop().run_in_executor(
            None, bucket_client.init_multipart_upload, key, headers
        )
        
        try:
            parts = []
            with open(file_path, 'rb') as f:
                part_number = 1
                while True:
                    data = f.read(part_size)
                    if not data:
                        break
                    
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, bucket_client.upload_part, key, upload_id, part_number, data
                    )
                    parts.append(oss2.models.PartInfo(part_number, result.etag))
                    part_number += 1
            
            # Complete multipart upload
            await asyncio.get_event_loop().run_in_executor(
                None, bucket_client.complete_multipart_upload, key, upload_id, parts
            )
            
        except Exception as e:
            # Abort multipart upload on error
            await asyncio.get_event_loop().run_in_executor(
                None, bucket_client.abort_multipart_upload, key, upload_id
            )
            raise e
    
    async def _multipart_upload_data(self, bucket_client: oss2.Bucket, key: str, data: bytes, headers: Dict[str, str]):
        """Perform multipart upload for large data."""
        # Calculate part size
        data_size = len(data)
        part_size = max(self.config.multipart_threshold // 10, 100 * 1024)  # Min 100KB
        
        # Initiate multipart upload
        upload_id = await asyncio.get_event_loop().run_in_executor(
            None, bucket_client.init_multipart_upload, key, headers
        )
        
        try:
            parts = []
            part_number = 1
            offset = 0
            
            while offset < data_size:
                end = min(offset + part_size, data_size)
                part_data = data[offset:end]
                
                result = await asyncio.get_event_loop().run_in_executor(
                    None, bucket_client.upload_part, key, upload_id, part_number, part_data
                )
                parts.append(oss2.models.PartInfo(part_number, result.etag))
                
                part_number += 1
                offset = end
            
            # Complete multipart upload
            await asyncio.get_event_loop().run_in_executor(
                None, bucket_client.complete_multipart_upload, key, upload_id, parts
            )
            
        except Exception as e:
            # Abort multipart upload on error
            await asyncio.get_event_loop().run_in_executor(
                None, bucket_client.abort_multipart_upload, key, upload_id
            )
            raise e
    
    async def download_object(
        self,
        bucket: str,
        key: str,
        options: Optional[DownloadOptions] = None
    ) -> StorageObject:
        """Download an object from OSS."""
        await self._ensure_initialized()
        
        options = options or DownloadOptions()
        bucket_client = self._get_bucket(bucket)
        
        try:
            headers = {}
            
            # Set range if specified
            if options.range_start is not None or options.range_end is not None:
                start = options.range_start or 0
                end = options.range_end or ''
                headers['Range'] = f'bytes={start}-{end}'
            
            # Set conditional headers
            if options.if_modified_since:
                headers['If-Modified-Since'] = options.if_modified_since.strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            if options.if_unmodified_since:
                headers['If-Unmodified-Since'] = options.if_unmodified_since.strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            # Get object
            result = await asyncio.get_event_loop().run_in_executor(
                None, bucket_client.get_object, key, headers
            )
            
            # Read content
            content = result.read()
            
            # Create metadata
            metadata = StorageMetadata(
                size=result.content_length or len(content),
                content_type=result.content_type or 'application/octet-stream',
                created_at=result.last_modified or datetime.utcnow(),
                modified_at=result.last_modified or datetime.utcnow(),
                etag=result.etag.strip('"') if result.etag else '',
                version=result.version_id,
                custom_metadata=result.object_meta or {}
            )
            
            return StorageObject(
                key=key,
                bucket=bucket,
                metadata=metadata,
                content=content
            )
            
        except (OssError, NoSuchKey) as e:
            if isinstance(e, NoSuchKey) or (hasattr(e, 'code') and e.code == 'NoSuchKey'):
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
            bucket_client = self._get_bucket(bucket)
            
            headers = {}
            if options:
                if options.range_start is not None or options.range_end is not None:
                    start = options.range_start or 0
                    end = options.range_end or ''
                    headers['Range'] = f'bytes={start}-{end}'
            
            await asyncio.get_event_loop().run_in_executor(
                None, bucket_client.get_object_to_file, key, str(file_path), headers
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to download object {key} to file {file_path}: {e}")
            return False
    
    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete an object from OSS."""
        await self._ensure_initialized()
        
        try:
            bucket_client = self._get_bucket(bucket)
            await asyncio.get_event_loop().run_in_executor(
                None, bucket_client.delete_object, key
            )
            logger.debug(f"Deleted object {key} from bucket {bucket}")
            return True
        except OssError as e:
            logger.error(f"Failed to delete object {key} from bucket {bucket}: {e}")
            return False
    
    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists in OSS."""
        await self._ensure_initialized()
        
        try:
            bucket_client = self._get_bucket(bucket)
            await asyncio.get_event_loop().run_in_executor(
                None, bucket_client.head_object, key
            )
            return True
        except (OssError, NoSuchKey):
            return False
    
    async def get_object_metadata(self, bucket: str, key: str) -> Optional[StorageMetadata]:
        """Get metadata for an OSS object."""
        await self._ensure_initialized()
        
        try:
            bucket_client = self._get_bucket(bucket)
            result = await asyncio.get_event_loop().run_in_executor(
                None, bucket_client.head_object, key
            )
            
            return StorageMetadata(
                size=result.content_length or 0,
                content_type=result.content_type or 'application/octet-stream',
                created_at=result.last_modified or datetime.utcnow(),
                modified_at=result.last_modified or datetime.utcnow(),
                etag=result.etag.strip('"') if result.etag else '',
                version=result.version_id,
                custom_metadata=result.object_meta or {}
            )
        except (OssError, NoSuchKey):
            return None
    
    async def update_object_metadata(
        self,
        bucket: str,
        key: str,
        metadata: Dict[str, str]
    ) -> bool:
        """Update metadata for an existing OSS object."""
        await self._ensure_initialized()
        
        try:
            bucket_client = self._get_bucket(bucket)
            
            # OSS requires copying the object to update metadata
            headers = {}
            for k, v in metadata.items():
                headers[f'x-oss-meta-{k}'] = str(v)
            
            headers['x-oss-metadata-directive'] = 'REPLACE'
            
            await asyncio.get_event_loop().run_in_executor(
                None, bucket_client.copy_object, bucket, key, key, headers
            )
            return True
        except OssError as e:
            logger.error(f"Failed to update metadata for object {key}: {e}")
            return False
    
    async def list_objects(
        self,
        bucket: str,
        options: Optional[ListOptions] = None
    ) -> List[StorageObject]:
        """List objects in an OSS bucket."""
        await self._ensure_initialized()
        
        options = options or ListOptions()
        bucket_client = self._get_bucket(bucket)
        objects = []
        
        try:
            # Create object iterator
            object_iterator = oss2.ObjectIterator(
                bucket_client,
                prefix=options.prefix or '',
                max_keys=min(options.max_keys, 1000)  # OSS limit
            )
            
            for obj in object_iterator:
                key = obj.key
                
                # Apply suffix filter if specified
                if options.suffix and not key.endswith(options.suffix):
                    continue
                
                metadata = StorageMetadata(
                    size=obj.size or 0,
                    created_at=obj.last_modified or datetime.utcnow(),
                    modified_at=obj.last_modified or datetime.utcnow(),
                    etag=obj.etag.strip('"') if obj.etag else ''
                )
                
                # Include detailed metadata if requested
                if options.include_metadata:
                    detailed_metadata = await self.get_object_metadata(bucket, key)
                    if detailed_metadata:
                        metadata = detailed_metadata
                
                objects.append(StorageObject(
                    key=key,
                    bucket=bucket,
                    metadata=metadata
                ))
                
                # Respect max_keys limit
                if len(objects) >= options.max_keys:
                    break
            
            return objects
            
        except OssError as e:
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
        """Copy an object within or between OSS buckets."""
        await self._ensure_initialized()
        
        try:
            dest_bucket_client = self._get_bucket(dest_bucket)
            
            headers = {}
            if metadata:
                for k, v in metadata.items():
                    headers[f'x-oss-meta-{k}'] = str(v)
                headers['x-oss-metadata-directive'] = 'REPLACE'
            
            await asyncio.get_event_loop().run_in_executor(
                None, dest_bucket_client.copy_object, source_bucket, source_key, dest_key, headers
            )
            
            logger.debug(f"Copied object from {source_bucket}/{source_key} to {dest_bucket}/{dest_key}")
            return True
            
        except OssError as e:
            logger.error(f"Failed to copy object: {e}")
            return False
    
    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration: timedelta = timedelta(hours=1),
        method: str = "GET"
    ) -> str:
        """Generate a presigned URL for OSS object access."""
        await self._ensure_initialized()
        
        try:
            bucket_client = self._get_bucket(bucket)
            
            expires = int(expiration.total_seconds())
            
            if method.upper() == 'GET':
                url = bucket_client.sign_url('GET', key, expires)
            elif method.upper() == 'PUT':
                url = bucket_client.sign_url('PUT', key, expires)
            elif method.upper() == 'DELETE':
                url = bucket_client.sign_url('DELETE', key, expires)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return url
            
        except OssError as e:
            logger.error(f"Failed to generate presigned URL for {bucket}/{key}: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the OSS service is healthy."""
        await self._ensure_initialized()
        
        try:
            # Try to list buckets as a health check
            await asyncio.get_event_loop().run_in_executor(
                None, self.service.list_buckets
            )
            return True
        except Exception as e:
            logger.error(f"OSS health check failed: {e}")
            return False
"""
MinIO-based object storage implementation.

Provides a complete implementation of the storage interfaces using MinIO,
compatible with Amazon S3 API and other S3-compatible storage systems.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin
import hashlib
import json

from minio import Minio
from minio.error import S3Error, InvalidResponseError
import httpx

from .interfaces import (
    IObjectStorage, IFileManager, IContentProcessor,
    StorageObject, StorageMetadata, UploadOptions, DownloadOptions,
    ListOptions, SearchCriteria, AccessLevel, ContentType,
    detect_content_type, validate_file_type, generate_unique_key,
    StorageConfig
)

logger = logging.getLogger(__name__)


class MinIOStorage(IObjectStorage):
    """
    MinIO implementation of object storage interface.
    
    Provides full S3-compatible object storage capabilities with
    additional MinIO-specific features and optimizations.
    """
    
    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        secure: bool = False,
        region: str = "us-east-1",
        session_token: Optional[str] = None
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.region = region
        self.session_token = session_token
        
        # Initialize MinIO client
        self._client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
            session_token=session_token
        )
        
        self._is_connected = False
        
    async def _ensure_connected(self) -> None:
        """Ensure connection to MinIO is established."""
        if not self._is_connected:
            try:
                # Test connection by listing buckets
                list(self._client.list_buckets())
                self._is_connected = True
                logger.info(f"Connected to MinIO at {self.endpoint}")
            except Exception as e:
                logger.error(f"Failed to connect to MinIO: {e}")
                raise
    
    def _run_sync(self, func, *args, **kwargs):
        """Run synchronous MinIO operations in async context."""
        # MinIO client is synchronous, so we run it in a thread pool
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, func, *args, **kwargs)
    
    def _extract_metadata(self, stat_result) -> StorageMetadata:
        """Extract metadata from MinIO stat result."""
        return StorageMetadata(
            size=stat_result.size,
            content_type=stat_result.content_type or ContentType.BINARY.value,
            created_at=stat_result.last_modified,
            modified_at=stat_result.last_modified,
            etag=stat_result.etag,
            version=stat_result.version_id,
            custom_metadata=stat_result.metadata or {},
            tags={}  # Would need separate call to get tags
        )
    
    async def create_bucket(
        self,
        bucket_name: str,
        region: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Create a new bucket in MinIO."""
        await self._ensure_connected()
        
        try:
            await self._run_sync(
                self._client.make_bucket,
                bucket_name,
                location=region or self.region
            )
            logger.info(f"Created bucket: {bucket_name}")
            return True
        except S3Error as e:
            if e.code == 'BucketAlreadyOwnedByYou':
                logger.warning(f"Bucket {bucket_name} already exists")
                return True
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating bucket {bucket_name}: {e}")
            return False
    
    async def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete a bucket from MinIO."""
        await self._ensure_connected()
        
        try:
            if force:
                # Delete all objects first
                objects = await self.list_objects(bucket_name)
                for obj in objects:
                    await self.delete_object(bucket_name, obj.key)
            
            await self._run_sync(self._client.remove_bucket, bucket_name)
            logger.info(f"Deleted bucket: {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete bucket {bucket_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting bucket {bucket_name}: {e}")
            return False
    
    async def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists."""
        await self._ensure_connected()
        
        try:
            return await self._run_sync(self._client.bucket_exists, bucket_name)
        except Exception as e:
            logger.error(f"Error checking bucket existence {bucket_name}: {e}")
            return False
    
    async def list_buckets(self) -> List[str]:
        """List all available buckets."""
        await self._ensure_connected()
        
        try:
            buckets = await self._run_sync(self._client.list_buckets)
            return [bucket.name for bucket in buckets]
        except Exception as e:
            logger.error(f"Error listing buckets: {e}")
            return []
    
    async def upload_object(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO, str, Path],
        options: Optional[UploadOptions] = None
    ) -> StorageObject:
        """Upload an object to MinIO."""
        await self._ensure_connected()
        options = options or UploadOptions()
        
        try:
            # Ensure bucket exists
            if not await self.bucket_exists(bucket):
                await self.create_bucket(bucket)
            
            # Prepare data
            if isinstance(data, (str, Path)):
                file_path = Path(data)
                data_stream = open(file_path, 'rb')
                data_length = file_path.stat().st_size
            elif isinstance(data, bytes):
                from io import BytesIO
                data_stream = BytesIO(data)
                data_length = len(data)
            else:
                data_stream = data
                # Try to get length
                try:
                    current_pos = data_stream.tell()
                    data_stream.seek(0, 2)  # Seek to end
                    data_length = data_stream.tell()
                    data_stream.seek(current_pos)  # Seek back
                except:
                    data_length = -1  # Unknown length
            
            # Determine content type
            content_type = options.content_type or detect_content_type(key)
            
            # Prepare metadata
            metadata = options.metadata or {}
            if options.tags:
                # MinIO stores tags separately, but we can include them in metadata for now
                metadata.update({f"tag_{k}": v for k, v in options.tags.items()})
            
            # Upload object
            result = await self._run_sync(
                self._client.put_object,
                bucket,
                key,
                data_stream,
                length=data_length,
                content_type=content_type,
                metadata=metadata
            )
            
            # Close stream if we opened it
            if isinstance(data, (str, Path)):
                data_stream.close()
            
            # Create storage object
            storage_obj = StorageObject(
                key=key,
                bucket=bucket,
                metadata=StorageMetadata(
                    size=data_length if data_length > 0 else 0,
                    content_type=content_type,
                    etag=result.etag,
                    version=result.version_id,
                    custom_metadata=metadata
                ),
                access_level=options.access_level
            )
            
            logger.debug(f"Uploaded object {key} to bucket {bucket}")
            return storage_obj
            
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
        await self._ensure_connected()
        options = options or DownloadOptions()
        
        try:
            # Get object metadata first
            stat_result = await self._run_sync(self._client.stat_object, bucket, key)
            metadata = self._extract_metadata(stat_result)
            
            # Download object data
            response = await self._run_sync(self._client.get_object, bucket, key)
            content = response.read()
            response.close()
            response.release_conn()
            
            storage_obj = StorageObject(
                key=key,
                bucket=bucket,
                metadata=metadata,
                content=content
            )
            
            logger.debug(f"Downloaded object {key} from bucket {bucket}")
            return storage_obj
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                logger.warning(f"Object {key} not found in bucket {bucket}")
                raise FileNotFoundError(f"Object {key} not found")
            logger.error(f"Failed to download object {key} from bucket {bucket}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading object {key}: {e}")
            raise
    
    async def download_object_to_file(
        self,
        bucket: str,
        key: str,
        file_path: Union[str, Path],
        options: Optional[DownloadOptions] = None
    ) -> bool:
        """Download an object directly to a file."""
        await self._ensure_connected()
        
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            await self._run_sync(
                self._client.fget_object,
                bucket,
                key,
                str(file_path)
            )
            
            logger.debug(f"Downloaded object {key} to file {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download object {key} to file {file_path}: {e}")
            return False
    
    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete an object from MinIO."""
        await self._ensure_connected()
        
        try:
            await self._run_sync(self._client.remove_object, bucket, key)
            logger.debug(f"Deleted object {key} from bucket {bucket}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete object {key} from bucket {bucket}: {e}")
            return False
    
    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists."""
        await self._ensure_connected()
        
        try:
            await self._run_sync(self._client.stat_object, bucket, key)
            return True
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            raise
        except Exception:
            return False
    
    async def get_object_metadata(self, bucket: str, key: str) -> Optional[StorageMetadata]:
        """Get metadata for an object."""
        await self._ensure_connected()
        
        try:
            stat_result = await self._run_sync(self._client.stat_object, bucket, key)
            return self._extract_metadata(stat_result)
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
        """Update metadata for an existing object."""
        await self._ensure_connected()
        
        try:
            # MinIO requires copying the object to update metadata
            copy_conditions = {}
            copy_source = {"Bucket": bucket, "Key": key}
            
            await self._run_sync(
                self._client.copy_object,
                bucket,
                key,
                copy_source,
                metadata=metadata,
                metadata_directive="REPLACE"
            )
            
            logger.debug(f"Updated metadata for object {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to update metadata for object {key}: {e}")
            return False
    
    async def list_objects(
        self,
        bucket: str,
        options: Optional[ListOptions] = None
    ) -> List[StorageObject]:
        """List objects in a bucket."""
        await self._ensure_connected()
        options = options or ListOptions()
        
        try:
            objects = []
            
            # List objects
            object_list = await self._run_sync(
                self._client.list_objects,
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
                
                # Create storage object
                metadata = StorageMetadata(
                    size=obj.size,
                    created_at=obj.last_modified,
                    modified_at=obj.last_modified,
                    etag=obj.etag
                )
                
                # Get detailed metadata if requested
                if options.include_metadata:
                    detailed_metadata = await self.get_object_metadata(bucket, obj.object_name)
                    if detailed_metadata:
                        metadata = detailed_metadata
                
                storage_obj = StorageObject(
                    key=obj.object_name,
                    bucket=bucket,
                    metadata=metadata
                )
                
                objects.append(storage_obj)
                count += 1
            
            logger.debug(f"Listed {len(objects)} objects from bucket {bucket}")
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
        """Copy an object within or between buckets."""
        await self._ensure_connected()
        
        try:
            # Ensure destination bucket exists
            if not await self.bucket_exists(dest_bucket):
                await self.create_bucket(dest_bucket)
            
            copy_source = {"Bucket": source_bucket, "Key": source_key}
            
            copy_kwargs = {}
            if metadata:
                copy_kwargs['metadata'] = metadata
                copy_kwargs['metadata_directive'] = "REPLACE"
            
            await self._run_sync(
                self._client.copy_object,
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
        """Generate a presigned URL for temporary access."""
        await self._ensure_connected()
        
        try:
            if method.upper() == "GET":
                url = await self._run_sync(
                    self._client.get_presigned_url,
                    "GET",
                    bucket,
                    key,
                    expires=expiration
                )
            elif method.upper() == "PUT":
                url = await self._run_sync(
                    self._client.get_presigned_url,
                    "PUT",
                    bucket,
                    key,
                    expires=expiration
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            logger.debug(f"Generated presigned URL for {bucket}/{key}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if MinIO is healthy."""
        try:
            await self._ensure_connected()
            # Try to list buckets as a health check
            await self._run_sync(self._client.list_buckets)
            return True
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return False


class MinIOFileManager(IFileManager):
    """
    High-level file manager implementation using MinIO.
    
    Provides convenient file operations with automatic organization,
    metadata management, and content processing integration.
    """
    
    def __init__(
        self,
        storage: MinIOStorage,
        default_bucket: str = StorageConfig.DOCUMENTS_BUCKET,
        content_processor: Optional[IContentProcessor] = None
    ):
        self.storage = storage
        self.default_bucket = default_bucket
        self.content_processor = content_processor
        
        # File ID to storage mapping (could be stored in database)
        self._file_registry: Dict[str, Dict[str, str]] = {}
    
    async def save_file(
        self,
        file_data: Union[bytes, BinaryIO, str, Path],
        filename: Optional[str] = None,
        folder: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        public: bool = False
    ) -> str:
        """Save a file with automatic organization."""
        # Generate filename if not provided
        if not filename:
            if isinstance(file_data, (str, Path)):
                filename = Path(file_data).name
            else:
                filename = f"file_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate unique storage key
        storage_key = generate_unique_key(filename, folder)
        
        # Prepare upload options
        options = UploadOptions(
            content_type=detect_content_type(filename),
            metadata={'original_filename': filename},
            tags=tags,
            access_level=AccessLevel.PUBLIC_READ if public else AccessLevel.PRIVATE
        )
        
        # Upload file
        storage_obj = await self.storage.upload_object(
            self.default_bucket,
            storage_key,
            file_data,
            options
        )
        
        # Generate file ID
        file_id = hashlib.sha256(f"{self.default_bucket}/{storage_key}".encode()).hexdigest()[:16]
        
        # Register file
        self._file_registry[file_id] = {
            'bucket': self.default_bucket,
            'key': storage_key,
            'filename': filename,
            'folder': folder or '',
            'public': public
        }
        
        # Process content if processor is available
        if self.content_processor:
            try:
                await self.content_processor.get_file_info(storage_obj)
            except Exception as e:
                logger.warning(f"Content processing failed for {file_id}: {e}")
        
        logger.info(f"Saved file {filename} with ID {file_id}")
        return file_id
    
    async def get_file(self, file_id: str) -> Optional[StorageObject]:
        """Get a file by its ID."""
        if file_id not in self._file_registry:
            return None
        
        file_info = self._file_registry[file_id]
        try:
            return await self.storage.download_object(
                file_info['bucket'],
                file_info['key']
            )
        except Exception as e:
            logger.error(f"Failed to get file {file_id}: {e}")
            return None
    
    async def get_file_url(
        self,
        file_id: str,
        expiration: Optional[timedelta] = None
    ) -> Optional[str]:
        """Get a URL to access a file."""
        if file_id not in self._file_registry:
            return None
        
        file_info = self._file_registry[file_id]
        expiration = expiration or StorageConfig.DEFAULT_EXPIRATION
        
        try:
            return await self.storage.generate_presigned_url(
                file_info['bucket'],
                file_info['key'],
                expiration
            )
        except Exception as e:
            logger.error(f"Failed to get URL for file {file_id}: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file by its ID."""
        if file_id not in self._file_registry:
            return False
        
        file_info = self._file_registry[file_id]
        success = await self.storage.delete_object(
            file_info['bucket'],
            file_info['key']
        )
        
        if success:
            del self._file_registry[file_id]
            logger.info(f"Deleted file {file_id}")
        
        return success
    
    async def search_files(
        self,
        criteria: SearchCriteria,
        limit: int = 100,
        offset: int = 0
    ) -> List[StorageObject]:
        """Search files based on criteria."""
        # This is a simplified implementation
        # In practice, you'd want to use a proper search index
        
        all_files = []
        for file_id, file_info in self._file_registry.items():
            try:
                metadata = await self.storage.get_object_metadata(
                    file_info['bucket'],
                    file_info['key']
                )
                
                if not metadata:
                    continue
                
                # Apply search criteria
                if criteria.content_type and metadata.content_type != criteria.content_type:
                    continue
                
                if criteria.size_min and metadata.size < criteria.size_min:
                    continue
                
                if criteria.size_max and metadata.size > criteria.size_max:
                    continue
                
                if criteria.created_after and metadata.created_at < criteria.created_after:
                    continue
                
                if criteria.created_before and metadata.created_at > criteria.created_before:
                    continue
                
                # Create storage object
                storage_obj = StorageObject(
                    key=file_info['key'],
                    bucket=file_info['bucket'],
                    metadata=metadata
                )
                
                all_files.append(storage_obj)
                
            except Exception as e:
                logger.warning(f"Error searching file {file_id}: {e}")
                continue
        
        # Apply pagination
        return all_files[offset:offset + limit]
    
    async def get_file_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_files = len(self._file_registry)
        total_size = 0
        content_types = {}
        
        for file_id, file_info in self._file_registry.items():
            try:
                metadata = await self.storage.get_object_metadata(
                    file_info['bucket'],
                    file_info['key']
                )
                
                if metadata:
                    total_size += metadata.size
                    content_type = metadata.content_type
                    content_types[content_type] = content_types.get(content_type, 0) + 1
                    
            except Exception:
                continue
        
        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'content_types': content_types,
            'average_file_size': round(total_size / total_files, 2) if total_files > 0 else 0
        }
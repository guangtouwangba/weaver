"""
AWS S3 storage provider implementation.

This module provides integration with Amazon S3 object storage,
supporting all standard S3 operations through the unified storage interface.
"""

import logging
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError
import io

from ..interfaces import (
    IObjectStorage, StorageProvider, StorageObject, StorageMetadata,
    UploadOptions, DownloadOptions, ListOptions, AccessLevel,
    detect_content_type, ProviderConfig
)

logger = logging.getLogger(__name__)


class AWSS3Storage(IObjectStorage):
    """
    AWS S3 implementation of the object storage interface.
    
    Provides full S3 compatibility including multipart uploads,
    presigned URLs, versioning, and cross-region operations.
    """
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize AWS S3 storage client.
        
        Args:
            config: Provider configuration with AWS credentials and settings
        """
        if config.provider != StorageProvider.AWS_S3:
            raise ValueError(f"Invalid provider: {config.provider}. Expected AWS_S3")
        
        self.config = config
        self.session = None
        self.s3_client = None
        self._initialized = False
        
    async def _ensure_initialized(self):
        """Ensure the S3 client is initialized."""
        if not self._initialized:
            await self._initialize_client()
    
    async def _initialize_client(self):
        """Initialize the boto3 session and S3 client."""
        try:
            # Create aioboto3 session
            self.session = aioboto3.Session(
                aws_access_key_id=self.config.credentials.access_key,
                aws_secret_access_key=self.config.credentials.secret_key,
                region_name=self.config.credentials.region or 'us-east-1'
            )
            
            # Additional AWS-specific configuration
            aws_config = {
                'region_name': self.config.credentials.region or 'us-east-1',
                'connect_timeout': self.config.connect_timeout,
                'read_timeout': self.config.read_timeout,
                'retries': {'max_attempts': self.config.retry_attempts}
            }
            
            # Add endpoint URL if provided (for S3-compatible services)
            if self.config.credentials.endpoint_url:
                aws_config['endpoint_url'] = self.config.credentials.endpoint_url
            
            # Merge with AWS-specific settings
            aws_config.update(self.config.aws_settings)
            
            self.s3_client = self.session.client('s3', **aws_config)
            self._initialized = True
            
            logger.info(f"AWS S3 client initialized for region: {aws_config['region_name']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS S3 client: {e}")
            raise
    
    @property
    def provider(self) -> StorageProvider:
        """Get the storage provider type."""
        return StorageProvider.AWS_S3
    
    async def create_bucket(
        self,
        bucket_name: str,
        region: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Create a new S3 bucket."""
        await self._ensure_initialized()
        
        try:
            create_bucket_config = {}
            target_region = region or self.config.region or 'us-east-1'
            
            # Don't specify LocationConstraint for us-east-1 (default region)
            if target_region != 'us-east-1':
                create_bucket_config['LocationConstraint'] = target_region
            
            await self.s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration=create_bucket_config if create_bucket_config else None
            )
            
            # Configure bucket versioning if enabled
            if self.config.versioning_enabled:
                await self.s3_client.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
            
            # Configure bucket encryption if enabled
            if self.config.encryption_enabled:
                await self.s3_client.put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={
                        'Rules': [{
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256'
                            }
                        }]
                    }
                )
            
            logger.info(f"Created S3 bucket: {bucket_name} in region: {target_region}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'BucketAlreadyExists':
                logger.warning(f"Bucket {bucket_name} already exists")
                return False
            elif error_code == 'BucketAlreadyOwnedByYou':
                logger.info(f"Bucket {bucket_name} already owned by you")
                return True
            else:
                logger.error(f"Failed to create bucket {bucket_name}: {e}")
                raise
    
    async def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete an S3 bucket."""
        await self._ensure_initialized()
        
        try:
            if force:
                # Delete all objects first
                paginator = self.s3_client.get_paginator('list_objects_v2')
                async for page in paginator.paginate(Bucket=bucket_name):
                    if 'Contents' in page:
                        objects = [{'Key': obj['Key']} for obj in page['Contents']]
                        if objects:
                            await self.s3_client.delete_objects(
                                Bucket=bucket_name,
                                Delete={'Objects': objects}
                            )
            
            await self.s3_client.delete_bucket(Bucket=bucket_name)
            logger.info(f"Deleted S3 bucket: {bucket_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete bucket {bucket_name}: {e}")
            return False
    
    async def bucket_exists(self, bucket_name: str) -> bool:
        """Check if S3 bucket exists."""
        await self._ensure_initialized()
        
        try:
            await self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            return False
    
    async def list_buckets(self) -> List[str]:
        """List all S3 buckets."""
        await self._ensure_initialized()
        
        try:
            response = await self.s3_client.list_buckets()
            return [bucket['Name'] for bucket in response.get('Buckets', [])]
        except ClientError as e:
            logger.error(f"Failed to list buckets: {e}")
            return []
    
    async def upload_object(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO, str, Path],
        options: Optional[UploadOptions] = None
    ) -> StorageObject:
        """Upload an object to S3."""
        await self._ensure_initialized()
        
        options = options or UploadOptions()
        
        try:
            # Prepare upload parameters
            upload_args = {
                'Bucket': bucket,
                'Key': key,
            }
            
            # Handle different data types
            if isinstance(data, (str, Path)):
                # File path
                file_path = Path(data)
                with open(file_path, 'rb') as f:
                    body = f.read()
                if not options.content_type:
                    options.content_type = detect_content_type(str(file_path))
            elif isinstance(data, bytes):
                body = data
            elif hasattr(data, 'read'):
                # File-like object
                body = data.read()
                if hasattr(data, 'name') and not options.content_type:
                    options.content_type = detect_content_type(data.name)
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")
            
            upload_args['Body'] = body
            
            # Set content type
            if options.content_type:
                upload_args['ContentType'] = options.content_type
            
            # Set metadata
            if options.metadata:
                upload_args['Metadata'] = options.metadata
            
            # Set tags
            if options.tags:
                tag_set = '&'.join([f"{k}={v}" for k, v in options.tags.items()])
                upload_args['Tagging'] = tag_set
            
            # Set access control
            if options.access_level == AccessLevel.PUBLIC_READ:
                upload_args['ACL'] = 'public-read'
            elif options.access_level == AccessLevel.PUBLIC_READ_WRITE:
                upload_args['ACL'] = 'public-read-write'
            
            # Set server-side encryption if enabled
            if self.config.encryption_enabled:
                upload_args['ServerSideEncryption'] = 'AES256'
            
            # Perform upload
            if len(body) > self.config.multipart_threshold:
                # Use multipart upload for large files
                await self._multipart_upload(upload_args, body)
            else:
                # Simple upload
                await self.s3_client.put_object(**upload_args)
            
            # Get object metadata
            metadata = await self.get_object_metadata(bucket, key)
            
            return StorageObject(
                key=key,
                bucket=bucket,
                metadata=metadata,
                access_level=options.access_level
            )
            
        except ClientError as e:
            logger.error(f"Failed to upload object {key} to bucket {bucket}: {e}")
            raise
    
    async def _multipart_upload(self, upload_args: Dict[str, Any], body: bytes):
        """Perform multipart upload for large objects."""
        bucket = upload_args['Bucket']
        key = upload_args['Key']
        
        # Remove Body from upload_args for multipart initiation
        multipart_args = upload_args.copy()
        del multipart_args['Body']
        
        # Initiate multipart upload
        response = await self.s3_client.create_multipart_upload(**multipart_args)
        upload_id = response['UploadId']
        
        try:
            # Calculate part size and number of parts
            part_size = max(self.config.multipart_threshold // 10, 5 * 1024 * 1024)  # Min 5MB
            total_size = len(body)
            num_parts = (total_size + part_size - 1) // part_size
            
            # Upload parts
            parts = []
            for part_num in range(1, num_parts + 1):
                start = (part_num - 1) * part_size
                end = min(start + part_size, total_size)
                part_data = body[start:end]
                
                part_response = await self.s3_client.upload_part(
                    Bucket=bucket,
                    Key=key,
                    PartNumber=part_num,
                    UploadId=upload_id,
                    Body=part_data
                )
                
                parts.append({
                    'ETag': part_response['ETag'],
                    'PartNumber': part_num
                })
            
            # Complete multipart upload
            await self.s3_client.complete_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
        except Exception as e:
            # Abort multipart upload on error
            await self.s3_client.abort_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id
            )
            raise e
    
    async def download_object(
        self,
        bucket: str,
        key: str,
        options: Optional[DownloadOptions] = None
    ) -> StorageObject:
        """Download an object from S3."""
        await self._ensure_initialized()
        
        options = options or DownloadOptions()
        
        try:
            get_args = {
                'Bucket': bucket,
                'Key': key,
            }
            
            # Set version if specified
            if options.version:
                get_args['VersionId'] = options.version
            
            # Set range if specified
            if options.range_start is not None or options.range_end is not None:
                start = options.range_start or 0
                end = options.range_end or ''
                get_args['Range'] = f'bytes={start}-{end}'
            
            # Set conditional headers
            if options.if_modified_since:
                get_args['IfModifiedSince'] = options.if_modified_since
            
            if options.if_unmodified_since:
                get_args['IfUnmodifiedSince'] = options.if_unmodified_since
            
            response = await self.s3_client.get_object(**get_args)
            
            # Read content
            async with response['Body'] as stream:
                content = await stream.read()
            
            # Create metadata
            metadata = StorageMetadata(
                size=response.get('ContentLength', len(content)),
                content_type=response.get('ContentType', 'application/octet-stream'),
                created_at=response.get('LastModified', datetime.utcnow()),
                modified_at=response.get('LastModified', datetime.utcnow()),
                etag=response.get('ETag', '').strip('"'),
                version=response.get('VersionId'),
                custom_metadata=response.get('Metadata', {})
            )
            
            return StorageObject(
                key=key,
                bucket=bucket,
                metadata=metadata,
                content=content
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
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
        try:
            storage_object = await self.download_object(bucket, key, options)
            if storage_object and storage_object.content:
                with open(file_path, 'wb') as f:
                    f.write(storage_object.content)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to download object {key} to file {file_path}: {e}")
            return False
    
    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete an object from S3."""
        await self._ensure_initialized()
        
        try:
            await self.s3_client.delete_object(Bucket=bucket, Key=key)
            logger.debug(f"Deleted object {key} from bucket {bucket}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete object {key} from bucket {bucket}: {e}")
            return False
    
    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists in S3."""
        await self._ensure_initialized()
        
        try:
            await self.s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False
    
    async def get_object_metadata(self, bucket: str, key: str) -> Optional[StorageMetadata]:
        """Get metadata for an S3 object."""
        await self._ensure_initialized()
        
        try:
            response = await self.s3_client.head_object(Bucket=bucket, Key=key)
            
            return StorageMetadata(
                size=response.get('ContentLength', 0),
                content_type=response.get('ContentType', 'application/octet-stream'),
                created_at=response.get('LastModified', datetime.utcnow()),
                modified_at=response.get('LastModified', datetime.utcnow()),
                etag=response.get('ETag', '').strip('"'),
                version=response.get('VersionId'),
                custom_metadata=response.get('Metadata', {})
            )
        except ClientError:
            return None
    
    async def update_object_metadata(
        self,
        bucket: str,
        key: str,
        metadata: Dict[str, str]
    ) -> bool:
        """Update metadata for an existing S3 object."""
        await self._ensure_initialized()
        
        try:
            # S3 requires copying the object to update metadata
            copy_source = {'Bucket': bucket, 'Key': key}
            
            await self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=bucket,
                Key=key,
                Metadata=metadata,
                MetadataDirective='REPLACE'
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to update metadata for object {key}: {e}")
            return False
    
    async def list_objects(
        self,
        bucket: str,
        options: Optional[ListOptions] = None
    ) -> List[StorageObject]:
        """List objects in an S3 bucket."""
        await self._ensure_initialized()
        
        options = options or ListOptions()
        objects = []
        
        try:
            list_args = {
                'Bucket': bucket,
                'MaxKeys': min(options.max_keys, 1000),  # S3 limit
            }
            
            if options.prefix:
                list_args['Prefix'] = options.prefix
            
            if options.continuation_token:
                list_args['ContinuationToken'] = options.continuation_token
            
            response = await self.s3_client.list_objects_v2(**list_args)
            
            for obj in response.get('Contents', []):
                key = obj['Key']
                
                # Apply suffix filter if specified
                if options.suffix and not key.endswith(options.suffix):
                    continue
                
                metadata = StorageMetadata(
                    size=obj.get('Size', 0),
                    created_at=obj.get('LastModified', datetime.utcnow()),
                    modified_at=obj.get('LastModified', datetime.utcnow()),
                    etag=obj.get('ETag', '').strip('"')
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
            
            return objects
            
        except ClientError as e:
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
        """Copy an object within or between S3 buckets."""
        await self._ensure_initialized()
        
        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            copy_args = {
                'CopySource': copy_source,
                'Bucket': dest_bucket,
                'Key': dest_key,
            }
            
            if metadata:
                copy_args['Metadata'] = metadata
                copy_args['MetadataDirective'] = 'REPLACE'
            
            await self.s3_client.copy_object(**copy_args)
            logger.debug(f"Copied object from {source_bucket}/{source_key} to {dest_bucket}/{dest_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to copy object: {e}")
            return False
    
    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration: timedelta = timedelta(hours=1),
        method: str = "GET"
    ) -> str:
        """Generate a presigned URL for S3 object access."""
        await self._ensure_initialized()
        
        try:
            operation_map = {
                'GET': 'get_object',
                'PUT': 'put_object',
                'DELETE': 'delete_object'
            }
            
            operation = operation_map.get(method.upper(), 'get_object')
            
            url = await self.s3_client.generate_presigned_url(
                operation,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=int(expiration.total_seconds())
            )
            
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {bucket}/{key}: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the S3 service is healthy."""
        await self._ensure_initialized()
        
        try:
            # Try to list buckets as a health check
            await self.s3_client.list_buckets()
            return True
        except Exception as e:
            logger.error(f"S3 health check failed: {e}")
            return False
    
    async def close(self):
        """Close the S3 client connection."""
        if self.s3_client:
            await self.s3_client.close()
            self._initialized = False
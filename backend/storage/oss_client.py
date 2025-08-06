#!/usr/bin/env python3
"""
Alibaba Cloud OSS Client for ArXiv Paper Storage
Based on the official Alibaba Cloud OSS Python SDK
https://github.com/aliyun/aliyun-oss-python-sdk

Handles PDF upload, download, and management in OSS buckets.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import hashlib
import tempfile
from datetime import datetime
import threading
import time

try:
    import oss2
    from oss2 import SizedFileAdapter, determine_part_size
    from oss2.models import PartInfo
    OSS_AVAILABLE = True
except ImportError:
    OSS_AVAILABLE = False
    logging.warning("OSS2 library not available. OSS functionality will be disabled.")

logger = logging.getLogger(__name__)

class OSSClient:
    """Alibaba Cloud OSS client for paper storage"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OSS client with configuration
        
        Args:
            config: OSS configuration dictionary
        """
        if not OSS_AVAILABLE:
            raise ImportError("oss2 library is required for OSS functionality. Install with: pip install oss2")
        
        self.config = config
        self._validate_config()
        self._init_client()
    
    def _validate_config(self):
        """Validate OSS configuration"""
        required_fields = ['endpoint', 'access_key_id', 'access_key_secret', 'bucket_name']
        
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required OSS config field: {field}")
        
        # Handle environment variable substitution
        for field in ['access_key_id', 'access_key_secret']:
            value = self.config[field]
            if value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                env_value = os.getenv(env_var)
                if not env_value:
                    raise ValueError(f"Environment variable {env_var} not set")
                self.config[field] = env_value
    
    def _init_client(self):
        """Initialize OSS client and bucket with optimized timeouts"""
        try:
            # Create auth object
            auth = oss2.Auth(
                self.config['access_key_id'], 
                self.config['access_key_secret']
            )
            
            # Create session with shorter timeouts
            session = oss2.Session()
            session.adapters['http://'].init_poolmanager(
                connections=10,
                maxsize=10,
                block=False,
                timeout=10,  # 10 second timeout instead of 60
                retries=2    # Only 2 retries instead of default
            )
            session.adapters['https://'].init_poolmanager(
                connections=10,
                maxsize=10,
                block=False,
                timeout=10,  # 10 second timeout instead of 60
                retries=2    # Only 2 retries instead of default
            )
            
            # Create bucket object with custom session
            self.bucket = oss2.Bucket(
                auth, 
                self.config['endpoint'], 
                self.config['bucket_name'],
                session=session
            )
            
            # Test connection with timeout
            self._test_connection()
            
            logger.info(f"OSS client initialized successfully for bucket: {self.config['bucket_name']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OSS client: {e}")
            raise
    
    def _test_connection(self):
        """Test OSS connection and permissions"""
        try:
            # Test by checking if bucket exists
            self.bucket.get_bucket_info()
            logger.info("OSS connection test passed")
        except oss2.exceptions.NoSuchBucket:
            raise ValueError(f"OSS bucket '{self.config['bucket_name']}' does not exist")
        except oss2.exceptions.AccessDenied:
            raise ValueError("OSS access denied. Check your credentials and permissions")
        except Exception as e:
            raise ValueError(f"OSS connection test failed: {e}")
    
    def _generate_object_key(self, arxiv_id: str, published_date: datetime) -> str:
        """
        Generate OSS object key for a paper
        
        Args:
            arxiv_id: ArXiv paper ID
            published_date: Paper publication date
            
        Returns:
            OSS object key path
        """
        base_prefix = self.config.get('base_prefix', 'papers')
        filename_format = self.config.get('filename_format', '{arxiv_id}.pdf')
        create_subdirs = self.config.get('create_subdirectories', True)
        
        # Format filename
        filename = filename_format.format(
            arxiv_id=arxiv_id,
            title_safe=arxiv_id,  # Fallback to arxiv_id for safety
            date=published_date.strftime('%Y-%m-%d')
        )
        
        # Build object key
        if create_subdirs:
            date_prefix = published_date.strftime('%Y-%m-%d')
            object_key = f"{base_prefix}/{date_prefix}/{filename}"
        else:
            object_key = f"{base_prefix}/{filename}"
        
        return object_key
    
    def upload_file(self, local_file_path: str, arxiv_id: str, published_date: datetime) -> str:
        """
        Upload a PDF file to OSS
        
        Args:
            local_file_path: Path to local PDF file
            arxiv_id: ArXiv paper ID
            published_date: Paper publication date
            
        Returns:
            OSS object key of uploaded file
        """
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"Local file not found: {local_file_path}")
        
        object_key = self._generate_object_key(arxiv_id, published_date)
        
        try:
            # Note: File existence check is done by StorageManager to avoid duplicate checks
            # Get file size for progress tracking
            file_size = os.path.getsize(local_file_path)
            multipart_threshold = self.config.get('multipart_threshold', 100) * 1024 * 1024  # Convert MB to bytes
            
            # Choose upload method based on file size
            if file_size > multipart_threshold:
                self._upload_multipart(local_file_path, object_key, file_size)
            else:
                self._upload_simple(local_file_path, object_key)
            
            logger.info(f"Successfully uploaded {local_file_path} to OSS: {object_key}")
            return object_key
            
        except Exception as e:
            logger.error(f"Failed to upload {local_file_path} to OSS: {e}")
            raise
    
    def _upload_simple(self, local_file_path: str, object_key: str):
        """Simple upload for smaller files"""
        with open(local_file_path, 'rb') as file:
            result = self.bucket.put_object(object_key, file)
            
            if result.status != 200:
                raise Exception(f"Upload failed with status: {result.status}")
    
    def _upload_multipart(self, local_file_path: str, object_key: str, file_size: int):
        """
        Multipart upload for larger files using official SDK best practices
        Uses automatic part size calculation and progress tracking
        """
        # Calculate optimal part size (recommended by official SDK)
        part_size = determine_part_size(file_size, preferred_size=10 * 1024 * 1024)  # 10MB preferred
        
        # Initialize multipart upload with optional server-side encryption
        init_headers = {}
        if self.config.get('server_side_encryption', False):
            init_headers['x-oss-server-side-encryption'] = 'AES256'
        
        upload_id = self.bucket.init_multipart_upload(object_key, headers=init_headers).upload_id
        logger.info(f"Initialized multipart upload for {object_key}, upload_id: {upload_id}")
        
        try:
            parts = []
            part_number = 1
            uploaded_size = 0
            
            # Use SizedFileAdapter for better memory management
            with open(local_file_path, 'rb') as file:
                while uploaded_size < file_size:
                    # Calculate this part's size
                    this_part_size = min(part_size, file_size - uploaded_size)
                    
                    # Create SizedFileAdapter for this part
                    adapter = SizedFileAdapter(file, this_part_size)
                    
                    # Upload part with retry logic
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            result = self.bucket.upload_part(object_key, upload_id, part_number, adapter)
                            parts.append(PartInfo(part_number, result.etag))
                            break
                        except Exception as e:
                            if attempt == max_retries - 1:
                                raise e
                            logger.warning(f"Part {part_number} upload failed (attempt {attempt + 1}), retrying: {e}")
                            time.sleep(2 ** attempt)  # Exponential backoff
                            file.seek(uploaded_size)  # Reset file position
                            adapter = SizedFileAdapter(file, this_part_size)
                    
                    uploaded_size += this_part_size
                    progress = (uploaded_size / file_size) * 100
                    logger.info(f"Uploaded part {part_number}/{((file_size - 1) // part_size) + 1} ({progress:.1f}%)")
                    part_number += 1
            
            # Complete multipart upload
            self.bucket.complete_multipart_upload(object_key, upload_id, parts)
            logger.info(f"Completed multipart upload for {object_key}")
            
        except Exception as e:
            # Abort multipart upload on failure
            try:
                self.bucket.abort_multipart_upload(object_key, upload_id)
                logger.info(f"Aborted multipart upload for {object_key}")
            except:
                pass
            raise e
    
    def download_file(self, object_key: str, local_file_path: str) -> bool:
        """
        Download a file from OSS to local path
        
        Args:
            object_key: OSS object key
            local_file_path: Local destination path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            
            # Download file
            self.bucket.get_object_to_file(object_key, local_file_path)
            
            logger.info(f"Downloaded {object_key} to {local_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {object_key}: {e}")
            return False
    
    def object_exists(self, object_key: str) -> bool:
        """
        Check if an object exists in OSS
        
        Args:
            object_key: OSS object key to check
            
        Returns:
            True if object exists, False otherwise
        """
        try:
            self.bucket.head_object(object_key)
            return True
        except oss2.exceptions.NoSuchKey:
            return False
        except Exception as e:
            logger.error(f"Error checking object existence {object_key}: {e}")
            return False
    
    def get_object_url(self, object_key: str, expires: int = 3600) -> str:
        """
        Generate a signed URL for accessing an object
        
        Args:
            object_key: OSS object key
            expires: URL expiration time in seconds
            
        Returns:
            Signed URL for the object
        """
        try:
            return self.bucket.sign_url('GET', object_key, expires)
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {object_key}: {e}")
            return ""
    
    def delete_object(self, object_key: str) -> bool:
        """
        Delete an object from OSS
        
        Args:
            object_key: OSS object key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.bucket.delete_object(object_key)
            logger.info(f"Deleted object: {object_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {object_key}: {e}")
            return False
    
    def list_objects(self, prefix: str = "", max_keys: int = 100) -> list:
        """
        List objects in the bucket with optional prefix
        
        Args:
            prefix: Object key prefix to filter
            max_keys: Maximum number of objects to return
            
        Returns:
            List of object information dictionaries
        """
        try:
            objects = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix, max_keys=max_keys):
                objects.append({
                    'key': obj.key,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag
                })
            
            return objects
            
        except Exception as e:
            logger.error(f"Failed to list objects with prefix {prefix}: {e}")
            return []
    
    def get_bucket_info(self) -> Dict[str, Any]:
        """
        Get bucket information and statistics
        
        Returns:
            Dictionary with bucket information
        """
        try:
            bucket_info = self.bucket.get_bucket_info()
            
            return {
                'name': bucket_info.name,
                'location': bucket_info.location,
                'creation_date': bucket_info.creation_date,
                'storage_class': bucket_info.storage_class,
                'owner': bucket_info.owner.display_name if bucket_info.owner else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get bucket info: {e}")
            return {}

# Utility function for creating OSS client from config
def create_oss_client(config: Dict[str, Any]) -> Optional[OSSClient]:
    """
    Create OSS client from configuration
    
    Args:
        config: OSS configuration dictionary
        
    Returns:
        OSSClient instance or None if OSS not available
    """
    if not OSS_AVAILABLE:
        logger.warning("OSS2 library not available. Cannot create OSS client.")
        return None
    
    try:
        return OSSClient(config)
    except Exception as e:
        logger.error(f"Failed to create OSS client: {e}")
        return None
"""Supabase Storage service for file uploads."""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import BinaryIO, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class PresignedUrlResponse:
    """Response from presigned URL generation."""
    upload_url: str
    file_path: str
    token: str
    expires_at: datetime


@dataclass
class SignedDownloadUrlResponse:
    """Response from signed download URL generation."""
    signed_url: str
    expires_at: datetime


class SupabaseStorageService:
    """Service for interacting with Supabase Storage."""

    def __init__(
        self,
        supabase_url: str,
        service_role_key: str,
        bucket_name: str = "documents",
    ):
        self.supabase_url = supabase_url.rstrip("/")
        self.service_role_key = service_role_key
        self.bucket_name = bucket_name
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def storage_url(self) -> str:
        """Get the storage API URL."""
        return f"{self.supabase_url}/storage/v1"

    @property
    def headers(self) -> dict:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {self.service_role_key}",
            "apikey": self.service_role_key,
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def create_signed_upload_url(
        self,
        project_id: str,
        filename: str,
    ) -> PresignedUrlResponse:
        """
        Create a signed URL for uploading a file.
        
        Args:
            project_id: The project ID to organize files under
            filename: Original filename
            
        Returns:
            PresignedUrlResponse with upload URL, file path, and expiration
        """
        # Generate unique file path: projects/{project_id}/{uuid}_{filename}
        file_id = str(uuid.uuid4())
        # Sanitize filename (remove special chars)
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        file_path = f"projects/{project_id}/{file_id}_{safe_filename}"
        
        client = await self._get_client()
        
        # Call Supabase Storage API to create signed upload URL
        url = f"{self.storage_url}/object/upload/sign/{self.bucket_name}/{file_path}"
        
        logger.info(f"Creating signed upload URL for: {file_path}")
        
        response = await client.post(
            url,
            headers=self.headers,
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to create signed upload URL: {response.status_code} - {response.text}")
            raise Exception(f"Failed to create signed upload URL: {response.text}")
        
        data = response.json()
        
        # The response contains a token that must be used for upload
        token = data.get("token", "")
        
        # Construct the full upload URL
        upload_url = f"{self.storage_url}/object/upload/{self.bucket_name}/{file_path}?token={token}"
        
        # Signed URLs are valid for 2 hours by default
        expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
        
        return PresignedUrlResponse(
            upload_url=upload_url,
            file_path=file_path,
            token=token,
            expires_at=expires_at,
        )

    async def create_signed_download_url(
        self,
        file_path: str,
        expires_in_seconds: int = 3600,
    ) -> SignedDownloadUrlResponse:
        """
        Create a signed URL for downloading a file.
        
        Args:
            file_path: The path to the file in storage
            expires_in_seconds: How long the URL should be valid (default 1 hour)
            
        Returns:
            SignedDownloadUrlResponse with signed URL and expiration
        """
        client = await self._get_client()
        
        url = f"{self.storage_url}/object/sign/{self.bucket_name}/{file_path}"
        
        response = await client.post(
            url,
            headers=self.headers,
            json={"expiresIn": expires_in_seconds},
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to create signed download URL: {response.status_code} - {response.text}")
            raise Exception(f"Failed to create signed download URL: {response.text}")
        
        data = response.json()
        signed_url = f"{self.supabase_url}/storage/v1{data['signedURL']}"
        
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        
        return SignedDownloadUrlResponse(
            signed_url=signed_url,
            expires_at=expires_at,
        )

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            file_path: The path to the file in storage
            
        Returns:
            True if file exists, False otherwise
        """
        client = await self._get_client()
        
        # Use HEAD request to check if file exists
        url = f"{self.storage_url}/object/{self.bucket_name}/{file_path}"
        
        response = await client.head(url, headers=self.headers)
        
        return response.status_code == 200

    async def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        Get file metadata from storage.
        
        Args:
            file_path: The path to the file in storage
            
        Returns:
            File metadata dict or None if not found
        """
        client = await self._get_client()
        
        url = f"{self.storage_url}/object/info/{self.bucket_name}/{file_path}"
        
        response = await client.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return None
        
        return response.json()

    async def download_file(self, file_path: str) -> bytes:
        """
        Download a file from storage.
        
        Args:
            file_path: The path to the file in storage
            
        Returns:
            File content as bytes
        """
        client = await self._get_client()
        
        url = f"{self.storage_url}/object/{self.bucket_name}/{file_path}"
        
        response = await client.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to download file: {response.text}")
        
        return response.content

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: The path to the file in storage
            
        Returns:
            True if deleted successfully
        """
        client = await self._get_client()
        
        url = f"{self.storage_url}/object/{self.bucket_name}"
        
        response = await client.delete(
            url,
            headers=self.headers,
            json={"prefixes": [file_path]},
        )
        
        return response.status_code == 200

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


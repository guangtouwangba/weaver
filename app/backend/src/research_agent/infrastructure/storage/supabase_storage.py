"""Supabase Storage service for file uploads."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import BinaryIO, Optional

import httpx

from research_agent.shared.utils.logger import setup_logger

logger = setup_logger(__name__)

# Singleton instance for the storage service
_supabase_storage_instance: Optional["SupabaseStorageService"] = None


def get_supabase_storage() -> Optional["SupabaseStorageService"]:
    """
    Get a singleton instance of SupabaseStorageService.

    Returns:
        SupabaseStorageService instance if configured, None otherwise.
    """
    global _supabase_storage_instance

    if _supabase_storage_instance is not None:
        return _supabase_storage_instance

    # Lazy import to avoid circular imports
    from research_agent.config import get_settings

    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_service_role_key:
        logger.warning("Supabase Storage not configured (missing URL or service role key)")
        return None

    _supabase_storage_instance = SupabaseStorageService(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
    )

    return _supabase_storage_instance


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
            # Explicitly disable proxy to avoid SOCKS proxy issues
            # trust_env=False disables reading proxy settings from environment variables
            self._client = httpx.AsyncClient(
                timeout=30.0,
                trust_env=False,  # Disable proxy from environment variables
            )
        return self._client

    async def create_signed_upload_url(
        self,
        project_id: str,
        filename: str,
        user_id: str,
    ) -> PresignedUrlResponse:
        """
        Create a signed URL for uploading a file.

        Args:
            project_id: The project ID to organize files under
            filename: Original filename
            user_id: The user ID to scope files under

        Returns:
            PresignedUrlResponse with upload URL, file path, and expiration
        """
        # Generate unique file path: {user_id}/projects/{project_id}/{uuid}.{extension}
        file_id = str(uuid.uuid4())

        # Extract file extension from original filename
        ext = ""
        if "." in filename:
            ext = filename.rsplit(".", 1)[-1].lower()
            # Only keep safe extensions
            if ext not in ["pdf", "txt", "md", "docx", "doc"]:
                ext = "pdf"  # Default to pdf
        else:
            ext = "pdf"

        # Use only UUID and extension for the storage path (no Chinese chars)
        # This avoids "Invalid key" errors from Supabase
        file_path = f"{user_id}/projects/{project_id}/{file_id}.{ext}"

        client = await self._get_client()

        # Call Supabase Storage API to create signed upload URL
        # See: https://supabase.com/docs/reference/python/storage-from-createsigneduploadurl
        url = f"{self.storage_url}/object/upload/sign/{self.bucket_name}/{file_path}"

        logger.info(f"[Supabase Storage] Creating signed upload URL")
        logger.info(f"[Supabase Storage] Request URL: {url}")
        logger.info(f"[Supabase Storage] Bucket: {self.bucket_name}")
        logger.info(f"[Supabase Storage] File path: {file_path}")
        logger.debug(f"[Supabase Storage] Headers: {list(self.headers.keys())}")

        try:
            response = await client.post(
                url,
                headers=self.headers,
            )

            logger.info(f"[Supabase Storage] Response status: {response.status_code}")
            logger.debug(f"[Supabase Storage] Response headers: {dict(response.headers)}")
            logger.debug(
                f"[Supabase Storage] Response body: {response.text[:500]}"
            )  # First 500 chars

            if response.status_code != 200:
                logger.error(
                    f"[Supabase Storage] Failed to create signed upload URL: "
                    f"status={response.status_code}, body={response.text}"
                )
                raise Exception(
                    f"Failed to create signed upload URL: {response.status_code} - {response.text}"
                )
        except httpx.ProxyError as e:
            logger.error(f"[Supabase Storage] Proxy error: {e}")
            raise Exception(
                f"Proxy configuration error: {e}. Please check HTTP_PROXY/HTTPS_PROXY environment variables."
            )
        except httpx.RequestError as e:
            logger.error(f"[Supabase Storage] Request error: {e}")
            raise Exception(f"Request failed: {e}")
        except Exception as e:
            logger.error(f"[Supabase Storage] Unexpected error: {e}", exc_info=True)
            raise

        data = response.json()

        # The response contains a token that we use to authorize the upload
        token = data.get("token", "")

        # For uploadToSignedUrl, we need to PUT to /object/{bucket}/{path}
        # with the token as a query parameter or Authorization header
        # See: https://supabase.com/docs/reference/javascript/storage-from-uploadtosignedurl
        upload_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{file_path}"

        logger.info(f"Supabase response: {data}")
        logger.info(f"Generated upload URL: {upload_url}")
        logger.info(f"Token (first 20 chars): {token[:20]}...")

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

        logger.info(f"[Supabase Storage] Creating signed download URL for: {file_path}")
        logger.debug(f"[Supabase Storage] Request URL: {url}")
        logger.debug(f"[Supabase Storage] Expires in: {expires_in_seconds}s")

        try:
            response = await client.post(
                url,
                headers=self.headers,
                json={"expiresIn": expires_in_seconds},
            )

            logger.debug(f"[Supabase Storage] Response status: {response.status_code}")
            logger.debug(f"[Supabase Storage] Response body: {response.text[:500]}")

            if response.status_code != 200:
                logger.error(
                    f"[Supabase Storage] Failed to create signed download URL: "
                    f"status={response.status_code}, body={response.text}"
                )
                raise Exception(
                    f"Failed to create signed download URL: {response.status_code} - {response.text}"
                )
        except httpx.ProxyError as e:
            logger.error(f"[Supabase Storage] Proxy error: {e}")
            raise Exception(f"Proxy configuration error: {e}")
        except httpx.RequestError as e:
            logger.error(f"[Supabase Storage] Request error: {e}")
            raise Exception(f"Request failed: {e}")

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

        logger.info(f"[Supabase Storage] Downloading file: {file_path}")
        logger.debug(f"[Supabase Storage] Request URL: {url}")

        try:
            response = await client.get(url, headers=self.headers)

            logger.debug(f"[Supabase Storage] Response status: {response.status_code}")
            logger.debug(
                f"[Supabase Storage] Content length: {len(response.content) if response.status_code == 200 else 0} bytes"
            )

            if response.status_code != 200:
                logger.error(
                    f"[Supabase Storage] Failed to download file: "
                    f"status={response.status_code}, body={response.text[:500]}"
                )
                raise Exception(
                    f"Failed to download file: {response.status_code} - {response.text}"
                )

            return response.content
        except httpx.ProxyError as e:
            logger.error(f"[Supabase Storage] Proxy error: {e}")
            raise Exception(f"Proxy configuration error: {e}")
        except httpx.RequestError as e:
            logger.error(f"[Supabase Storage] Request error: {e}")
            raise Exception(f"Request failed: {e}")

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: The path to the file in storage

        Returns:
            True if deleted successfully
        """
        client = await self._get_client()

        # Supabase Storage delete API uses DELETE with path in URL
        # See: https://supabase.com/docs/reference/javascript/storage-from-remove
        url = f"{self.storage_url}/object/{self.bucket_name}/{file_path}"

        logger.info(f"Deleting file from Supabase Storage: {url}")

        response = await client.delete(url, headers=self.headers)

        logger.info(f"Delete response status: {response.status_code}, body: {response.text}")

        if response.status_code not in [200, 204]:
            logger.warning(f"Failed to delete file: {response.status_code} - {response.text}")
            return False

        return True

    async def delete_directory(self, folder_path: str) -> bool:
        """
        Delete a folder and all its contents from storage.

        Args:
            folder_path: The path to the folder in storage (e.g., "projects/{project_id}")

        Returns:
            True if deleted successfully
        """
        client = await self._get_client()

        # List all files in the folder
        list_url = f"{self.storage_url}/object/list/{self.bucket_name}"

        logger.info(f"Listing files in folder: {folder_path}")

        response = await client.post(
            list_url,
            headers=self.headers,
            json={
                "prefix": folder_path,
                "limit": 1000,  # Max files to list
            },
        )

        if response.status_code != 200:
            logger.warning(
                f"Failed to list files in folder: {response.status_code} - {response.text}"
            )
            return False

        files = response.json()

        if not files:
            logger.info(f"No files found in folder: {folder_path}")
            return True

        # Delete all files in batch
        file_paths = [f"{folder_path}/{f['name']}" for f in files if "name" in f]

        if not file_paths:
            return True

        logger.info(f"Deleting {len(file_paths)} files from folder: {folder_path}")

        # Supabase Storage batch delete API
        # See: https://supabase.com/docs/reference/javascript/storage-from-remove
        delete_url = f"{self.storage_url}/object/{self.bucket_name}"

        response = await client.delete(
            delete_url, headers=self.headers, json={"prefixes": [folder_path]}
        )

        logger.info(f"Delete folder response status: {response.status_code}, body: {response.text}")

        if response.status_code not in [200, 204]:
            logger.warning(f"Failed to delete folder: {response.status_code} - {response.text}")
            return False

        return True

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

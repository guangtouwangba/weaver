"""Local file storage implementation."""

import asyncio
import os
import shutil
from pathlib import Path
from typing import BinaryIO

from research_agent.infrastructure.storage.base import StorageService
from research_agent.shared.exceptions import StorageError


class LocalStorageService(StorageService):
    """Local file system storage service."""

    def __init__(self, base_dir: str):
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, path: str, content: BinaryIO) -> str:
        """Save file to local storage."""
        try:
            full_path = self._base_dir / path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Run file write in thread pool
            await asyncio.to_thread(self._write_file, full_path, content)

            return str(full_path)
        except Exception as e:
            raise StorageError(f"Failed to save file: {e}")

    def _write_file(self, path: Path, content: BinaryIO) -> None:
        """Synchronous file write."""
        with open(path, "wb") as f:
            shutil.copyfileobj(content, f)

    async def delete(self, path: str) -> bool:
        """Delete file from local storage."""
        try:
            full_path = self._base_dir / path
            if full_path.exists():
                await asyncio.to_thread(full_path.unlink)
                return True
            return False
        except Exception as e:
            raise StorageError(f"Failed to delete file: {e}")

    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        full_path = self._base_dir / path
        return full_path.exists()

    def get_full_path(self, path: str) -> str:
        """Get full file system path."""
        return str(self._base_dir / path)

    async def delete_directory(self, path: str) -> bool:
        """Delete directory and all its contents."""
        try:
            full_path = self._base_dir / path
            if full_path.exists() and full_path.is_dir():
                await asyncio.to_thread(shutil.rmtree, full_path)
                return True
            return False
        except Exception as e:
            raise StorageError(f"Failed to delete directory: {e}")


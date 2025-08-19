from infrastructure.database.models.file import File, FileStatus
from infrastructure.database.repositories import BaseRepository
from typing import List, Optional


class FileRepository(BaseRepository[File]):
    """Repository for File entities."""

    def __init__(self, session):
        super().__init__(session, File)

    async def get_by_storage_key(self, storage_key: str) -> Optional[File]:
        """Get a file by its storage key."""
        return await self.session.query(File).filter(File.storage_key == storage_key).first()

    async def mark_as_deleted(self, file_id: str) -> None:
        """Mark a file as deleted."""
        file = await self.get(file_id)
        if file:
            file.mark_as_deleted()
            await self.session.commit()

    async def get(self, file_id: str) -> Optional[File]:
        """Get a file by its ID."""
        return await self.session.query(File).filter(File.id == file_id).first()

    async def get_by_status(self, status: FileStatus, limit: Optional[int] = None) -> List[File]:
        """Get files by status."""
        query = self.session.query(File).filter(File.status == status)
        if limit:
            query = query.limit(limit)
        return await query.all()

    async def get_available_files(self, limit: Optional[int] = None) -> List[File]:
        """Get all available files."""
        return await self.get_by_status(FileStatus.AVAILABLE, limit)

    async def get_processing_files(self, limit: Optional[int] = None) -> List[File]:
        """Get all files currently being processed."""
        return await self.get_by_status(FileStatus.PROCESSING, limit)

    async def get_failed_files(self, limit: Optional[int] = None) -> List[File]:
        """Get all failed files."""
        return await self.get_by_status(FileStatus.FAILED, limit)

    async def update_status(self, file_id: str, new_status: FileStatus) -> Optional[File]:
        """Update file status."""
        file = await self.get(file_id)
        if file:
            file.status = new_status
            await self.session.commit()
            await self.session.refresh(file)
        return file

    async def mark_as_processing(self, file_id: str) -> Optional[File]:
        """Mark file as processing."""
        return await self.update_status(file_id, FileStatus.PROCESSING)

    async def mark_as_available(self, file_id: str) -> Optional[File]:
        """Mark file as available."""
        return await self.update_status(file_id, FileStatus.AVAILABLE)

    async def mark_as_failed(self, file_id: str) -> Optional[File]:
        """Mark file as failed."""
        return await self.update_status(file_id, FileStatus.FAILED)

    async def get_files_by_topic_and_status(self, topic_id: int, status: FileStatus) -> List[File]:
        """Get files by topic ID and status."""
        return await self.session.query(File).filter(
            File.topic_id == topic_id,
            File.status == status
        ).all()

    async def count_by_status(self, status: FileStatus) -> int:
        """Count files by status."""
        return await self.session.query(File).filter(File.status == status).count()

    async def get_status_summary(self) -> dict:
        """Get summary of file counts by status."""
        summary = {}
        for status in FileStatus:
            count = await self.count_by_status(status)
            summary[status.value] = count
        return summary

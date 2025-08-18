"""
Upload completion monitoring service.

This module provides background monitoring for orphaned uploads - files that were
uploaded to storage but never confirmed via the completion endpoint.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

from domain.fileupload import FileStatus
from infrastructure.tasks.service import process_file_complete
from infrastructure.tasks.models import TaskPriority

logger = logging.getLogger(__name__)


class UploadMonitorService:
    """
    Background service that monitors for orphaned uploads.
    
    This service periodically checks for files in UPLOADING status that
    have been uploaded to storage but not confirmed via the completion endpoint.
    """
    
    def __init__(
        self,
        check_interval: int = 300,  # 5 minutes
        orphan_threshold: int = 1800,  # 30 minutes
        max_concurrent_checks: int = 10
    ):
        self.check_interval = check_interval
        self.orphan_threshold = orphan_threshold
        self.max_concurrent_checks = max_concurrent_checks
        self._running = False
        self._background_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start the background monitoring service."""
        if self._running:
            logger.warning("Upload monitor already running")
            return
            
        self._running = True
        self._background_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started upload monitor (interval: {self.check_interval}s, threshold: {self.orphan_threshold}s)")
    
    async def stop(self) -> None:
        """Stop the background monitoring service."""
        if not self._running:
            return
            
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped upload monitor")
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check_orphaned_uploads()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Upload monitor error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_orphaned_uploads(self) -> None:
        """Check for and handle orphaned uploads."""
        try:
            # Get orphaned uploads from database
            orphaned_files = await self._find_orphaned_uploads()
            
            if not orphaned_files:
                logger.debug("No orphaned uploads found")
                return
            
            logger.info(f"Found {len(orphaned_files)} potentially orphaned uploads")
            
            # Process orphaned files in batches
            semaphore = asyncio.Semaphore(self.max_concurrent_checks)
            tasks = [
                self._process_orphaned_file(file_info, semaphore)
                for file_info in orphaned_files
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            processed = sum(1 for r in results if r is True)
            errors = sum(1 for r in results if isinstance(r, Exception))
            
            logger.info(f"Processed {processed} orphaned uploads, {errors} errors")
            
        except Exception as e:
            logger.error(f"Failed to check orphaned uploads: {e}")
    
    async def _find_orphaned_uploads(self) -> List[Dict[str, Any]]:
        """Find files in UPLOADING status that may be orphaned."""
        try:
            import asyncpg
            
            threshold_time = datetime.utcnow() - timedelta(seconds=self.orphan_threshold)
            
            conn = await asyncpg.connect('postgresql://rag_user:rag_password@localhost:5432/rag_db')
            
            rows = await conn.fetch('''
                SELECT 
                    id, owner_id, original_name, file_size, content_type,
                    storage_bucket, storage_key, topic_id, created_at, updated_at
                FROM files 
                WHERE status = 'uploading' 
                AND created_at < $1
                AND (updated_at IS NULL OR updated_at < $1)
                ORDER BY created_at ASC
                LIMIT 50
            ''', threshold_time)
            
            await conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to find orphaned uploads: {e}")
            return []
    
    async def _process_orphaned_file(
        self, 
        file_info: Dict[str, Any], 
        semaphore: asyncio.Semaphore
    ) -> bool:
        """Process a single orphaned file."""
        async with semaphore:
            file_id = file_info['id']
            
            try:
                logger.debug(f"Checking orphaned file {file_id}")
                
                # Check if file exists in storage
                exists = await self._check_file_in_storage(file_info)
                
                if exists:
                    # File exists in storage, mark as available and trigger processing
                    await self._confirm_orphaned_upload(file_info)
                    logger.info(f"Confirmed orphaned upload: {file_id}")
                    return True
                else:
                    # File doesn't exist in storage, mark as failed
                    await self._mark_upload_failed(file_id, "File not found in storage")
                    logger.warning(f"Marked orphaned upload as failed: {file_id}")
                    return True
                    
            except Exception as e:
                logger.error(f"Failed to process orphaned file {file_id}: {e}")
                return False
    
    async def _check_file_in_storage(self, file_info: Dict[str, Any]) -> bool:
        """Check if file exists in storage."""
        try:
            from infrastructure.storage.factory import create_storage_from_env
            
            storage = create_storage_from_env()
            
            bucket = file_info.get('storage_bucket', 'files')
            key = file_info.get('storage_key')
            
            if not key:
                logger.warning(f"No storage key for file {file_info['id']}")
                return False
            
            exists = await storage.object_exists(bucket=bucket, key=key)
            
            if exists:
                # Also check file size matches
                try:
                    metadata = await storage.get_object_metadata(bucket=bucket, key=key)
                    storage_size = metadata.get("size", 0)
                    expected_size = file_info.get('file_size', 0)
                    
                    if storage_size != expected_size:
                        logger.warning(
                            f"Size mismatch for {file_info['id']}: "
                            f"expected {expected_size}, got {storage_size}"
                        )
                        # Still consider it as existing, size might be updated later
                    
                except Exception as e:
                    logger.warning(f"Could not verify size for {file_info['id']}: {e}")
            
            return exists
            
        except Exception as e:
            logger.error(f"Storage check failed for {file_info['id']}: {e}")
            return False
    
    async def _confirm_orphaned_upload(self, file_info: Dict[str, Any]) -> None:
        """Confirm an orphaned upload and trigger processing."""
        try:
            import asyncpg
            
            file_id = str(file_info['id'])
            
            # Update file status to AVAILABLE
            conn = await asyncpg.connect('postgresql://rag_user:rag_password@localhost:5432/rag_db')
            
            await conn.execute('''
                UPDATE files 
                SET status = 'available', updated_at = $1
                WHERE id = $2::uuid
            ''', datetime.utcnow(), file_id)
            
            await conn.close()
            
            # Trigger RAG processing
            if file_info.get('storage_key'):
                try:
                    task_ids = await process_file_complete(
                        file_id=file_id,
                        file_path=file_info['storage_key'],
                        file_name=file_info.get('original_name', 'unknown'),
                        file_size=file_info.get('file_size', 0),
                        mime_type=file_info.get('content_type', 'application/octet-stream'),
                        topic_id=file_info.get('topic_id'),
                        user_id=file_info.get('owner_id', ''),
                        priority=TaskPriority.LOW  # Lower priority for orphaned files
                    )
                    logger.info(f"Started processing for orphaned file {file_id}: {task_ids}")
                except Exception as e:
                    logger.error(f"Failed to start processing for orphaned file {file_id}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to confirm orphaned upload {file_info['id']}: {e}")
            raise
    
    async def _mark_upload_failed(self, file_id: str, reason: str) -> None:
        """Mark an upload as failed."""
        try:
            import asyncpg
            
            conn = await asyncpg.connect('postgresql://rag_user:rag_password@localhost:5432/rag_db')
            
            await conn.execute('''
                UPDATE files 
                SET status = 'failed', updated_at = $1
                WHERE id = $2::uuid
            ''', datetime.utcnow(), file_id)
            
            await conn.close()
            
            logger.info(f"Marked upload {file_id} as failed: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to mark upload {file_id} as failed: {e}")
            raise


# Global instance
_upload_monitor: Optional[UploadMonitorService] = None


async def get_upload_monitor() -> UploadMonitorService:
    """Get the global upload monitor instance."""
    global _upload_monitor
    if _upload_monitor is None:
        _upload_monitor = UploadMonitorService()
    return _upload_monitor


async def start_upload_monitor() -> None:
    """Start the upload monitoring service."""
    monitor = await get_upload_monitor()
    await monitor.start()


async def stop_upload_monitor() -> None:
    """Stop the upload monitoring service."""
    global _upload_monitor
    if _upload_monitor:
        await _upload_monitor.stop()
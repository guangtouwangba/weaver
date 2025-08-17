"""
Unified File Service Bridge

This service provides a unified interface to query files from both legacy and new systems:
- Legacy: topic_resources table
- New: files table (MinIO-based upload system)

This bridge allows gradual migration while maintaining compatibility.
"""

import logging
from typing import List, Dict, Any, Optional
import asyncpg
from datetime import datetime

logger = logging.getLogger(__name__)


class UnifiedFileService:
    """
    Service that bridges legacy topic resources and new file upload system.
    
    Provides unified queries that combine results from both systems.
    """
    
    def __init__(self, db_connection_string: str = None):
        self.db_connection_string = db_connection_string or 'postgresql://rag_user:rag_password@localhost:5432/rag_db'
    
    async def get_files_for_topic(self, topic_id: int) -> List[Dict[str, Any]]:
        """
        Get all files associated with a topic from both legacy and new systems.
        
        Returns:
            List of unified file objects with standardized fields
        """
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Query legacy topic_resources
            legacy_files = await self._get_legacy_files(conn, topic_id)
            
            # Query new files table
            new_files = await self._get_new_files(conn, topic_id)
            
            await conn.close()
            
            # Combine and standardize results
            unified_files = []
            unified_files.extend(self._normalize_legacy_files(legacy_files))
            unified_files.extend(self._normalize_new_files(new_files))
            
            # Sort by upload/creation date (newest first)
            unified_files.sort(key=lambda x: x['created_at'], reverse=True)
            
            logger.info(f"Retrieved {len(unified_files)} files for topic {topic_id} ({len(legacy_files)} legacy, {len(new_files)} new)")
            return unified_files
            
        except Exception as e:
            logger.error(f"Failed to get files for topic {topic_id}: {e}")
            raise
    
    async def _get_legacy_files(self, conn: asyncpg.Connection, topic_id: int) -> List[Dict[str, Any]]:
        """Query legacy topic_resources table."""
        query = """
            SELECT 
                id, original_name, file_name, file_path, file_size, mime_type,
                resource_type, is_parsed, parse_status, total_pages, parsed_pages,
                content_preview, metadata, uploaded_at, parsed_at, last_accessed_at
            FROM topic_resources 
            WHERE topic_id = $1 AND is_deleted = false
            ORDER BY uploaded_at DESC
        """
        
        results = await conn.fetch(query, topic_id)
        return [dict(record) for record in results]
    
    async def _get_new_files(self, conn: asyncpg.Connection, topic_id: int) -> List[Dict[str, Any]]:
        """Query new files table."""
        query = """
            SELECT 
                id, owner_id, original_name, file_size, content_type, storage_bucket,
                storage_key, category, tags, status, access_level, download_count,
                custom_metadata, created_at, updated_at, last_accessed_at
            FROM files 
            WHERE topic_id = $1 AND is_deleted = false
            ORDER BY created_at DESC
        """
        
        results = await conn.fetch(query, topic_id)
        return [dict(record) for record in results]
    
    def _normalize_legacy_files(self, legacy_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize legacy file records to unified format."""
        normalized = []
        
        for file_record in legacy_files:
            normalized_file = {
                'id': str(file_record['id']),
                'source_system': 'legacy',
                'original_name': file_record['original_name'],
                'display_name': file_record['file_name'],
                'file_size': file_record['file_size'] or 0,
                'content_type': file_record['mime_type'] or 'application/octet-stream',
                'category': None,  # Legacy system doesn't have categories
                'tags': [],  # Legacy system doesn't have tags
                'status': self._map_legacy_status(file_record['parse_status']),
                'access_level': 'private',  # Legacy files are private by default
                'download_count': 0,  # Legacy system doesn't track downloads
                'metadata': {
                    'resource_type': file_record['resource_type'],
                    'is_parsed': file_record['is_parsed'],
                    'parse_status': file_record['parse_status'],
                    'total_pages': file_record['total_pages'],
                    'parsed_pages': file_record['parsed_pages'],
                    'content_preview': file_record['content_preview'],
                    'file_path': file_record['file_path'],
                    'legacy_metadata': file_record['metadata']
                },
                'created_at': file_record['uploaded_at'],
                'updated_at': file_record['parsed_at'] or file_record['uploaded_at'],
                'last_accessed_at': file_record['last_accessed_at'],
                'download_url': None,  # Legacy files need special handling for downloads
                'can_download': True,
                'is_processed': file_record['is_parsed'],
                'processing_status': file_record['parse_status']
            }
            normalized.append(normalized_file)
        
        return normalized
    
    def _normalize_new_files(self, new_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize new file records to unified format."""
        normalized = []
        
        for file_record in new_files:
            normalized_file = {
                'id': str(file_record['id']),
                'source_system': 'new',
                'original_name': file_record['original_name'],
                'display_name': file_record['original_name'],
                'file_size': file_record['file_size'] or 0,
                'content_type': file_record['content_type'] or 'application/octet-stream',
                'category': file_record['category'],
                'tags': file_record['tags'] or [],
                'status': file_record['status'],
                'access_level': file_record['access_level'],
                'download_count': file_record['download_count'] or 0,
                'metadata': {
                    'storage_bucket': file_record['storage_bucket'],
                    'storage_key': file_record['storage_key'],
                    'owner_id': file_record['owner_id'],
                    'custom_metadata': file_record['custom_metadata']
                },
                'created_at': file_record['created_at'],
                'updated_at': file_record['updated_at'],
                'last_accessed_at': file_record['last_accessed_at'],
                'download_url': None,  # Will be generated on demand
                'can_download': file_record['status'] in ['available', 'uploading'],
                'is_processed': file_record['status'] == 'available',
                'processing_status': file_record['status']
            }
            normalized.append(normalized_file)
        
        return normalized
    
    def _map_legacy_status(self, parse_status: str) -> str:
        """Map legacy parse status to new file status."""
        status_mapping = {
            'pending': 'uploading',
            'processing': 'processing', 
            'completed': 'available',
            'failed': 'failed'
        }
        return status_mapping.get(parse_status, 'uploading')
    
    async def get_file_statistics(self, topic_id: int) -> Dict[str, Any]:
        """Get file statistics for a topic from both systems."""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Legacy files stats
            legacy_stats_query = """
                SELECT 
                    COUNT(*) as total_files,
                    COALESCE(SUM(file_size), 0) as total_size,
                    COUNT(CASE WHEN is_parsed = true THEN 1 END) as processed_files,
                    COUNT(CASE WHEN parse_status = 'failed' THEN 1 END) as failed_files
                FROM topic_resources 
                WHERE topic_id = $1 AND is_deleted = false
            """
            
            # New files stats  
            new_stats_query = """
                SELECT 
                    COUNT(*) as total_files,
                    COALESCE(SUM(file_size), 0) as total_size,
                    COUNT(CASE WHEN status = 'available' THEN 1 END) as processed_files,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_files,
                    COALESCE(SUM(download_count), 0) as total_downloads
                FROM files 
                WHERE topic_id = $1 AND is_deleted = false
            """
            
            legacy_stats = await conn.fetchrow(legacy_stats_query, topic_id)
            new_stats = await conn.fetchrow(new_stats_query, topic_id)
            
            await conn.close()
            
            # Combine statistics
            combined_stats = {
                'total_files': legacy_stats['total_files'] + new_stats['total_files'],
                'total_size_bytes': legacy_stats['total_size'] + new_stats['total_size'],
                'processed_files': legacy_stats['processed_files'] + new_stats['processed_files'],
                'failed_files': legacy_stats['failed_files'] + new_stats['failed_files'],
                'total_downloads': new_stats['total_downloads'],  # Only new system tracks downloads
                'legacy_files': legacy_stats['total_files'],
                'new_files': new_stats['total_files'],
                'system_breakdown': {
                    'legacy': {
                        'files': legacy_stats['total_files'],
                        'size_bytes': legacy_stats['total_size'],
                        'processed': legacy_stats['processed_files'],
                        'failed': legacy_stats['failed_files']
                    },
                    'new': {
                        'files': new_stats['total_files'],
                        'size_bytes': new_stats['total_size'],
                        'processed': new_stats['processed_files'],
                        'failed': new_stats['failed_files'],
                        'downloads': new_stats['total_downloads']
                    }
                }
            }
            
            # Calculate derived metrics
            if combined_stats['total_files'] > 0:
                combined_stats['avg_file_size_mb'] = combined_stats['total_size_bytes'] / (1024 * 1024) / combined_stats['total_files']
                combined_stats['processing_success_rate'] = combined_stats['processed_files'] / combined_stats['total_files']
            else:
                combined_stats['avg_file_size_mb'] = 0
                combined_stats['processing_success_rate'] = 0
            
            combined_stats['total_size_mb'] = combined_stats['total_size_bytes'] / (1024 * 1024)
            
            return combined_stats
            
        except Exception as e:
            logger.error(f"Failed to get file statistics for topic {topic_id}: {e}")
            raise
    
    async def search_files(self, topic_id: int, query: Optional[str] = None, 
                          file_type: Optional[str] = None, 
                          status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search files across both systems."""
        try:
            # Get all files for the topic
            all_files = await self.get_files_for_topic(topic_id)
            
            # Apply filters
            filtered_files = all_files
            
            if query:
                query_lower = query.lower()
                filtered_files = [
                    f for f in filtered_files 
                    if query_lower in f['original_name'].lower() or 
                       query_lower in f['display_name'].lower()
                ]
            
            if file_type:
                filtered_files = [
                    f for f in filtered_files 
                    if file_type.lower() in f['content_type'].lower()
                ]
            
            if status:
                filtered_files = [
                    f for f in filtered_files 
                    if f['status'] == status
                ]
            
            logger.info(f"Search for topic {topic_id} returned {len(filtered_files)} files (filtered from {len(all_files)})")
            return filtered_files
            
        except Exception as e:
            logger.error(f"Failed to search files for topic {topic_id}: {e}")
            raise


# Convenience function for API usage
async def get_unified_files_for_topic(topic_id: int) -> List[Dict[str, Any]]:
    """Convenience function to get unified files for a topic."""
    service = UnifiedFileService()
    return await service.get_files_for_topic(topic_id)


async def get_unified_file_stats_for_topic(topic_id: int) -> Dict[str, Any]:
    """Convenience function to get unified file statistics for a topic."""
    service = UnifiedFileService()
    return await service.get_file_statistics(topic_id)
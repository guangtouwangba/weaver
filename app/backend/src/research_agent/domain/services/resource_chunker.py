"""Unified chunking service for all resource types."""

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from research_agent.domain.entities.resource import Resource, ResourceType
from research_agent.domain.entities.resource_chunk import ResourceChunk
from research_agent.shared.utils.logger import logger


class ResourceChunker:
    """Unified chunking service for all resource types.
    
    This service handles chunking of content from any resource type
    (documents, videos, web pages, notes) with appropriate strategies
    and metadata preservation.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        media_chunk_duration: float = 60.0,  # seconds for video/audio
    ):
        """Initialize the chunker.
        
        Args:
            chunk_size: Target size for text chunks (characters)
            chunk_overlap: Overlap between consecutive chunks
            media_chunk_duration: Duration for media chunks (seconds)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.media_chunk_duration = media_chunk_duration

    def chunk_resource(
        self,
        resource: Resource,
        content: Optional[str] = None,
    ) -> List[ResourceChunk]:
        """Chunk a resource based on its type.
        
        Args:
            resource: The resource to chunk
            content: Optional content override (uses resource.content if not provided)
            
        Returns:
            List of ResourceChunk entities
        """
        text = content or resource.content
        if not text:
            logger.warning(f"[ResourceChunker] No content for resource {resource.id}")
            return []

        if resource.type == ResourceType.DOCUMENT:
            return self._chunk_document(resource, text)
        elif resource.type in (ResourceType.VIDEO, ResourceType.AUDIO):
            return self._chunk_media(resource, text)
        elif resource.type == ResourceType.WEB_PAGE:
            return self._chunk_webpage(resource, text)
        else:
            return self._chunk_generic(resource, text)

    def chunk_text(
        self,
        text: str,
        resource_id: UUID,
        resource_type: ResourceType,
        project_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ResourceChunk]:
        """Chunk raw text content.
        
        Lower-level API for chunking text without a Resource object.
        
        Args:
            text: Text content to chunk
            resource_id: Parent resource ID
            resource_type: Type of resource
            project_id: Project ID
            metadata: Optional metadata to include in all chunks
            
        Returns:
            List of ResourceChunk entities
        """
        if not text:
            return []

        base_metadata = metadata or {}
        chunks = self._split_text(text)

        return [
            ResourceChunk(
                id=uuid4(),
                resource_id=resource_id,
                resource_type=resource_type,
                project_id=project_id,
                chunk_index=i,
                content=chunk_text,
                metadata=base_metadata.copy(),
            )
            for i, chunk_text in enumerate(chunks)
        ]

    def _chunk_document(self, resource: Resource, text: str) -> List[ResourceChunk]:
        """Chunk document content, preserving page numbers if available.
        
        For documents with page structure, chunks are created per page.
        For documents without page info, standard text chunking is used.
        """
        base_metadata = {
            "title": resource.title,
            "platform": resource.platform,
        }

        # Check if we have page-structured content
        pages = resource.metadata.get("pages", [])
        if pages:
            return self._chunk_by_pages(resource, pages, base_metadata)

        # Standard text chunking
        chunks = self._split_text(text)
        return [
            ResourceChunk(
                id=uuid4(),
                resource_id=resource.id,
                resource_type=resource.type,
                project_id=resource.metadata.get("project_id"),
                chunk_index=i,
                content=chunk_text,
                metadata=base_metadata.copy(),
            )
            for i, chunk_text in enumerate(chunks)
        ]

    def _chunk_by_pages(
        self,
        resource: Resource,
        pages: List[Dict[str, Any]],
        base_metadata: Dict[str, Any],
    ) -> List[ResourceChunk]:
        """Chunk document by pages, preserving page numbers."""
        all_chunks = []
        chunk_index = 0

        for page in pages:
            page_num = page.get("page_number", 0)
            page_text = page.get("content", "")

            if not page_text:
                continue

            page_chunks = self._split_text(page_text)
            for chunk_text in page_chunks:
                metadata = base_metadata.copy()
                metadata["page_number"] = page_num

                all_chunks.append(
                    ResourceChunk(
                        id=uuid4(),
                        resource_id=resource.id,
                        resource_type=resource.type,
                        project_id=resource.metadata.get("project_id"),
                        chunk_index=chunk_index,
                        content=chunk_text,
                        metadata=metadata,
                    )
                )
                chunk_index += 1

        return all_chunks

    def _chunk_media(self, resource: Resource, text: str) -> List[ResourceChunk]:
        """Chunk video/audio transcript, preserving timestamps.
        
        For transcripts with timestamp data, chunks are created by time windows.
        For plain transcripts, standard text chunking is used.
        """
        base_metadata = {
            "title": resource.title,
            "platform": resource.platform,
        }

        # Check for timestamped segments
        segments = resource.metadata.get("segments", [])
        if segments:
            return self._chunk_by_timestamps(resource, segments, base_metadata)

        # Standard text chunking for plain transcripts
        chunks = self._split_text(text)
        return [
            ResourceChunk(
                id=uuid4(),
                resource_id=resource.id,
                resource_type=resource.type,
                project_id=resource.metadata.get("project_id"),
                chunk_index=i,
                content=chunk_text,
                metadata=base_metadata.copy(),
            )
            for i, chunk_text in enumerate(chunks)
        ]

    def _chunk_by_timestamps(
        self,
        resource: Resource,
        segments: List[Dict[str, Any]],
        base_metadata: Dict[str, Any],
    ) -> List[ResourceChunk]:
        """Chunk transcript by time windows, preserving start/end times."""
        all_chunks = []
        chunk_index = 0

        # Group segments into time windows
        current_window_start = 0.0
        current_window_text = []
        current_window_end = 0.0

        for segment in segments:
            seg_start = segment.get("start", 0.0)
            seg_end = segment.get("end", seg_start)
            seg_text = segment.get("text", "")

            if not seg_text:
                continue

            # Check if we should start a new window
            if seg_start - current_window_start >= self.media_chunk_duration and current_window_text:
                # Save current window as chunk
                metadata = base_metadata.copy()
                metadata["start_time"] = current_window_start
                metadata["end_time"] = current_window_end

                all_chunks.append(
                    ResourceChunk(
                        id=uuid4(),
                        resource_id=resource.id,
                        resource_type=resource.type,
                        project_id=resource.metadata.get("project_id"),
                        chunk_index=chunk_index,
                        content=" ".join(current_window_text),
                        metadata=metadata,
                    )
                )
                chunk_index += 1

                # Start new window
                current_window_start = seg_start
                current_window_text = []

            current_window_text.append(seg_text)
            current_window_end = seg_end

        # Don't forget the last window
        if current_window_text:
            metadata = base_metadata.copy()
            metadata["start_time"] = current_window_start
            metadata["end_time"] = current_window_end

            all_chunks.append(
                ResourceChunk(
                    id=uuid4(),
                    resource_id=resource.id,
                    resource_type=resource.type,
                    project_id=resource.metadata.get("project_id"),
                    chunk_index=chunk_index,
                    content=" ".join(current_window_text),
                    metadata=metadata,
                )
            )

        return all_chunks

    def _chunk_webpage(self, resource: Resource, text: str) -> List[ResourceChunk]:
        """Chunk webpage content by paragraphs or sections."""
        base_metadata = {
            "title": resource.title,
            "platform": resource.platform,
        }

        # Standard text chunking
        chunks = self._split_text(text)
        return [
            ResourceChunk(
                id=uuid4(),
                resource_id=resource.id,
                resource_type=resource.type,
                project_id=resource.metadata.get("project_id"),
                chunk_index=i,
                content=chunk_text,
                metadata=base_metadata.copy(),
            )
            for i, chunk_text in enumerate(chunks)
        ]

    def _chunk_generic(self, resource: Resource, text: str) -> List[ResourceChunk]:
        """Generic chunking for other resource types."""
        base_metadata = {
            "title": resource.title,
            "platform": resource.platform,
        }

        chunks = self._split_text(text)
        return [
            ResourceChunk(
                id=uuid4(),
                resource_id=resource.id,
                resource_type=resource.type,
                project_id=resource.metadata.get("project_id"),
                chunk_index=i,
                content=chunk_text,
                metadata=base_metadata.copy(),
            )
            for i, chunk_text in enumerate(chunks)
        ]

    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap.
        
        Uses a simple character-based splitting with sentence boundary awareness.
        """
        if not text:
            return []

        # If text is smaller than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        chunks = []
        start = 0

        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size

            if end >= len(text):
                # Last chunk
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # Try to find a good break point (sentence boundary)
            chunk_text = text[start:end]
            
            # Look for sentence endings
            for sep in [". ", "。", "! ", "? ", "\n\n", "\n"]:
                last_sep = chunk_text.rfind(sep)
                if last_sep > self.chunk_size // 2:
                    end = start + last_sep + len(sep)
                    break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - self.chunk_overlap
            if start < 0:
                start = 0

        return chunks

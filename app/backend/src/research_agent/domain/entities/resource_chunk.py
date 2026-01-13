"""Unified resource chunk domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from research_agent.domain.entities.resource import ResourceType


@dataclass
class ResourceChunk:
    """Unified chunk entity for all resource types.
    
    This entity represents a text chunk from any resource type (document, video,
    audio, web page, note, etc.) with consistent interface for storage and retrieval.
    
    Attributes:
        id: Unique chunk identifier
        resource_id: Parent resource ID (document, url_content, etc.)
        resource_type: Type of the parent resource
        project_id: Project this chunk belongs to
        chunk_index: Position of this chunk within the resource
        content: Text content of the chunk
        embedding: Vector embedding (optional, may be stored externally)
        metadata: Type-specific metadata (title, platform, page_number, timestamps)
        created_at: Creation timestamp
    
    Metadata fields by resource type:
        - All types: title, platform
        - Document: page_number
        - Video/Audio: start_time, end_time (in seconds)
        - Web page: section_title
    """

    id: UUID = field(default_factory=uuid4)
    resource_id: Optional[UUID] = None
    resource_type: ResourceType = ResourceType.DOCUMENT
    project_id: Optional[UUID] = None
    chunk_index: int = 0
    content: str = ""
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def set_embedding(self, embedding: List[float]) -> None:
        """Set the embedding vector."""
        self.embedding = embedding

    @property
    def has_embedding(self) -> bool:
        """Check if chunk has embedding."""
        return self.embedding is not None and len(self.embedding) > 0

    @property
    def title(self) -> str:
        """Get resource title from metadata."""
        return self.metadata.get("title", "")

    @property
    def platform(self) -> str:
        """Get platform from metadata."""
        return self.metadata.get("platform", "local")

    @property
    def page_number(self) -> Optional[int]:
        """Get page number (for documents)."""
        return self.metadata.get("page_number")

    @property
    def start_time(self) -> Optional[float]:
        """Get start time in seconds (for video/audio)."""
        return self.metadata.get("start_time")

    @property
    def end_time(self) -> Optional[float]:
        """Get end time in seconds (for video/audio)."""
        return self.metadata.get("end_time")

    def to_search_context(self) -> str:
        """Format chunk for use in LLM context with source attribution."""
        source_info = f"[{self.resource_type.value}] {self.title}"
        
        if self.resource_type == ResourceType.DOCUMENT and self.page_number:
            source_info += f" (Page {self.page_number})"
        elif self.resource_type in (ResourceType.VIDEO, ResourceType.AUDIO):
            if self.start_time is not None:
                minutes = int(self.start_time // 60)
                seconds = int(self.start_time % 60)
                source_info += f" ({minutes}:{seconds:02d})"
        
        return f"{source_info}\n{self.content}"

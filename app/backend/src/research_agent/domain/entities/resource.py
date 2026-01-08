"""Resource domain entity - unified abstraction for all content types."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID


class ResourceType(str, Enum):
    """
    Content category-based resource types.
    
    ResourceType represents the content category (what the content IS),
    not the source platform (where it came from). Platform information
    is stored in metadata.platform field.
    
    Examples:
        - A YouTube video → ResourceType.VIDEO, metadata.platform = "youtube"
        - A local MP4 file → ResourceType.VIDEO, metadata.platform = "local"
        - A PDF document → ResourceType.DOCUMENT, metadata.platform = "local"
        - A web article → ResourceType.WEB_PAGE, metadata.platform = "web"
    """
    
    # Text-based content
    DOCUMENT = "document"  # PDF, Word, PPT, Markdown, plain text
    WEB_PAGE = "web_page"  # Articles, blog posts, web content
    NOTE = "note"          # User-created notes in the system
    
    # Media content
    VIDEO = "video"        # All video: local files, YouTube, Bilibili, Douyin
    AUDIO = "audio"        # All audio: local files, podcasts, voice memos
    IMAGE = "image"        # Images, diagrams, screenshots
    
    # Special types
    COLLECTION = "collection"  # Grouped resources (future)


@dataclass
class Resource:
    """
    Unified resource abstraction.
    
    This dataclass represents a content resource from any source (documents,
    URLs, inbox items) with a consistent interface. It provides:
    
    - Unified ID and type for consistent handling
    - Content access regardless of source
    - Type-specific metadata for rendering
    - Source attribution via source_url and metadata.platform
    
    Attributes:
        id: Unique identifier (UUID from underlying model)
        type: Content category (ResourceType)
        title: Display title
        content: Extracted/full text content (primary use case)
        summary: AI-generated summary if available
        metadata: Type-specific data (platform, duration, page_count, etc.)
        thumbnail_url: Preview image URL
        source_url: Original URL (None for local files)
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    
    Examples:
        >>> # Document resource
        >>> Resource(
        ...     id=uuid,
        ...     type=ResourceType.DOCUMENT,
        ...     title="Research Paper.pdf",
        ...     content="Full extracted text...",
        ...     metadata={"platform": "local", "page_count": 42}
        ... )
        
        >>> # YouTube video resource
        >>> Resource(
        ...     id=uuid,
        ...     type=ResourceType.VIDEO,
        ...     title="Tutorial Video",
        ...     content="Transcript text...",
        ...     metadata={
        ...         "platform": "youtube",
        ...         "video_id": "abc123",
        ...         "duration": 3600,
        ...         "channel_name": "TechChannel"
        ...     },
        ...     source_url="https://youtube.com/watch?v=abc123"
        ... )
    """
    
    id: UUID
    type: ResourceType
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    thumbnail_url: Optional[str] = None
    source_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def platform(self) -> str:
        """Get the platform/source of this resource."""
        return self.metadata.get("platform", "unknown")
    
    @property
    def has_content(self) -> bool:
        """Check if resource has extractable content."""
        return bool(self.content)
    
    @property
    def display_content(self) -> str:
        """Get content for display, preferring full content over summary."""
        return self.content or self.summary or ""
    
    def get_formatted_content(self) -> str:
        """
        Get formatted content string for use in LLM context.
        
        Returns content with appropriate header based on resource type.
        """
        type_labels = {
            ResourceType.DOCUMENT: "Document",
            ResourceType.VIDEO: f"Video ({self.platform})",
            ResourceType.AUDIO: f"Audio ({self.platform})",
            ResourceType.WEB_PAGE: "Web Page",
            ResourceType.IMAGE: "Image",
            ResourceType.NOTE: "Note",
            ResourceType.COLLECTION: "Collection",
        }
        
        label = type_labels.get(self.type, "Resource")
        content = self.display_content
        
        if not content:
            return f"## {label}: {self.title}\n\n(No content available)"
        
        return f"## {label}: {self.title}\n\n{content}"

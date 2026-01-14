"""
ResourceResolver - Unified content access for all resource types.

This service resolves resource IDs to unified Resource objects, abstracting
away the underlying storage models (DocumentModel, UrlContentModel, etc.).

Usage:
    async with get_async_session() as session:
        resolver = ResourceResolver(session)

        # Get a single resource
        resource = await resolver.resolve(uuid)

        # Get multiple resources
        resources = await resolver.resolve_many([uuid1, uuid2, uuid3])

        # Get just the content (most common use case)
        content = await resolver.get_content(uuid)

        # Get formatted content for multiple resources
        formatted = await resolver.get_combined_content([uuid1, uuid2])
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.resource import Resource, ResourceType
from research_agent.infrastructure.database.models import DocumentModel, UrlContentModel

logger = logging.getLogger(__name__)


def _document_to_resource(doc: DocumentModel) -> Resource:
    """Convert DocumentModel to Resource."""
    # Determine ResourceType based on mime_type
    mime_type = doc.mime_type or ""

    if mime_type.startswith("video/"):
        resource_type = ResourceType.VIDEO
    elif mime_type.startswith("audio/"):
        resource_type = ResourceType.AUDIO
    elif mime_type.startswith("image/"):
        resource_type = ResourceType.IMAGE
    else:
        resource_type = ResourceType.DOCUMENT

    # Build metadata
    metadata: dict = {
        "platform": "local",
        "mime_type": doc.mime_type,
        "file_size": doc.file_size,
        "page_count": doc.page_count,
    }

    # Add parsing metadata if available
    if doc.parsing_metadata:
        metadata["parsing"] = doc.parsing_metadata
        if doc.parsing_metadata.get("duration_seconds"):
            metadata["duration"] = doc.parsing_metadata["duration_seconds"]

    return Resource(
        id=doc.id,
        type=resource_type,
        title=doc.original_filename or doc.filename or "Untitled",
        content=doc.full_content,
        summary=doc.summary,
        metadata=metadata,
        thumbnail_url=doc.thumbnail_path,  # Local path, may need URL conversion
        source_url=None,  # Local files have no source URL
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _url_content_to_resource(url_content: UrlContentModel) -> Resource:
    """Convert UrlContentModel to Resource."""
    # Determine ResourceType based on content_type and platform
    content_type = url_content.content_type or ""
    platform = url_content.platform or ""

    # Video platforms
    if content_type == "video" or platform in ("youtube", "bilibili", "douyin", "tiktok"):
        resource_type = ResourceType.VIDEO
    # Audio content
    elif content_type == "audio" or platform in ("spotify", "apple_podcasts", "podcast"):
        resource_type = ResourceType.AUDIO
    # Web pages and articles
    else:
        resource_type = ResourceType.WEB_PAGE

    # Build metadata from url_content's meta_data plus standard fields
    metadata: dict = {
        "platform": platform,
        "content_type": content_type,
        **(url_content.meta_data or {}),
    }

    return Resource(
        id=url_content.id,
        type=resource_type,
        title=url_content.title or url_content.url,
        content=url_content.content,
        summary=None,  # URL contents don't have separate summary
        metadata=metadata,
        thumbnail_url=url_content.thumbnail_url,
        source_url=url_content.url,
        created_at=url_content.created_at,
        updated_at=url_content.updated_at,
    )


class ResourceResolver:
    """
    Resolves resource IDs to unified Resource objects.

    This service abstracts the underlying storage models and provides
    a consistent interface for accessing content from any source.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def resolve(
        self,
        resource_id: UUID,
        type_hint: ResourceType | None = None,
        platform_hint: str | None = None,
    ) -> Resource | None:
        """
        Resolve a single resource by ID.

        Args:
            resource_id: UUID of the resource
            type_hint: Optional type hint to speed up lookup
            platform_hint: Optional platform hint (e.g., "youtube") to speed up lookup

        Returns:
            Resource object if found, None otherwise
        """
        # Try platform hint first for URL content
        if platform_hint:
            url_content = await self._get_url_content_by_id(resource_id)
            if url_content and url_content.platform == platform_hint:
                return _url_content_to_resource(url_content)

        # Try type hint to narrow search
        if type_hint:
            if type_hint == ResourceType.DOCUMENT:
                doc = await self._get_document_by_id(resource_id)
                if doc:
                    return _document_to_resource(doc)
            elif type_hint in (ResourceType.VIDEO, ResourceType.AUDIO, ResourceType.WEB_PAGE):
                # Could be either DocumentModel (local file) or UrlContentModel
                url_content = await self._get_url_content_by_id(resource_id)
                if url_content:
                    return _url_content_to_resource(url_content)
                doc = await self._get_document_by_id(resource_id)
                if doc:
                    return _document_to_resource(doc)

        # No hint: try all sources
        # Try DocumentModel first (more common)
        doc = await self._get_document_by_id(resource_id)
        if doc:
            return _document_to_resource(doc)

        # Try UrlContentModel
        url_content = await self._get_url_content_by_id(resource_id)
        if url_content:
            return _url_content_to_resource(url_content)

        logger.warning(f"[ResourceResolver] Resource not found: {resource_id}")
        return None

    async def resolve_many(
        self,
        resource_ids: list[UUID],
    ) -> list[Resource]:
        """
        Resolve multiple resources by ID.

        Uses batch queries for efficiency. Returns resources in the same
        order as input IDs, skipping any that don't resolve.

        Args:
            resource_ids: List of UUIDs to resolve

        Returns:
            List of Resource objects (may be shorter than input if some don't resolve)
        """
        if not resource_ids:
            return []

        # Batch query both tables
        docs_by_id = await self._batch_get_documents(resource_ids)
        url_contents_by_id = await self._batch_get_url_contents(resource_ids)

        # Build result in order
        resources: list[Resource] = []
        for rid in resource_ids:
            if rid in docs_by_id:
                resources.append(_document_to_resource(docs_by_id[rid]))
            elif rid in url_contents_by_id:
                resources.append(_url_content_to_resource(url_contents_by_id[rid]))
            else:
                logger.warning(f"[ResourceResolver] Resource not found during batch: {rid}")

        return resources

    async def get_content(self, resource_id: UUID) -> str:
        """
        Get content for a resource (convenience method).

        Args:
            resource_id: UUID of the resource

        Returns:
            Content string, or empty string if not found
        """
        resource = await self.resolve(resource_id)
        if resource:
            return resource.display_content
        return ""

    async def get_combined_content(
        self,
        resource_ids: list[UUID],
        separator: str = "\n\n---\n\n",
    ) -> str:
        """
        Get formatted content from multiple resources, combined.

        Args:
            resource_ids: List of UUIDs
            separator: String to join content sections

        Returns:
            Combined formatted content string
        """
        resources = await self.resolve_many(resource_ids)

        formatted_parts = []
        for resource in resources:
            formatted = resource.get_formatted_content()
            if formatted:
                formatted_parts.append(formatted)

        return separator.join(formatted_parts)

    # Private helper methods

    async def _get_document_by_id(self, doc_id: UUID) -> DocumentModel | None:
        """Get DocumentModel by ID."""
        return await self._session.get(DocumentModel, doc_id)

    async def _get_url_content_by_id(self, url_id: UUID) -> UrlContentModel | None:
        """Get UrlContentModel by ID."""
        return await self._session.get(UrlContentModel, url_id)

    async def _batch_get_documents(self, doc_ids: list[UUID]) -> dict[UUID, DocumentModel]:
        """Batch fetch DocumentModels by IDs."""
        if not doc_ids:
            return {}

        stmt = select(DocumentModel).where(DocumentModel.id.in_(doc_ids))
        result = await self._session.execute(stmt)
        docs = result.scalars().all()
        return {doc.id: doc for doc in docs}

    async def _batch_get_url_contents(self, url_ids: list[UUID]) -> dict[UUID, UrlContentModel]:
        """Batch fetch UrlContentModels by IDs."""
        if not url_ids:
            return {}

        stmt = select(UrlContentModel).where(UrlContentModel.id.in_(url_ids))
        result = await self._session.execute(stmt)
        url_contents = result.scalars().all()
        return {uc.id: uc for uc in url_contents}

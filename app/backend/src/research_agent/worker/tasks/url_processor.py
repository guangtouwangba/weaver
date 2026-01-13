"""URL content extraction task for ARQ worker."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.domain.entities.resource import ResourceType
from research_agent.domain.entities.resource_chunk import ResourceChunk
from research_agent.infrastructure.database.models import UrlContentModel
from research_agent.infrastructure.database.repositories.chunk_repo_factory import (
    get_chunk_repository,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_url_content_repo import (
    SQLAlchemyUrlContentRepository,
)
from research_agent.infrastructure.database.session import get_async_session
from research_agent.infrastructure.embedding.openrouter import OpenRouterEmbeddingService
from research_agent.infrastructure.url_extractor import URLExtractorFactory
from research_agent.shared.utils.logger import logger
from research_agent.worker.tasks.base import BaseTask


class URLProcessorTask(BaseTask):
    """
    Task for processing URL content extraction and embedding.

    Pipeline:
    1. Update status to processing
    2. Detect platform and extract content
    3. Update UrlContent record with extracted data
    4. Chunk content and generate embeddings
    5. Save chunks to resource_chunks table
    6. Update status to completed/failed
    """

    @property
    def task_type(self) -> str:
        return "process_url"

    async def execute(self, payload: Dict[str, Any], session: AsyncSession) -> None:
        """
        Process URL extraction and embedding.

        Payload:
            url_content_id: UUID of the UrlContent record
            url: The URL to extract
            project_id: Optional project ID for chunk association
        """
        url_content_id = UUID(payload["url_content_id"])
        url = payload["url"]
        project_id = UUID(payload["project_id"]) if payload.get("project_id") else None

        logger.info(
            f"🌐 Starting URL extraction - url_content_id={url_content_id}, url={url}"
        )

        repo = SQLAlchemyUrlContentRepository(session)

        # Update status to processing
        try:
            await repo.update_status(url_content_id, status="processing")
            await session.commit()
            logger.debug(f"✅ Updated URL content {url_content_id} status to PROCESSING")
        except Exception as e:
            logger.error(f"❌ Failed to update status to PROCESSING: {e}", exc_info=True)
            raise

        try:
            # Extract content
            result = await URLExtractorFactory.extract(url)

            if result.success:
                # Update with extracted content
                url_content = await repo.get_by_id(url_content_id)
                if url_content:
                    url_content.title = result.title
                    url_content.content = result.content
                    url_content.thumbnail_url = result.thumbnail_url
                    url_content.meta_data = {
                        **url_content.meta_data,
                        **result.metadata,
                    }
                    url_content.status = "completed"
                    url_content.extracted_at = datetime.utcnow()
                    url_content.error_message = None

                    await session.commit()
                    await session.refresh(url_content)

                    # Get project_id from url_content if not provided in payload
                    effective_project_id = project_id or url_content.project_id

                    # Generate chunks and embeddings if we have content and project
                    if result.content and effective_project_id:
                        await self._process_chunks_and_embeddings(
                            url_content_id=url_content_id,
                            project_id=effective_project_id,
                            content=result.content,
                            title=result.title or url,
                            platform=url_content.platform,
                            content_type=url_content.content_type,
                            metadata=result.metadata,
                        )

                logger.info(
                    f"✅ URL extraction completed - url_content_id={url_content_id}, "
                    f"title='{result.title}', content_length={len(result.content or '')}"
                )
            else:
                # Update with error
                await repo.update_status(
                    url_content_id,
                    status="failed",
                    error_message=result.error,
                )
                await session.commit()

                logger.warning(
                    f"⚠️ URL extraction failed - url_content_id={url_content_id}, "
                    f"error={result.error}"
                )

        except Exception as e:
            logger.error(
                f"❌ URL extraction error - url_content_id={url_content_id}: {e}",
                exc_info=True,
            )

            # Update status to failed
            try:
                await repo.update_status(
                    url_content_id,
                    status="failed",
                    error_message=str(e),
                )
                await session.commit()
            except Exception as update_error:
                logger.error(f"❌ Failed to update error status: {update_error}")

            raise

    async def _process_chunks_and_embeddings(
        self,
        url_content_id: UUID,
        project_id: UUID,
        content: str,
        title: str,
        platform: str,
        content_type: str,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Chunk URL content and generate embeddings.
        
        Args:
            url_content_id: UUID of the URL content record
            project_id: Project ID for chunk association
            content: Extracted text content
            title: Content title
            platform: Platform (youtube, bilibili, web, etc.)
            content_type: Content type (video, article, etc.)
            metadata: Additional metadata from extraction
        """
        settings = get_settings()

        # Determine resource type based on content_type
        resource_type = self._get_resource_type(content_type)

        logger.info(
            f"📝 Processing chunks for URL content - "
            f"url_content_id={url_content_id}, resource_type={resource_type.value}"
        )

        # Chunk the content
        chunks = self._chunk_content(
            content=content,
            resource_id=url_content_id,
            resource_type=resource_type,
            project_id=project_id,
            title=title,
            platform=platform,
            metadata=metadata,
        )

        if not chunks:
            logger.warning(f"⚠️ No chunks generated for URL content {url_content_id}")
            return

        logger.info(f"📦 Generated {len(chunks)} chunks for URL content {url_content_id}")

        # Generate embeddings
        try:
            embedding_service = OpenRouterEmbeddingService(
                api_key=settings.openrouter_api_key,
                model=settings.embedding_model,
            )

            contents = [chunk.content for chunk in chunks]
            embeddings = await embedding_service.embed_batch(contents)

            # Set embeddings on chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.set_embedding(embedding)

            logger.info(f"✅ Generated {len(embeddings)} embeddings for URL content")

        except Exception as e:
            logger.error(f"❌ Embedding generation failed for URL content: {e}")
            # Continue without embeddings - chunks can still be saved for reference
            pass

        # Save chunks using repository
        await self._save_chunks(chunks)

    def _get_resource_type(self, content_type: str) -> ResourceType:
        """Map content_type to ResourceType."""
        type_mapping = {
            "video": ResourceType.VIDEO,
            "audio": ResourceType.AUDIO,
            "article": ResourceType.WEB_PAGE,
            "link": ResourceType.WEB_PAGE,
        }
        return type_mapping.get(content_type, ResourceType.WEB_PAGE)

    def _chunk_content(
        self,
        content: str,
        resource_id: UUID,
        resource_type: ResourceType,
        project_id: UUID,
        title: str,
        platform: str,
        metadata: Dict[str, Any],
    ) -> List[ResourceChunk]:
        """
        Chunk content based on resource type.
        
        For video/audio with timestamps, preserves time information.
        For articles/web pages, uses standard text chunking.
        """
        from research_agent.domain.services.resource_chunker import ResourceChunker

        chunker = ResourceChunker(
            chunk_size=1000,
            chunk_overlap=200,
            media_chunk_duration=60.0,
        )

        # Build base metadata
        base_metadata = {
            "title": title,
            "platform": platform,
        }

        # Check for transcript segments (video/audio with timestamps)
        segments = metadata.get("segments", [])
        if segments and resource_type in (ResourceType.VIDEO, ResourceType.AUDIO):
            return self._chunk_with_timestamps(
                segments=segments,
                resource_id=resource_id,
                resource_type=resource_type,
                project_id=project_id,
                base_metadata=base_metadata,
            )

        # Standard text chunking
        return chunker.chunk_text(
            text=content,
            resource_id=resource_id,
            resource_type=resource_type,
            project_id=project_id,
            metadata=base_metadata,
        )

    def _chunk_with_timestamps(
        self,
        segments: List[Dict[str, Any]],
        resource_id: UUID,
        resource_type: ResourceType,
        project_id: UUID,
        base_metadata: Dict[str, Any],
    ) -> List[ResourceChunk]:
        """Chunk transcript segments preserving timestamps."""
        chunks = []
        chunk_duration = 60.0  # seconds per chunk

        current_window_start = 0.0
        current_window_text = []
        current_window_end = 0.0
        chunk_index = 0

        for segment in segments:
            seg_start = segment.get("start", 0.0)
            seg_end = segment.get("end", seg_start)
            seg_text = segment.get("text", "")

            if not seg_text:
                continue

            # Check if we should start a new window
            if seg_start - current_window_start >= chunk_duration and current_window_text:
                # Save current window as chunk
                metadata = base_metadata.copy()
                metadata["start_time"] = current_window_start
                metadata["end_time"] = current_window_end

                chunks.append(
                    ResourceChunk(
                        id=uuid4(),
                        resource_id=resource_id,
                        resource_type=resource_type,
                        project_id=project_id,
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

            chunks.append(
                ResourceChunk(
                    id=uuid4(),
                    resource_id=resource_id,
                    resource_type=resource_type,
                    project_id=project_id,
                    chunk_index=chunk_index,
                    content=" ".join(current_window_text),
                    metadata=metadata,
                )
            )

        return chunks

    async def _save_chunks(self, chunks: List[ResourceChunk]) -> None:
        """Save chunks using the chunk repository."""
        if not chunks:
            return

        batch_size = 50
        total_chunks = len(chunks)
        saved_count = 0

        for i in range(0, total_chunks, batch_size):
            batch = chunks[i : i + batch_size]

            async with get_async_session() as batch_session:
                chunk_repo = get_chunk_repository(batch_session)
                await chunk_repo.save_batch(batch)
                await batch_session.commit()

            saved_count += len(batch)
            logger.debug(f"✅ Saved {saved_count}/{total_chunks} URL content chunks")

        logger.info(f"✅ All {saved_count} URL content chunks saved successfully")


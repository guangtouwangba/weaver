"""URL content extraction task for ARQ worker."""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.models import UrlContentModel
from research_agent.infrastructure.database.repositories.sqlalchemy_url_content_repo import (
    SQLAlchemyUrlContentRepository,
)
from research_agent.infrastructure.url_extractor import URLExtractorFactory
from research_agent.shared.utils.logger import logger
from research_agent.worker.tasks.base import BaseTask


class URLProcessorTask(BaseTask):
    """
    Task for processing URL content extraction.

    Pipeline:
    1. Update status to processing
    2. Detect platform and extract content
    3. Update UrlContent record with extracted data
    4. Update status to completed/failed
    """

    @property
    def task_type(self) -> str:
        return "process_url"

    async def execute(self, payload: Dict[str, Any], session: AsyncSession) -> None:
        """
        Process URL extraction.

        Payload:
            url_content_id: UUID of the UrlContent record
            url: The URL to extract
        """
        url_content_id = UUID(payload["url_content_id"])
        url = payload["url"]

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


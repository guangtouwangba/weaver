"""Thumbnail generator task - generates PDF first-page thumbnails."""

from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.models import DocumentModel
from research_agent.infrastructure.websocket.notification_service import (
    document_notification_service,
)
from research_agent.shared.utils.logger import logger
from research_agent.worker.tasks.base import BaseTask


class ThumbnailGeneratorTask(BaseTask):
    """Generate PDF thumbnail from first page."""

    @property
    def task_type(self) -> str:
        return "thumbnail_generator"

    async def execute(self, payload: dict[str, Any], session: AsyncSession) -> None:
        """
        Generate thumbnail for a PDF document.

        Payload:
            document_id: UUID of the document
            project_id: UUID of the project
            file_path: Path to the PDF file
        """
        document_id = UUID(payload["document_id"])
        project_id = UUID(payload["project_id"])
        file_path = payload["file_path"]

        logger.info(f"[THUMBNAIL] Starting thumbnail generation for {document_id}")

        # Update status to processing
        await self._update_thumbnail_status(session, document_id, "processing")
        await session.commit()

        try:
            # Generate thumbnail
            thumbnail_path = await self._generate_thumbnail(file_path, document_id)

            if thumbnail_path:
                # Update document with thumbnail path
                await self._update_thumbnail_status(session, document_id, "ready", thumbnail_path)
                await session.commit()

                # Send WebSocket notification
                await document_notification_service.notify_thumbnail_ready(
                    project_id=str(project_id),
                    document_id=str(document_id),
                    thumbnail_url=f"/api/v1/documents/{document_id}/thumbnail",
                )

                logger.info(f"[THUMBNAIL] Thumbnail generated for {document_id}")
            else:
                await self._update_thumbnail_status(session, document_id, "error")
                await session.commit()
                logger.warning(f"[THUMBNAIL] Failed to generate thumbnail for {document_id}")

        except Exception as e:
            logger.error(f"[THUMBNAIL] Error generating thumbnail for {document_id}: {e}")
            await self._update_thumbnail_status(session, document_id, "error")
            await session.commit()
            raise

    async def _generate_thumbnail(self, file_path: str, document_id: UUID) -> str | None:
        """
        Generate thumbnail from PDF first page using PyMuPDF.

        Args:
            file_path: Path to PDF file
            document_id: Document UUID for output filename

        Returns:
            Path to generated thumbnail, or None on failure
        """
        try:
            import fitz  # PyMuPDF

            pdf_path = Path(file_path)
            if not pdf_path.exists():
                logger.warning(f"[THUMBNAIL] PDF not found: {file_path}")
                return None

            # Open PDF and get first page
            doc = fitz.open(str(pdf_path))
            if len(doc) == 0:
                doc.close()
                return None

            page = doc[0]

            # Calculate zoom for 300px width
            target_width = 300
            page_width = page.rect.width
            zoom = target_width / page_width

            # Render page to pixmap
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            # Create thumbnails directory
            thumbnails_dir = pdf_path.parent.parent / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)

            # Save as WebP for smaller file size
            output_path = thumbnails_dir / f"{document_id}.webp"

            # Convert to PIL and save as WebP
            import io

            from PIL import Image

            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            img.save(str(output_path), "WEBP", quality=80)

            doc.close()

            return str(output_path)

        except ImportError:
            logger.warning("[THUMBNAIL] PyMuPDF not installed, skipping thumbnail generation")
            return None
        except Exception as e:
            logger.error(f"[THUMBNAIL] Error generating thumbnail: {e}")
            return None

    async def _update_thumbnail_status(
        self,
        session: AsyncSession,
        document_id: UUID,
        status: str,
        thumbnail_path: str | None = None,
    ) -> None:
        """Update document thumbnail status in database."""
        values = {"thumbnail_status": status}
        if thumbnail_path:
            values["thumbnail_path"] = thumbnail_path

        await session.execute(
            update(DocumentModel).where(DocumentModel.id == document_id).values(**values)
        )

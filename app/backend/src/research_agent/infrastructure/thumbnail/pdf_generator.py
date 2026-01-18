"""PDF thumbnail generator.

Generates thumbnails from PDF first page using PyMuPDF.
"""

import io
from pathlib import Path
from uuid import UUID

from research_agent.infrastructure.thumbnail.base import (
    ThumbnailGenerator,
    ThumbnailResult,
)
from research_agent.shared.utils.logger import logger


class PDFThumbnailGenerator(ThumbnailGenerator):
    """Generate thumbnail from PDF first page using PyMuPDF."""

    def supported_mime_types(self) -> list[str]:
        return ["application/pdf"]

    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    async def generate(
        self,
        file_path: str,
        document_id: UUID,
        output_dir: Path,
    ) -> ThumbnailResult:
        """
        Generate thumbnail from PDF first page.

        Args:
            file_path: Path to PDF file.
            document_id: Document UUID for output filename.
            output_dir: Directory to save thumbnail.

        Returns:
            ThumbnailResult with path to generated WebP image.
        """
        try:
            import fitz  # PyMuPDF
            from PIL import Image

            pdf_path = Path(file_path)
            if not pdf_path.exists():
                logger.warning(f"[PDFThumbnail] PDF not found: {file_path}")
                return ThumbnailResult(
                    path=None,
                    success=False,
                    error=f"PDF file not found: {file_path}",
                )

            # Open PDF and get first page
            doc = fitz.open(str(pdf_path))
            if len(doc) == 0:
                doc.close()
                return ThumbnailResult(
                    path=None,
                    success=False,
                    error="PDF has no pages",
                )

            page = doc[0]

            # Calculate zoom for 300px width
            target_width = 300
            page_width = page.rect.width
            zoom = target_width / page_width

            # Render page to pixmap
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            # Ensure output directory exists
            output_dir.mkdir(exist_ok=True, parents=True)

            # Save as WebP for smaller file size
            output_path = output_dir / f"{document_id}.webp"

            # Convert to PIL and save as WebP
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            img.save(str(output_path), "WEBP", quality=80)

            doc.close()

            logger.info(f"[PDFThumbnail] Generated thumbnail at {output_path}")
            return ThumbnailResult(
                path=str(output_path),
                success=True,
            )

        except ImportError as e:
            logger.warning(
                f"[PDFThumbnail] Missing dependency: {e}. PyMuPDF or Pillow not installed?"
            )
            return ThumbnailResult(
                path=None,
                success=False,
                error=f"Missing dependency: {e}",
            )
        except Exception as e:
            logger.error(f"[PDFThumbnail] Error generating thumbnail: {e}", exc_info=True)
            return ThumbnailResult(
                path=None,
                success=False,
                error=str(e),
            )

"""Thumbnail service - handles PDF thumbnail generation."""

import logging
from pathlib import Path
from uuid import UUID

logger = logging.getLogger(__name__)


class ThumbnailService:
    """Service for generating document thumbnails."""

    async def generate_thumbnail(
        self, file_path: str, document_id: UUID, output_dir: Path | None = None
    ) -> str | None:
        """
        Generate thumbnail from PDF first page using PyMuPDF.

        Args:
            file_path: Path to PDF file
            document_id: Document UUID for output filename
            output_dir: Optional directory to save thumbnail. If None, derived from file_path.

        Returns:
            Path to generated thumbnail, or None on failure
        """
        try:
            import io

            import fitz  # PyMuPDF
            from PIL import Image

            pdf_path = Path(file_path)
            if not pdf_path.exists():
                logger.warning(f"[THUMBNAIL] PDF not found: {file_path}")
                return None

            # Open PDF and get first page
            # Use fitz.open with filetype hint if needed, or just path
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
            if output_dir:
                thumbnails_dir = output_dir
            else:
                # Fallback to existing logic (relative path)
                thumbnails_dir = pdf_path.parent.parent / "thumbnails"

            thumbnails_dir.mkdir(exist_ok=True, parents=True)

            # Save as WebP for smaller file size
            output_path = thumbnails_dir / f"{document_id}.webp"

            # Convert to PIL and save as WebP
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            img.save(str(output_path), "WEBP", quality=80)

            doc.close()

            logger.info(f"[THUMBNAIL] Generated thumbnail at {output_path}")
            return str(output_path)

        except ImportError as e:
            logger.warning(f"[THUMBNAIL] Missing dependency: {e}. PyMuPDF or Pillow not installed?")
            return None
        except Exception as e:
            logger.error(f"[THUMBNAIL] Error generating thumbnail: {e}", exc_info=True)
            return None

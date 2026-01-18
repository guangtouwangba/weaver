"""Text file thumbnail generator.

Generates preview images from text file content using Pillow.
"""

from pathlib import Path
from uuid import UUID

from research_agent.infrastructure.thumbnail.base import (
    ThumbnailGenerator,
    ThumbnailResult,
)
from research_agent.shared.utils.logger import logger


class TextThumbnailGenerator(ThumbnailGenerator):
    """Generate preview image from text file content."""

    # Configuration
    PREVIEW_LINES = 20  # Number of lines to show
    IMAGE_WIDTH = 300
    IMAGE_HEIGHT = 400
    FONT_SIZE = 12
    LINE_HEIGHT = 16
    PADDING = 15
    BG_COLOR = "#FFFFFF"
    TEXT_COLOR = "#333333"
    BORDER_COLOR = "#E5E7EB"

    def supported_mime_types(self) -> list[str]:
        return ["text/plain"]

    def supported_extensions(self) -> list[str]:
        return [".txt", ".md", ".csv"]

    async def generate(
        self,
        file_path: str,
        document_id: UUID,
        output_dir: Path,
    ) -> ThumbnailResult:
        """
        Generate preview image from text file.

        Args:
            file_path: Path to text file.
            document_id: Document UUID for output filename.
            output_dir: Directory to save thumbnail.

        Returns:
            ThumbnailResult with path to generated WebP image.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont

            text_path = Path(file_path)
            if not text_path.exists():
                logger.warning(f"[TextThumbnail] File not found: {file_path}")
                return ThumbnailResult(
                    path=None,
                    success=False,
                    error=f"File not found: {file_path}",
                )

            # Read first N lines from file
            try:
                with open(text_path, encoding="utf-8") as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= self.PREVIEW_LINES:
                            break
                        # Truncate long lines
                        lines.append(line.rstrip()[:50])
            except UnicodeDecodeError:
                # Fallback to latin-1
                with open(text_path, encoding="latin-1") as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= self.PREVIEW_LINES:
                            break
                        lines.append(line.rstrip()[:50])

            # Create image
            img = Image.new("RGB", (self.IMAGE_WIDTH, self.IMAGE_HEIGHT), self.BG_COLOR)
            draw = ImageDraw.Draw(img)

            # Draw border
            draw.rectangle(
                [(0, 0), (self.IMAGE_WIDTH - 1, self.IMAGE_HEIGHT - 1)],
                outline=self.BORDER_COLOR,
                width=1,
            )

            # Try to use a monospace font, fall back to default
            try:
                font = ImageFont.truetype("DejaVuSansMono.ttf", self.FONT_SIZE)
            except OSError:
                try:
                    font = ImageFont.truetype("Courier", self.FONT_SIZE)
                except OSError:
                    font = ImageFont.load_default()

            # Draw text lines
            y = self.PADDING
            for line in lines:
                if y + self.LINE_HEIGHT > self.IMAGE_HEIGHT - self.PADDING:
                    # Draw ellipsis if content is cut off
                    draw.text((self.PADDING, y), "...", fill=self.TEXT_COLOR, font=font)
                    break
                draw.text((self.PADDING, y), line, fill=self.TEXT_COLOR, font=font)
                y += self.LINE_HEIGHT

            # Ensure output directory exists
            output_dir.mkdir(exist_ok=True, parents=True)

            # Save as WebP
            output_path = output_dir / f"{document_id}.webp"
            img.save(str(output_path), "WEBP", quality=80)

            logger.info(f"[TextThumbnail] Generated preview at {output_path}")
            return ThumbnailResult(
                path=str(output_path),
                success=True,
            )

        except ImportError as e:
            logger.warning(f"[TextThumbnail] Missing dependency: {e}. Pillow not installed?")
            return ThumbnailResult(
                path=None,
                success=False,
                error=f"Missing dependency: {e}",
            )
        except Exception as e:
            logger.error(f"[TextThumbnail] Error generating thumbnail: {e}", exc_info=True)
            return ThumbnailResult(
                path=None,
                success=False,
                error=str(e),
            )

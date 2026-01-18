"""Text file parser for plain text documents.

This module provides a simple parser for `.txt` files, reading the entire
content as a single page.
"""

from research_agent.infrastructure.parser.base import (
    DocumentParser,
    DocumentParsingError,
    DocumentType,
    ParsedPage,
    ParseResult,
)


class TextParser(DocumentParser):
    """
    Parser for plain text files (.txt).

    Reads the file content as UTF-8 and returns it as a single page.
    The chunking service will handle splitting if needed.
    """

    async def parse(self, file_path: str) -> ParseResult:
        """
        Parse a plain text file.

        Args:
            file_path: Path to the .txt file.

        Returns:
            ParseResult containing the text content as a single page.

        Raises:
            DocumentParsingError: If reading the file fails.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1 if UTF-8 fails
            try:
                with open(file_path, encoding="latin-1") as f:
                    content = f.read()
            except Exception as e:
                raise DocumentParsingError(
                    f"Failed to read text file with fallback encoding: {e}",
                    file_path=file_path,
                    cause=e,
                )
        except Exception as e:
            raise DocumentParsingError(
                f"Failed to read text file: {e}",
                file_path=file_path,
                cause=e,
            )

        page = ParsedPage(
            page_number=1,
            content=content,
            metadata={"source_type": "text"},
        )

        return ParseResult(
            pages=[page],
            document_type=DocumentType.UNKNOWN,  # Text files don't have a specific DocumentType
            metadata={"file_path": file_path},
            page_count=1,
            parser_name=self.parser_name,
        )

    def supported_formats(self) -> list[str]:
        """Return supported MIME types."""
        return ["text/plain"]

    def supported_extensions(self) -> list[str]:
        """Return supported file extensions."""
        return [".txt"]

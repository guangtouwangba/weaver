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
        # Smart encoding detection for text files
        encoding_to_try = ["utf-8"]

        # Try to detect encoding using chardet if available
        try:
            import chardet

            with open(file_path, "rb") as f:
                raw_data = f.read(8192)  # Read first 8KB for detection
                result = chardet.detect(raw_data)
                detected_encoding = result.get("encoding")
                if detected_encoding and detected_encoding.lower() != "utf-8":
                    encoding_to_try.insert(0, detected_encoding)
        except ImportError:
            pass  # chardet not available, continue with default encodings

        # Add common CJK encodings as fallbacks
        encoding_to_try.extend(["gbk", "gb2312", "gb18030", "latin-1"])

        content = None
        for encoding in encoding_to_try:
            try:
                with open(file_path, encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if content is None:
            raise DocumentParsingError(
                "Failed to read text file: could not decode with any supported encoding",
                file_path=file_path,
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

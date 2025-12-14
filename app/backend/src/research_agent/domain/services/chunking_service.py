"""Text chunking service with dynamic strategy selection."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from langchain_text_splitters import (
    Language,
    MarkdownTextSplitter,
    PythonCodeTextSplitter,
    RecursiveCharacterTextSplitter,
)

from research_agent.shared.utils.logger import logger


@runtime_checkable
class PageLike(Protocol):
    """Protocol for page-like objects (PDFPage, ParsedPage, etc.)."""

    page_number: int
    content: str


class DocumentType(Enum):
    """Document type classification."""

    SHORT_TEXT = "short_text"
    LONG_DOCUMENT = "long_document"
    CODE = "code"
    MARKDOWN = "markdown"
    UNSTRUCTURED = "unstructured"


@dataclass
class ChunkConfig:
    """Chunking configuration."""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100


class ChunkingStrategy(ABC):
    """Base class for chunking strategies."""

    def __init__(self, config: ChunkConfig):
        self.config = config

    @abstractmethod
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces.

        Args:
            text: Text to chunk
            metadata: Additional metadata (e.g., page_number, file_type)

        Returns:
            List of chunk dictionaries with 'content' and 'metadata'
        """
        pass


class NoChunkingStrategy(ChunkingStrategy):
    """Strategy for short texts that don't need chunking."""

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the entire text as a single chunk."""
        if not text.strip():
            return []

        logger.debug(f"NoChunking: Text length {len(text)} chars")
        return [{"content": text.strip(), "metadata": {**metadata, "chunk_type": "full_text"}}]


class RecursiveChunkingStrategy(ChunkingStrategy):
    """Strategy for long documents (PDF/Markdown) using recursive character splitting."""

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text using recursive character splitting."""
        if not text.strip():
            return []

        # Use RecursiveCharacterTextSplitter with smart separators
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
            length_function=len,
        )

        chunks = splitter.split_text(text)
        logger.debug(f"RecursiveChunking: {len(chunks)} chunks from {len(text)} chars")

        return [
            {"content": chunk.strip(), "metadata": {**metadata, "chunk_type": "recursive"}}
            for chunk in chunks
            if len(chunk.strip()) >= self.config.min_chunk_size
        ]


class MarkdownChunkingStrategy(ChunkingStrategy):
    """Strategy for Markdown documents with header-aware splitting."""

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk Markdown text preserving structure."""
        if not text.strip():
            return []

        # Use MarkdownTextSplitter for header-aware chunking
        splitter = MarkdownTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )

        chunks = splitter.split_text(text)
        logger.debug(f"MarkdownChunking: {len(chunks)} chunks from {len(text)} chars")

        return [
            {"content": chunk.strip(), "metadata": {**metadata, "chunk_type": "markdown"}}
            for chunk in chunks
            if len(chunk.strip()) >= self.config.min_chunk_size
        ]


class CodeChunkingStrategy(ChunkingStrategy):
    """Strategy for code files using language-specific splitters."""

    def __init__(self, config: ChunkConfig, language: str = "python"):
        super().__init__(config)
        self.language = language

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk code using language-specific splitter."""
        if not text.strip():
            return []

        # Select appropriate splitter based on language
        if self.language.lower() == "python":
            splitter = PythonCodeTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
            )
        else:
            # Fallback to RecursiveCharacterTextSplitter for other languages
            # with code-friendly separators
            splitter = RecursiveCharacterTextSplitter.from_language(
                language=Language.PYTHON,  # Default to Python-like structure
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
            )

        chunks = splitter.split_text(text)
        logger.debug(f"CodeChunking ({self.language}): {len(chunks)} chunks from {len(text)} chars")

        return [
            {
                "content": chunk.strip(),
                "metadata": {**metadata, "chunk_type": "code", "language": self.language},
            }
            for chunk in chunks
            if len(chunk.strip()) >= self.config.min_chunk_size
        ]


class SemanticChunkingStrategy(ChunkingStrategy):
    """
    Strategy for unstructured text (meeting transcripts, podcasts).
    Uses simpler recursive splitting since true semantic chunking requires embeddings.
    """

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk unstructured text with smaller chunks for better semantic coherence."""
        if not text.strip():
            return []

        # Use smaller chunks for better semantic coherence
        # True semantic chunking would require embedding-based similarity
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size // 2,  # Smaller chunks
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
            length_function=len,
        )

        chunks = splitter.split_text(text)
        logger.debug(f"SemanticChunking: {len(chunks)} chunks from {len(text)} chars")

        return [
            {"content": chunk.strip(), "metadata": {**metadata, "chunk_type": "semantic"}}
            for chunk in chunks
            if len(chunk.strip()) >= self.config.min_chunk_size
        ]


class ChunkingStrategyFactory:
    """Factory for selecting appropriate chunking strategy."""

    SHORT_TEXT_THRESHOLD = 1000  # Characters
    CODE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".rb"}
    MARKDOWN_EXTENSIONS = {".md", ".markdown"}

    @classmethod
    def get_strategy(
        cls,
        text: str,
        mime_type: str,
        filename: str,
        config: ChunkConfig,
    ) -> ChunkingStrategy:
        """
        Select appropriate chunking strategy based on document characteristics.

        Args:
            text: Document text content
            mime_type: MIME type of the document
            filename: Original filename
            config: Chunking configuration

        Returns:
            Appropriate ChunkingStrategy instance
        """
        text_length = len(text.strip())
        file_extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        # Rule 1: Short text - no chunking
        if text_length < cls.SHORT_TEXT_THRESHOLD:
            logger.info(f"Selected NoChunkingStrategy (text length: {text_length})")
            return NoChunkingStrategy(config)

        # Rule 2: Code files - language-specific chunking
        if file_extension in cls.CODE_EXTENSIONS:
            language = file_extension[1:]  # Remove the dot
            logger.info(f"Selected CodeChunkingStrategy (language: {language})")
            return CodeChunkingStrategy(config, language=language)

        # Rule 3: Markdown files - header-aware chunking
        if file_extension in cls.MARKDOWN_EXTENSIONS or "markdown" in mime_type.lower():
            logger.info("Selected MarkdownChunkingStrategy")
            return MarkdownChunkingStrategy(config)

        # Rule 4: Check for structured content (headers, lists)
        # Simple heuristic: if document has many markdown-like headers
        line_count = text.count("\n") + 1
        header_count = text.count("\n#") + text.count("\n##") + text.count("\n###")

        if header_count > line_count * 0.05:  # More than 5% of lines are headers
            logger.info("Selected MarkdownChunkingStrategy (detected headers)")
            return MarkdownChunkingStrategy(config)

        # Rule 5: Unstructured long text (transcripts, etc.) - semantic chunking
        # Heuristic: Very few punctuation marks relative to length
        sentence_count = text.count(". ") + text.count("! ") + text.count("? ")

        if text_length > 5000 and sentence_count < text_length / 500:
            logger.info("Selected SemanticChunkingStrategy (unstructured text)")
            return SemanticChunkingStrategy(config)

        # Default: Recursive chunking for general long documents
        logger.info("Selected RecursiveChunkingStrategy (default)")
        return RecursiveChunkingStrategy(config)


class ChunkingService:
    """Service for chunking text with dynamic strategy selection."""

    def __init__(self, config: ChunkConfig | None = None):
        self.config = config or ChunkConfig()

    def chunk_pages(
        self,
        pages: List[PageLike],
        mime_type: str = "application/pdf",
        filename: str = "document.pdf",
    ) -> List[dict]:
        """
        Chunk PDF pages into smaller pieces using dynamic strategy selection.

        Args:
            pages: List of PDF pages
            mime_type: MIME type of the document
            filename: Original filename

        Returns:
            List of chunk dictionaries
        """
        # Combine all pages text for strategy selection
        full_text = "\n\n".join([page.content for page in pages])

        # Select chunking strategy
        strategy = ChunkingStrategyFactory.get_strategy(
            text=full_text,
            mime_type=mime_type,
            filename=filename,
            config=self.config,
        )

        # Chunk each page with the selected strategy
        chunks = []
        chunk_index = 0

        for page in pages:
            page_metadata = {"page_number": page.page_number}
            page_chunks = strategy.chunk_text(page.content, page_metadata)

            for chunk_data in page_chunks:
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": chunk_data["content"],
                        "page_number": chunk_data["metadata"].get("page_number"),
                        "metadata": chunk_data["metadata"],
                    }
                )
                chunk_index += 1

        logger.info(
            f"Created {len(chunks)} chunks from {len(pages)} pages using {strategy.__class__.__name__}"
        )
        return chunks

    def chunk_text(
        self,
        text: str,
        mime_type: str = "text/plain",
        filename: str = "document.txt",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[dict]:
        """
        Chunk arbitrary text using dynamic strategy selection.

        Args:
            text: Text to chunk
            mime_type: MIME type
            filename: Original filename
            metadata: Additional metadata

        Returns:
            List of chunk dictionaries
        """
        strategy = ChunkingStrategyFactory.get_strategy(
            text=text,
            mime_type=mime_type,
            filename=filename,
            config=self.config,
        )

        base_metadata = metadata or {}
        chunk_results = strategy.chunk_text(text, base_metadata)

        # Format for compatibility
        chunks = []
        for i, chunk_data in enumerate(chunk_results):
            chunks.append(
                {
                    "chunk_index": i,
                    "content": chunk_data["content"],
                    "metadata": chunk_data["metadata"],
                }
            )

        logger.info(f"Created {len(chunks)} chunks using {strategy.__class__.__name__}")
        return chunks

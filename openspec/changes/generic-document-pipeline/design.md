# Design: Generic Document Pipeline

## Overview

This design introduces a unified document processing pipeline where each stage (parsing, thumbnail generation, chunking) follows the same extensible Registry pattern.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Document Processing Pipeline                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Upload → FileTypeDetector → ParserRegistry → ThumbnailRegistry │
│                                    ↓                             │
│                            ChunkerRegistry → EmbeddingService    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Pattern: Registry + Strategy

Each processing capability follows the same pattern:

```python
# 1. Abstract Base Class
class Handler(ABC):
    @abstractmethod
    def supported_mime_types(self) -> list[str]: ...
    @abstractmethod
    def supported_extensions(self) -> list[str]: ...
    @abstractmethod
    async def process(self, file_path: str, **kwargs) -> Result: ...

# 2. Registry
class Registry:
    def register(self, handler: Handler): ...
    def get_handler(self, mime_type, extension) -> Handler | None: ...
    def is_supported(self, mime_type, extension) -> bool: ...

# 3. Factory (public interface)
class Factory:
    @staticmethod
    def get(mime_type, extension) -> Handler: ...
    @staticmethod
    def is_supported(mime_type, extension) -> bool: ...
```

## Component: ThumbnailRegistry

### Structure

```
infrastructure/thumbnail/
├── __init__.py
├── base.py              # ThumbnailGenerator ABC, ThumbnailResult
├── factory.py           # ThumbnailRegistry, ThumbnailFactory
├── pdf_generator.py     # PDFThumbnailGenerator
├── text_generator.py    # TextThumbnailGenerator
└── image_generator.py   # ImageThumbnailGenerator (future)
```

### Interface

```python
@dataclass
class ThumbnailResult:
    path: str | None       # Output file path
    success: bool          # Whether generation succeeded
    error: str | None      # Error message if failed

class ThumbnailGenerator(ABC):
    @property
    def generator_name(self) -> str: ...
    
    @abstractmethod
    def supported_mime_types(self) -> list[str]: ...
    
    @abstractmethod
    def supported_extensions(self) -> list[str]: ...
    
    @abstractmethod
    async def generate(
        self,
        file_path: str,
        document_id: UUID,
        output_dir: Path
    ) -> ThumbnailResult: ...
```

### Usage

```python
# Before (hardcoded)
if file_extension == ".pdf":
    thumbnail_service.generate_thumbnail(...)

# After (registry)
if ThumbnailFactory.is_supported(extension=file_extension):
    result = await ThumbnailFactory.generate(
        file_path,
        document_id,
        output_dir,
        extension=file_extension
    )
```

## File Type Support Matrix

| Type | Parser | Thumbnail | Chunker |
|------|--------|-----------|---------|
| PDF | ✅ PyMuPDF | ✅ PDFThumbnail | ✅ Semantic |
| TXT | ✅ TextParser | ✅ TextThumbnail | ✅ Semantic |
| DOCX | ✅ Unstructured | 🔜 DocxThumbnail | ✅ Semantic |
| CSV | 🔜 | 🔜 | 🔜 RowChunker |
| Video | 🔜 | 🔜 FrameThumbnail | 🔜 TranscriptChunker |

## Trade-offs

| Decision | Rationale |
|----------|-----------|
| Registry over if/else | Extensibility without modifying core code |
| Async generators | Some generation (Pillow) could be CPU-bound, but keeping consistent with parser pattern |
| Module-level registry | Simple initialization, matches ParserRegistry pattern |

## Migration Path

1. **Phase 1**: Create ThumbnailRegistry, migrate PDF logic, add TXT support
2. **Phase 2**: Add ChunkerRegistry for format-specific chunking
3. **Phase 3**: Create unified DocumentPipeline orchestrator

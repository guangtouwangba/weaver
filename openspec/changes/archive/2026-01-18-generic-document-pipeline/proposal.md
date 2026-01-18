# Proposal: Generic Document Pipeline

## Goal
Refactor document processing into a pluggable pipeline with Registry pattern, enabling:
- Easy addition of new file types (txt, docx, video, audio)
- Consistent processing behavior across all formats
- Single point of responsibility for each capability

## Context
Current state:
- **Parser**: ✅ Uses Registry pattern (`ParserFactory`)
- **Thumbnail**: ❌ Hardcoded PDF-only logic in 3+ files
- **Chunker**: ⚠️ Generic only, no format-aware chunking

Adding `.txt` support exposed these issues - thumbnail generation failed because it assumed PDF.

## Proposed Changes

### Backend (Phase 1: Thumbnail)
1. Create `infrastructure/thumbnail/` module:
   - `base.py` - ThumbnailGenerator ABC
   - `factory.py` - ThumbnailRegistry + Factory
   - `pdf_generator.py` - PDF thumbnails (PyMuPDF)
   - `text_generator.py` - Text preview image (Pillow)

2. Refactor callers:
   - `documents.py` - Use `ThumbnailFactory.is_supported()`
   - `document_processor.py` - Use `ThumbnailFactory.is_supported()`

3. Delete:
   - `thumbnail_service.py` - Logic migrated to generators

### Backend (Phase 2: Chunker) - Future
- Add `infrastructure/chunker/` with ChunkerRegistry
- Enable format-specific chunking (CSV rows, transcript timestamps)

## Verification Plan
1. Upload `.txt` file - should process without thumbnail errors
2. Upload `.pdf` file - thumbnail should still generate
3. Run unit tests for ThumbnailFactory

# Tasks

## Phase 1: ThumbnailRegistry ✅

- [x] Create `infrastructure/thumbnail/__init__.py`
- [x] Create `infrastructure/thumbnail/base.py` with ThumbnailGenerator ABC
- [x] Create `infrastructure/thumbnail/factory.py` with Registry + Factory
- [x] Create `infrastructure/thumbnail/pdf_generator.py` migrated from thumbnail_service
- [x] Create `infrastructure/thumbnail/text_generator.py` for .txt preview
- [x] Update `api/v1/documents.py` to use `ThumbnailFactory.is_supported()`
- [x] Update `worker/tasks/document_processor.py` to use `ThumbnailFactory`
- [x] Update `application/use_cases/document/upload_document.py` to use `ThumbnailFactory`
- [x] Delete `domain/services/thumbnail_service.py` after migration
- [x] Add unit tests for ThumbnailFactory
- [ ] Manual verification: upload .txt and .pdf files

## Phase 2: ChunkerRegistry ✅

- [x] Create `infrastructure/chunker/__init__.py`
- [x] Create `infrastructure/chunker/base.py` with Chunker ABC
- [x] Create `infrastructure/chunker/factory.py` with Registry + Factory
- [x] Create `infrastructure/chunker/default_chunker.py` wrapping ChunkingService
- [x] Create `infrastructure/chunker/csv_chunker.py` for row-based chunking
- [x] Create `infrastructure/chunker/transcript_chunker.py` for timestamp-aware chunking
- [x] Add unit tests for ChunkerFactory
- [ ] Integrate with document_processor.py (optional - existing ChunkingService still works)

## Phase 3: Pipeline Unification (Future)

- [ ] Create `domain/services/document_pipeline.py`
- [ ] Simplify document_processor.py to use pipeline

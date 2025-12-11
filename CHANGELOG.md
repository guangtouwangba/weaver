# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed - 2025-12-11

#### Markdown Rendering in AI Responses

**Frontend:**
- **Markdown Support** (`components/studio/AssistantPanel.tsx`):
  - Added `react-markdown`, `remark-gfm`, and `rehype-raw` dependencies for proper markdown rendering
  - AI responses now render with full markdown formatting (bold, lists, headers, code blocks, blockquotes, etc.)
  - Custom `MarkdownContent` component with MUI-styled typography
  - `CitationRenderer` component for interactive citation tags with drag-and-drop support
  - GitHub Flavored Markdown (GFM) support including tables and task lists

**Technical Details:**
- **Author**: aqiu
- **Implementation**: Replaced manual regex-based citation parsing with ReactMarkdown + rehype-raw for HTML/XML tag support
- **Scope**: AssistantPanel chat responses

### Added - 2025-12-09

#### Multi-Format Document Parser Architecture

**Backend:**
- **Extensible Parser Interface** (`infrastructure/parser/base.py`):
  - `DocumentParser` abstract base class for all format-specific parsers
  - `ParsedPage` dataclass with support for text, OCR metadata, timestamps, and speaker IDs
  - `ParseResult` for document-level metadata including page count, OCR status, and duration
  - `DocumentType` enum: PDF, DOCX, PPTX, AUDIO, VIDEO, UNKNOWN

- **Docling Parser** (`infrastructure/parser/docling_parser.py`):
  - Handles PDF, DOCX, PPTX files with OCR support
  - Advanced layout analysis for multi-column and table content
  - Automatic page extraction and structure preservation

- **Parser Factory** (`infrastructure/parser/factory.py`):
  - Registry pattern for pluggable parser architecture
  - `ParserFactory.get_parser()` for MIME type or extension-based parser selection
  - Easy extension for future formats (WhisperX for Audio/Video)

- **Document Entity Updates** (`domain/entities/document.py`):
  - `DocumentType` enum with `from_mime_type()` class method
  - Helper properties: `has_ocr`, `is_audio_video`, `duration_seconds`, `document_type`
  - Full support for `parsing_metadata` JSONB field

- **Worker Refactoring** (`worker/tasks/document_processor.py`):
  - Replaced `PyMuPDFParser` with `ParserFactory` for dynamic parser selection
  - Generic processing pipeline supporting any `ParsedPage`-compatible output
  - Parser metadata integration in document processing

**Infrastructure:**
- Added `docling>=2.0.0` dependency (already present in pyproject.toml)
- Retained `pymupdf>=1.24.0` as fallback option

**Technical Details:**
- **Author**: aqiu
- **Implementation**: Multi-format parser architecture as per multi-format_document_support plan
- **Scope**: PDF processing migration to Docling, foundation for Word/PPT/Audio/Video support

### Added - 2025-12-09

#### RAG Memory Optimization - Short-term and Long-term Memory

**Backend:**
- **Long-Term Episodic Memory**: Vectorized conversation history for semantic retrieval
  - New `chat_memories` table with vector embeddings for Q&A pairs
  - `SQLAlchemyMemoryRepository` for memory CRUD operations and similarity search
  - Automatic memory ingestion after each RAG response
  - Semantic retrieval of relevant past discussions based on query similarity

- **Short-Term Working Memory**: Session summaries for context efficiency
  - New `chat_summaries` table for storing conversation summaries
  - `MemoryService` with LLM-based summarization for older conversation turns
  - Sliding window approach to maintain context while staying within token limits

- **Memory-Aware RAG Pipeline**: 
  - Updated `GraphState` with `session_summary` and `retrieved_memories` fields
  - New `retrieve_memory` and `get_session_summary` graph nodes
  - `format_memory_for_context` helper for prompt injection
  - Memory context injection in both traditional and streaming generation modes

- **Updated Prompts**: 
  - New `MEMORY_AWARE_SYSTEM_PROMPT` for context-aware responses
  - Updated generation prompts to explain available context types

**Database:**
- Migration `20241209_000001_add_chat_memory_tables.py`:
  - `chat_memories` table with vector similarity index (ivfflat)
  - `chat_summaries` table for session-level summaries

### Added - 2025-12-07

#### RAG Architecture Refactoring - Mega-Prompt with XML Citations

**Backend:**
- **WebSocket Notifications**: Real-time document processing status updates
  - New `DocumentNotificationService` for managing WebSocket connections
  - WebSocket endpoints: `/ws/projects/{project_id}/documents` and `/ws/projects/{project_id}/documents/{document_id}`
  - Integration with document processor for status notifications (PROCESSING, READY, ERROR, graph_status)
  
- **Full Document Retrieval Service**: Advanced RAG retrieval with dynamic context degradation
  - `FullDocumentRetrievalService` for retrieving entire documents instead of chunks
  - Adaptive context strategy: intelligently truncates documents when exceeding LLM context limits
  - Configurable retrieval modes: CHUNKS, FULL_DOCUMENT, AUTO
  
- **Mega-Prompt System**: XML-structured prompts for long-context RAG
  - `build_mega_prompt()` function with structured XML format:
    - `<system_instruction>`: Role and behavior guidelines
    - `<documents>`: Full document content with metadata
    - `<output_rules>`: Strict citation format requirements
    - `<thinking_process>`: Intent-driven reasoning templates
    - `<user_query>`: User question
  - Intent-based thinking process templates (factual, conceptual, comparison, howto, summary, explanation)
  
- **XML Citation Parser**: Robust parsing of `<cite>` tags from LLM output
  - `XMLCitationParser` with streaming support for real-time citation extraction
  - Handles malformed/incomplete tags gracefully
  - Validates citation format and content
  
- **Quote-to-Coordinate Service**: Precise citation localization
  - `TextLocator` service using fuzzy matching (rapidfuzz) to locate quoted text
  - Calculates character positions and page numbers from page_map
  - Supports exact match and fuzzy match with configurable threshold
  
- **Streaming Citation Events**: Real-time citation parsing during LLM generation
  - `StreamingCitationParser` class for incremental citation extraction
  - Emits `citation` events during token streaming
  - Final `citations` event with all parsed citations at end of response
  
- **Configuration**: New settings for Mega-Prompt mode
  - `mega_prompt_citation_mode`: xml_quote | text_markers | json_mode
  - `citation_match_threshold`: Fuzzy match threshold (0-100) for Quote-to-Coordinate

**Frontend:**
- **Citation Rendering**: Interactive citation display in chat interface
  - `Citation` interface with document_id, quote, page_number, char_start, char_end
  - `renderContentWithCitations()` function to parse and render XML `<cite>` tags
  - Clickable citations that navigate to source document and page
  - Tooltip showing source document and quoted text
  
- **WebSocket Integration**: Real-time document status updates
  - Updated `ProjectDocument` interface with `summary` and `task_id` fields
  - WebSocket connection for document processing notifications
  
- **Type Updates**: Enhanced TypeScript types
  - `ChatMessage` interface with `citations` field
  - `ChatResponse` with citation events support

**Infrastructure:**
- Added `rapidfuzz>=3.10.0` dependency for fuzzy string matching

**API Changes:**
- Deprecated synchronous document upload endpoint (POST `/projects/{project_id}/documents`)
  - Marked with `deprecated=True` flag
  - Recommends using presigned URL upload flow instead
- Enhanced `DocumentResponse` DTO with `summary`, `graph_status` fields
- Enhanced `DocumentUploadResponse` DTO with `task_id` field

**Documentation:**
- Removed obsolete plan documents:
  - `CONFIG_REFACTOR_PLAN.md`
  - `RAG_ARCHITECTURE_REFACTOR_PLAN.md`
  - `USER_CONFIG_CENTER_PLAN.md`

### Changed
- Document processing now includes summary generation and page mapping
- RAG graph supports both traditional chunk-based and new Mega-Prompt modes
- Citation format changed from inline markers to XML tags for precise localization

### Technical Details
- **Author**: aqiu <819110812@qq.com>
- **Implementation**: Complete RAG architecture refactoring as per RAG_ARCHITECTURE_REFACTOR_PLAN.md
- **Phases Completed**: Phase 2 (WebSocket), Phase 5 (Mega-Prompt), Phase 6 (Frontend), Phase 7 (Config)

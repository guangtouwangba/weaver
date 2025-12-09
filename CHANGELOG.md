# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

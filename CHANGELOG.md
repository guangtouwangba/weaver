# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2025-12-26

#### Interactive Mind Map Editing with Layout Selection

**Summary:**
Mind maps are now fully interactive. Users can drag nodes to reorganize layouts, switch between different layout styles (Radial, Tree, Balanced), add/delete/edit nodes manually, and export mind maps as PNG images or JSON data. Performance optimizations ensure smooth operation even with large mind maps.

**Frontend:**
- **Layout Algorithms** (`components/studio/mindmap/layoutAlgorithms.ts`):
  - `radialLayout()`: Nodes arranged in concentric circles around root
  - `treeLayout()`: Hierarchical left-to-right tree structure
  - `balancedLayout()`: Child nodes distributed evenly on both sides of root
  - `applyLayout()`: Unified layout application with bounds calculation

- **Interactive Editor** (`components/studio/mindmap/MindMapEditor.tsx`):
  - Full-screen editor with draggable nodes
  - Pan and zoom canvas (scroll to zoom, drag to pan)
  - Layout selector UI (Balanced/Radial/Tree button group)
  - Node editing toolbar (Add/Delete/Edit actions)
  - Node edit dialog for label and content editing
  - Double-click to edit node inline
  - Export menu (PNG image, JSON data)
  - "Unsaved changes" indicator
  - Performance warning when node count > 200

- **Performance Optimizations**:
  - Level of Detail (LOD) rendering: full → labels only → simple shapes
  - Throttled drag updates via `useThrottledCallback` hook
  - `React.memo` on DraggableNode component
  - Viewport culling for large mind maps
  - Proper Konva object cleanup on unmount

- **Updated MindMapFullView** (`components/studio/mindmap/MindMapViews.tsx`):
  - Now opens the interactive MindMapEditor instead of static modal
  - Supports `onDataChange` callback for state persistence

**Visual Design:**
| Layout | Description | Icon |
|--------|-------------|------|
| Balanced | Nodes on both sides of root | GitBranch |
| Radial | Concentric circles | Circle |
| Tree | Hierarchical left-to-right | Layers |

| LOD Level | Zoom Threshold | Rendering |
|-----------|----------------|-----------|
| Full | ≥ 0.7 | Label + content |
| Labels | 0.5 - 0.7 | Label only |
| Simple | < 0.3 | Basic shapes |

**Technical Details:**
- **Author**: aqiu
- **Implementation**: Mind Map Interactive Editing per add-mindmap-editing OpenSpec
- **Scope**: Layout algorithms, interactive editor, performance optimizations

### Added - 2025-12-25

#### Concurrent Canvas Outputs - Multiple Simultaneous Generations

**Summary:**
Users can now generate multiple outputs (Summary, Mindmap, etc.) simultaneously. Each output appears as a draggable card on the canvas at the viewport position where the user clicked the action button. The InspirationDock remains active during generation, allowing users to pan the canvas and trigger additional generations.

**Frontend:**
- **State Management Refactor** (`contexts/StudioContext.tsx`):
  - New `GenerationTask` type with id, type, status, position, result fields
  - `generationTasks: Map<string, GenerationTask>` for concurrent tracking
  - Helper methods: `startGeneration()`, `updateGenerationTask()`, `completeGeneration()`, `failGeneration()`, `removeGenerationTask()`
  - `getActiveGenerationsOfType()` and `hasActiveGenerations()` for UI state

- **Concurrent Generation Manager** (`hooks/useCanvasActions.ts`):
  - `handleGenerateContentConcurrent()`: Non-blocking generation with position tracking
  - `getViewportCenterPosition()`: Captures canvas center at click time
  - Legacy `handleGenerateContent()` preserved for backward compatibility

- **Per-Button Loading States** (`components/studio/InspirationDock.tsx`):
  - Individual spinners per action button instead of global loading state
  - Dock remains interactive during all generations
  - Success/error state feedback per button
  - Visual indicators for completed and failed generations

- **Canvas Node Components** (`components/studio/canvas-nodes/`):
  - `SummaryCanvasNode.tsx`: Compact summary card with expand modal
  - `MindMapCanvasNode.tsx`: Compact mindmap preview with expand modal
  - Both components support drag handles and position-aware rendering
  - Scale-aware rendering based on viewport zoom level

- **Canvas Integration** (`components/studio/KonvaCanvas.tsx`):
  - New node types: `summary_output`, `mindmap_output` with distinct styling
  - `GenerationOutputsOverlay.tsx`: Renders completed tasks as positioned overlays
  - Overlay components track viewport for screen-space positioning

**Visual Design:**
| Node Type | Border Color | Background | Icon |
|-----------|--------------|------------|------|
| summary_output | #8B5CF6 (Purple) | #FAF5FF | ⚡ |
| mindmap_output | #10B981 (Green) | #ECFDF5 | 🔀 |

**Technical Details:**
- **Author**: Cursor Agent
- **Implementation**: Concurrent Canvas Outputs per plan
- **Scope**: State management, generation hooks, UI components, canvas integration

### Added - 2025-12-23

#### Freeform Canvas Visual Redesign

**Frontend:**
- **Sidebar Redesign** (`web/src/components/prototype/freeform/Sidebar.tsx`):
  - Two-section LIBRARY layout: "Generated Content" and "Source Files"
  - Import Source button with dashed border style
  - Content type icons with color-coded backgrounds (Mind Map, Podcast, Summary, Flashcards)
  - Eye icon indicator for items currently on canvas
  - Active state highlight for mind maps
  - Type-specific metadata display (duration, page count, card count)

- **New Card Components** (`web/src/components/prototype/freeform/cards/`):
  - `TopicCard.tsx`: Topic insights with colored icon backgrounds and subtitles
  - `MindMapCard.tsx`: Central hub nodes with MIND MAP badge and expand button
  - `PodcastCard.tsx`: Audio preview with animated waveform visualization
  - `DataCard.tsx`: Metric display cards with accent color
  - `BriefCard.tsx`: Document preview with left accent border and "Open" action
  - `FlashcardNode.tsx`: Interactive flashcard with flip animation and progress bar

- **Header Enhancement** (`web/src/components/prototype/freeform/ProjectHeader.tsx`):
  - "EDITABLE" badge indicator
  - "Last saved X mins ago" status
  - Collaborator avatar stack with online indicators
  - +N remaining collaborators count
  - Purple "Share" button with refined styling

- **Toolbar Restructure** (`web/src/components/prototype/freeform/CanvasToolbar.tsx`):
  - Grid/List view toggle buttons at top
  - Select/Hand mode toggles
  - Zoom controls with percentage display
  - Add node button with plus icon

- **Chat Input Polish** (`web/src/components/prototype/freeform/ChatInput.tsx`):
  - Updated placeholder: "Ask Weaver to regroup or summarize these insights..."
  - Sparkles icon for AI indicator
  - Focus state with purple border highlight
  - Refined send button with arrow icon

- **Canvas Integration** (`web/src/components/prototype/freeform/Canvas.tsx`):
  - New node types: `topic`, `mindmap`, `podcast`, `data`, `brief`, `flashcard`
  - Card component rendering for each new type
  - Consistent selection and drag behavior

- **Data Model Extension** (`web/src/app/prototype/freeform/page.tsx`):
  - Extended Node interface with card-specific properties
  - Demo nodes showcasing all new card types
  - Demo edges connecting the demonstration nodes

**Color Palette:**
| Element | Color |
|---------|-------|
| Primary Purple | #6366F1 |
| Topic Orange | #F97316 |
| Topic Red | #EF4444 |
| Data Green | #10B981 |
| Podcast Purple | #8B5CF6 |
| Brief Blue | #3B82F6 |
| Flashcard Orange | #F97316 |

**Technical Details:**
- **Author**: Cursor Agent
- **Implementation**: Freeform Canvas Visual Redesign per design reference
- **Scope**: Prototype web app (`web/src/components/prototype/freeform/`)

### Fixed - 2025-12-15

#### Critical: Database Connection Startup Fix

**Problem:** Production deployment crashed with `TimeoutError` during database connection initialization, causing continuous container restarts.

**Root Cause:** `init_db()` raised exceptions on timeout, blocking application startup when database was temporarily slow/unavailable.

**Solution:**
- **Non-blocking startup** (`infrastructure/database/session.py`):
  - `init_db()` no longer raises exceptions on failure
  - Increased connection timeout from 10s to 30s for slow cloud DB
  - Added `CancelledError` handling for graceful shutdown
  - Application starts even if initial DB check fails
  - Requests will retry DB connection on-demand

- **Improved error handling** (`main.py`):
  - Wrapped `init_db()` in try-catch
  - Application continues startup even on DB init warning

- **Enhanced logging** (`worker/worker.py`, `api/v1/documents.py`):
  - Added detailed task scheduling logs with task_id and environment
  - Better worker startup and task pop logging

- **Diagnostic endpoint** (`api/v1/maintenance.py`):
  - New `GET /api/v1/maintenance/tasks/status` endpoint
  - Shows pending/processing/completed/failed task counts
  - Helps diagnose document processing issues

**Impact:** Production deployment stability improved - app no longer crashes on temporary DB connectivity issues.

### Added - 2025-12-15

#### Thinking Path Edge Relation Classification System

**Backend:**
- **EdgeRelationType Enum** (`domain/entities/thinking_path.py`):
  - New enum with 12 relation types: `answers`, `prompts_question`, `derives`, `causes`, `compares`, `supports`, `contradicts`, `revises`, `extends`, `parks`, `groups`, `custom`
  - Semantic classification for edge relationships in thinking path visualization

- **Edge Classification Prompts** (`application/prompts/thinking_path_extraction.py`):
  - `EDGE_RELATION_CLASSIFICATION_SYSTEM_PROMPT`: LLM prompt for classifying edge relations
  - `EDGE_RELATION_CLASSIFICATION_USER_PROMPT`: User prompt template
  - `EDGE_RELATION_DEFAULT_LABELS`: Default Chinese labels for each relation type
  - `EDGE_RELATION_KEYWORDS`: Keyword patterns for fast-path detection (causes, compares, revises, parks, prompts_question)

- **Edge Classification Service** (`application/services/thinking_path_service.py`):
  - `_classify_edge_relation()`: 3-tier classification (heuristic → keyword → LLM)
  - `_llm_classify_edge_relation()`: LLM-based classification fallback
  - `_create_edge_with_relation()`: Edge factory with relation metadata
  - Updated edge creation to include `relationType`, `label`, and `direction` fields

**Frontend:**
- **CanvasEdge Type Update** (`lib/api.ts`):
  - Extended `relationType` to include all 12 relation types
  - Added `direction` field for bidirectional relations

- **Edge Visual System** (`components/studio/KonvaCanvas.tsx`):
  - `EDGE_STYLES` config with color, strokeWidth, dash patterns, and icons for each relation type
  - Updated `renderEdges()` with:
    - Relation-specific stroke colors and dash patterns
    - Arrows at edge endpoints
    - Bidirectional arrows for `compares` relations
    - Icon display at edge midpoint (emoji icons)
    - AI-generated label rendering with styled pill background
  - Added `Circle` import for icon rendering

- **Parking Section** (`lib/layout.ts`, `components/studio/ThinkingPathGenerator.tsx`):
  - `PARKING_SECTION_CONFIG`: Configuration for parking area position and styling
  - `ParkingSection` interface for parking state
  - `createParkingSection()`: Section factory
  - `layoutParkingNodes()`: Node layout within parking area
  - `isWithinParkingSection()`, `getDropPositionInParking()`: Interaction helpers
  - `parkedNodeIds` state for tracking parked nodes
  - Parking indicator chip in UI

- **WebSocket Update** (`hooks/useCanvasWebSocket.ts`):
  - `onEdgeAdded` callback now includes full `edgeData` parameter
  - Edge events include `relationType` and `label` fields

**Visual Design:**
| Relation | Color | Style | Icon |
|----------|-------|-------|------|
| answers | Green | Solid | ✓ |
| prompts_question | Violet | Dashed | ? |
| derives | Amber | Solid | 💡 |
| causes | Red | Bold | → |
| compares | Blue | Dotted | ⇆ |
| revises | Pink | Long-dash | ✎ |
| parks | Gray | Sparse-dash | ⏸ |

**Technical Details:**
- **Author**: Cursor Agent
- **Implementation**: Thinking Path Edge Relation Classification as per plan
- **Scope**: Backend (entities, prompts, service), Frontend (types, canvas, layout, websocket)

### Added - 2025-12-14

#### Thinking Graph (Dynamic Mind Map) Full Stack Implementation

**Backend:**
- **Intent Classification Prompts** (`application/prompts/thinking_path_extraction.py`):
  - `THINKING_GRAPH_INTENT_CLASSIFICATION_PROMPT`: Classifies user messages as continuation, branch, or new_topic
  - `THINKING_GRAPH_INTENT_USER_PROMPT`: User prompt template with active topics and conversation history
  - `THINKING_GRAPH_EXTRACTION_SYSTEM_PROMPT`: Extracts structured thinking steps (claim, reason, evidence, uncertainty, decision)
  - `THINKING_GRAPH_EXTRACTION_USER_PROMPT`: User prompt template for step extraction

- **TopicContext Tracking** (`application/services/thinking_path_service.py`):
  - `TopicContext` dataclass for managing conversation topics/branches
  - `IntentClassificationResult` dataclass for intent classification results
  - `ThinkingStepExtraction` dataclass for structured step extraction
  - Topic context stack (`_topic_contexts`) for tracking multiple conversation threads
  - Active topic tracking (`_active_topic`) for branching support
  - `_classify_message_intent()`: LLM-based intent classification
  - `_find_related_topic()`: Semantic search for related topics
  - `_create_new_topic()`: Create new topic contexts with parent references
  - `_extract_thinking_step()`: Extract structured thinking fields
  - `set_active_topic()`: Frontend API for setting fork points
  - `get_topic_contexts()`: Retrieve all topic contexts for a project

- **Enhanced Duplicate Detection** (`application/services/thinking_path_service.py`):
  - **Node-level**: `_detect_duplicate_node()` with type-specific thresholds
  - **Path-level**: `_detect_similar_path()` using path embeddings
  - **Concept-level**: `detect_and_merge_concept()` for synonym merging
  - Type-specific thresholds: question=0.85, answer=0.90, insight=0.88, thinking_step=0.85, thinking_branch=0.80

**Frontend:**
- **CanvasNode Interface Extension** (`lib/api.ts`):
  - `thinkingStepIndex`: Step number in thinking sequence
  - `thinkingFields`: Structured fields (claim, reason, evidence, uncertainty, decision)
  - `branchType`: 'alternative' | 'question' | 'counterargument'
  - `depth`, `parentStepId`, `isDraft`, `topicId`: Tree structure and state
  - `relatedConcepts`, `suggestedBranches`: AI-suggested exploration paths

- **StudioContext Thinking Graph Support** (`contexts/StudioContext.tsx`):
  - `activeThinkingId`: Currently active thinking node (fork point)
  - `thinkingStepCounter`: Counter for step numbering
  - `appendThinkingDraftStep()`: Optimistic UI - create draft node immediately
  - `finalizeThinkingStep()`: Update draft with backend data
  - `startNewTopic()`: Clear active thinking to start new topic

- **Tree Layout Algorithm** (`lib/layout.ts`):
  - `layoutThinkingGraph()`: Horizontal tree layout for mind map visualization
  - `calculateThinkingNodePosition()`: Position calculation for new nodes
  - Recursive subtree height calculation for centered parent positioning
  - Branch node offset for visual distinction

- **Optimistic Node Generation** (`components/studio/AssistantPanel.tsx`):
  - Creates draft thinking node immediately when user sends message
  - Provides instant visual feedback on canvas

- **Canvas Thinking Graph Visuals** (`components/studio/KonvaCanvas.tsx`):
  - New node styles: `thinking_step`, `thinking_step_draft`, `thinking_branch`
  - Branch type variants: `thinking_branch_question`, `thinking_branch_alternative`, `thinking_branch_counterargument`
  - Step index badge (#1, #2, etc.)
  - Active context badge (purple highlight)
  - Draft badge (yellow "Draft" indicator)
  - Click to set active thinking node for forking

**Technical Details:**
- **Author**: Cursor Agent
- **Implementation**: Thinking Graph Full Stack as per plan
- **Scope**: Backend (prompts, service, duplicate detection), Frontend (data model, context, layout, rendering)

### Added - 2025-12-11

#### Async Canvas Clear with Generation System

**Backend:**
- **Generation-based Canvas Clearing** (`domain/entities/canvas.py`):
  - Added `generation` field to `CanvasNode`, `CanvasEdge`, `CanvasSection` entities
  - Added `current_generation` field to `Canvas` entity
  - `clear()` and `clear_view()` now increment generation instead of deleting items (O(1) operation)
  - Added `get_visible_nodes/edges/sections()` methods for current generation filtering
  - Added `to_visible_dict()` method for API responses with filtered items
  - Added `remove_old_items()` for background cleanup

- **New TaskType** (`domain/entities/task.py`):
  - Added `CLEANUP_CANVAS` task type for async cleanup

- **Clear Canvas Use Case** (`application/use_cases/canvas/clear_canvas.py`):
  - Refactored to use generation-based clearing
  - Schedules background cleanup task automatically
  - Returns cleanup task ID and pending item count

- **Canvas Cleanup Task** (`worker/tasks/canvas_cleanup.py`):
  - New background task to physically remove old generation items
  - Runs asynchronously after clear operation
  - Logs cleanup progress and results

- **API Updates** (`api/v1/canvas.py`):
  - `get_canvas` now returns only current generation items
  - `clear_canvas` uses TaskQueueService for async cleanup

**Frontend:**
- Added `generation` field to `CanvasNode`, `CanvasEdge`, `CanvasSection` types (`lib/api.ts`)

**Benefits:**
- Clear operation is instant (O(1) - just increment a number)
- Users can immediately add new nodes after clearing
- No blocking while deleting large numbers of nodes
- Background cleanup happens asynchronously

**Technical Details:**
- **Author**: aqiu
- **Implementation**: Generation ID pattern for async canvas operations
- **Scope**: Canvas clear operation, background cleanup

### Fixed - 2025-12-11

#### Citation Filename Display

**Frontend:**
- **Citation Matching Improvement** (`components/studio/AssistantPanel.tsx`):
  - Fixed citation tooltip showing `doc_01` instead of actual filename
  - Improved matching logic: tries exact match (doc_id + quote) first, then fallback to doc_id only
  - Added documents list fallback for filename lookup when citation doesn't have filename
  - `CitationRenderer` and `MarkdownContent` now receive `documents` prop for robust filename resolution

**Technical Details:**
- **Author**: aqiu
- **Implementation**: Multi-level fallback for filename: citation.filename -> documents[document_id].filename -> docId
- **Scope**: AssistantPanel citation rendering

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


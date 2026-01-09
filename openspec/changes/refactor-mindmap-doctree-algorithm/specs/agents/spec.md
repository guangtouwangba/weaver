# Spec: Mindmap Agent (Direct Generation Algorithm)

## MODIFIED Requirements

### Requirement: Mindmap Generation Algorithm
The mindmap agent SHALL use a 2-step direct generation algorithm: (1) generate the entire mindmap from full document context, (2) refine to remove duplicates and improve structure.

#### Scenario: Standard document processing
- **WHEN** a user requests mindmap generation for a document
- **THEN** the system sends the full document to the LLM in a single call
- **AND** receives a structured Markdown outline as output
- **AND** refines the output with a second LLM call to clean duplicates
- **AND** parses the Markdown to MindmapNode/MindmapEdge format

#### Scenario: Large document handling
- **WHEN** the document exceeds 500K tokens (configurable via MAX_DIRECT_TOKENS)
- **THEN** the system truncates to fit the context window
- **AND** logs a warning about truncation
- **AND** generates mindmap from the available content

#### Scenario: Depth control
- **WHEN** the user specifies a max depth (1-5)
- **THEN** the generation prompt instructs the LLM to limit hierarchy depth
- **AND** the refinement step enforces 3-4 levels maximum

## ADDED Requirements

### Requirement: Direct Generation Phase
The system SHALL generate the mindmap in a single LLM call using the full document context.

#### Scenario: Generating structured outline
- **WHEN** the direct generation phase runs
- **THEN** it sends a carefully designed prompt to the LLM containing:
  - The full document text
  - Instructions to extract 5-10 core points
  - Instructions to add elaboration and supporting details
  - Rules to preserve specific information (names, numbers, dates)
- **AND** receives a Markdown outline as output

#### Scenario: Multi-language support
- **WHEN** the language parameter is set to "zh" (Chinese)
- **THEN** the system uses Chinese prompts for generation and refinement
- **WHEN** the language parameter is set to "en" (English)
- **THEN** the system uses English prompts
- **WHEN** the language parameter is "auto"
- **THEN** the system defaults to Chinese prompts

### Requirement: Refinement Phase
The system SHALL refine the generated mindmap to remove duplicates and improve structure.

#### Scenario: Removing parent-child duplicates
- **WHEN** a parent and child node have the same or similar names
- **THEN** the refinement removes the duplicate child
- **AND** preserves any unique content from the child

#### Scenario: Removing sibling duplicates
- **WHEN** sibling nodes are duplicates
- **THEN** the refinement keeps only one instance

#### Scenario: Fixing mixed categories
- **WHEN** child nodes under a parent belong to different categories
- **THEN** the refinement reorganizes them under appropriate parents

#### Scenario: Cleanup noise content
- **WHEN** nodes contain usernames, acknowledgements, or greetings
- **THEN** the refinement removes these nodes
- **AND** preserves nodes with actual content

### Requirement: Markdown to Node Conversion
The system SHALL parse the refined Markdown outline into MindmapNode and MindmapEdge structures.

#### Scenario: Parsing Markdown hierarchy
- **WHEN** the refined Markdown is received
- **THEN** the system parses the heading (#) as root node
- **AND** parses bullet points (-) as child nodes
- **AND** uses indentation (2 spaces) to determine hierarchy level

#### Scenario: Generating node IDs and edges
- **WHEN** nodes are parsed from Markdown
- **THEN** each node receives a unique ID
- **AND** edges are created connecting parent to child nodes
- **AND** depth/color properties are assigned based on level

### Requirement: Source Reference Preservation
The system SHALL preserve source references so users can click on nodes to navigate to the original content (PDF page, video timestamp).

#### Scenario: PDF page annotation input
- **WHEN** the input is from a PDF document
- **THEN** the system receives text annotated with page markers: `[PAGE:X]`
- **AND** the generation prompt instructs the LLM to include `[Page X]` markers in output
- **AND** these markers are parsed into `source_refs` on each node

#### Scenario: Video timestamp annotation input
- **WHEN** the input is from a video transcript
- **THEN** the system receives text annotated with time markers: `[TIME:MM:SS]`
- **AND** the generation prompt instructs the LLM to include `[MM:SS]` markers in output
- **AND** these markers are parsed into `source_refs` with `start_time`

#### Scenario: Parsing source markers from output
- **WHEN** the LLM output contains markers like `[Page 15]` or `[12:30]`
- **THEN** the parser extracts these markers
- **AND** creates `SourceRef` objects with type (pdf/video), page/timestamp
- **AND** attaches them to the corresponding `MindmapNode`

#### Scenario: Click-to-navigate for PDF
- **WHEN** a user clicks on a node with PDF source reference
- **THEN** the frontend opens the PDF viewer at the specified page number

#### Scenario: Click-to-navigate for video
- **WHEN** a user clicks on a node with video source reference
- **THEN** the frontend seeks the video player to the specified timestamp

### Requirement: Streaming Events
The system SHALL emit streaming events for frontend responsiveness.

#### Scenario: Generation started
- **WHEN** the workflow begins
- **THEN** a `GENERATION_STARTED` event is emitted with document title

#### Scenario: Progress during phases
- **WHEN** each phase completes
- **THEN** a `GENERATION_PROGRESS` event is emitted with phase name and progress percentage

#### Scenario: Nodes added
- **WHEN** the Markdown is parsed to nodes
- **THEN** `NODE_ADDED` events are emitted for each node
- **AND** `EDGE_ADDED` events are emitted for each edge

#### Scenario: Generation complete
- **WHEN** all nodes and edges are emitted
- **THEN** a `GENERATION_COMPLETE` event is emitted with total node count

## REMOVED Requirements

### Requirement: Semantic Chunk Parsing
**Reason**: No longer needed - direct generation uses full document context
**Migration**: Remove chunker, semantic_parser modules

### Requirement: Page-Aware Chunking
**Reason**: No longer needed - not chunking the document
**Migration**: Source references handled differently (see design.md)

### Requirement: Embedding-Based Tree Aggregation
**Reason**: No longer needed - LLM generates tree structure directly
**Migration**: Remove clustering, embedding modules

### Requirement: MapReduce Concept Aggregation (DISABLED)
**Reason**: Already disabled, now completely removed
**Migration**: Remove mapreduce module

# rag Specification

## Purpose
TBD - created by archiving change enhance-rag-context. Update Purpose after archive.
## Requirements
### Requirement: Context-Aware Entity Resolution
The system SHALL resolve natural language references (e.g., "this video", "that document") to specific entities based on conversation context.

#### Scenario: Resolve "this video" after upload
- **WHEN** the user uploads a video "Intro to Agile"
- **AND** asks "summarize this video"
- **THEN** the system identifies "Intro to Agile" as the target entity
- **AND** rewrites the query to "summarize video 'Intro to Agile'"
- **AND** filters retrieval to the specific video ID.

#### Scenario: Verify context persistence
- **WHEN** the conversation focus is on "Project Plan.pdf"
- **AND** the user asks a follow-up "what are the key dates?"
- **THEN** reference resolution maintains focus on "Project Plan.pdf" for retrieval.

#### Scenario: Switch context by entity type
- **WHEN** the user has previously discussed "Report.pdf"
- **AND** currently focuses on video "Demo.mp4"
- **AND** asks "what was in the PDF?"
- **THEN** reference resolution identifies "Report.pdf" as the target
- **AND** rewrites query to "what was in document 'Report.pdf'?"
- **AND** filters retrieval by `document_id` of "Report.pdf".

### Requirement: Entity-Based Retrieval Filtering
The system SHALL support filtering retrieval results by specific entity IDs (e.g., document_id, video_id) when a focus entity is identified.

#### Scenario: Filter by video ID
- **WHEN** a query is resolved to focus on video `v123`
- **THEN** the retrieval step MUST apply a filter `video_id=v123`
- **AND** only return chunks belonging to that video.


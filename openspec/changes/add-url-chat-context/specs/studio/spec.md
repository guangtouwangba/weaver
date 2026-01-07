# studio Specification Delta

## MODIFIED Requirements

### Requirement: Drag to Chat Context
The system SHALL allow users to drag content from the canvas, source list, or URL content list into the chat to use as context for the next query.

#### Scenario: Visual Integration of Context
- **WHEN** the user drops a resource into the chat input
- **THEN** the resource SHALL be displayed as a chip *within* or *visually attached* to the input container
- **AND** the chat interface SHALL NOT shift position abruptly
- **AND** the input container SHALL resolve to a cohesive unit containing both context and text input

#### Scenario: Drop URL content into chat
- **WHEN** the user drags a URL content item (YouTube, Bilibili, Douyin, or web page) from the Resource Sidebar
- **AND** drops it onto the chat input area
- **THEN** the URL content SHALL be added to the chat context
- **AND** a context chip SHALL appear with the platform icon and title
- **AND** duplicate drops of the same URL SHALL be ignored

#### Scenario: URL context chip display
- **WHEN** a URL content item is added to chat context
- **THEN** the context chip SHALL display:
  - Platform icon (YouTube: red play, Bilibili: blue TV, Douyin: black note, Web: gray globe)
  - Truncated title (max 30 characters with ellipsis)
  - Remove button (X)
- **AND** hovering over the chip SHALL show the full title as tooltip

#### Scenario: Pending URL extraction state
- **WHEN** a URL content item with status "pending" or "processing" is dropped
- **THEN** the context chip SHALL display a loading spinner
- **AND** the chip title SHALL show "Extracting..."
- **AND** the system SHALL poll for extraction completion
- **WHEN** extraction completes
- **THEN** the chip SHALL update to show the extracted title

#### Scenario: Failed URL extraction state
- **WHEN** a URL content item with status "failed" is dropped
- **THEN** the context chip SHALL display an error indicator
- **AND** hovering SHALL show the error message
- **AND** the user MAY still send the query (AI will acknowledge missing context)

#### Scenario: Remove URL from context
- **WHEN** the user clicks the remove button on a URL context chip
- **THEN** the URL content SHALL be removed from the chat context
- **AND** the chip SHALL disappear immediately

## ADDED Requirements

### Requirement: URL Content RAG Integration
The system SHALL include URL content (transcripts, article text) in the RAG retrieval context when provided as chat context.

#### Scenario: YouTube transcript as context
- **WHEN** the user sends a query with a YouTube video in context
- **THEN** the system SHALL include the video transcript in the RAG retrieval
- **AND** the AI response SHALL be informed by the video content
- **AND** citations SHALL reference the YouTube video with platform icon

#### Scenario: Web article as context
- **WHEN** the user sends a query with a web page in context
- **THEN** the system SHALL include the article text in the RAG retrieval
- **AND** the AI response SHALL be informed by the article content
- **AND** citations SHALL reference the web page with site name

#### Scenario: Mixed document and URL context
- **WHEN** the user provides both documents and URL content as context
- **THEN** the system SHALL include both in the RAG retrieval
- **AND** the AI SHALL consider all provided sources
- **AND** citations SHALL indicate the source type (document vs URL)

#### Scenario: URL content without transcript
- **WHEN** a video URL has no available transcript (e.g., Douyin, some Bilibili)
- **AND** only video description is available
- **THEN** the system SHALL use the description as context
- **AND** the AI response SHALL indicate limited context availability if relevant

### Requirement: URL Citation Interaction
The system SHALL display clickable citations for URL sources in AI responses.

#### Scenario: Click URL citation
- **WHEN** the user clicks on a URL citation chip in an AI response
- **THEN** the original URL SHALL open in a new browser tab
- **AND** the citation chip SHALL display the platform icon

#### Scenario: URL citation chip appearance
- **WHEN** a citation references a URL source
- **THEN** the citation chip SHALL display:
  - Platform icon (YouTube, Bilibili, Douyin, or Globe)
  - Source title or domain name
  - Visual distinction from document citations


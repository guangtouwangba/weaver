# studio Spec Delta: enable-mindmap-drilldown

## ADDED Requirements

### Requirement: Mindmap Node Source References
The system SHALL enrich mindmap nodes with source references linking to original document content.

#### Scenario: Node generation includes source refs
- **WHEN** the backend generates a mindmap node
- **THEN** the node SHALL include `source_refs` containing source references
- **AND** each reference SHALL contain `source_id`, `source_type`, `location` (optional), and `quote`
- **AND** for PDF documents, `location` SHALL indicate the page number
- **AND** for Time-based media (Video/Audio), `location` SHALL indicate the timestamp in seconds
- **AND** for Web sources (URL), `location` SHALL be the URL with optional text fragment anchors

#### Scenario: Source refs serialization
- **WHEN** mindmap data is returned via API
- **THEN** each node's `source_refs` SHALL be included in the JSON response
- **AND** the frontend data model SHALL parse and store these references

---

### Requirement: Interactive Mindmap Node Click
The mindmap nodes SHALL be clickable entry points for source exploration.

#### Scenario: Node click triggers drilldown
- **WHEN** a user clicks on a mindmap node in the MindMapEditor
- **THEN** the Source Context Panel SHALL open
- **AND** the panel SHALL display the clicked node's source references

#### Scenario: Node hover affordance
- **WHEN** a user hovers over a mindmap node
- **THEN** the cursor SHALL change to pointer
- **AND** the node SHALL display a subtle highlight effect indicating interactivity

#### Scenario: Node without source refs
- **WHEN** a user clicks a node that has no source references
- **THEN** the Source Context Panel SHALL display a message indicating "This concept is synthesized from multiple sections"

---

### Requirement: Source Context Panel Display
The system SHALL provide a panel to display source references when a mindmap node is selected.

#### Scenario: Panel appearance
- **WHEN** the Source Context Panel opens
- **THEN** it SHALL slide in from the right side of the MindMapEditor
- **AND** it SHALL display the selected node's label as a header
- **AND** it SHALL list all source references as cards

#### Scenario: Source reference card content
- **WHEN** a source reference card is displayed
- **THEN** it SHALL show:
  - Document name with file icon
  - Page number indicator
  - Quoted text excerpt (up to 300 characters with ellipsis)
  - Action button appropriate for content type ("Open PDF", "Play Video", "Visit Link")

#### Scenario: Navigate to PDF
- **WHEN** a user clicks "Open in PDF" on a source reference card
- **THEN** the PDF Preview Modal SHALL open
- **AND** it SHALL navigate to the referenced page number
- **AND** it SHALL highlight the quoted text if exact match is found

#### Scenario: Navigate to Video/Audio
- **WHEN** a user clicks "Play Video" (or "Play Audio") on a source reference card
- **THEN** the Media Preview Modal SHALL open with the referenced file
- **AND** the player SHALL automatically seek to the timestamp specified in `location`
- **AND** the player SHALL start playback immediately

#### Scenario: Navigate to Web URL
- **WHEN** a user clicks "Visit Link" on a source reference card
- **THEN** the URL SHALL open in a new browser tab
- **AND** if supported, it SHALL use Scroll-to-Text Fragment to highlight the quoted text

#### Scenario: Preview launch failure
- **WHEN** the system attempts to open a source reference (PDF, Video, etc.)
- **AND** the file cannot be opened (e.g., deleted, corrupted, unsupported)
- **THEN** the system SHALL display a user-friendly error toast
- **AND** the Source Context Panel SHALL remain open
- **AND** the quoted text SHALL remain visible so the user still has context

#### Scenario: Invalid location fallback
- **WHEN** the system opens a source reference
- **AND** the specified location (page/timestamp) is invalid or out of bounds
- **THEN** the viewer SHALL open at the beginning (Page 1 or 00:00)
- **AND** a warning toast SHALL indicate that the specific location could not be found

#### Scenario: Close panel and return
- **WHEN** a user clicks the close button on the Source Context Panel
- **THEN** the panel SHALL close
- **AND** the user SHALL return to the mindmap view
- **AND** no node SHALL be selected


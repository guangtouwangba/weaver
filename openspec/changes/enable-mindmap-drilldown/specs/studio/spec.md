# studio Spec Delta: enable-mindmap-drilldown

## ADDED Requirements

### Requirement: Mindmap Node Source References
The system SHALL enrich mindmap nodes with source references linking to original document content.

#### Scenario: Node generation includes source refs
- **WHEN** the backend generates a mindmap node
- **THEN** the node SHALL include `source_refs` containing document references
- **AND** each reference SHALL contain `document_id`, `page_number`, and `quote`

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
  - "Open in PDF" action button

#### Scenario: Navigate to PDF
- **WHEN** a user clicks "Open in PDF" on a source reference card
- **THEN** the PDF Preview Modal SHALL open
- **AND** it SHALL navigate to the referenced page number
- **AND** it SHALL highlight the quoted text if exact match is found

#### Scenario: Close panel and return
- **WHEN** a user clicks the close button on the Source Context Panel
- **THEN** the panel SHALL close
- **AND** the user SHALL return to the mindmap view
- **AND** no node SHALL be selected


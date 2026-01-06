# Studio Spec Deltas

## ADDED Requirements

### Requirement: Note Entity Structure
The system SHALL distinguish between the "Note Card" (canvas representation) and "Note Page" (content entity).

#### Scenario: Note Card Visualization
- **WHEN** a Note is displayed on the canvas
- **THEN** it renders as a "Card" containing:
  - Title (truncated if necessary)
  - Content preview (first N lines)
  - Visual styling (color/border) inherited from note properties
- **AND** it omits full content controls to remain lightweight

#### Scenario: Note Page Editing
- **WHEN** a user double-clicks a Note Card
- **OR** triggers "Add Note"
- **THEN** a "Note Page" interface opens (modal or panel)
- **AND** allows rich editing of the full note content (e.g., Markdown, checkboxes)
- **AND** changes are auto-saved to the Note entity

### Requirement: Note Creation Flow
The creation of a note SHALL emphasize content capture first.

#### Scenario: Create Note
- **WHEN** a user selects "Add Note" from the toolbar or context menu
- **THEN** a blank Note Page opens immediately
- **AND** the user can start typing content

#### Scenario: Auto-save on Blur
- **WHEN** the user clicks outside the Note Page (e.g., on the canvas background)
- **THEN** the Note Page closes automatically
- **AND** the content is saved immediately (no "Save" button required)
- **AND** the corresponding Note Card appears or updates on the canvas

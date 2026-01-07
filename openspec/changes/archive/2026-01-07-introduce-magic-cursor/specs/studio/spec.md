# Studio Spec Deltas

## ADDED Requirements

### Requirement: Magic Cursor Tool
The Studio toolbar SHALL include a "Magic Cursor" tool that enables AI-assisted generation workflows.

#### Scenario: Activate Magic Cursor
- **WHEN** the user clicks the "Magic Cursor" icon (Sparkle) in the toolbar
- **THEN** the cursor changes to a "Magic Wand" or "Sparkle" visual style
- **AND** the standard selection behavior is replaced by Magic Selection

### Requirement: Magic Selection Interaction
The Magic Cursor SHALL provide a distinctive "Flowing Gradient" selection box to indicate active AI context capture.

#### Scenario: Magic Area Selection
- **WHEN** the user presses and drags on the canvas with Magic Cursor active
- **THEN** a selection box is drawn with a "flowing gradient" dashed border
- **AND** the fill color provides a subtle iridescent effect
- **AND** the selection captures all nodes intersecting the box

#### Scenario: Selection Release and Intent Menu
- **WHEN** the user releases the mouse button after Defining a Magic Selection
- **THEN** the selection box remains visible
- **AND** an "Intent Menu" automatically floats at the bottom-right corner of the selection
- **AND** no right-click is required to trigger this menu

### Requirement: Intent Menu Actions
The Intent Menu SHALL offer immediate AI generation options based on the selected context.

#### Scenario: Intent Menu Items
- **WHEN** the Intent Menu appears
- **THEN** it displays primary actions:
  - "Draft Article"
  - "Action List"

#### Scenario: Select Action
- **WHEN** the user selects an action (e.g., "Draft Article") from the menu
- **THEN** the menu disappears
- **AND** a generation task is initiated using the selected nodes as context
- **AND** a "Result Container" placeholder appears near the selection

### Requirement: Result Container (Super Cards)
The system SHALL display generation results in distinct "Super Cards" that visually differentiate them from standard notes.

#### Scenario: Document Card Appearance
- **WHEN** a "Draft Article" action completes
- **THEN** a "Document Card" is created on the canvas
- **AND** it features an A4-paper-like aspect ratio and styling
- **AND** it includes a distinct header/footer
- **AND** it includes an "Export PDF" action
- **AND** hovering the card visually highlights the source nodes used for generation (bi-directional linking)

#### Scenario: Ticket Card Appearance
- **WHEN** an "Action List" action completes
- **THEN** a "Ticket Card" is created on the canvas
- **AND** it features a "receipt" or "ticket" visual style (possibly with torn edges)
- **AND** it creates interactive checklist items
- **AND** it includes integration actions like "Add to Calendar" or "Sync to Todoist"

### Requirement: Snapshot Context Refresh
Generated Super Cards SHALL retain a link to their original spatial context to allow context-aware refreshing.

#### Scenario: Refresh Result
- **WHEN** the user clicks the "Refresh" button on a Super Card
- **THEN** the system re-scans the original spatial coordinates (Snapshot Context) of the generation
- **AND** identifies any *new* or *modified* nodes within that area
- **AND** initiates a re-generation using the updated set of nodes
- **AND** updates the card content with the new result

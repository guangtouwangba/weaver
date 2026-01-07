# Studio Spec Deltas

## ADDED Requirements

### Requirement: Article Generation from Magic Selection
The system SHALL generate structured articles from canvas nodes selected via Magic Cursor.

#### Scenario: Draft Article action
- **WHEN** the user selects "Draft Article" from the Intent Menu
- **THEN** the system collects content from all selected nodes
- **AND** sends a generation request to the backend with node data
- **AND** displays a loading indicator on the selection area
- **AND** the Intent Menu closes immediately

#### Scenario: Article generation completes
- **WHEN** article generation completes successfully
- **THEN** a new Super Card (Document Card) appears on the canvas
- **AND** the card is positioned at the bottom-right of the selection, offset by 20px
- **AND** the card contains the generated article with sections
- **AND** the magic selection box is cleared
- **AND** the tool mode switches back to "select"

#### Scenario: Article generation fails
- **WHEN** article generation encounters an error
- **THEN** an error toast notification is displayed
- **AND** the magic selection remains visible for retry
- **AND** the user can retry or dismiss the selection

### Requirement: Action List Generation from Magic Selection
The system SHALL extract action items and tasks from canvas nodes selected via Magic Cursor.

#### Scenario: Action List action
- **WHEN** the user selects "Action List" from the Intent Menu
- **THEN** the system collects content from all selected nodes
- **AND** sends a generation request to the backend with node data
- **AND** displays a loading indicator on the selection area
- **AND** the Intent Menu closes immediately

#### Scenario: Action list generation completes
- **WHEN** action list generation completes successfully
- **THEN** a new Super Card (Ticket Card) appears on the canvas
- **AND** the card is positioned at the bottom-right of the selection, offset by 20px
- **AND** the card contains checkable action items
- **AND** each item can be toggled between done/not done
- **AND** the magic selection box is cleared

#### Scenario: No actions found
- **WHEN** action list generation completes
- **AND** no actionable items were identified in the content
- **THEN** a toast notification informs the user "No action items found"
- **AND** no new card is created
- **AND** the selection is cleared

### Requirement: Node Content as Generation Input
The system SHALL use canvas node content (not document content) for Magic Cursor generation.

#### Scenario: Collect node content
- **WHEN** a Magic Cursor generation is triggered
- **THEN** the system collects the `title` and `content` fields from each selected node
- **AND** combines them into a structured input for the AI agent
- **AND** preserves node IDs for source attribution

#### Scenario: Empty node content
- **WHEN** all selected nodes have empty content
- **THEN** generation is skipped
- **AND** a toast notification displays "Selected nodes have no content"

#### Scenario: Maximum node limit
- **WHEN** more than 50 nodes are selected via Magic Cursor
- **THEN** only the first 50 nodes (by position, top-left to bottom-right) are included
- **AND** a toast notification displays "Selection limited to 50 nodes"

### Requirement: Result Card Positioning
The system SHALL position generated Super Cards to avoid overlapping with source nodes.

#### Scenario: Result card offset
- **WHEN** a generation completes and creates a Super Card
- **THEN** the card is positioned at the bottom-right corner of the original selection
- **AND** offset by 20px from the selection boundary
- **AND** the card does not overlap with the selected source nodes

### Requirement: Super Card Interaction
The system SHALL allow users to open Super Cards for viewing and editing.

#### Scenario: Open Document Card
- **WHEN** the user clicks on a Document Card
- **THEN** a modal or panel opens displaying the full article content
- **AND** the content is rendered in rich text format with sections
- **AND** the user can edit the article text

#### Scenario: Open Ticket Card
- **WHEN** the user clicks on a Ticket Card
- **THEN** a modal or panel opens displaying all action items
- **AND** the user can add, edit, or delete action items
- **AND** the user can reorder items via drag and drop

#### Scenario: Save edits
- **WHEN** the user makes edits in the Super Card modal
- **AND** closes the modal or clicks "Save"
- **THEN** the changes are persisted to the backend
- **AND** the card preview on the canvas updates to reflect changes

#### Scenario: Toggle action item on canvas
- **WHEN** the user clicks a checkbox on a Ticket Card directly on the canvas
- **THEN** the item's done/not-done state toggles immediately
- **AND** the change is persisted without opening the modal

### Requirement: Generation Loading State
The system SHALL provide visual feedback during Magic Cursor generation.

#### Scenario: Loading indicator
- **WHEN** generation is in progress
- **THEN** the magic selection box displays a pulsing animation
- **AND** a small "Generating..." label appears near the selection
- **AND** the user cannot start another magic selection

#### Scenario: Cancel during loading
- **WHEN** the user presses Escape during generation
- **THEN** the generation request is cancelled (if supported)
- **AND** the loading state is cleared
- **AND** no result card is created

## MODIFIED Requirements

### Requirement: Magic Selection Interaction
The Magic Cursor SHALL provide a distinctive "Flowing Gradient" selection box to indicate active AI context capture.

#### Scenario: Selection Visuals
- **WHEN** the user drags to select an area with the Magic Cursor
- **THEN** the selection box displays a flowing gradient border ("Magic selection")
- **AND** the fill is a subtle iridescent wash
- **AND** the selection captures all nodes intersecting the box

#### Scenario: Intent Menu
- **WHEN** the user releases the mouse after a magic selection
- **AND** at least one node is within the selection
- **THEN** an "Intent Menu" automatically floats at the bottom-right corner of the selection
- **AND** options include "Draft Article" and "Action List"
- **AND** clicking an option triggers the corresponding generation flow

#### Scenario: Empty Selection
- **WHEN** the user releases the mouse after a magic selection
- **AND** no nodes are within the selection
- **THEN** the selection box is cleared
- **AND** no Intent Menu is shown


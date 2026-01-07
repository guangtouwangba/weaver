# Studio Spec Deltas

## ADDED Requirements

### Requirement: Unified Canvas Node Model
The system SHALL represent all canvas elements (notes, generation outputs, source nodes) as a single unified `CanvasNode` data structure.

#### Scenario: Mindmap as CanvasNode
- **WHEN** a mindmap generation completes
- **THEN** a `CanvasNode` with `type: 'mindmap'` is created
- **AND** the node contains `outputData` with the mindmap structure (nodes, edges)
- **AND** the node is added to the canvas nodes array
- **AND** the node appears in the spatial index for selection

#### Scenario: Summary as CanvasNode
- **WHEN** a summary generation completes
- **THEN** a `CanvasNode` with `type: 'summary'` is created
- **AND** the node contains `outputData` with summary sections and key points
- **AND** the node is added to the canvas nodes array
- **AND** the node appears in the spatial index for selection

#### Scenario: Unified node persistence
- **WHEN** a generation output node is dragged to a new position
- **THEN** the position is persisted via the outputs API
- **AND** the position is restored when the project is reloaded

### Requirement: Generation Output Canvas Cards
The system SHALL render generation outputs (mindmap, summary) as selectable cards within the Konva canvas layer.

#### Scenario: Mindmap card preview
- **WHEN** a mindmap node is rendered on the canvas
- **THEN** it displays a compact preview showing the root node and first-level children
- **AND** a badge indicates the total node count
- **AND** the card uses the same selection styling as other canvas nodes

#### Scenario: Summary card preview
- **WHEN** a summary node is rendered on the canvas
- **THEN** it displays the title and a text excerpt
- **AND** a badge indicates the number of sections
- **AND** the card uses the same selection styling as other canvas nodes

#### Scenario: Double-click to expand
- **WHEN** the user double-clicks a mindmap or summary card
- **THEN** a full-screen modal opens with the complete content
- **AND** the modal allows viewing and editing the content

### Requirement: Magic Cursor Selects All Node Types
The system SHALL include all node types (notes, mindmaps, summaries, super cards) in Magic Cursor box selection.

#### Scenario: Select mindmap with Magic Cursor
- **WHEN** the user draws a Magic Selection box
- **AND** the box intersects a mindmap node
- **THEN** the mindmap node is included in the selection
- **AND** the mindmap node is highlighted with the magic selection style

#### Scenario: Generate from mixed selection
- **WHEN** the user selects nodes of different types (e.g., note + mindmap + summary)
- **AND** triggers a generation action from the Intent Menu
- **THEN** content is extracted from all selected nodes
- **AND** mindmap nodes contribute their node labels and content
- **AND** summary nodes contribute their sections and key points
- **AND** the combined content is used as generation input

## MODIFIED Requirements

### Requirement: Magic Selection Interaction
The Magic Cursor SHALL provide a distinctive "Flowing Gradient" selection box to indicate active AI context capture.

#### Scenario: Selection Visuals
- **WHEN** the user drags to select an area with the Magic Cursor
- **THEN** the selection box displays a flowing gradient border ("Magic selection")
- **AND** the fill is a subtle iridescent wash
- **AND** the selection captures all nodes intersecting the box
- **AND** the selection includes all node types (notes, mindmaps, summaries, super cards)

### Requirement: Result Container (Super Cards)
The system SHALL display generation results in distinct "Super Cards" that visually differentiate them from standard notes.

#### Scenario: Document Card Appearance
- **WHEN** a "Draft Article" action completes
- **THEN** a `CanvasNode` with `type: 'super_article'` is created
- **AND** it features an A4-paper-like aspect ratio and styling
- **AND** it is added to the canvas nodes array
- **AND** it is selectable by Magic Cursor

#### Scenario: Mindmap Output Appearance
- **WHEN** a mindmap generation completes
- **THEN** a `CanvasNode` with `type: 'mindmap'` is created
- **AND** it features a compact card with node preview
- **AND** it is added to the canvas nodes array
- **AND** it is selectable by Magic Cursor

#### Scenario: Summary Output Appearance
- **WHEN** a summary generation completes
- **THEN** a `CanvasNode` with `type: 'summary'` is created
- **AND** it features a compact card with text excerpt
- **AND** it is added to the canvas nodes array
- **AND** it is selectable by Magic Cursor


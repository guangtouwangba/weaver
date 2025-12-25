## ADDED Requirements

### Requirement: Mind Map Layout Selection
The system SHALL provide multiple layout options for organizing mind map nodes visually.

#### Scenario: Switch to radial layout
- **WHEN** a user selects "Radial" from the layout options
- **THEN** nodes are arranged in a circular pattern around the root node
- **AND** child nodes fan out in concentric circles based on depth
- **AND** edges curve smoothly to connect nodes

#### Scenario: Switch to tree layout
- **WHEN** a user selects "Tree" from the layout options
- **THEN** nodes are arranged in a hierarchical top-down or left-right structure
- **AND** sibling nodes are aligned on the same level
- **AND** edges connect parent to children in straight or orthogonal lines

#### Scenario: Switch to balanced layout
- **WHEN** a user selects "Balanced" from the layout options
- **THEN** child nodes are distributed evenly on both sides of the root
- **AND** the layout minimizes visual clutter and crossing edges

#### Scenario: Preserve custom positions after layout change
- **WHEN** a user switches layout
- **AND** then manually drags nodes to custom positions
- **THEN** the custom positions are preserved until another layout is applied

### Requirement: Mind Map Interactive Canvas
The Mind Map full view SHALL provide an interactive canvas where users can reorganize the layout.

#### Scenario: Drag node to reposition
- **WHEN** a user drags a node in the full view
- **THEN** the node moves to the new position
- **AND** connected edges update to follow the node
- **AND** the layout change is preserved in the current session

#### Scenario: Pan and zoom canvas
- **WHEN** a user scrolls the mouse wheel on the canvas
- **THEN** the view zooms in or out centered on the cursor
- **WHEN** a user drags on the canvas background
- **THEN** the view pans in the drag direction

### Requirement: Mind Map Node Editing
The system SHALL allow users to manually add, delete, and edit nodes after generation.

#### Scenario: Add new node
- **WHEN** a user clicks the "Add Node" action
- **AND** selects a parent node
- **AND** enters a label for the new node
- **THEN** a new node appears as a child of the selected parent
- **AND** an edge connects the new node to its parent

#### Scenario: Delete node
- **WHEN** a user selects a node
- **AND** clicks the "Delete" action
- **THEN** the node is removed from the mindmap
- **AND** all child nodes and their edges are also removed
- **AND** edges connected to the deleted node are removed

#### Scenario: Edit node label
- **WHEN** a user double-clicks a node label
- **THEN** the label becomes editable inline
- **WHEN** the user confirms the edit (Enter or click outside)
- **THEN** the label is updated

### Requirement: Mind Map Export
The system SHALL allow users to download the mindmap in common formats.

#### Scenario: Export as image
- **WHEN** a user clicks the "Download" button
- **AND** selects "PNG" format
- **THEN** the current mindmap is exported as a PNG image
- **AND** the browser initiates a download with filename based on the mindmap title

#### Scenario: Export as data
- **WHEN** a user clicks the "Download" button
- **AND** selects "JSON" format
- **THEN** the current mindmap data (nodes, edges, positions) is exported as JSON
- **AND** the browser initiates a download with `.json` extension

### Requirement: Mind Map Performance Optimization
The system SHALL maintain smooth performance when handling large mindmaps with many nodes.

#### Scenario: Viewport culling for off-screen nodes
- **WHEN** a mindmap contains more than 50 nodes
- **THEN** only nodes within or near the visible viewport are fully rendered
- **AND** nodes far outside the viewport are skipped or rendered as simplified shapes
- **AND** the frame rate remains above 30fps during pan and zoom

#### Scenario: Level of detail rendering
- **WHEN** the user zooms out to view many nodes at once
- **THEN** node details (content text, icons) are hidden progressively
- **AND** only labels are shown at medium zoom levels
- **AND** nodes become simple shapes at far zoom levels
- **AND** edges are simplified to straight lines at far zoom levels

#### Scenario: Throttled drag updates
- **WHEN** a user drags a node
- **THEN** position updates are throttled to 60fps maximum
- **AND** edge recalculations are debounced during active drag
- **AND** full edge redraw only occurs on drag end

#### Scenario: Layout calculation offloading
- **WHEN** a layout algorithm is applied to a large mindmap (>100 nodes)
- **THEN** the calculation runs asynchronously without blocking the UI
- **AND** a loading indicator is shown during calculation
- **AND** the UI remains responsive to cancel or other actions

#### Scenario: Batch rendering for streaming nodes
- **WHEN** new nodes are generated during AI streaming
- **THEN** nodes are batched and rendered in groups (e.g., every 100ms)
- **AND** individual node additions do not trigger full re-renders
- **AND** React reconciliation is optimized using stable keys

#### Scenario: Memory cleanup on unmount
- **WHEN** the mindmap view is closed or unmounted
- **THEN** all Konva objects and event listeners are properly disposed
- **AND** no memory leaks occur from repeated open/close cycles
- **AND** large node content is released from memory

#### Scenario: Performance warning for very large mindmaps
- **WHEN** a mindmap exceeds 200 nodes
- **THEN** a subtle warning indicator is shown
- **AND** the user is offered options to collapse branches or limit visible depth
- **AND** the system suggests exporting before adding more nodes


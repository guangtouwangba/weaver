# studio Specification

## Purpose
TBD - created by archiving change add-document-summary. Update Purpose after archive.
## Requirements
### Requirement: Document Selection State
The Resource Sidebar SHALL provide visual feedback when documents are selected.

#### Scenario: Active document styling
- **WHEN** a user clicks a document card
- **THEN** the card border becomes highlighted (e.g., primary color)
- **AND** the background color changes to indicate selection

### Requirement: Inspiration Dock Summary Action
The Inspiration Dock SHALL offer a mechanism to trigger summarization.

#### Scenario: Summarize button availability
- **WHEN** one or more documents are selected in the sidebar
- **THEN** the Inspiration Dock displays a "Summarize" option/icon

### Requirement: Summary Card Display
The system SHALL display the generated summary in a dedicated card format.

#### Scenario: Summary presentation
- **WHEN** the summary generation is complete
- **THEN** a Summary Card appears containing:
  - A header with title and AI attribution
  - Tags (e.g., STRATEGY, INSIGHTS)
  - A brief narrative text
  - A highlights section with key metrics or points
  - A "Read Full Summary" action

#### Scenario: Full content expansion
- **WHEN** the user selects "Read Full Summary"
- **THEN** the card expands or opens a modal to show the complete detailed summary

### Requirement: Inspiration Dock Visibility Control
The system MUST allow users to toggle the visibility of the Inspiration Dock.
The Inspiration Dock SHALL automatically hide when outputs already exist on the canvas.

#### Scenario: Closing the Dock
- **WHEN** the user clicks the "Close" (X) button on the Inspiration Dock
- **THEN** the Inspiration Dock disappears from the view
- **AND** a "Sparkles" icon/toggle becomes available/highlighted in the toolbar


#### Scenario: Auto-hide when outputs exist
- **WHEN** the canvas has one or more completed generation outputs (e.g., mindmap, summary)
- **THEN** the Inspiration Dock SHALL NOT be displayed
- **AND** users can generate additional content via the right-click context menu

#### Scenario: Show dock on empty canvas with documents
- **WHEN** the canvas has no generation outputs
- **AND** one or more documents are uploaded
- **THEN** the Inspiration Dock is displayed as the primary entry point for generation

### Requirement: Right-Click Context Menu Generation
The canvas context menu SHALL provide content generation options that place outputs at the right-click position.

#### Scenario: Generate mindmap via context menu
- **WHEN** a user right-clicks on the canvas
- **AND** selects "Generate Mind Map" from the context menu
- **THEN** the mindmap generation starts
- **AND** a loading placeholder card SHALL appear immediately at the click position
- **AND** the placeholder SHALL display a spinner with "Generating..." text
- **AND** the generated mindmap replaces the placeholder when complete

#### Scenario: Generate summary via context menu
- **WHEN** a user right-clicks on the canvas
- **AND** selects "Generate Summary" from the context menu
- **THEN** the summary generation starts
- **AND** a loading placeholder card SHALL appear immediately at the click position
- **AND** the placeholder SHALL display a spinner with "Generating..." text
- **AND** the generated summary replaces the placeholder when complete

#### Scenario: Context menu available when dock is hidden
- **WHEN** the Inspiration Dock is hidden (either manually or due to existing outputs)
- **THEN** the right-click context menu remains the primary method for generating content

#### Scenario: Consistent feedback across entry points
- **WHEN** content generation is triggered from either Inspiration Dock or context menu
- **THEN** the loading feedback SHALL be visually consistent
- **AND** both entry points SHALL show the same loading state pattern

### Requirement: Studio Layout
The Studio SHALL provide a workspace centered around an infinite whiteboard canvas.

#### Scenario: Default layout
- **WHEN** a user opens a project
- **THEN** they see the whiteboard canvas occupying the majority of the screen
- **AND** a resource sidebar on the left
- **AND** floating controls for chat and navigation overlaid on the canvas.

### Requirement: Resource Management
The Studio SHALL provide a dedicated sidebar for managing project resources.

#### Scenario: File upload
- **WHEN** a user drags a file onto the "Drop files here" zone in the sidebar
- **THEN** the file is uploaded and added to the resource list.

### Requirement: Canvas Interaction
The Studio SHALL provide high-performance canvas interactions.

#### Scenario: Navigation
- **WHEN** a user interacts with the floating navigation controls
- **THEN** the canvas zooms or pans accordingly with smooth transitions.

#### Scenario: Pan mode with hand tool
- **WHEN** the user selects the hand tool from the toolbar or presses 'H' key
- **AND** clicks and drags on the canvas
- **THEN** the canvas viewport SHALL pan in the direction of the drag
- **AND** node selection SHALL NOT occur
- **AND** nodes SHALL NOT be draggable while hand tool is active

#### Scenario: Pan mode with spacebar
- **WHEN** the user holds the spacebar key
- **AND** clicks and drags on the canvas
- **THEN** the canvas viewport SHALL pan in the direction of the drag
- **AND** this SHALL work regardless of the currently selected tool

### Requirement: Output Card Dragging
The generated output cards (summary, mindmap) displayed on the canvas SHALL be draggable to allow users to reposition them.

#### Scenario: Drag output card to new position
- **WHEN** the user clicks and drags the drag handle of an output card
- **THEN** the card SHALL follow the mouse cursor during drag
- **AND** the card position SHALL update to the final drop position
- **AND** the new position SHALL be persisted in the generation task state

#### Scenario: Drag respects viewport transforms
- **WHEN** the user drags an output card while the canvas is zoomed or panned
- **THEN** the drag movement SHALL correctly account for the current viewport scale and offset
- **AND** the card SHALL visually follow the cursor accurately

#### Scenario: Drag visual feedback
- **WHEN** the user starts dragging an output card
- **THEN** the card SHALL display visual feedback indicating it is being dragged (e.g., elevated shadow, cursor change)
- **AND** the card z-index SHALL be elevated above other elements during drag

### Requirement: Floating Chat Interface
The Studio SHALL provide a floating chat interface for AI assistance.

#### Scenario: Chat interaction
- **WHEN** a user types in the bottom-center chat bar
- **THEN** the message is sent to the AI and the response is displayed contextually.

### Requirement: Inspiration Dock Mind Map Action
The Inspiration Dock SHALL offer a mechanism to trigger mind map generation.

#### Scenario: Mind Map button availability
- **WHEN** one or more documents are selected in the sidebar
- **THEN** the Inspiration Dock displays a "Generate Mind Map" option/icon

### Requirement: Mind Map Card Display
The system SHALL display the generated mind map in a unified card format with consistent styling across all generation states, and provide full editing capabilities in expanded view.

#### Scenario: Mind Map presentation during generation
- **WHEN** the mind map generation starts
- **THEN** a Mind Map Card appears in the workspace
- **AND** the card displays:
  - A header with an icon badge (green gradient), drag handle, and title
  - A "MINDMAP" chip tag
  - A streaming indicator (spinner) next to the title
  - A preview area showing nodes as they appear incrementally
- **AND** nodes appear incrementally ("grow") as they are generated
- **AND** the card shows a simplified or zoomed-out view of the structure

#### Scenario: Mind Map presentation after completion
- **WHEN** the mind map generation completes
- **THEN** the Mind Map Card retains the same visual styling as during generation
- **AND** the card displays:
  - The same header layout with icon badge, drag handle, and title
  - A "MINDMAP" chip tag
  - A "{count} NODES" chip tag showing total node count
  - The streaming indicator is hidden
- **AND** the user can click to expand to full view with editing

#### Scenario: Full Mind Map expansion with editing
- **WHEN** the user interacts with the Mind Map Card (e.g., clicks expand button)
- **THEN** the mind map opens in a full view modal with MindMapEditor
- **AND** the user can freely zoom using:
  - Mouse scroll wheel
  - Pinch gestures on trackpad
  - Zoom in/out buttons
- **AND** the user can pan the canvas by dragging the background
- **AND** the user can switch between layouts (radial, tree, balanced)
- **AND** the user can edit nodes (add, delete, edit label/content)
- **AND** the user can export the mindmap (PNG, JSON)

#### Scenario: Mind Map card visual consistency
- **WHEN** the Mind Map Card is shown via any display method (canvas overlay or dock overlay)
- **THEN** the card uses identical visual styling including:
  - Green gradient icon badge
  - Drag handle in header
  - "MINDMAP" chip tag
  - Node count chip when available
  - Same border, spacing, and dimensions

### Requirement: Mind Map Real-time Rendering
The system SHALL render mind map nodes in real-time as they are generated by the backend.

#### Scenario: Node growth animation
- **WHEN** a new node is received from the backend stream
- **THEN** it appears on the canvas with an animation (e.g., fading in or growing from parent)
- **AND** it is automatically connected to its parent node

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

### Requirement: Icon Abstraction Layer
The frontend SHALL provide a centralized icon abstraction layer to decouple components from specific icon library implementations.

#### Scenario: Centralized icon exports
- **WHEN** a component needs to use an icon
- **THEN** it SHALL import from `@/components/ui/icons`
- **AND** SHALL NOT import directly from any icon library (e.g., `lucide-react`, `@mui/icons-material`)

#### Scenario: Consistent icon props interface
- **WHEN** an icon is rendered
- **THEN** it SHALL accept a standard `IconProps` interface
- **AND** `size` SHALL accept semantic values ('xs', 'sm', 'md', 'lg', 'xl') or pixel numbers
- **AND** `color` SHALL accept semantic values ('primary', 'secondary', 'error', etc.)

#### Scenario: Design system swap
- **WHEN** the underlying icon library needs to change
- **THEN** only the `components/ui/icons/` folder needs modification
- **AND** consuming components SHALL NOT require changes

### Requirement: MUI Icon Implementation
The icon abstraction layer SHALL use `@mui/icons-material` as the underlying implementation.

#### Scenario: Icon theming
- **WHEN** an icon is rendered
- **THEN** it SHALL respect MUI theme colors
- **AND** SHALL integrate with MUI's `SvgIcon` system

#### Scenario: Tree-shaking support
- **WHEN** the application is built
- **THEN** only used icons SHALL be included in the bundle
- **AND** unused icons SHALL be eliminated by tree-shaking

### Requirement: Output Persistence Across Sessions
The system SHALL restore previously generated outputs (summary, mindmap) when a user returns to a project.

#### Scenario: Load most recent summary on page mount
- **WHEN** a user opens a project page
- **AND** a completed summary output exists for that project
- **THEN** the most recent complete summary is loaded into state
- **AND** the summary data is available for viewing in the Inspiration Dock
- **AND** the summary overlay is NOT automatically shown

#### Scenario: Load most recent mindmap on page mount
- **WHEN** a user opens a project page
- **AND** a completed mindmap output exists for that project
- **THEN** the most recent complete mindmap is loaded into state
- **AND** the mindmap data is available for viewing in the Inspiration Dock
- **AND** the mindmap overlay is NOT automatically shown

#### Scenario: No outputs exist
- **WHEN** a user opens a project page
- **AND** no completed outputs exist for that project
- **THEN** the summary and mindmap states remain null
- **AND** the Inspiration Dock shows generation options normally

#### Scenario: Multiple outputs exist
- **WHEN** a user opens a project page
- **AND** multiple completed outputs of the same type exist
- **THEN** only the most recently created output is loaded
- **AND** older outputs remain in the database for potential future history features

### Requirement: Canvas Navigation Gestures
The canvas MUST support standard trackpad and mouse gestures for navigation.

#### Scenario: Panning with Trackpad
- **WHEN** the user performs a two-finger scroll gesture (without pinching)
- **THEN** the canvas viewport should pan in the direction of the scroll
- **AND** the zoom level should remain unchanged

#### Scenario: Zooming with Trackpad
- **WHEN** the user performs a pinch gesture (two fingers moving apart or together)
- **THEN** the canvas viewport should zoom in or out centered on the pointer position
- **AND** the viewport position should adjust to keep the content under the pointer stable


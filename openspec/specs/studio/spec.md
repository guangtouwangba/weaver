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
The Studio SHALL provide high-performance canvas interactions with optimized rendering for large node sets.

#### Scenario: Navigation
- **WHEN** a user interacts with the floating navigation controls
- **THEN** the canvas zooms or pans accordingly with smooth transitions.

#### Scenario: Large canvas performance
- **WHEN** the canvas contains 1000+ nodes
- **THEN** pan and zoom operations maintain 60fps
- **AND** box selection responds within 16ms
- **AND** the UI remains responsive during all interactions

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

### Requirement: Canvas Spatial Indexing
The canvas SHALL use spatial indexing (R-tree) to enable efficient spatial queries for large node sets.

#### Scenario: Efficient box selection with spatial index
- **WHEN** the user performs a box selection on a canvas with 1000+ nodes
- **THEN** only nodes intersecting the selection box are identified
- **AND** the query completes in under 5ms regardless of total node count
- **AND** no visible lag occurs during the selection operation

#### Scenario: Spatial index auto-rebuild
- **WHEN** canvas nodes are added, removed, or moved
- **THEN** the spatial index is automatically rebuilt
- **AND** subsequent spatial queries reflect the updated node positions

### Requirement: Canvas Viewport Culling
The canvas SHALL render only nodes within or near the visible viewport to maintain performance.

#### Scenario: Off-screen nodes not rendered
- **WHEN** the canvas contains 5000+ nodes
- **AND** only 50 nodes are within the visible viewport
- **THEN** only the 50 visible nodes (plus a padding buffer) are rendered
- **AND** the frame rate remains above 30fps during pan and zoom operations

#### Scenario: Nodes appear on scroll into view
- **WHEN** the user pans the canvas
- **AND** a node enters the visible viewport area
- **THEN** the node is rendered immediately without visual pop-in
- **AND** nodes outside the viewport (plus buffer) are no longer rendered

#### Scenario: Viewport culling respects zoom level
- **WHEN** the user zooms out to view more nodes
- **THEN** the viewport culling recalculates visible bounds
- **AND** more nodes are rendered as they fit within the zoomed-out view
- **AND** performance scales with visible node count, not total count

### Requirement: Optimized Grid Background Rendering
The canvas grid background SHALL be rendered efficiently using native canvas API.

#### Scenario: Grid renders as single draw operation
- **WHEN** the canvas grid is rendered
- **THEN** all grid dots are drawn using a single Konva Shape with native canvas commands
- **AND** no individual React components are created for each grid dot

#### Scenario: Grid adapts to viewport
- **WHEN** the user pans or zooms the canvas
- **THEN** only grid dots within the visible area are drawn
- **AND** grid dot density adjusts appropriately to zoom level
- **AND** grid rendering does not cause frame drops

### Requirement: Document Preview Card Display
The Resource Sidebar SHALL display document cards with rich visual preview including thumbnail, file type icon, and metadata.

#### Scenario: PDF document preview card
- **WHEN** a PDF document is uploaded and processed
- **THEN** the document card displays:
  - A thumbnail preview of the first page (or placeholder if not yet generated)
  - A document type icon badge (PDF icon)
  - The filename as title
  - File size and page count metadata
  - Action buttons (download, more options)

#### Scenario: Thumbnail loading state
- **WHEN** a document is uploaded and thumbnail is not yet generated
- **THEN** the preview card shows an animated skeleton placeholder in the thumbnail area
- **AND** the skeleton displays a shimmer loading animation
- **AND** a semi-transparent file type icon overlays the skeleton
- **AND** the document filename and basic metadata display immediately

#### Scenario: Thumbnail becomes available
- **WHEN** the backend completes thumbnail generation
- **THEN** the frontend receives notification (via WebSocket or polling)
- **AND** the animated placeholder smoothly transitions to the actual thumbnail
- **AND** the transition uses a fade animation for visual continuity

#### Scenario: Thumbnail unavailable fallback
- **WHEN** thumbnail generation fails or document type does not support thumbnails
- **THEN** the preview card shows a large file type icon as placeholder
- **AND** the card remains fully functional for other interactions

### Requirement: Document Drag Initiation
The Document Preview Card SHALL be draggable to allow users to reference documents on the canvas.

#### Scenario: Start dragging document
- **WHEN** a user clicks and drags a document preview card
- **THEN** a drag ghost image appears showing the document thumbnail
- **AND** the DataTransfer object contains document metadata (id, title, thumbnailUrl)
- **AND** the drag effect is set to "copy"

#### Scenario: Drag visual feedback
- **WHEN** dragging a document over valid drop zones
- **THEN** the cursor indicates the drop action is available
- **AND** the original card shows reduced opacity to indicate active drag

### Requirement: Canvas Document Drop Zone
The Canvas SHALL accept dropped documents and create reference nodes at the drop position.

#### Scenario: Drop document on canvas
- **WHEN** a user drops a document preview card onto the canvas
- **THEN** a Document Reference Node is created at the drop position
- **AND** the node position accounts for current viewport offset and scale
- **AND** the node is automatically selected after creation

#### Scenario: Drop position calculation
- **WHEN** the user drops a document while canvas is zoomed and panned
- **THEN** the node appears at the visual drop location
- **AND** the position correctly transforms from screen coordinates to canvas coordinates

#### Scenario: Drop zone highlight
- **WHEN** dragging a document over the canvas area
- **THEN** the canvas shows visual feedback indicating it is a valid drop target
- **AND** the feedback disappears when drag leaves the canvas

### Requirement: Document Reference Node Display
The Canvas SHALL display dropped documents as Document Reference Nodes with thumbnail and metadata.

#### Scenario: Document reference node appearance
- **WHEN** a Document Reference Node is displayed on the canvas
- **THEN** it shows:
  - Document thumbnail (or placeholder icon)
  - Document title
  - File type badge (e.g., "PDF")
  - Page count indicator
- **AND** the node uses the "source" subType designation

#### Scenario: Document reference node interaction
- **WHEN** a user double-clicks a Document Reference Node
- **THEN** the source panel opens showing the full document
- **AND** the document is loaded in the PDF viewer if applicable

#### Scenario: Document reference node dragging
- **WHEN** a user drags a Document Reference Node on the canvas
- **THEN** the node moves following standard canvas node drag behavior
- **AND** any connected edges update to follow the node position

### Requirement: Async Thumbnail Generation
The system SHALL generate PDF thumbnails asynchronously after document upload for preview display.

#### Scenario: Automatic async thumbnail generation
- **WHEN** a PDF document upload completes successfully
- **THEN** a thumbnail generation task is queued immediately
- **AND** the upload response returns without waiting for thumbnail
- **AND** the document record includes `thumbnail_status: 'pending'`

#### Scenario: Thumbnail generation completion
- **WHEN** the thumbnail generation task completes
- **THEN** the thumbnail is stored with the document record
- **AND** the document `thumbnail_status` updates to `'ready'`
- **AND** a WebSocket notification is sent to connected clients
- **AND** the `thumbnail_url` becomes available in API responses

#### Scenario: Thumbnail quality and size
- **WHEN** generating a PDF thumbnail
- **THEN** the thumbnail is rendered at a maximum width of 300 pixels
- **AND** maintains the original page aspect ratio
- **AND** uses WebP format for efficient storage and loading

### Requirement: PDF Preview Modal
The system SHALL provide a full-screen modal for immersive PDF document preview with annotation capabilities.

#### Scenario: Open preview from sidebar
- **WHEN** a user clicks a PDF document in the Resource Sidebar source files list
- **THEN** the PDF Preview Modal opens in full-screen
- **AND** the document loads at page 1
- **AND** the page thumbnail sidebar shows all pages
- **AND** the tools panel is visible on the right

#### Scenario: Open preview from canvas
- **WHEN** a user double-clicks a Document Reference Node on the canvas
- **THEN** the PDF Preview Modal opens for that document
- **AND** the document loads at page 1 (or last viewed page if tracked)

#### Scenario: Close preview modal
- **WHEN** a user clicks the close button or presses Escape key
- **THEN** the PDF Preview Modal closes
- **AND** the canvas workspace is restored to view

### Requirement: Page Thumbnail Navigation
The PDF Preview Modal SHALL provide a page thumbnail sidebar for quick navigation.

#### Scenario: Display page thumbnails
- **WHEN** the PDF Preview Modal is open
- **THEN** the left sidebar displays thumbnail previews of all pages
- **AND** each thumbnail shows the page number below it
- **AND** the current page thumbnail is highlighted

#### Scenario: Navigate via thumbnail click
- **WHEN** a user clicks a page thumbnail
- **THEN** the main content area scrolls/jumps to that page
- **AND** the clicked thumbnail becomes highlighted as current

#### Scenario: Thumbnail virtualization for large documents
- **WHEN** a PDF has more than 20 pages
- **THEN** only visible thumbnails are fully rendered
- **AND** scrolling loads additional thumbnails progressively

### Requirement: Annotation Toolbar
The PDF Preview Modal SHALL provide an annotation toolbar with multiple tool types.

#### Scenario: Display annotation tools
- **WHEN** the Tools tab is active in the right panel
- **THEN** the toolbar displays icons for:
  - Highlight (marker icon)
  - Underline (U icon)
  - Strikethrough (S with line icon)
  - Pen/freehand (pen icon)
  - Comment (speech bubble icon)
  - Image (image icon, future phase)
  - Diagram (chart icon, future phase)

#### Scenario: Select annotation tool
- **WHEN** a user clicks a tool icon
- **THEN** that tool becomes active (visually highlighted)
- **AND** the cursor changes to indicate the active tool mode
- **AND** text selection behavior adapts to the active tool

#### Scenario: Apply highlight annotation
- **WHEN** highlight tool is active
- **AND** a user selects text in the PDF
- **THEN** the selection is highlighted with the current color
- **AND** the annotation is saved to the database
- **AND** the annotation appears in Recent Annotations list

#### Scenario: Apply underline annotation
- **WHEN** underline tool is active
- **AND** a user selects text in the PDF
- **THEN** an underline decoration is applied to the selection
- **AND** the annotation is saved with type "underline"

#### Scenario: Apply strikethrough annotation
- **WHEN** strikethrough tool is active
- **AND** a user selects text in the PDF
- **THEN** a strikethrough line is drawn through the selection
- **AND** the annotation is saved with type "strikethrough"

#### Scenario: Freehand pen drawing
- **WHEN** pen tool is active
- **AND** a user clicks and drags on the PDF page
- **THEN** a freehand path is drawn following the cursor
- **AND** the path is saved as a pen annotation on release

### Requirement: Recent Annotations Panel
The tools panel SHALL display a list of recent annotations for the current document.

#### Scenario: Display recent annotations
- **WHEN** the Tools tab is active
- **THEN** the Recent Annotations section shows all annotations for this document
- **AND** each item displays:
  - Color indicator dot matching annotation color
  - Page number ("Page X")
  - Text snippet (first 50 characters for text annotations)
  - Timestamp ("Just now", "2h ago", etc.)
  - Delete button (trash icon)

#### Scenario: Navigate to annotation
- **WHEN** a user clicks an annotation item in the list
- **THEN** the PDF viewer navigates to that annotation's page
- **AND** the annotation is scrolled into view
- **AND** the annotation is briefly highlighted/pulsed

#### Scenario: Delete annotation from list
- **WHEN** a user clicks the delete button on an annotation item
- **THEN** the annotation is removed from the document
- **AND** the annotation disappears from the list
- **AND** the visual overlay is removed from the PDF page

### Requirement: Comments Panel
The PDF Preview Modal SHALL provide a Comments tab for document-level discussions.

#### Scenario: Display comments tab
- **WHEN** a user clicks the Comments tab
- **THEN** the panel switches to show the comments view
- **AND** the tab header shows comment count (e.g., "Comments (3)")

#### Scenario: Add new comment
- **WHEN** a user types in the comment input field
- **AND** submits the comment (Enter or button)
- **THEN** the comment is saved to the database
- **AND** the comment appears in the comments list
- **AND** the comment count updates

#### Scenario: Display comment threads
- **WHEN** comments exist for the document
- **THEN** each comment shows:
  - Author indicator (avatar or icon)
  - Comment text content
  - Timestamp
  - Optional page/annotation anchor reference

### Requirement: Selection Popover Actions
The PDF viewer SHALL display a popover menu when text is selected.

#### Scenario: Show selection popover
- **WHEN** a user selects text in the PDF viewer
- **THEN** a popover appears near the selection with action buttons:
  - Add (creates annotation with current tool)
  - Edit (opens note editor, if applicable)
  - Copy (copies text to clipboard)

#### Scenario: Quick add annotation via popover
- **WHEN** text is selected
- **AND** a user clicks the Add button in the popover
- **THEN** an annotation is created using the current tool type and color
- **AND** the popover closes
- **AND** the annotation appears in Recent Annotations

### Requirement: Add to Whiteboard
The system SHALL allow users to export annotations and text selections to the canvas as snippet nodes.

#### Scenario: Add selection to whiteboard
- **WHEN** text is selected in the PDF preview
- **AND** a user clicks the "Add to Whiteboard" button
- **THEN** the PDF Preview Modal closes
- **AND** a new Snippet Node is created on the canvas
- **AND** the node contains the selected text
- **AND** the node includes source document reference (document name, page number)
- **AND** the node is positioned at the center of the current viewport
- **AND** the node is automatically selected

#### Scenario: Add annotation to whiteboard
- **WHEN** an annotation is displayed in Recent Annotations
- **AND** the annotation has associated text
- **AND** a user clicks the "Add to Whiteboard" button (or annotation's add action)
- **THEN** the annotation text is exported as a Snippet Node
- **AND** the node styling reflects the annotation color

#### Scenario: Snippet node appearance
- **WHEN** a Snippet Node is displayed on the canvas
- **THEN** it shows:
  - The annotated/selected text content
  - A source indicator (document icon + page number)
  - A colored accent matching the annotation color (if applicable)
  - Standard node interactions (drag, select, connect)

#### Scenario: Navigate from snippet to source
- **WHEN** a user double-clicks a Snippet Node on the canvas
- **THEN** the PDF Preview Modal opens
- **AND** navigates to the source page and scrolls to the original annotation position

### Requirement: Annotation Color Selection
The annotation toolbar SHALL provide color options for highlight and pen annotations.

#### Scenario: Display color palette
- **WHEN** highlight or pen tool is active
- **THEN** a color palette is visible showing available colors:
  - Yellow (default)
  - Green
  - Blue
  - Pink

#### Scenario: Change annotation color
- **WHEN** a user selects a different color from the palette
- **THEN** subsequent annotations use the new color
- **AND** the active color is visually indicated in the toolbar

### Requirement: Project Chat Interface
The system SHALL provide a chat interface accessible from the canvas to allow users to interact with project content.

#### Scenario: Wake up chat
- **WHEN** the user clicks the "Ask AI" button at the bottom of the canvas
- **THEN** the chat panel SHALL slide up or appear overlaid on the canvas
- **AND** the latest chat history SHALL be displayed

#### Scenario: Chat Layout
- **WHEN** the chat panel is open
- **THEN** it SHALL display a list of previous messages
- **AND** it SHALL provide an input area at the bottom
- **AND** the input area SHALL support text entry and drag-and-drop targets

#### Scenario: Citation Click Interaction
- **WHEN** the user clicks on a citation chip/link in a chat answer
- **THEN** the Source Panel SHALL open (if closed)
- **AND** the system SHALL switch to the cited Document ID
- **AND** the system SHALL navigate to the specific Page Number
- **AND** the system SHALL highlight the cited text (Quote) in the document viewer

### Requirement: Project RAG Endpoint
The system SHALL provide an API endpoint to answer user queries based on project documents and provided context.

#### Scenario: Answer with Context
- **WHEN** the frontend sends a query with a Project ID
- **AND** optionally provides specific context item IDs (documents)
- **THEN** the system SHALL retrieve relevant chunks from the specified documents (or all project documents if none specified)
- **AND** generate an answer using the LLM
- **AND** return the answer text along with citations

### Requirement: Source Attribution
The system SHALL provide citations for every answer generated from project documents.

#### Scenario: Citation Format
- **WHEN** the system generates an answer
- **THEN** it SHALL return a list of source references (Document ID, Page Number, Quote) used for the answer
- **AND** the Quote SHALL contain the exact text content used from the source to allow for precise highlighting
- **AND** the frontend SHALL display these citations interactively (e.g., clickable to open source)

### Requirement: Drag to Chat Context
The system SHALL allow users to drag content from the canvas or source list into the chat to use as context for the next query.

#### Scenario: Drag Source Document
- **WHEN** the user drags a Source Document from the source list
- **AND** drops it into the Chat Input area
- **THEN** the document ID SHALL be added to the pending context list
- **AND** a visual indicator of the attached document SHALL appear in the input area

#### Scenario: Drag Canvas Node
- **WHEN** the user drags a generic Canvas Node (Note, Text, etc.)
- **AND** drops it into the Chat Input area
- **THEN** the text content of the node SHALL be added to the context

### Requirement: Drag Response to Canvas
The system SHALL allow users to drag AI responses from the chat onto the canvas to create new nodes.

#### Scenario: Drag Response
- **WHEN** the user drags an AI response message bubble
- **AND** drops it onto the Canvas
- **THEN** a new Note Node SHALL be created at the drop position
- **AND** the content of the node SHALL be the text of the AI response


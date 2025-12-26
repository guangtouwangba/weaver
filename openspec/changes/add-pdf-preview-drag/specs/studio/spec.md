## ADDED Requirements

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


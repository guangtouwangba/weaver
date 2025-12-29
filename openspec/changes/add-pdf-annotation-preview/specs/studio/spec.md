## ADDED Requirements

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



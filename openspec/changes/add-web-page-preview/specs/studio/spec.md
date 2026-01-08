# studio Specification Delta

## ADDED Requirements

### Requirement: Web Page Preview Card Display
The Canvas SHALL display web page nodes as rich preview cards with consistent styling and metadata.

#### Scenario: Web page card appearance
- **WHEN** a canvas node has `type: 'knowledge'` and `fileMetadata.platform: 'web'`
- **THEN** it SHALL render as a Web Page Preview Card displaying:
  - A header with Globe icon and "Web Page" label using design system `colors.primary`
  - External link icon in header for quick access
  - Favicon image (loaded via Google Favicons API) with fallback to globe icon
  - Domain name prominently displayed (e.g., "github.com")
  - "Imported" badge using `colors.primary[100]` background and `colors.primary[700]` text
  - Page title (bold, truncated with ellipsis if needed)
  - Description/excerpt text (up to ~100 characters)
  - Source URL at the bottom with link icon
- **AND** the card SHALL have consistent dimensions with other source preview cards (approximately 240px width)
- **AND** all colors SHALL be sourced from `@/components/ui/tokens`

#### Scenario: Web page card with thumbnail
- **WHEN** the web page has an `og:image` or extracted thumbnail
- **THEN** the card SHALL display the thumbnail image in the content area
- **AND** the favicon and domain SHALL overlay the thumbnail
- **AND** text content SHALL appear below the thumbnail

#### Scenario: Web page card without thumbnail
- **WHEN** the thumbnail URL is missing or fails to load
- **THEN** the card SHALL display a light background using `colors.primary[50]`
- **AND** the favicon, domain, and text SHALL be prominently displayed

#### Scenario: Web page card with missing metadata
- **WHEN** optional metadata (description, favicon) is missing
- **THEN** those elements SHALL be gracefully hidden
- **AND** the card layout SHALL adjust to avoid empty space
- **AND** at minimum, the title or URL SHALL always be displayed

### Requirement: Web Page Node Creation from Drop
The Canvas SHALL create web page knowledge nodes when web URLs are dropped from the Resource Sidebar.

#### Scenario: Drop web URL item on canvas
- **WHEN** a user drags a URL item with `platform: 'web'` from the Resource Sidebar
- **AND** drops it onto the canvas
- **THEN** a new knowledge node SHALL be created with:
  - `type: 'knowledge'`
  - `subType: 'source'`
  - `title`: page title
  - `content`: article description/excerpt
  - `fileMetadata.platform: 'web'`
  - `fileMetadata.fileType: 'web'`
  - `fileMetadata.thumbnailUrl`: og:image URL (if available)
  - `fileMetadata.sourceUrl`: original page URL
  - `fileMetadata.siteName`: extracted site name or domain
- **AND** the node position SHALL be calculated from drop coordinates

### Requirement: Web Page Card Interaction
The Web Page Preview Card SHALL support standard canvas interactions and article-specific actions.

#### Scenario: Double-click opens reader modal
- **WHEN** a user double-clicks a Web Page Preview Card
- **THEN** the Web Page Reader Modal SHALL open
- **AND** display the full extracted article content

#### Scenario: Click external link opens source
- **WHEN** a user clicks the external link icon on a Web Page Preview Card
- **THEN** the original URL SHALL open in a new browser tab

#### Scenario: Standard canvas interactions
- **WHEN** a user interacts with a Web Page Preview Card
- **THEN** standard canvas node behaviors SHALL apply:
  - Single-click selects the node
  - Drag repositions the node
  - Shift-click adds to selection
  - Delete key removes the node

### Requirement: Web Page Card Connection Handles
The Web Page Preview Card SHALL support connection handles for linking with other canvas nodes.

#### Scenario: Connection handles display
- **WHEN** a user hovers over or selects a Web Page Preview Card
- **THEN** connection handles SHALL appear on all four sides:
  - Top center
  - Bottom center
  - Left center
  - Right center
- **AND** handles SHALL have the same visual style as other canvas node handles

#### Scenario: Create connection from web page card
- **WHEN** a user drags from a connection handle on a Web Page Preview Card
- **THEN** a temporary connection line SHALL follow the cursor
- **WHEN** the user releases over another node's connection handle
- **THEN** an edge SHALL be created between the two nodes
- **AND** the edge SHALL be persisted to the canvas state

### Requirement: Web Page Reader Modal
The system SHALL provide a modal dialog for reading extracted web article content without leaving the workspace.

#### Scenario: Reader modal appearance
- **WHEN** the Web Page Reader Modal opens
- **THEN** it SHALL display:
  - A centered modal overlay with dark backdrop
  - Article title as header
  - Site favicon and name below title
  - Scrollable article content with comfortable reading typography
  - Close button (X) in the top-right corner
  - "Open in Browser" button to visit original URL
- **AND** the modal SHALL be responsive to viewport size

#### Scenario: Reader modal typography
- **WHEN** the Web Page Reader Modal displays article content
- **THEN** the content SHALL use:
  - Comfortable reading font size (16-18px)
  - Appropriate line height (1.6-1.8)
  - Maximum content width for readability (~680px)
  - Proper paragraph spacing

#### Scenario: Close reader modal
- **WHEN** a user clicks the close button, backdrop, or presses Escape
- **THEN** the modal SHALL close
- **AND** focus SHALL return to the canvas

### Requirement: Sidebar Web Page Preview
The Resource Sidebar SHALL allow users to preview web page content by clicking on URL items.

#### Scenario: Click web page item opens preview
- **WHEN** a user clicks a web URL item (platform: 'web') in the Resource Sidebar
- **THEN** the Source Panel (right panel) SHALL switch to web page preview mode
- **AND** display the page title as header
- **AND** show the thumbnail/hero image if available
- **AND** display article content in scrollable area

#### Scenario: Web page preview panel layout
- **WHEN** the web page preview mode is active in Source Panel
- **THEN** the panel SHALL display:
  - Header with page title, site favicon, and close button
  - Hero image/thumbnail (if available) with aspect ratio preserved
  - Site name and domain
  - Published date (if available)
  - Article content in readable format
  - "Open Original" button to visit source URL
  - "Add to Canvas" button to create a node from current page

#### Scenario: Add web page to canvas from preview
- **WHEN** a user clicks "Add to Canvas" button in web page preview
- **THEN** a new Web Page Preview Card SHALL be created on the canvas
- **AND** the card SHALL appear at the center of the current viewport
- **AND** the card SHALL be automatically selected

#### Scenario: Empty content handling
- **WHEN** a web page has no extractable article content
- **THEN** the preview panel SHALL display:
  - The page title and URL
  - A message indicating "No article content extracted"
  - The thumbnail if available
  - "Open Original" button to view in browser

### Requirement: Web Page Drag Data from Sidebar
The Resource Sidebar URL items SHALL include platform-specific metadata in drag data for web page URLs.

#### Scenario: Drag web page URL item
- **WHEN** a user initiates drag on a web URL item (platform: 'web') in the Resource Sidebar
- **THEN** the drag data SHALL include:
  - `type: 'url'`
  - `platform: 'web'`
  - `contentType: 'article'`
  - `title`: page title
  - `thumbnailUrl`: og:image or extracted thumbnail
  - `metadata`: object containing `siteName`, `sourceUrl`, `description`


## ADDED Requirements

### Requirement: YouTube Video Preview Card Display
The Canvas SHALL display YouTube video nodes as rich preview cards with platform-specific branding and metadata.

#### Scenario: YouTube card appearance
- **WHEN** a canvas node has `type: 'knowledge'` and `fileMetadata.platform: 'youtube'`
- **THEN** it SHALL render as a YouTube Preview Card displaying:
  - A header with YouTube logo icon and "YouTube" label in red brand color (#FF0000)
  - Video thumbnail (from `fileMetadata.thumbnailUrl`)
  - A semi-transparent circular play button overlay centered on the thumbnail
  - Duration badge in bottom-right corner of thumbnail (format "HH:MM:SS" or "MM:SS")
  - Video title below thumbnail with ellipsis truncation
  - Channel avatar (circular), channel name, view count, and relative publish time
  - Source URL at the bottom with link icon
- **AND** the card SHALL have consistent dimensions with other source preview cards (approximately 240px width)

#### Scenario: YouTube card with missing thumbnail
- **WHEN** the thumbnail URL fails to load or is missing
- **THEN** the card SHALL display a YouTube-branded placeholder
- **AND** the placeholder SHALL show a muted YouTube logo or video icon

#### Scenario: YouTube card with missing metadata
- **WHEN** optional metadata (viewCount, duration, channelAvatar) is missing
- **THEN** those elements SHALL be gracefully hidden
- **AND** the card layout SHALL adjust to avoid empty space

### Requirement: YouTube Video Node Creation from Drop
The Canvas SHALL create YouTube-specific knowledge nodes when YouTube URLs are dropped from the Resource Sidebar.

#### Scenario: Drop YouTube URL item on canvas
- **WHEN** a user drags a URL item with `platform: 'youtube'` from the Resource Sidebar
- **AND** drops it onto the canvas
- **THEN** a new knowledge node SHALL be created with:
  - `type: 'knowledge'`
  - `subType: 'source'`
  - `title`: video title
  - `fileMetadata.platform: 'youtube'`
  - `fileMetadata.thumbnailUrl`: video thumbnail URL
  - `fileMetadata.duration`: video duration in seconds
  - `fileMetadata.channelName`: channel display name
  - `fileMetadata.channelAvatar`: channel avatar URL (optional)
  - `fileMetadata.viewCount`: view count string (e.g., "24K views")
  - `fileMetadata.publishedAt`: publish timestamp or relative string
  - `fileMetadata.videoId`: YouTube video ID
  - `fileMetadata.sourceUrl`: original YouTube URL
- **AND** the node position SHALL be calculated from drop coordinates

### Requirement: YouTube Video Card Interaction
The YouTube Preview Card SHALL support standard canvas interactions and video-specific actions.

#### Scenario: Click play button opens player modal
- **WHEN** a user clicks the play button overlay on a YouTube Preview Card
- **THEN** the YouTube Player Modal SHALL open
- **AND** the video SHALL start playing automatically

#### Scenario: Double-click opens player modal
- **WHEN** a user double-clicks a YouTube Preview Card
- **THEN** the YouTube Player Modal SHALL open
- **AND** the video SHALL start playing automatically

#### Scenario: Standard canvas interactions
- **WHEN** a user interacts with a YouTube Preview Card
- **THEN** standard canvas node behaviors SHALL apply:
  - Single-click selects the node
  - Drag repositions the node
  - Shift-click adds to selection
  - Delete key removes the node

### Requirement: YouTube Card Connection Handles
The YouTube Preview Card SHALL support connection handles for linking with other canvas nodes.

#### Scenario: Connection handles display
- **WHEN** a user hovers over or selects a YouTube Preview Card
- **THEN** connection handles SHALL appear on all four sides:
  - Top center
  - Bottom center
  - Left center
  - Right center
- **AND** handles SHALL have the same visual style as other canvas node handles

#### Scenario: Create connection from YouTube card
- **WHEN** a user drags from a connection handle on a YouTube Preview Card
- **THEN** a temporary connection line SHALL follow the cursor
- **WHEN** the user releases over another node's connection handle
- **THEN** an edge SHALL be created between the two nodes
- **AND** the edge SHALL be persisted to the canvas state

#### Scenario: Create connection to YouTube card
- **WHEN** a user drags a connection from another canvas node
- **AND** releases over a YouTube Preview Card's connection handle
- **THEN** an edge SHALL be created connecting to the YouTube card
- **AND** the connection SHALL behave identically to connections between other node types

#### Scenario: Connection edge styling
- **WHEN** an edge connects to or from a YouTube Preview Card
- **THEN** the edge SHALL use the same visual styling as other canvas edges
- **AND** support the same edge types (structural, support, contradict, relates-to) if applicable

### Requirement: YouTube Player Modal
The system SHALL provide a modal dialog for watching YouTube videos without leaving the workspace.

#### Scenario: Player modal appearance
- **WHEN** the YouTube Player Modal opens
- **THEN** it SHALL display:
  - A centered modal overlay with dark backdrop
  - Embedded YouTube iframe player (16:9 aspect ratio)
  - Video title above the player
  - Channel name and metadata below the player
  - Close button (X) in the top-right corner
  - "Open in YouTube" button to open in new tab
- **AND** the modal SHALL be responsive to viewport size

#### Scenario: Player modal controls
- **WHEN** the YouTube Player Modal is open
- **THEN** the embedded player SHALL support:
  - Play/Pause controls
  - Volume control
  - Fullscreen mode
  - Progress bar / seeking
  - Quality settings (via YouTube embed)
- **AND** pressing Escape key SHALL close the modal

#### Scenario: Close player modal
- **WHEN** a user clicks the close button or backdrop
- **THEN** the modal SHALL close
- **AND** video playback SHALL stop
- **AND** focus SHALL return to the canvas

### Requirement: Sidebar YouTube Video Preview
The Resource Sidebar SHALL allow users to preview YouTube videos by clicking on URL items.

#### Scenario: Click YouTube item opens preview
- **WHEN** a user clicks a YouTube URL item in the Resource Sidebar
- **THEN** the Source Panel (right panel) SHALL switch to video preview mode
- **AND** display the YouTube video title as header
- **AND** show the embedded YouTube player
- **AND** display video metadata (channel, views, published date) below player

#### Scenario: Video preview panel layout
- **WHEN** the video preview mode is active in Source Panel
- **THEN** the panel SHALL display:
  - Header with video title and close button
  - Embedded YouTube iframe player (responsive width)
  - Video description section (collapsible)
  - Channel avatar, name, and subscriber info
  - "View count • Published date" metadata
  - Transcript section if available (from URL extractor)
  - "Add to Canvas" button to create a node from current video

#### Scenario: Add video to canvas from preview
- **WHEN** a user clicks "Add to Canvas" button in video preview
- **THEN** a new YouTube Preview Card SHALL be created on the canvas
- **AND** the card SHALL appear at the center of the current viewport
- **AND** the card SHALL be automatically selected

### Requirement: YouTube Card Drag Data from Sidebar
The Resource Sidebar URL items SHALL include platform-specific metadata in drag data for YouTube URLs.

#### Scenario: Drag YouTube URL item
- **WHEN** a user initiates drag on a YouTube URL item in the Resource Sidebar
- **THEN** the drag data SHALL include:
  - `type: 'url'`
  - `platform: 'youtube'`
  - `contentType: 'video'`
  - `title`: video title
  - `thumbnailUrl`: video thumbnail
  - `metadata`: object containing `duration`, `channelName`, `viewCount`, `publishedAt`, `videoId`


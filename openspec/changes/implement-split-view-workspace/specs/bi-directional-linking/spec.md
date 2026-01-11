# Spec: Bi-directional Linking

## ADDED Requirements

### Requirement: Transcript-to-Canvas Drag & Drop
Users MUST be able to select text from the video transcript and drag it onto the canvas to create a linked node.

#### Scenario: Creating a node from video
- **Given** a video is playing in the Content Panel with transcripts visible.
- **When** I select a sentence in the transcript.
- **And** I drag the selection to the Mindmap Canvas.
- **Then** a new Note Node should be created.
- **And** the node content should match the selected text.
- **And** the node should store the video ID and timestamp of the segment.

### Requirement: Node-to-Source Navigation
Clicking a node with a source link MUST automatically scroll the Content Panel to the relevant position.

#### Scenario: Clicking a linked node
- **Given** a node linked to a specific timestamp in a video.
- **When** I click the "Source" icon on the node.
- **Then** the Content Panel should ensure the correct video is loaded.
- **And** the video player should seek to the stored timestamp.

### Requirement: Source-to-Node Highlighting
Selecting content in the source Viewer MUST visually emphasize any canvas nodes linked to that content.

#### Scenario: Selecting text in PDF
- **Given** a PDF is open in the Content Panel.
- **And** there is a node on the canvas linked to a specific paragraph.
- **When** I scroll to or select that paragraph in the PDF.
- **Then** the corresponding node on the canvas should highlight (e.g., glow or pulse).

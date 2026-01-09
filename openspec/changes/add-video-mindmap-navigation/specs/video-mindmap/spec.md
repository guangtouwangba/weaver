# Spec: Video Mindmap Navigation

## ADDED Requirements

### Requirement: Timestamp Extraction
The system SHALL support extracting and retaining timestamp information from video sources to enable temporal navigation.

#### Scenario: Extracting Timestamped Transcripts
Given a YouTube video URL
When the `YouTubeExtractor` processes the video
Then the content should be formatted with timestamps (e.g. `[MM:SS] Text content...`)
And the metadata should indicate `has_timestamps: true`

### Requirement: Temporal Node Generation
The mindmap generation process SHALL identify and persist timestamp references for nodes derived from video content.

#### Scenario: Generating Nodes with Video References
Given a document content containing timestamped transcript segments
When the `MindmapAgent` generates nodes
Then the `SourceRef` for the node should include `sourceType: "video"`
And the `location` field should contain the timestamp in seconds (e.g. "125")
And the `quote` should contain the relevant transcript text

### Requirement: Interactive Video Navigation
The frontend SHALL provide a mechanism to play video content starting from the specific timestamp associated with a mindmap node.

#### Scenario: Navigating from Node to Video
Given a Mindmap Node with a valid video `SourceRef`
When the user clicks the "Play" button on the node
Then the Studio Video Player should load the video (if not loaded)
And the player should seek to the specified timestamp
And the video should start playing automatically

### Requirement: Unified Mixed-Media Handling
The system SHALL support seamless switching between different source types (Video, PDF, Web) within a single project session.

#### Scenario: Switching from PDF to Video
Given the user is currently viewing a PDF document in the source panel
When the user clicks a Mindmap Node associated with a Video
Then the source panel should switch from the PDF Viewer to the Video Player
And the video should be loaded and sought to the correct timestamp
And the PDF state (e.g. current page) should be preserved if possible

#### Scenario: Switching from Video to PDF
Given the user is currently watching a Video
When the user clicks a Mindmap Node associated with a PDF
Then the source panel should switch from the Video Player to the PDF Viewer
And the PDF should open at the specified page

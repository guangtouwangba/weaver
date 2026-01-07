# Change: Add YouTube Video Preview and Playback on Canvas

## Why
When users drag a YouTube video URL onto the canvas, they currently see a generic source node. A rich YouTube-specific preview card with embedded video playback would provide immediate visual recognition and allow users to watch videos without leaving the workspace—similar to how PDF documents can be viewed in the preview modal.

## What Changes
- Add YouTube Video Preview Card as a new canvas node visualization for `type: 'knowledge'` nodes with YouTube-specific metadata
- Card displays: YouTube brand header, video thumbnail with play button overlay, duration badge, title, channel avatar/name, view count, and age
- **Sidebar Video Preview**: Click YouTube item in Resource Sidebar opens video preview panel with embedded YouTube player
- **Canvas Video Playback**: Click play button on canvas card opens embedded YouTube player modal
- Support for dragging YouTube URL items from Resource Sidebar onto canvas
- Consistent styling with existing SourcePreviewCard pattern but YouTube-branded

## Impact
- Affected specs: `studio` (MODIFIED - add YouTube preview card rendering and video playback)
- Affected code:
  - Frontend: `KonvaCanvas.tsx` - add `YouTubePreviewCard` Konva component
  - Frontend: `ResourceSidebar.tsx` - update drag data and click handler for URL items
  - Frontend: Add `YouTubePlayerModal` component for video playback
  - Frontend: Extend `SourcePanel` or create dedicated video preview panel
  - Frontend: Extend drop handler to create YouTube-typed knowledge nodes


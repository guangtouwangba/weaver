# Add Video Mindmap Navigation

## Summary
Enable users to navigate from mindmap nodes to specific timestamps in source videos (YouTube, Bilibili, etc.) by extracting timestamped transcripts and integrating a video player in the Studio interface.

## Background
Currently, the system extracts plain text transcripts from videos, losing the temporal information. When a mindmap is generated, nodes point back to the "video" generally but cannot jump to the specific moment where the concept is discussed. This feature adds high-precision "Source-to-Video" navigation, enhancing the "Visual Thinking Assistant" experience.

## Problem
1. **Loss of Context**: Transcripts are flattened to text; users can't verify or dive deeper into a specific point in a long video.
2. **Disconnected UX**: Users have to manually scrub the video to find where a concept was mentioned.

## Solution
1. **Backend**: 
   - Update `YouTubeExtractor` (and others) to format transcripts with timestamps (e.g., `[00:15] ...`).
   - Update `MindmapGraph` prompts to extract these timestamps into `SourceRef.location` (in seconds).
2. **Frontend**: 
   - **Unified Source Manager**: Implement a "Source Switcher" in the Studio that dynamically renders `PDFViewer`, `VideoPlayer` (new), or `WebReader` based on the active node's `sourceType`.
   - **Video Player**: Integrate `react-player` for video playback with `seekTo` capability.
   - **Interaction**: Wire `onOpenSource` events from `MindMapNode` and `SourceContextPanel` to update the global `activeSource` state, triggering a view switch.

## Risks
- **Transcript Length**: Adding timestamps increases token count. We may need to optimize the format.
- **Mixed Content State**: Switching between PDF and Video frequently might lose state (e.g., scroll position) if not handled carefully.
- **Player Compatibility**: Some video platforms (like Bilibili) might have restrictive embedding policies.

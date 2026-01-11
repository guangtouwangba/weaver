# Add Video Mindmap Navigation

## Summary
Enable users to navigate from mindmap nodes to specific timestamps in source videos (YouTube, Bilibili, etc.) by leveraging existing timestamp extraction and robustly integrating the video player in the Studio interface.

## Background
The backend (`YouTubeExtractor` and `MindmapGraph`) already supports extracting and preserving timestamps (e.g., `[TIME:MM:SS]`). However, the frontend currently fails to play these timestamped videos if the corresponding video node is not explicitly present on the canvas, leading to a disconnected user experience.

## Problem
1.  **Likely Failure**: `KonvaCanvas` currently relies on finding a `CanvasNode` to get video metadata. If the video exists in the project (documents list) but wasn't dragged onto the canvas, clicking "Play Video" does nothing.
2.  **Disconnected UX**: Users expect to jump to the video context regardless of whether the video card is on the board.

## Solution
1.  **Frontend Fix (`KonvaCanvas.tsx`)**:
    -   Update `onOpenSourceRef` handler to look up video metadata in the global project `documents` and `urlContents` list if the `sourceNode` is not found on the canvas.
    -   Ensure the `location` string (format `MM:SS` or `HH:MM:SS`) is correctly parsed into seconds for the `startTime` prop.
2.  **Verification**:
    -   Verify standard YouTube video with timestamps.
    -   Verify Bilibili video support (if applicable).
    -   Verify mixed content (PDF + Video).

## Risks
-   **Resource Lookup**: Need to ensure `KonvaCanvas` has access to the full `documents` list via `useStudio` context (confirmed available).
-   **Timestamp Format**: Relying on LLM for `[TIME:MM:SS]` format might occasionally fail if LLM hallucinates format, but regex extraction is robust.

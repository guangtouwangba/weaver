# Design: Video Mindmap Navigation

## 1. Current Architecture (Backend)

The backend implementation for timestamp extraction is already in place:

1.  **Extraction**: `YouTubeExtractor.py` inserts `[TIME:MM:SS]` markers into the transcript at natural paragraph breaks.
2.  **Generation**: The LLM preserves these markers in the markdown output.
3.  **Parsing**: `MindmapGraph.py` extracts `[TIME:MM:SS]` and populates `MindmapNode.source_refs` with `location="MM:SS"`.

## 2. Missing Piece: Frontend Resource Resolution

The critical gap is in `KonvaCanvas.tsx`. Currently, it attempts to resolve the video source by looking for a **Canvas Node** with a matching ID. However, users often generate mindmaps from documents/videos that are in the project library but **not** dragged onto the canvas.

### Logic Flow (Proposed Fix)

We will modify the `onOpenSourceRef` handler in `KonvaCanvas.tsx` to implement a fallback lookup strategy:

1.  **Try Canvas Nodes**: First, look for a node on the canvas matching `sourceId` (existing behavior).
2.  **Fallback to Project Documents**: If not found, search the `documents` list from `StudioContext`.
3.  **Fallback to URL Contents**: If still not found, search `urlContents` (for direct URL resources).

### Video Metadata Resolution

Once the resource is found (either as a node or a document object), we need to extract:
-   `videoId` (for YouTube/Bilibili embed)
-   `startTime` (parsed from the `location` string "MM:SS")

```typescript
// Proposed logic in onOpenSourceRef
let videoId = sourceNode?.fileMetadata?.videoId;
if (!videoId) {
  // Fallback: look in documents
  const doc = documents.find(d => d.id === sourceId);
  videoId = doc?.metadata?.video_id; // Check metadata structure
}
```

## 3. Timestamp Parsing

The `location` string comes from the backend as `MM:SS` or `HH:MM:SS`. The frontend `KonvaCanvas.tsx` already has logic to split by `:` and calculate seconds. We must ensure this logic is robust to whitespace or variations (e.g. `[TIME:MM:SS]` vs just `MM:SS`).

The regex in `MindmapGraph.py` currently strips the `[TIME:]` prefix, so the frontend receives raw `MM:SS`. The existing parsing logic in `KonvaCanvas` should handle this correctly, provided the `location` string is populated.

## 4. Interaction Design

When a user clicks "Play Video" on a mindmap node:
1.  Frontend resolves the video ID and timestamp.
2.  `YouTubePlayerModal` opens overlaying the studio.
3.  Video starts playing at the calculated seconds.


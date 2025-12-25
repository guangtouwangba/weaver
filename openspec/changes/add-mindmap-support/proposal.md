# Change: Add Mind Map Support

## Why
Users need a structured way to visualize the hierarchy and relationships of concepts within a document. A mind map provides an intuitive "bird's eye view" that complements the linear summary.
The current "Summary" feature is text-heavy. A visual mind map helps in quick comprehension and knowledge structuring.

## What Changes
- **Frontend**:
  - Add `MindMapCard` component for the minimized view in Inspiration Dock or workspace.
  - Add `MindMapFullView` component (likely a modal or expanded canvas state) for detailed exploration.
  - Implement real-time rendering logic using Konva to visualize nodes "growing" as they are streamed from the backend.
- **Backend**:
  - Existing `MindmapAgent` and `MindmapData` structures are leveraged.
  - Ensure API endpoints correctly stream `NODE_ADDED` events for frontend consumption. (Likely already supported by generic output streaming).

## Impact
- **Specs**: `studio` capability will be updated to include Mind Map requirements.
- **Code**:
  - `app/frontend/src/components/studio/` will receive new Mind Map components.
  - `app/frontend/src/hooks/` may need updates to handle specific Mind Map streaming events if generic output hook isn't sufficient.


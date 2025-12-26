# Change: Add Mind Map Interactive Editing

## Why
The current mindmap is read-only after generation. Users want to customize the layout by dragging nodes, make corrections by adding/deleting nodes, and export their work for sharing or archiving. This transforms the mindmap from a static output into an interactive knowledge structuring tool aligned with the "Visual Thinking Assistant" vision.

## What Changes
- **Layout Selection**: Users can switch between different layout styles (Radial, Tree, Balanced) similar to XMind. Radial layout arranges nodes in concentric circles around the root; Tree layout uses hierarchical structure; Balanced layout distributes nodes evenly on both sides.
- **Interactive Canvas**: The mindmap full view becomes an interactive whiteboard where nodes can be dragged to reorganize the layout.
- **Node Editing**: Users can manually add new nodes, delete existing nodes, and edit node labels/content after generation completes.
- **Export/Download**: Users can download the mindmap as an image (PNG) or structured data (JSON) for external use.
- **Performance Optimization**: Ensure smooth rendering for large mindmaps (100+ nodes) via viewport culling, LOD rendering, throttled updates, async layout calculation, and proper memory management. Prevent UI freezing and maintain 30+ fps during interactions.

## Impact
- **Specs**: `studio` capability will be updated with mindmap editing requirements.
- **Code**:
  - `app/frontend/src/components/studio/mindmap/MindMapNode.tsx` - Add draggable behavior, LOD rendering
  - `app/frontend/src/components/studio/mindmap/MindMapViews.tsx` - Add editing toolbar, state management, export
  - `app/frontend/src/components/studio/mindmap/MindMapRenderer.tsx` - Viewport culling, performance optimizations
  - New `MindMapEditor.tsx` component for the interactive editing experience
  - New `mindmapLayoutWorker.ts` for offloading layout calculations
  - Update `MindmapData` state management to track local changes


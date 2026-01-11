# Proposal: Enable Mindmap Node Collapsing

## Goal
Enable users to manage complexity in large mindmaps by collapsing and expanding subtrees. This allows users to focus on specific branches without being overwhelmed by the entire graph.

## Why
As the Research Agent generates increasingly complex mindmaps (often 50+ nodes), it becomes difficult to navigate the canvas. Users need a way to focus on specific branches without being overwhelmed by the entire graph. A collapsing feature is a standard mindmap interaction that allows hierarchical data to be manageable and improves the user experience when working with large mindmaps.

## Background
This feature addresses the scalability issue of mindmap visualization. Without collapsing, users must zoom and pan extensively to navigate large mindmaps, which is inefficient and frustrating.

## What Changes
1. **Backend DTO**: Extended `MindmapNode` dataclass in `output.py` to include optional `collapsed: bool` field with default `False`. The field is serialized/deserialized in `to_dict()` and `from_dict()` methods.
2. **Frontend Node Model**: Extended `MindmapNode` interface in `frontend/src/lib/api.ts` to include optional `collapsed?: boolean`.
3. **MindMapEditor Component**: 
   - Implemented visibility filtering logic using `isNodeVisible` function that recursively checks ancestor collapse state.
   - Added `nodesWithChildren` memoized map to efficiently determine which nodes have children.
   - Filtered `visibleNodes` and `visibleEdges` before rendering.
   - Added `handleToggleCollapse` callback to update node collapse state.
   - Preserved `collapsed` state during external data updates.
4. **RichMindMapNode Component**:
   - Added `hasChildren` and `onToggleCollapse` props.
   - Rendered toggle button (▶/▼) for nodes with children, positioned at right edge, vertically centered.
   - Implemented event handling to prevent drag when clicking toggle button.
5. **Persistence**: The `collapsed` state is preserved in the node data structure and automatically saved when the mindmap is saved.

## Proposed Changes
1.  **Backend DTO**: No formal schema change needed as the `data` field in `Output` is a generic JSON.
2.  **Frontend Node Model**: Extend `MindmapNode` to include an optional `collapsed` boolean.
3.  **MindMapEditor Component**: 
    - Maintain `collapsedNodeIds` in state or within the `data.nodes` objects.
    - Implement a filter to determine visibility of nodes and edges based on ancestor collapse state.
    - Add a toggle handler.
4.  **RichMindMapNode Component**:
    - Detect if a node has children.
    - Render a toggle button (e.g., `+`/`-`) on the right side of nodes with children.
5.  **Persistence**: Ensure the `collapsed` state is saved when the user saves the mindmap.

## User Review Required
- Should the root node be collapsable? (Recommendation: Yes, for consistency).
- Should layout be recalculated when collapsing? (Recommendation: Not for the initial version; just hide nodes to maintain spatial memory. Recalculation is a separate, more complex task).

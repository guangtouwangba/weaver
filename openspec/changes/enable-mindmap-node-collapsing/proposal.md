# Proposal: Enable Mindmap Node Collapsing

## Goal
Enable users to manage complexity in large mindmaps by collapsing and expanding subtrees. This allows users to focus on specific branches without being overwhelmed by the entire graph.

## Background
As the Research Agent generates increasingly complex mindmaps (often 50+ nodes), it becomes difficult to navigate the canvas. A collapsing feature is a standard mindmap interaction that allows hierarchical data to be manageable.

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

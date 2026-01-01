# Proposal: Prevent Mind Map Node Overlap

## Goal
Improve the Mind Map editing experience by automatically resolving node overlaps after dragging or editing, ensuring a clean and readable layout similar to tools like XMind.

## Context
Currently, dragging a node to a new location can result in it overlapping with existing nodes. The existing `applyLayout` function recalculates the entire tree from scratch, which destroys the user's manual adjustments. We need a "soft" layout adjustment that respects the user's placement while preventing collisions.

## Proposed Solution
Implement an **Incremental Overlap Removal** strategy.

1.  **Trigger**: When a node is dragged and released (`handleNodeDragEnd`).
2.  **Algorithm**:
    -   Identify the "Moved Node".
    -   Find all other nodes that intersect with the Moved Node (with some padding).
    -   For each intersecting node (Collision):
        -   Calculate a "push vector" to move the Collision Node away from the Moved Node.
        -   Apply the push to the Collision Node.
        -   **Cascade**: If the Collision Node has children, recursively move its entire subtree by the same delta vector to preserve the branch structure.
        -   **Iterate**: Repeat the collision check for the moved Collision Node (optional, or limit depth).

## Scope
-   **Frontend Only**: Modifying `MindMapEditor.tsx` and adding a helper in `layoutAlgorithms.ts`.
-   **No Backend Changes**: Data persistence is already handled by the previous feature.

## User Experience
-   User drags Node A onto Node B.
-   On release, Node B (and its children) gently slides away to make room for Node A.
-   The rest of the graph remains untouched.

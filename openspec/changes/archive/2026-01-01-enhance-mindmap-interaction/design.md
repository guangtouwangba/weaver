# Design: Enhance Mind Map Interaction

## 1. State Management

### Selection State
-   **Current**: `selectedNodeId: string | null`
-   **New**: `selectedNodeIds: Set<string>`
-   **API**:
    -   `toggleSelection(id: string)`
    -   `select(id: string, clearOthers: boolean)`
    -   `clearSelection()`

### History Management (Undo/Redo)
-   Implement a `useHistory<T>` hook.
-   **State**: `past: T[]`, `present: T`, `future: T[]`.
-   **Actions**: `undo()`, `redo()`, `push(newState)`.
-   **Integration**: Wrap `data` in `useHistory`. `setHasChanges` triggers when pushing to history.

## 2. Interaction Logic

### Keyboard Handling
-   Use a global `keydown` listener attached to the `window` or the specific container (if focusable).
-   **Context Awareness**: Shortcuts only active when:
    -   Editor is mounted.
    -   No modal/dialog is open.
    -   Not editing text (except `Enter`/`Tab` handling inside text input might differ).

### Rubber-band Selection
-   **State**: `selectionBox: { startX, startY, endX, endY } | null`.
-   **Logic**:
    -   `onMouseDown` on Stage (bg): Start selection box.
    -   `onMouseMove`: Update end coordinates.
    -   `onMouseUp`: Calculate intersection between selection box and all nodes. Update `selectedNodeIds`.

### Multi-Node Dragging
-   **Logic**:
    -   When dragging starts (`handleDragStart` on Node), record `startPos` for all selected nodes.
    -   On `dragMove` (or custom throttled update), apply `delta` to all selected nodes.
    -   **Constraint**: If dragging a node that is NOT in the current selection, usually it should select THAT node exclusively first (unless modifier key held). Standard behavior:
        -   Drag selected node -> Move all selected.
        -   Drag unselected node -> Select only it, then move it.

## 3. Component Updates
-   **RichMindMapNode**:
    -   Update `isSelected` prop logic.
    -   Update `onClick` to pass `MouseEvent` for modifier check.
-   **MindMapEditor**:
    -   Major state refactor.
    -   Add `<SelectionRect>` (Konva Rect) to Layer.

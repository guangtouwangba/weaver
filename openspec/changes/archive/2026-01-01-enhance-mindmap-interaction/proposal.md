# Proposal: Enhance Mind Map Interaction

## Goal
Bring the Mind Map editor experience closer to professional tools like XMind by implementing core keyboard shortcuts and multi-selection capabilities. This will significantly improve user efficiency and usability.

## Context
Currently, the mind map editor is mouse-centric and only supports single-node selection. Users cannot perform common bulk actions or valid keyboard operations (like Tab to add child, Enter to add sibling), which are standard expectations for mind mapping software.

## Proposed Changes

### 1. Core Keyboard Shortcuts
Implement a centralized keyboard event handler to support:
-   **Tab**: Add child node.
-   **Enter**: Add sibling node.
-   **Backspace/Delete**: Delete selected node(s).
-   **Space**: Edit selected node label.
-   **Arrow Keys**: Navigate selection (Up/Down/Left/Right).
-   **Cmd+Z / Shift+Cmd+Z**: Undo / Redo.

### 2. Multi-Selection
-   Upgrade selection state from `string | null` to `Set<string>`.
-   Support `Shift + Click` and `Cmd/Ctrl + Click` to add/toggle selection.
-   Support **Rubber-band selection** (drag on canvas background to select multiple nodes).

### 3. Multi-Node Operations
-   **Bulk Move**: Dragging one selected node moves all selected nodes while maintaining their relative positions.
-   **Bulk Delete**: Deleting one deletes all selected.

## Technical Impact
-   **State Management**: `MindMapEditor` state needs refactoring to support `selectedNodeIds`.
-   **Event Handling**: `RichMindMapNode` needs to pass click events with modifier key info. `Stage` needs to handle rubber-band selection logic.
-   **Undo/Redo**: Introduce a `useHistory` hook to track `data` state changes.

# Proposal: Improve Studio UX

## Background
A design review identified significant UX/UI issues in the Studio interface, including consistency gaps with the Dashboard (e.g., identity confusion, navigation shifts) and interaction flaws (e.g., dangerous delete button, toolbar grouping).

## Why
The current Studio interface suffers from usability issues that confuse users (project identity, navigation) and risk data loss (accidental deletion). Improving these is critical for a professional, trustworthy user experience.

## Goals
1.  **Restore Context**: Display human-readable project names instead of IDs.
2.  **Unify Identity**: Clean up redundant avatars and navigation modes.
3.  **Safe Interaction**: Reposition the "Delete" action to prevent accidental data loss.
4.  **Optimize Layout**: Reorganize toolbars and panels to maximize workspace.

## What Changes

### 1. Header & Navigation (Consistency)
-   **Project Context**: Replace `Project {uuid}` with the actual Project Name (fetched from context/API).
-   **Back Navigation**: Add a clear "Back to Dashboard" tooltip/label to the back arrow.
-   **Identity**: Remove the duplicate avatar from the header since it's already in the global sidebar (if present) or strictly follow the "User Menu" pattern in the top-right.

### 2. Interaction Safety
-   **Delete Button**: Remove the floating "Trash Can" FAB from the bottom-right. Move "Delete" to the context menu (right-click on node) or a dedicated "Edit" menu in the toolbar.
-   **Shortcuts**: Ensure `Delete`/`Backspace` keys work for selection (already implemented, just needs visual backup).

### 3. Toolbar Refactoring
-   **Grouping**: Separate "Tools" (Select, Hand) from "View Controls" (Zoom, Fit).
-   **Position**: Move Tools to a top-center or left-floating bar. Keep Zoom in bottom-right.

### 4. Layout Optimization
-   **Resource Panel**: Collapse by default or use a Drawer pattern to free up startup space.

## Risks
-   **Context Fetching**: Need to ensure Project Name is available in the `StudioContext` or fetched efficiently.

# Change: Redesign Studio Layout

## Why
The current studio layout is cluttered and does not prioritize the whiteboard as the primary workspace. A redesign is needed to create a cleaner, more immersive experience where the canvas is the "main battlefield". This involves streamlining the sidebar, enhancing the canvas, and introducing floating controls for better usability.

## What Changes
-   **Layout**: Move to a full-screen canvas layout with a dedicated left sidebar for resources.
-   **Sidebar**: Redesign `SourcePanel` into `ResourceSidebar` with drag-and-drop support and a cleaner list view.
-   **Canvas**: Make `KonvaCanvas` the central component with infinite grid and high-performance rendering.
-   **Controls**: Introduce floating controls for chat, canvas navigation, and contextual actions.
-   **Header**: Simplify the project header.

## Impact
-   **Affected Specs**: `studio`
-   **Affected Code**:
    -   `app/frontend/src/app/studio/[projectId]/page.tsx`
    -   `app/frontend/src/components/studio/SourcePanel.tsx`
    -   `app/frontend/src/components/studio/CanvasPanel.tsx`
    -   `app/frontend/src/components/studio/KonvaCanvas.tsx`
    -   New components in `app/frontend/src/components/studio/`


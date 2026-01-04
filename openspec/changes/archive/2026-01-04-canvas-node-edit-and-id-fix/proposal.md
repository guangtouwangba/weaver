# Proposal: Canvas Node Editing & ID Fix

## Goal
To ensure data integrity by fixing potential node ID collisions and to improve usability by allowing users to edit the content of canvas nodes.

## Context
- **ID Collisions**: Currently, node IDs are generated using `Date.now()`, which can lead to duplicates if nodes are created in rapid succession. Users have reported nodes sharing IDs.
- **Editing**: Users currently cannot edit the title or content of nodes on the canvas. Double-clicking is reserved for opening source documents (PDFs), leaving no way to modify created nodes.

## What Changes
1.  **Unique ID Generation**:
    - Replace the current `Date.now()` based ID generation with `crypto.randomUUID()` (UUID v4) to guarantee uniqueness.
    - Affected file: `app/frontend/src/contexts/StudioContext.tsx` and any other ad-hoc creation points.

2.  **Node Editing UI**:
    - Implement an "Edit" mode for nodes.
    - **Interaction**:
        - For **Text/Sticky Nodes**: Double-click to edit.
        - For **Source/PDF Nodes**: Double-click opens the file (existing behavior). Add an "Edit" option to the Context Menu to modify the title/notes without opening the file.
    - **Visuals**:
        - Display a highly visible HTML overlay (TextArea) over the node when editing.
        - Support editing both Title and Content.

## Value
- **Reliability**: Eliminates weird bugs caused by duplicate IDs (e.g., deleting one node deletes another).
- **Usability**: Essential feature for a mind-map/canvas tool. Users need to refine their thoughts.

## Risks
- **Event Handling**: Need to carefully manage click vs. double-click vs. drag events to avoid accidental edits or navigation.
- **Performance**: HTML overlays on top of Canvas need to be positioned correctly and transparent to unexpected events.

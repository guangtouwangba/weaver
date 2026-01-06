# Refine Note Interaction

## Goal
Improve the user experience for adding and editing notes by introducing a clear distinction between the "Note Card" (the canvas representation) and the "Note Page" (the focused content editor). This ensures users have a dedicated space for rich content creation while maintaining a digestible canvas overview.

## Context
Currently, notes are treated as simple canvas nodes or "sticky notes," often limited in size and editing capability. Users struggle to add substantial content or organize their thoughts effectively within the constraints of a small canvas card.

## Key Changes
1.  **Note Card (Canvas View):**
    - A lightweight, summary representation of the note on the whiteboard.
    - Displays title, snippet/preview, and meta-data (tags, colors).
    - Optimized for moving, grouping, and linking (standard node behaviors).
2.  **Note Page (Detail View):**
    - A focused, full-screen or large modal interface for content editing.
    - Supports rich text/markdown, checklists, and longer-form writing.
    - Triggered by double-clicking a Note Card or creating a new note.
3.  **Creation Flow:**
    - "Add Note" action immediately opens the Note Page for initial content entry.
    - Saving the page generates the Note Card on the canvas.

## User Review Required
- **Visual Transition:** How does the UI transition from Card to Page? (Zoom-in, modal overlay, or side panel?) *Proposal: Modal or Side Panel for stability.*
- **Content Sync:** Updates in the Page view must immediately reflect in the Card preview.

## Impact
- **Specs Changed:** `specs/studio/spec.md`
- **Code Changed:** `Canvas.tsx`, `NoteNode.tsx`, new `NoteEditor.tsx`.

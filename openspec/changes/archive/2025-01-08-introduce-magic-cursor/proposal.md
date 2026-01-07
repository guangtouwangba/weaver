# Introduce Magic Cursor

## Goal
Introduce a specialized "Magic Cursor" tool to the Studio whiteboard that explicitly signals AI intent, streamlines content generation via area selection, and produces distinct "Super Cards" (Document and Ticket types) that serve as finished result containers.

## Context
Currently, the whiteboard lacks a dedicated mode for AI operations, relying on generic selection or context menus. The "Magic Cursor" solves this by:
1.  **Explicit Intent:** Switching to this tool signals "I want AI to work."
2.  **Efficient Interaction:** Area selection provides immediate context for generation.
3.  **Refined Output:** Generates polished "Super Cards" distinct from raw notes.

## Key Changes
1.  **Magic Cursor Tool:**
    - New toolbar item (Sparkle icon).
    - Custom cursor styling (sparkles/colors).
    - "Flowing gradient" visual for selection box.
2.  **Auto-Floating Intent Menu:**
    - Appears immediately on mouse release (no right-click needed).
    - Options: "Draft Article", "Action List".
3.  **Super Cards (Result Containers):**
    - **Document Card:** A4-like style, header/footer, Export PDF, bi-directional linking.
    - **Ticket Card:** Receipt/Work order style, torn edges, interactive checkboxes, calendar/todoist sync.
    - **Snapshot Context:** "Refresh" button to re-scan the original selection area for new content.

## User Review Required
- **Visual Design:** The "flowing gradient" selection and "Super Card" styles will need close coordination with the design system (Tailwind/CSS).
- **Backend implications:** The "Snapshot Context" requires storing the selection coordinates and re-querying the spatial index upon refresh.



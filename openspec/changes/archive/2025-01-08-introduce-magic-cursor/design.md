# Magic Cursor Design

## Architectural Overview
The Magic Cursor is a client-side interaction mode that triggers standard backend generation flows but presents them through a specialized UI. It introduces a permanent "Snapshot Context" concept where the input scope (area) is preserved for future regeneration.

## User Interface Design

### 1. Tool Activation
- **Toolbar:** Add "Magic Cursor" (Sparkle Icon) to the main toolbar.
- **Cursor State:** When active, cursor changes to `cursor-magic` (custom CSS cursor with sparkle).

### 2. Selection Interaction through `MagicSelectionLayer`
- **Visuals:** Unlike standard blue selection, this uses a customized `SelectionOverlay`.
    - Border: Animated gradient (flowing colors).
    - Fill: Subtle iridescent wash.
- **Micro-interactions:**
    - `MouseDown`: Start tracing.
    - `MouseUp`: Freeze selection area, calculate intersection, spawn Intent Menu.

### 3. Intent Menu (Auto-Floating)
- **Position:** Bottom-right corner of the selection box.
- **Behavior:** Fade in on `MouseUp`. Dismiss on click outside or tool switch.
- **Items:**
    - `Draft Article` -> Triggers `generate_document` capability.
    - `Action List` -> Triggers `generate_mindmap` (or new `generate_actions`) capability.

### 4. Super Cards (New Node Subtypes)

#### A. Document Card (`ResultCard` variant)
- **Visual:** White background, drop shadow `xl`, explicit header/footer separation.
- **Interactions:**
    - `Hover`: Highlights linked source nodes on canvas (via `graph-store` lookups).
    - `Refresh`: Re-sends the query using the original `box_coordinates` to find current nodes.

#### B. Ticket Card (`ResultCard` variant)
- **Visual:** Light yellow/grey background, CSS `clip-path` for "jagged/torn" bottom edge.
- **Interactions:**
    - `Checkbox`: Interactive state toggle.
    - `Action Buttons`: External link stubs (Calendar, Todoist).

## Data Model Changes

### 1. Canvas Node Schema
- New Node Types or Subtypes:
    - type: `super-card`
    - subtype: `document` | `ticket`
- Metadata Extension:
    - `snapshot_context`: `{ x, y, w, h }` (The original selection box).
    - `generated_from`: `[node_ids]` (List of source IDs for linking).

## Technical Implementation Steps
1.  **Frontend (Studio):**
    - Update `CanvasTool` state machine to include `MAGIC_CURSOR`.
    - Implement `MagicSelectionBox` component.
    - Create `IntentMenu` component.
    - Implement `DocumentCard` and `TicketCard` React components.
2.  **Backend (API):**
    - Ensure generation endpoints accept `selection_bounds` to allow re-querying via spatial index (already supported ideally, or needs verification).

## Questions / Open Items
- **Persistence:** Does the "Snapshot Context" box remain visible? *Decision: No, it's invisible until "Refresh" is hovered or clicked (TBD).*
- **Refresh Logic:** Does refresh strictly use the *same box* or the *same nodes*? *Proposal says "re-scan the box", implying spatial query.*



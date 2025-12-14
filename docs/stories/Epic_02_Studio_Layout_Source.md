# Epic 02: Studio Framework & Source Management

**Goal**: Establish the fluid 3-column workspace and enable consumption of heterogeneous sources (PDF, Media).

---

## Feature: Global Layout

### Story 2.1: Fluid Column Resizing
**As a** User,
**I want** to seamlessly adjust the width of my workspace columns,
**So that** I can prioritize reading, processing, or writing space.

*   **Acceptance Criteria**:
    *   [ ] **Left Resize Handle**: Located between Source (Left) and Assistant (Center).
    *   [ ] **Right Resize Handle**: Located between Assistant (Center) and Canvas (Right).
    *   [ ] **Visuals**: Handles are 4px wide transparent zones (`z-index: 50`) that turn `primary.main` on active/hover (or just cursor change).
    *   [ ] **Behavior**:
        *   Dragging updates width state in real-time (no ghost dragging).
        *   Disables text selection (`userSelect: none`) on the body during drag.
        *   Cursor force-set to `col-resize` globally during drag.
    *   [ ] **Constraints**: Widths clamped between 280px (min) and 800px (max).

### Story 2.2: Source Column Collapsing (Left)
**As a** User,
**I want** to minimize the file browser to focus on the canvas,
**So that** I have more screen real estate.

*   **Acceptance Criteria**:
    *   [ ] **Toggle Action**:
        *   Keyboard: `Cmd + \`.
        *   UI: "Close Panel" icon button in the column header.
    *   [ ] **Collapsed State UI**:
        *   Width shrinks to fixed 48px.
        *   Displays a single **Active Resource Icon** (PDF/Video/Audio/Link) vertically centered or at top.
        *   **Tooltip**: Hovering the collapsed strip shows the Resource Title and "Expand (Cmd+\)".
    *   [ ] **Interaction**: Clicking the collapsed strip/icon restores previous width.

### Story 2.3: Assistant Column Collapsing (Center)
**As a** User,
**I want** to hide the AI assistant when not needed,
**So that** I can work without distractions.

*   **Acceptance Criteria**:
    *   [ ] **Toggle Action**:
        *   Keyboard: `Cmd + .`.
        *   UI: "Close Panel" icon button in the column header.
    *   [ ] **Collapsed State UI**:
        *   Width shrinks to fixed 40px (narrower than left).
        *   Displays a **Bot Icon**.
        *   **Status Indicator**: Shows a green badge (dot) if Assistant is "Ready", hidden if "Quiet Mode" is on.
    *   [ ] **Interaction**: Clicking the collapsed strip/icon restores previous width.

---

## Feature: Source Browser & Reader (Left Column)

### Story 2.4: Dynamic Split View (Browser vs. Reader)
**As a** User,
**I want** to resize the split between my file list and the document viewer,
**So that** I can manage my viewing context.

*   **Acceptance Criteria**:
    *   [ ] **Vertical Handle**: Located between File Browser (top) and Reader (bottom).
    *   [ ] **Behavior**: Dragging adjusts `splitRatio` (height percentage).
    *   [ ] **Min/Max**: Clamped between 20% and 80%.

### Story 2.5: Reader Maximization
**As a** User,
**I want** to read a document full-height within the column,
**So that** I can see more text at once.

*   **Acceptance Criteria**:
    *   [ ] **Toggle**: "Maximize/Minimize" icon button in the Reader Header.
    *   [ ] **Expanded State**:
        *   File Browser height becomes 0 (hidden).
        *   Reader takes 100% height (minus header).
        *   Split drag handle is disabled/hidden.
    *   [ ] **Restored State**: Returns to previous `splitRatio`.

### Story 2.6: Multimedia Reader (Video/Audio)
**As a** Learner,
**I want** to see the transcript alongside the video player,
**So that** I can read what is being said.

*   **Acceptance Criteria**:
    *   [ ] **Layout**: Player area (Top 45%) + Transcript area (Bottom 55%).
    *   [ ] **Transcript**:
        *   Scrollable list of timestamped lines.
        *   Current line highlighted (visual cue).
        *   Lines are draggable (Drag & Drop to Canvas).
    *   [ ] **Controls**: Standard play/pause/seek controls in the player area.

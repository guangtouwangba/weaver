# Epic 03: Studio Output OS & Canvas

**Goal**: Enable users to synthesize knowledge on an infinite whiteboard, managed within a multi-tab operating system.

---

## Feature: Output OS (Tab System)

### Story 3.0: Tab Management
**As a** Multi-tasking User,
**I want** to open multiple views (Canvas, Podcast, Writer) in tabs,
**So that** I can work on different outputs without losing context.

*   **Acceptance Criteria**:
    *   [ ] **Tab Bar**: Displayed at the top of the Right Column.
    *   [ ] **Create**: Clicking "+" opens a Launcher Menu to add new tabs.
    *   [ ] **Switch**: Clicking a tab switches the active view immediately.
    *   [ ] **Close**: Clicking "x" on a tab closes it.
    *   [ ] **Persistence**: Switching away from a Canvas tab and back preserves the viewport and node positions exactly.
    *   [ ] **Default State**: At least one "Canvas" tab is always present (auto-create if last one closed).

### Story 3.1: Capability Launcher
**As a** User,
**I want** to choose what kind of output to create,
**So that** I can pick the right tool for the job.

*   **Acceptance Criteria**:
    *   [ ] Clicking the "+" button shows a dropdown menu.
    *   [ ] **Create New**: Options for "Canvas" and "Writer" (instant open).
    *   [ ] **Generate with AI**: Options for "Podcast", "Flashcards", "Slides" (starts in 'generating' state).

---

## Feature: Canvas Navigation

### Story 3.2: Infinite Pan & Zoom
**As a** Visual Thinker,
**I want** to pan around an infinite space and zoom in/out,
**So that** I can manage large knowledge graphs.

*   **Acceptance Criteria**:
    *   [ ] **Pan**: Hold `Space` + Drag Mouse moves the viewport.
    *   [ ] **Zoom**: `Ctrl/Cmd` + Wheel zooms focused on the cursor position.
    *   [ ] **Grid**: Background dot grid scales visually with zoom level.
    *   [ ] Cursor changes to `grab`/`grabbing` appropriately.

---

## Feature: Node Management

### Story 3.3: Create Card from PDF (Right Click)
**As a** Reader,
**I want** to select text in a PDF and turn it into a card,
**So that** I can save important excerpts.

*   **Acceptance Criteria**:
    *   [ ] Selecting text in the PDF reader shows a custom context menu.
    *   [ ] Clicking "Create as Card" adds a new node to the center of the current viewport.

### Story 3.4: Drag & Drop from Source (PDF/Media)
**As a** User,
**I want** to drag highlighted text or transcript lines directly to the canvas,
**So that** I can intuitively organize information.

*   **Acceptance Criteria**:
    *   [ ] **Draggable**: PDF highlights and Transcript lines are draggable.
    *   [ ] **Drop Zone**: A visual "Drop [type] from..." indicator appears at the bottom of the canvas during drag.
    *   [ ] **Drop Logic**: Dropping creates a card at the exact mouse position (converted to canvas coordinates).
    *   [ ] **Metadata**:
        *   Video/Audio drops include a "Play" chip with the timestamp.
        *   PDF drops include the source citation.

### Story 3.5: Node Manipulation
**As a** User,
**I want** to move, select, and delete cards,
**So that** I can organize my thoughts.

*   **Acceptance Criteria**:
    *   [ ] **Drag**: Dragging a card moves it. (Must implement threshold to prevent accidental moves on click).
    *   [ ] **Select**: Clicking a card adds a blue border.
    *   [ ] **Delete**: Selected card shows a red `×` button. Clicking it removes the card. `Delete` key also works.

---

## Feature: Connections

### Story 3.6: Create Connections (Handles)
**As a** User,
**I want** to draw lines between related cards,
**So that** I can build a knowledge graph.

*   **Acceptance Criteria**:
    *   [ ] Hovering a card reveals a Blue Handle on the right.
    *   [ ] Dragging from the handle draws a dashed temporary line.
    *   [ ] Hovering a target card shows a Green Receiver Handle.
    *   [ ] Releasing on the target creates a permanent curved line.

### Story 3.7: Manage Connections
**As a** User,
**I want** to delete incorrect connections,
**So that** my graph remains accurate.

*   **Acceptance Criteria**:
    *   [ ] Clicking a connection line selects it (turns red).
    *   [ ] Selected line shows a red `×` button at the midpoint.
    *   [ ] Clicking the `×` or pressing `Delete` removes the connection.

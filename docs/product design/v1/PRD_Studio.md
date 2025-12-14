# PRD: Deep Work Studio (Core Workbench)

| Document Info | Details |
| --- | --- |
| **Version** | v3.1 (Canvas-First Implementation) |
| **Status** | Implemented / Live |
| **Scope** | Studio Page (`/studio`) |

---

## 1. Overview
The **Deep Work Studio** is the central workbench for the Research Agent. It follows an strict **Input → Processor → Output** data flow architecture, allowing users to ingest heterogeneous sources (PDF, Audio, Video), process them via AI, and synthesize them into structured knowledge on an infinite canvas.

## 2. Layout Architecture
The page uses a **3-Column Fluid Layout** with adjustable widths.

### 2.1 Left Column: The Source (Input)
*   **Function**: Browser for raw materials and content consumption.
*   **Width**: Resizable (280px - 800px). Collapsible (`Cmd+\`).
*   **States**:
    *   **Browser Mode**: Displays file tree (Papers, Media, Links).
    *   **Reader Mode**: Split view with Browser (top) and Content Viewer (bottom).
    *   **Collapsed**: Shows a thin strip (48px) with a dynamic icon representing the active resource type.
*   **Key Interaction**: Dragging the handle between Browser and Reader adjusts the split ratio.

### 2.2 Center Column: The Processor (Assistant)
*   **Function**: AI reasoning, bridging connections, and quick command input.
*   **Width**: Resizable. Collapsible (`Cmd+.`).
*   **Components**:
    *   **Feed**: A scrollable list of AI insights (Concepts, Link Detections).
    *   **Input**: A text field for natural language commands ("Summarize this", "Find connections").
    *   **Quiet Mode**: A filter toggle that hides non-essential AI notifications to reduce cognitive load.
*   **Collapsed State**: Displays a generic "Bot" icon with a status badge (green dot).

### 2.3 Right Column: The Output OS
*   **Function**: The synthesis destination. A tabbed operating system for creating content.
*   **Tabs System**:
    *   Supports multiple active views: `Canvas` (default), `Podcast`, `Flashcards`, `Slides`, `Writer`.
    *   **Launcher**: A "+" button opens a menu to "Create New" or "Generate with AI".
    *   **Persistence**: At least one canvas tab is always maintained.

---

## 3. Feature Specifications: The Infinite Canvas
The Canvas is the default and primary output surface.

### 3.1 Viewport & Navigation
*   **Infinite Pan/Zoom**:
    *   **Pan**: Hold `Space` + Drag, or Middle Mouse Click.
    *   **Zoom**: `Ctrl/Cmd` + Mouse Wheel (zooms toward cursor).
*   **Grid**: A generated dot grid (`radial-gradient`) that scales with the viewport `scale` to provide spatial reference.

### 3.2 Node System
*   **Node Structure**:
    *   `id`, `title`, `content`, `x`, `y`, `type` (card/group).
    *   **Metadata**: `timestamp` (for media), `sourceId` (for back-linking).
*   **Interaction**:
    *   **Selection**: Click to select (blue border). Click background to deselect.
    *   **Drag**: 3px movement threshold prevents accidental moves during selection.
    *   **Delete**: Selected node shows a floating red `×` button. `Delete`/`Backspace` key also works.

### 3.3 Connection System
*   **Creation Flow**:
    1.  Hover over any node → Blue **Connection Handle** appears on the right.
    2.  Drag from handle → A dashed temporary line follows the cursor.
    3.  Hover target node → Target shows a pulsing green "Receiver Handle".
    4.  Release → Connection created (SVG Bézier curve).
*   **Management**:
    *   **Selection**: Click directly on a line to select it (turns red).
    *   **Deletion**: Selected line shows a centered red `×` button.

### 3.4 Canvas Copilot (Magic Tools)
*   **Access**: A floating action button (Sparkles icon) in the bottom-right.
*   **UI**: A translucent glass-morphism panel.
*   **Features**:
    *   **Quick Actions**: Chips for "Auto Layout", "Connect", "Summarize".
    *   **Command Input**: Text field for natural language editing of the canvas.
*   **Philosophy**: No chat history. Execute and dismiss.

---

## 4. Feature Specifications: Multimedia Integration

### 4.1 PDF Reader
*   **Interaction**:
    *   Select text to highlight.
    *   **Right-Click Menu**: "Create as Card" (adds to canvas center).
    *   **Drag & Drop**: Drag highlighted text directly to the canvas.
*   **Visual Feedback**: While dragging, a "Drop Zone" pill appears at the bottom of the canvas ("Drop text from PDF").

### 4.2 Video/Audio Player
*   **Layout**: Split view. Top = Player Controls; Bottom = Interactive Transcript.
*   **Transcript Interaction**:
    *   **Time-sync**: Clicking a timestamp seeks the player.
    *   **Drag & Drop**: Dragging a transcript line creates a special **Timestamped Card** on the canvas.
*   **Data Payload**: Dropped cards retain `timestamp` and `sourceId`, displaying a "Play" chip on the canvas card.

---

## 5. Technical Constraints & State Management
*   **Event Propagation**: Strict management of `stopPropagation` to distinguish between Panning (Canvas), Dragging (Node), and Connecting (Handle).
*   **Performance**: `requestAnimationFrame` used for updating temporary connection lines during mouse moves.
*   **SVG Layer**: `pointer-events: visiblePainted` ensures lines are clickable but the SVG container doesn't block canvas panning.



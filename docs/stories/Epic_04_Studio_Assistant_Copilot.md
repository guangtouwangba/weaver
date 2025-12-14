# Epic 04: Assistant & Copilot Tools

**Goal**: Provide AI assistance both for processing source material (Center Column) and operating the canvas (Copilot).

---

## Feature: Center Assistant (The Processor)

### Story 4.1: Assistant Feed & Input
**As a** User,
**I want** a dedicated space to converse with AI about my documents,
**So that** I can get help understanding complex topics.

*   **Acceptance Criteria**:
    *   [ ] **Feed**: Displays a vertical list of AI insights (Concepts, Link Detections).
    *   [ ] **Input**: A persistent text field at the bottom ("Ask or summarize...").
    *   [ ] **Link Detection**: Special cards ("Link Detected") allow merging related concepts.

### Story 4.2: Quiet Mode
**As a** Focused User,
**I want** to hide proactive AI suggestions,
**So that** I can focus on reading without distraction.

*   **Acceptance Criteria**:
    *   [ ] Toggle button in the header ("Quiet Mode").
    *   [ ] When ON: Hides proactive feed items, shows a "Focus Mode On" banner.
    *   [ ] Status Icon (Bot) in the header updates to reflect state.

---

## Feature: Canvas Copilot (Magic Tools)

### Story 4.3: Copilot Launcher & UI
**As a** User,
**I want** a toolbox on the canvas,
**So that** I can perform bulk actions without leaving the visual context.

*   **Acceptance Criteria**:
    *   [ ] **Launcher**: Floating Action Button (Sparkles icon) fixed at bottom-right.
    *   [ ] **Toggle**: Clicking Launcher toggles icon to "Close" (X) and opens the panel.
    *   [ ] **Panel UI**:
        *   Translucent glass-morphism background.
        *   Title: "CANVAS COPILOT" (all caps, small font).
        *   Content: Quick Action Chips (e.g., Auto Layout, Connect, Summarize) + Command Input.
    *   [ ] **Input Field**: Includes a "Wand" icon and an "Arrow" submit button.

### Story 4.4: Copilot Interactions (Mock)
**As a** User,
**I want** to issue commands like "Summarize" or "Connect",
**So that** I can automate tedious canvas tasks.

*   **Acceptance Criteria**:
    *   [ ] **Chip Action**: Clicking a chip (e.g., "Auto Layout") triggers the action (console log) and auto-closes the panel.
    *   [ ] **Text Command**: Typing a command and pressing Enter triggers the action and auto-closes the panel.
    *   [ ] **No History**: The panel is a "Command Palette", not a chat window. It resets on every open.

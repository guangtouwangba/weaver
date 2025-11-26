# Epic 01: Onboarding & Triage (Dashboard & Inbox)

**Goal**: Provide a clear entry point for users to start new work and triage incoming raw materials before deep processing.

---

## Feature: Dashboard (Home)

### Story 1.1: Project Quick Start
**As a** Researcher,
**I want** a clear "Drop Zone" on the dashboard where I can drag files,
**So that** I can immediately start a new project without navigating menus.

*   **Acceptance Criteria**:
    *   [ ] Display a large, dashed-border drop zone area on `/dashboard`.
    *   [ ] Visual feedback (border color change) when dragging files over the zone.
    *   [ ] "Create Project" button is clickable (even if backend is mock).
    *   [ ] Clicking "Inbox" link navigates to `/inbox`.

### Story 1.2: Recent Projects Overview
**As a** User,
**I want** to see my most recently edited projects,
**So that** I can quickly resume my work.

*   **Acceptance Criteria**:
    *   [ ] Display a responsive grid of project cards.
    *   [ ] Each card shows: Project Title, "Last edited" timestamp.
    *   [ ] Hovering a card highlights the border (`primary.main`).
    *   [ ] Clicking a card navigates to `/studio/[id]`.

---

## Feature: Inbox (Triage)

### Story 1.3: Quick Capture
**As a** User,
**I want** a simple text input in the Inbox,
**So that** I can dump thoughts or URLs immediately.

*   **Acceptance Criteria**:
    *   [ ] Input field is always visible at the top of the Left Column.
    *   [ ] Pressing "Enter" or clicking "+" adds a new item to the local list state.
    *   [ ] The new item appears immediately at the top of the list.

### Story 1.4: Triage & Process Flow
**As a** User,
**I want** to review items one by one and decide where they go,
**So that** I can keep my inbox clean (Inbox Zero).

*   **Acceptance Criteria**:
    *   [ ] **Selection**: Clicking an item on the left displays its details on the right.
    *   [ ] **AI Suggestion**: The right panel shows a static AI summary and a "Suggested Project".
    *   [ ] **Move Action**: Clicking "Move to Project" removes the item from the list and auto-selects the next item.
    *   [ ] **Delete Action**: Clicking "Delete" removes the item and auto-selects the next item.
    *   [ ] **Empty State**: When all items are gone, show "Inbox Zero" illustration.


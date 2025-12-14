# Epic 05: Global Knowledge Graph (The Brain)

**Goal**: Visualize cross-project connections to reveal hidden insights.

---

## Feature: Global Graph Visualization

### Story 5.1: Project-Coded Nodes
**As a** User,
**I want** to see concepts from all my projects in one view,
**So that** I can spot thematic overlaps.

*   **Acceptance Criteria**:
    *   [ ] Render a full-screen graph.
    *   [ ] Nodes are colored by their Project source (e.g., Blue=NLP, Green=Biology).
    *   [ ] Nodes display a text label.
    *   [ ] Background uses the same dotted grid as Studio for consistency.

### Story 5.2: Bridge Nodes
**As a** User,
**I want** to easily identify concepts that link two different projects,
**So that** I can find interdisciplinary insights.

*   **Acceptance Criteria**:
    *   [ ] "Bridge Nodes" (connecting >1 project) have a distinct visual style (e.g., glow or unique color).

### Story 5.3: Insight Panel
**As a** User,
**I want** to click a node to see why it matters,
**So that** I can understand the AI's reasoning.

*   **Acceptance Criteria**:
    *   [ ] Clicking a node opens a floating right-side panel.
    *   [ ] Panel shows: Node Label, Project Source, and an AI Insight text block.
    *   [ ] **Action**: "Open Project" button deep-links to the Studio view (placeholder).

### Story 5.4: Global Search & Stats
**As a** User,
**I want** to search for specific concepts across the entire graph,
**So that** I can navigate quickly.

*   **Acceptance Criteria**:
    *   [ ] Floating Search Bar at the top center.
    *   [ ] Stats chips displaying total projects, concepts, and connections.
    *   [ ] Legend at bottom-left explaining color codes.


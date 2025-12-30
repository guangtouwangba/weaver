# Research Agent RAG - Product Roadmap 2025

> **Strategic Goal**: Transition from "Passive Knowledge Tool" to "**Agentic Workbench**".
> **North Star**: Building a "Junior Analyst" that pro-actively collects, connects, and synthesizes information asynchronously.

## Strategic Differentiators
1.  **Proactive Agency (vs. NotebookLM)**
    Your competitors (NotebookLM) act as "Safe Archives"—they only answer questions based on what you upload.
    **Our Moat**: We break the "Closed World" assumption. Our agents autonomously perform **Deep Research** on the open web to verify claims and find missing connections.

2.  **Asymptotic State (vs. YouMind/Notion)**
    Your competitors act as "Editors"—they only change state when you type.
    **Our Moat**: The **"Night Shift"**. Our agents work while you sleep, clustering concepts, identifying contradictions, and preparing synthesis. The Canvas evolves over time.

---

## 🗺️ Roadmap Phases

### Phase 1: The "Research Assistant" (Capture & Structure)
**Objective**: Solve the "Fragmentation" problem. "Capture Everything, Miss Nothing."

- **Unified Ingestion**:
    - [ ] **Chrome Extension**: One-click capture of URL, HTML, and Screenshots to the Inbox.
    - [ ] **Entity Resolution Engine**: Backend service to deduplicate entities (People, Companies) across disparate documents. (Turning a "List" into a "Database").
    - [ ] **Auto-Triage**: Semantic classification of incoming inbox items.
- **Inbox UX**:
    - [ ] Swipe-based triage (Archive vs. Project Assignment).

### Phase 2: The "Thinking Partner" (Agency & connection)
**Objective**: Solve the "Complexity" problem. "See the Unseen Patterns."

- **Spatial Workbench (Canvas)**:
    - [ ] **Auto-Cluster**: "Tidy Up" button that spatially groups related notes based on embedding proximity.
    - [ ] **Agentic Suggestion**: Visual badges on nodes indicating "I found related info on the web".
- **Deep Research Integration**:
    - [ ] **"Find Missing Link"**: Select two disparate nodes -> Agent triggers web search to find the connective tissue.
    - [ ] **The "Conflict Detector"**: Background job that identifies opposing claims between sources and generates "Insight Nodes".
- **UX**:
    - [ ] **Agent Activity Feed**: A notification center showing what the AI did while you were away.

### Phase 3: The "Content Studio" (Synthesis & Impact)
**Objective**: Solve the "Production" problem. "Turn Thoughts into Deliverables."

- **Grounded Writer**:
    - [ ] **Canvas-to-Outline**: Generate a structured outline based on spatial grouping.
    - [ ] **Active Citation**: Drag a node into the editor to insert a cited block.
    - [ ] **Bi-Directional Highlighting**: Click a sentence in the draft to zoom to the source node on the Canvas.
- **Multimodal Output**:
    - [ ] **Podcast Generation**: Convert the report into a 2-host audio dialogue.
    - [ ] **Slide Deck Builder**: structured export from Canvas groups.

---
*Last Updated: 2025-12-30*

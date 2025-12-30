# tasks.md

## Phase 1: The "Research Assistant" (Structure)
- [ ] **Data Layer**
    - [ ] **Entity Resolution Engine**: Backend service to deduplicate and link entities across documents. (Crucial for the "Database" moat).
    - [ ] **Background Processing Queue**: Infrastructure for long-running agent tasks (AsyncPG + Redis/Celery equivalent).

## Phase 2: The "Thinking Partner" (Agency)
- [ ] **Autonomy Features**
    - [ ] **"background_loop"**: A scheduled agent task that scans the graph for "Sparse Clusters" and triggers research jobs.
    - [ ] **"Conflict Detector"**: LLM pass to identify opposing claims between nodes and generate "Insight Nodes".
- [ ] **UX**
    - [ ] **"Agent Activity Feed"**: A notification center showing what the AI did while you were away ("Grouped 5 notes", "Found 2 citations").

## Phase 3: The "Content Studio" (Impact)
- [ ] **Living Documents**
    - [ ] **Live-Linked Blocks**: Text blocks in the Writer that auto-update if the source node changes (with user approval).

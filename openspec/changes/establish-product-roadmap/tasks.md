# tasks.md

## Phase 1: The "Research Assistant" (Structure)
- [ ] **Data Layer**
    - [ ] **Entity Resolution Engine**: Link "Elon" (Doc A) to "Musk" (Doc B).
    - [ ] **Background Processing Queue**: Infrastructure for long-running agent tasks.

## Phase 2: The "Curiosity Engine" (The Loop)
- [ ] **Dissonance Detection**
    - [ ] **"Conflict Node" Generator**: LLM pass to identify opposing claims in a cluster.
- [ ] **Resolution Loop**
    - [ ] **The "Tie-Breaker" Agent**: Triggered by a Conflict Node. Searches specific query: "Is X true or Y true?"
    - [ ] **Self-Healing Graph**: Auto-update the graph with the "Winner" or "Nuance" node.
- [ ] **UX**
    - [ ] **"Resolution Feed"**: Notification: "I noticed a conflict in your data on X, so I checked 3 more sources and found Y."

## Phase 3: The "Content Studio" (Impact)
- [ ] **Living Documents**
    - [ ] **Live-Linked Blocks**: Text updates if the Resolution Loop changes the underlying truth.

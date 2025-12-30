# Design: Product Roadmap 2025

## Competitive DNA Analysis
To survive, we must build what they *cannot* build due to their structural DNA.

### 1. The "Session" Trap (NotebookLM's Weakness)
*   **Their DNA**: "Chat". Interaction is ephemeral. You ask, it answers, you leave.
*   **Our Moat**: **Persistence**. Our Agents have "Object Permanence". They remember the goal you set 3 days ago.
    *   *Feature*: **"The Long-Running Research Task"**. You tell the system "Track developments in Fusion Energy," and it updates the graph *every week* without you asking. NotebookLM cannot do this; it has no concept of time or persistent goal state.

### 2. The "Editor" Trap (YouMind/Notion's Weakness)
*   **Their DNA**: "Document". The AI is a helper *inside* your cursor. It waits for you to type.
*   **Our Moat**: **Autonomy**. The AI is a **"Junior Analyst"**. It works in the background.
    *   *Feature*: **"The Night Shift"**. While you sleep, the agent clusters your logic, flags contradictions, and hunts for missing citations. When you wake up, the board has *evolved*. Editor apps can't do this because user-agent collision in a doc is bad UX; but on a *Canvas*, it's natural collaborative work.

## Phasing Strategy: The "Analyst" Evolution

### Phase 1: The "Research Assistant" (Capture & Triage)
*   **Value**: "Don't just File it; Process it."
*   **Critical Feature**: **Entity Resolution Layer**. Unlike a bookmark manager, we resolve "Elon Musk" in Article A to the same node as "Elon" in Article B. We build a *Database*, they build a *List*.

### Phase 2: The "Thinking Partner" (Connect & Visualize)
*   **Value**: "Work While I Sleep."
*   **Critical Feature**: **Asynchronous Graph Maintenance**. The system proactively suggests: "These two clusters contradict each other. I created a 'Conflict' node linking them."
    *   *Why they can't copy*: "Clippy" interrupting you in Notion is annoying. A "Conflict Node" appearing on a Canvas is helpful context. The UX form factor allows agency.

### Phase 3: The "Content Studio" (Synthesize & Publish)
*   **Value**: "Living Reports."
*   **Critical Feature**: **Dynamic Synthesis**. The report updates when the graph updates. It's not a snapshot; it's a view on the living database.

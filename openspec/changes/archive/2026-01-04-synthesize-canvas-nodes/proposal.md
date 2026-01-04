# Proposal: Synthesize Canvas Nodes

## Goal
Enable users to merge any two or more canvas items (Nodes, Sticky Notes, Web Snippets, etc.) to generate a new "Consolidated Insight" node using AI. This encourages users to synthesize information from different sources into higher-level insights.

## Context
The canvas serves as a free-form Thinking Space where users collect various items (notes, snippets, files). Currently, there is no easy mechanism to combine these disparate pieces of information.

Existing behavior:
- Dragging items often pushes them apart (Overlap Prevention).
- No "Merge" interaction for generic items.

## What Changes
## What Changes
1.  **Interaction**: Introduce a "Merge" drop zone when dragging *any* canvas item close to another.
2.  **Mode Selection**: Upon dropping, present a lightweight menu to choose the synthesis intent:
    *   🧩 **Connect**: Find hidden links and commonalities.
    *   💡 **Inspire**: Use one item's perspective to reframe the other.
    *   ⚔️ **Debate**: Highlight conflicts and critique arguments.
3.  **Visuals**: Display a "Merge with AI insights?" prompt during drag-hover, followed by the mode menu.
4.  **Backend**: Upgrade `SynthesisAgent` to support distinct prompts for each mode.
5.  **Output**: Generate a new Sticky Note or Insight Node with structured synthesis tailored to the selected mode.

## Why
- **Value**: Reduces cognitive load by automating the synthesis of disparate information.
- **flow**: Makes the "collaging" workflow (collecting snippets -> building insights) seamless.
- **Flexibility**: Works for sticky notes, generated nodes, and imported snippets.

## Risk
- **Conflict with Layout**: Overlap prevention might fight with merge intention. We need a clear gesture (e.g., hover delay or specific drop target) to distinguish them.

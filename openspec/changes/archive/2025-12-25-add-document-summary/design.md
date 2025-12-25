## Context
The goal is to allow users to generate summaries from selected documents. This involves a new interaction flow in the Studio and a specific visualization (Summary Card).

## Decisions
- **Agent Architecture**: The `SummaryAgent` will use the existing RAG pipeline to retrieve relevant chunks if documents are large, or process full text if small. It will output JSON structured data (`summary`, `key_findings`, `tags`).
- **UI State**: The Summary Card will be an overlay or a floating element in the canvas, distinct from standard nodes initially, but potentially "dockable" as a node.
- **Selection**: Document selection in the sidebar triggers the availability of the Summarize action in the Inspiration Dock.

## Open Questions
- Should the Summary Card automatically become a canvas node? (Decision: Initially transient overlay, user can "Add to Canvas").


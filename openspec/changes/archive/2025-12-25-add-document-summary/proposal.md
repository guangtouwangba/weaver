# Change: Add Document Summary Feature

## Why
Users need a way to quickly synthesize information from uploaded documents to grasp key insights without reading everything manually. This enhances the "Visual Thinking Assistant" value proposition by providing AI-generated summaries directly in the workspace.

## What Changes
- **Inspiration Dock**: Add a "Summarize" action that appears when documents are available/selected.
- **Summary Agent**: Implement a backend agent to process selected documents and generate a structured summary (key findings, narrative).
- **Summary Card**: specific UI component to display the generated summary with "Strategy" and "Insights" tags, and a "Read Full Summary" expansion option.
- **Document Active State**: Visual indication in the Resource Sidebar when a document is selected or being processed.

## Impact
- **Specs**: `studio` (UI), `agents` (Backend logic).
- **Frontend**: `InspirationDock.tsx`, `SummaryCard.tsx`, `ResourceSidebar.tsx`.
- **Backend**: New agent/service for summary generation.


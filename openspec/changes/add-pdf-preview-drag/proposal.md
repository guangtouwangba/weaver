# Change: Add PDF Document Preview and Drag-to-Canvas

## Why
Users need to quickly preview PDF documents in the resource sidebar and drag them onto the canvas as reference nodes. Currently, documents are listed as simple cards without visual preview. This feature aligns with the "Canvas as Workbench" philosophy where users drag items to focus on them.

## What Changes
- Add PDF thumbnail preview generation and display in document cards
- Implement rich document preview card showing thumbnail, file metadata (type, size, page count)
- Add drag-to-canvas functionality for document cards
- Create "Document Reference" node type on canvas when a document is dropped
- Integrate with existing Konva canvas drag-drop system

## Impact
- Affected specs: `studio`
- Affected code:
  - `app/frontend/src/components/studio/ResourceSidebar.tsx` - Enhanced document cards with preview
  - `app/frontend/src/components/studio/KonvaCanvas.tsx` - Handle drop events for documents
  - `app/frontend/src/lib/api.ts` - May need thumbnail endpoint
  - New component: `DocumentPreviewCard.tsx` for rich preview display
  - New canvas node: `DocumentReferenceNode` for dropped documents


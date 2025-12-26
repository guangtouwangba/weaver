# Change: Add PDF Annotation Preview with Whiteboard Integration

## Why
Users need a rich document reading experience where they can annotate PDFs (highlight, underline, comment) and transfer those annotations to the whiteboard as thinking clues. Currently, the PDF viewer exists but lacks a full-screen preview mode, comprehensive annotation tools, and the ability to export selections/annotations to the canvas as editable nodes.

## What Changes
- Add full-screen PDF preview modal with three-panel layout (page thumbnails, content, tools)
- Implement comprehensive annotation toolbar (highlight, underline, strikethrough, pen, comment, image, diagram)
- Add Recent Annotations panel showing all annotations with quick navigation
- Add Comments tab for document-level discussion threads
- Implement "Add to Whiteboard" feature to export selected text/annotations as canvas nodes
- Create two entry points: click PDF on canvas and click source file in sidebar

## Impact
- Affected specs: `studio`
- Affected code:
  - New component: `PDFPreviewModal.tsx` - Full-screen preview with three-panel layout
  - New component: `AnnotationToolbar.tsx` - Tool icons and mode switching
  - New component: `AnnotationsPanel.tsx` - Recent annotations list
  - New component: `CommentsPanel.tsx` - Comments/threads view
  - Extend: `app/frontend/src/components/pdf/PDFViewer.tsx` - Support new annotation types
  - Extend: `app/frontend/src/components/pdf/types.ts` - New annotation type definitions
  - Extend: `app/frontend/src/contexts/StudioContext.tsx` - Preview modal state
  - Extend: `app/frontend/src/components/studio/KonvaCanvas.tsx` - Handle annotation-to-node creation
  - Backend: New API endpoints for comments and extended annotation types


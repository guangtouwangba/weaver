## Context

The "Visual Thinking Assistant" positions the canvas as a workbench where users drag content to focus. Currently, uploaded documents appear as simple list items without visual preview, and users cannot directly reference them on the canvas by dragging. This change enables a richer document interaction pattern aligned with the product vision.

Based on the provided screenshot, the PDF preview card should show:
- Document type icon (PDF icon)
- Document title with action buttons (download, more options)
- Thumbnail preview of the first page
- File details (filename, file size)

## Goals / Non-Goals

**Goals:**
- Display rich PDF preview cards in the resource sidebar
- Enable drag-and-drop from sidebar to canvas
- Create persistent document reference nodes on canvas
- Provide visual feedback during drag operations
- Keep preview lightweight (thumbnail only, not full render)

**Non-Goals:**
- Full PDF rendering in sidebar (use existing PDFViewer for that)
- Multi-page thumbnail navigation in preview card
- Editing PDF content from the preview card
- Drag-drop for non-PDF document types (future enhancement)

## Decisions

### Decision 1: Thumbnail Generation Strategy
**Choice:** Generate PDF thumbnails asynchronously server-side after upload, with animated placeholder during generation.

**Rationale:**
- Upload completes quickly without waiting for thumbnail
- Background processing doesn't block user workflow
- Thumbnails appear progressively as they become ready
- Already have async document processing pipeline (Celery workers)

**Flow:**
```
1. User uploads PDF → Immediate success response
2. Frontend shows animated loading placeholder
3. Backend queues thumbnail generation task
4. Task generates first-page thumbnail (300px width)
5. WebSocket/polling notifies frontend when ready
6. Frontend swaps placeholder for actual thumbnail
```

**Placeholder Design:**
- Skeleton animation (shimmer effect) on thumbnail area
- Show file type icon overlay during loading
- Smooth fade transition when thumbnail loads

**Alternatives considered:**
- Client-side thumbnail generation using pdf.js → Rejected: Heavy client load, requires full PDF download
- Synchronous generation blocking upload → Rejected: Poor UX, slow uploads
- Static placeholder icon → Rejected: Less engaging, no progress indication

### Decision 2: Canvas Drop Integration
**Choice:** Use native HTML5 drag-and-drop with Konva stage event interception.

**Rationale:**
- Konva canvas already handles internal drag-drop
- Native drag-and-drop allows cross-component transfer
- DataTransfer API enables rich data payload (document ID, title, thumbnail URL)

**Implementation:**
```
1. Document card: Set draggable="true", onDragStart sets DataTransfer
2. Canvas container: Listen for dragover/drop events
3. On drop: Convert screen coordinates to canvas coordinates
4. Create DocumentReferenceNode at drop position
```

### Decision 3: Document Reference Node Design
**Choice:** Create a new "source" subType node with thumbnail display.

**Rationale:**
- `CanvasNode.subType: 'source'` already exists in type definition
- Reuses existing node infrastructure (selection, connections, etc.)
- Can link to full document view via double-click

**Node structure:**
```typescript
{
  id: string,
  type: 'document',
  subType: 'source',
  title: document.filename,
  content: document.summary || '',
  sourceId: document.id,
  fileMetadata: {
    fileType: 'pdf',
    pageCount: document.page_count,
    thumbnailUrl: string,
  },
  // Standard position/size fields...
}
```

### Decision 4: Preview Card Component Structure
**Choice:** Create `DocumentPreviewCard` as a standalone component used by `ResourceSidebar`.

**Rationale:**
- Separation of concerns (preview logic vs sidebar layout)
- Reusable in other contexts (search results, recent files)
- Cleaner code organization

## Risks / Trade-offs

**Risk:** Thumbnail generation increases document processing time
- **Mitigation:** Generate thumbnails asynchronously post-upload, show placeholder until ready
- **Mitigation:** Use low-resolution thumbnails (300px width max)

**Risk:** Large thumbnail storage for many documents
- **Mitigation:** Generate single first-page thumbnail only
- **Mitigation:** Use WebP format for smaller file sizes
- **Mitigation:** Optional: Lazy thumbnail generation on first view

**Trade-off:** Server-side thumbnails require backend changes
- Acceptable because we already have document processing pipeline
- Can start with placeholder UI while backend catches up

## Migration Plan

1. **Phase 1 (Frontend):** Implement preview card UI with placeholder thumbnail
2. **Phase 2 (Backend):** Add thumbnail generation to document processing
3. **Phase 3 (Integration):** Connect frontend to real thumbnails, add canvas drop

No breaking changes - existing documents work without thumbnails.

## Open Questions

1. Should we support thumbnail generation for existing documents via manual trigger?
2. What thumbnail dimensions work best for the sidebar width (300px)?
3. Should the dropped document node show the thumbnail or a simplified icon view?


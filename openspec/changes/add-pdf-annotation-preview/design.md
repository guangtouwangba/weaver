## Context

The Visual Thinking Assistant positions the canvas as a workbench where users build knowledge structures. PDF documents are primary source materials, and users need to deeply engage with them—highlighting key passages, adding comments, and extracting insights to the canvas. Currently, PDF viewing is limited to a sidebar panel without full annotation capabilities or whiteboard integration.

Based on the design mockup, the PDF preview experience should include:
- Three-panel modal layout (thumbnails | content | tools)
- Comprehensive annotation toolbar with 8 tool types
- Recent annotations list with page navigation
- Comments thread system
- "Add to Whiteboard" action for selected content

## Goals / Non-Goals

**Goals:**
- Provide immersive PDF reading experience via full-screen modal
- Support multiple annotation types (highlight, underline, strikethrough, pen, comment)
- Enable quick navigation via page thumbnails
- Show annotation history for document review
- Export selections/annotations to canvas as thinking clues
- Support two entry points (canvas PDF node, sidebar source file)

**Non-Goals:**
- Full PDF editing (text modification, page manipulation)
- Real-time collaborative annotation (future enhancement)
- OCR or AI-assisted annotation (separate feature)
- Annotation sync across devices (requires auth system)

## Decisions

### Decision 1: Modal vs Drawer for Preview
**Choice:** Full-screen modal with escape/close button

**Rationale:**
- Modal provides immersive reading experience
- Three-panel layout requires significant horizontal space
- Consistent with "focus" pattern in the product
- Easy to dismiss and return to canvas

**Alternatives considered:**
- Drawer/Slide-over panel → Rejected: Too constrained for three-panel layout
- New page/route → Rejected: Loses canvas context
- Inline expansion on canvas → Rejected: Conflicts with canvas zoom/pan

### Decision 2: Annotation Data Model
**Choice:** Extend existing `Highlight` model with annotation types

```typescript
type AnnotationType = 'highlight' | 'underline' | 'strikethrough' | 'pen' | 'comment' | 'image' | 'diagram';

interface Annotation {
  id: string;
  documentId: string;
  pageNumber: number;
  type: AnnotationType;
  color: HighlightColor;
  // For text-based annotations
  rects?: DOMRect[];
  selectedText?: string;
  // For freehand pen
  paths?: { x: number; y: number }[][];
  // For comments
  content?: string;
  // For image/diagram (future)
  assetUrl?: string;
  position?: { x: number; y: number };
  // Metadata
  createdAt: string;
  updatedAt: string;
}
```

**Rationale:**
- Single unified model simplifies API and storage
- Type field distinguishes rendering behavior
- Optional fields keep model flexible

### Decision 3: Add to Whiteboard Data Flow
**Choice:** Create new "snippet" canvas node type from annotation/selection

```typescript
interface SnippetNode {
  id: string;
  type: 'snippet';
  subType: 'annotation' | 'selection';
  content: string;           // The selected text
  sourceDocumentId: string;  // Reference to source PDF
  sourcePageNumber: number;
  annotationType?: AnnotationType;
  annotationColor?: HighlightColor;
  position: { x: number; y: number };
}
```

**Rationale:**
- Dedicated node type preserves source context
- Can link back to original document location
- Distinguishes from manually created text nodes
- Color coding maintains visual consistency with annotation

**Flow:**
1. User selects text or clicks annotation in preview
2. User clicks "Add to Whiteboard" button
3. Modal closes, canvas viewport adjusts
4. New snippet node appears at center of viewport (or drop position)
5. Node is automatically selected for immediate editing/repositioning

### Decision 4: Page Thumbnail Generation
**Choice:** Generate thumbnails on-demand using existing PDF.js rendering

**Rationale:**
- PDF.js already loaded for main viewer
- Thumbnails rendered at low resolution (150px width)
- Cached in component state during preview session
- No server-side thumbnail storage needed for preview

**Alternative considered:**
- Pre-generate all thumbnails server-side → Rejected: Adds processing overhead, storage cost

### Decision 5: Tool Panel State Management
**Choice:** Local component state for active tool, modal-level state for annotations

**Rationale:**
- Tool selection is ephemeral UI state
- Annotations need persistence and sync with backend
- React Context overkill for single-modal state

### Decision 6: Comments System Architecture
**Choice:** Document-level comments with optional page/annotation anchors

```typescript
interface Comment {
  id: string;
  documentId: string;
  anchorType: 'document' | 'page' | 'annotation';
  anchorId?: string;        // annotationId if anchored to annotation
  pageNumber?: number;      // if anchored to page
  content: string;
  authorId?: string;        // Optional for solo user
  createdAt: string;
  replies?: Comment[];      // Nested for threads
}
```

**Rationale:**
- Flexible anchoring supports different comment use cases
- Thread structure enables discussions
- Can be extended for collaboration later

## Risks / Trade-offs

**Risk:** PDF.js rendering performance with multiple thumbnails
- **Mitigation:** Virtualize thumbnail list, render only visible thumbnails
- **Mitigation:** Use requestIdleCallback for non-urgent thumbnail renders

**Risk:** Large annotation count slows panel rendering
- **Mitigation:** Paginate annotations list (load 20 at a time)
- **Mitigation:** Virtual scrolling for long lists

**Risk:** Complex modal state management
- **Mitigation:** Keep state flat, avoid nested updates
- **Mitigation:** Clear state on modal close

**Trade-off:** Modal blocks canvas interaction
- Acceptable because preview is a focused task
- Users can quickly exit via Escape key or close button

## UI Component Structure

```
PDFPreviewModal
├── PageThumbnailSidebar
│   └── ThumbnailItem (virtualized list)
├── PDFContentPane
│   ├── PDFViewerWrapper (existing)
│   ├── AnnotationOverlay (extended from HighlightOverlay)
│   └── SelectionPopover (Add/Edit/Copy actions)
└── ToolsPanel
    ├── TabBar (Tools | Comments)
    ├── AnnotationToolbar
    │   ├── HighlightTool
    │   ├── UnderlineTool
    │   ├── StrikethroughTool
    │   ├── PenTool
    │   ├── CommentTool
    │   ├── ImageTool (future)
    │   └── DiagramTool (future)
    ├── RecentAnnotationsList
    │   └── AnnotationItem
    ├── CommentsTab
    │   └── CommentThread
    └── AddToWhiteboardButton
```

## Open Questions

1. Should "Add to Whiteboard" close the modal or keep it open?
   - **Proposed:** Close modal to show the new node on canvas immediately
2. What's the maximum annotation size for "Add to Whiteboard"?
   - **Proposed:** Limit to 500 characters, show truncated preview if longer
3. Should pen drawings be exportable to whiteboard?
   - **Proposed:** Phase 2 feature, focus on text annotations first
4. How to handle annotations when document is re-processed?
   - **Proposed:** Store character offsets alongside rects for re-anchoring



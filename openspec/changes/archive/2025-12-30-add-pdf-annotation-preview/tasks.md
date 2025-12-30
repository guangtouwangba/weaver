## 1. Core Preview Modal

- [x] 1.1 Create `PDFPreviewModal` component with three-panel layout structure
- [x] 1.2 Add modal open/close state management in `StudioContext`
- [x] 1.3 Implement entry point from sidebar source file click
- [x] 1.4 Implement entry point from canvas PDF node click/double-click

## 2. Page Thumbnail Sidebar

- [x] 2.1 Create `PageThumbnailSidebar` component with virtualized list
- [x] 2.2 Implement thumbnail rendering using PDF.js at low resolution
- [x] 2.3 Add current page indicator and click-to-navigate behavior
- [x] 2.4 Add page number labels below each thumbnail

## 3. Annotation Tools Panel

- [x] 3.1 Create `AnnotationToolbar` with tool icons (highlight, underline, strikethrough, pen, comment)
- [x] 3.2 Implement tool selection state and cursor mode switching
- [x] 3.3 Extend annotation type definitions in `types.ts`
- [x] 3.4 Add underline annotation rendering in `AnnotationOverlay`
- [x] 3.5 Add strikethrough annotation rendering in `AnnotationOverlay`
- [ ] 3.6 Implement pen/freehand drawing tool with path capture

## 4. Recent Annotations Panel

- [x] 4.1 Create `RecentAnnotationsList` component (Implemented as `AnnotationsPanel`)
- [x] 4.2 Display annotation items with page number, text preview, timestamp, color indicator
- [x] 4.3 Add click-to-navigate functionality (jump to annotation page)
- [x] 4.4 Add delete annotation action per item
- [x] 4.5 Implement annotation type icon indicators

## 5. Comments System

- [x] 5.1 Create `CommentsPanel` component with thread display
- [x] 5.2 Add comment input form with submit handler
- [x] 5.3 Create backend API endpoints for comment CRUD
- [x] 5.4 Add comment count display in tab header
- [x] 5.5 Support optional page/annotation anchoring for comments

## 6. Selection Popover & Add to Whiteboard

- [ ] 6.1 Create `SelectionPopover` component with Add/Edit/Copy actions
- [x] 6.2 Implement "Add to Whiteboard" button in tools panel footer
- [x] 6.3 Create snippet node type for canvas
- [x] 6.4 Implement node creation flow: close modal → create node at viewport center
- [x] 6.5 Add source document reference to snippet nodes
- [x] 6.6 Style snippet nodes with source indicator and annotation color

## 7. Backend Extensions

- [x] 7.1 Extend annotation model to support new types (underline, strikethrough, pen)
- [x] 7.2 Add `selected_text` field to annotation storage
- [x] 7.3 Create comments table and API endpoints
- [x] 7.4 Add annotation text storage for "Add to Whiteboard" flow

## 8. Polish & Integration

- [x] 8.1 Add keyboard shortcuts (Escape to close, number keys for tool selection)
- [x] 8.2 Add loading states for thumbnail and annotation loading
- [x] 8.3 Handle edge cases (document not found, empty annotations)
- [x] 8.4 Add transition animations for modal open/close



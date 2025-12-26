## 1. Core Preview Modal

- [ ] 1.1 Create `PDFPreviewModal` component with three-panel layout structure
- [ ] 1.2 Add modal open/close state management in `StudioContext`
- [ ] 1.3 Implement entry point from sidebar source file click
- [ ] 1.4 Implement entry point from canvas PDF node click/double-click

## 2. Page Thumbnail Sidebar

- [ ] 2.1 Create `PageThumbnailSidebar` component with virtualized list
- [ ] 2.2 Implement thumbnail rendering using PDF.js at low resolution
- [ ] 2.3 Add current page indicator and click-to-navigate behavior
- [ ] 2.4 Add page number labels below each thumbnail

## 3. Annotation Tools Panel

- [ ] 3.1 Create `AnnotationToolbar` with tool icons (highlight, underline, strikethrough, pen, comment)
- [ ] 3.2 Implement tool selection state and cursor mode switching
- [ ] 3.3 Extend annotation type definitions in `types.ts`
- [ ] 3.4 Add underline annotation rendering in `AnnotationOverlay`
- [ ] 3.5 Add strikethrough annotation rendering in `AnnotationOverlay`
- [ ] 3.6 Implement pen/freehand drawing tool with path capture

## 4. Recent Annotations Panel

- [ ] 4.1 Create `RecentAnnotationsList` component
- [ ] 4.2 Display annotation items with page number, text preview, timestamp, color indicator
- [ ] 4.3 Add click-to-navigate functionality (jump to annotation page)
- [ ] 4.4 Add delete annotation action per item
- [ ] 4.5 Implement annotation type icon indicators

## 5. Comments System

- [ ] 5.1 Create `CommentsPanel` component with thread display
- [ ] 5.2 Add comment input form with submit handler
- [ ] 5.3 Create backend API endpoints for comment CRUD
- [ ] 5.4 Add comment count display in tab header
- [ ] 5.5 Support optional page/annotation anchoring for comments

## 6. Selection Popover & Add to Whiteboard

- [ ] 6.1 Create `SelectionPopover` component with Add/Edit/Copy actions
- [ ] 6.2 Implement "Add to Whiteboard" button in tools panel footer
- [ ] 6.3 Create snippet node type for canvas
- [ ] 6.4 Implement node creation flow: close modal → create node at viewport center
- [ ] 6.5 Add source document reference to snippet nodes
- [ ] 6.6 Style snippet nodes with source indicator and annotation color

## 7. Backend Extensions

- [ ] 7.1 Extend annotation model to support new types (underline, strikethrough, pen)
- [ ] 7.2 Add `selected_text` field to annotation storage
- [ ] 7.3 Create comments table and API endpoints
- [ ] 7.4 Add annotation text storage for "Add to Whiteboard" flow

## 8. Polish & Integration

- [ ] 8.1 Add keyboard shortcuts (Escape to close, number keys for tool selection)
- [ ] 8.2 Add loading states for thumbnail and annotation loading
- [ ] 8.3 Handle edge cases (document not found, empty annotations)
- [ ] 8.4 Add transition animations for modal open/close


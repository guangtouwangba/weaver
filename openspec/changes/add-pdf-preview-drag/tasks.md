## 1. Frontend - Document Preview Card

- [ ] 1.1 Create `DocumentPreviewCard` component with animated skeleton placeholder, file info display
- [ ] 1.2 Implement shimmer loading animation for thumbnail placeholder area
- [ ] 1.3 Add file type icon overlay on loading placeholder
- [ ] 1.4 Integrate `DocumentPreviewCard` into `ResourceSidebar` replacing simple document list items
- [ ] 1.5 Add drag-start handler with DataTransfer payload (documentId, title, thumbnailUrl)
- [ ] 1.6 Style preview card to match design mockup (thumbnail area, file icon, metadata)
- [ ] 1.7 Implement smooth fade transition when thumbnail becomes available

## 2. Frontend - Canvas Drop Integration

- [ ] 2.1 Add drop zone handler to canvas container (dragover, drop events)
- [ ] 2.2 Convert screen drop coordinates to canvas coordinates accounting for viewport transform
- [ ] 2.3 Create `DocumentReferenceNode` component for displaying dropped documents on canvas
- [ ] 2.4 Add drag visual feedback (ghost image, drop zone highlight)

## 3. Backend - Async Thumbnail Generation

- [ ] 3.1 Create Celery task for thumbnail generation (PyMuPDF first-page render, 300px width)
- [ ] 3.2 Queue thumbnail task automatically after document upload success
- [ ] 3.3 Store thumbnails in uploads directory with document reference (WebP format)
- [ ] 3.4 Add `thumbnail_url` and `thumbnail_status` fields to document model/API response
- [ ] 3.5 Create thumbnail endpoint for serving generated thumbnails
- [ ] 3.6 Send WebSocket notification when thumbnail generation completes

## 4. Integration & Polish

- [ ] 4.1 Connect preview card to WebSocket for thumbnail status updates
- [ ] 4.2 Swap loading placeholder to thumbnail on WebSocket notification
- [ ] 4.3 Handle documents without thumbnails gracefully (show static type icon)
- [ ] 4.4 Double-click on dropped document node opens source panel with that document
- [ ] 4.5 Persist thumbnail URL in dropped canvas node for reload


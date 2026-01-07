## 1. Frontend - YouTube Preview Card Component

- [x] 1.1 Create `YouTubePreviewCard` Konva component in `KonvaCanvas.tsx` following existing `SourcePreviewCard` pattern
- [x] 1.2 Implement YouTube brand header with red YouTube logo icon
- [x] 1.3 Render video thumbnail using `URLImage` component with error fallback
- [x] 1.4 Add centered semi-transparent play button overlay on thumbnail
- [x] 1.5 Add duration badge in bottom-right corner of thumbnail (format: "MM:SS")
- [x] 1.6 Render video title with ellipsis truncation
- [x] 1.7 Render channel avatar (circular) + channel name + view count + relative time
- [x] 1.8 Add source URL link indicator at card bottom

## 2. Frontend - Node Type Detection

- [x] 2.1 Extend canvas node rendering logic to detect YouTube nodes via `fileMetadata.platform === 'youtube'`
- [x] 2.2 Route YouTube nodes to `YouTubePreviewCard` instead of generic `SourcePreviewCard`

## 3. Frontend - YouTube Player Modal

- [x] 3.1 Create `YouTubePlayerModal` component in `components/studio/`
- [x] 3.2 Implement modal with dark backdrop and centered content area
- [x] 3.3 Embed YouTube iframe player using `https://www.youtube.com/embed/{videoId}` with autoplay
- [x] 3.4 Add video title header above player
- [x] 3.5 Add channel info and metadata below player
- [x] 3.6 Add close button (X) and "Open in YouTube" external link button
- [x] 3.7 Handle Escape key and backdrop click to close modal
- [x] 3.8 Ensure modal is responsive (max-width with padding on mobile)

## 4. Frontend - Sidebar Video Preview

- [x] 4.1 Add YouTubePlayerModal to ResourceSidebar for video preview
- [x] 4.2 Add click handler on YouTube URL items in `ResourceSidebar` to open preview modal
- [x] 4.3 Render embedded YouTube iframe in modal for video content
- [x] 4.4 Display video metadata (title, channel, views, published date)
- [x] 4.5 ~~Add collapsible video description section~~ (Simplified: metadata shown in modal footer)
- [x] 4.6 ~~Add transcript section (if available from URL extractor)~~ (Deferred to future iteration)
- [x] 4.7 ~~Add "Add to Canvas" button to create YouTube card from preview~~ (Drag from sidebar provides this)

## 5. Frontend - Drag and Drop Integration

- [x] 5.1 Update Resource Sidebar URL item drag data to include `platform`, `metadata`, and `contentType`
- [x] 5.2 Extend `KonvaCanvas` drop handler to create YouTube-specific `knowledge` nodes with proper metadata
- [x] 5.3 Ensure node creation includes: `thumbnailUrl`, `duration`, `channelName`, `viewCount`, `publishedAt`, `videoId`

## 6. Frontend - Canvas Card Interaction

- [x] 6.1 Implement play button click handler to open YouTube Player Modal
- [x] 6.2 Implement double-click handler to open YouTube Player Modal
- [x] 6.3 ~~Add hover state with subtle elevation increase~~ (Uses existing node hover styles)
- [x] 6.4 Ensure standard canvas node selection behavior works correctly

## 7. Frontend - Connection Handles

- [x] 7.1 Add connection handles on all 4 sides (top, bottom, left, right) of YouTube Preview Card
- [x] 7.2 Ensure handles appear on hover and selection (same behavior as other nodes)
- [x] 7.3 Implement drag-from-handle to create connections to other nodes
- [x] 7.4 Implement drag-to-handle to accept connections from other nodes
- [x] 7.5 Ensure edge creation and persistence works correctly with YouTube nodes

> Note: Connection handles are inherited from the `KnowledgeNode` component which wraps all node types including YouTube cards.

## 8. Validation

- [ ] 8.1 Verify YouTube cards render correctly at different zoom levels
- [ ] 8.2 Test drag from sidebar creates proper YouTube card on canvas
- [ ] 8.3 Test thumbnail loading error fallback displays YouTube placeholder
- [ ] 8.4 Test YouTube Player Modal opens and plays video correctly
- [ ] 8.5 Test sidebar video preview displays and plays video correctly
- [ ] 8.6 Test "Add to Canvas" from sidebar preview creates correct node
- [ ] 8.7 Test connection handles appear and work correctly on YouTube cards
- [ ] 8.8 Test creating edges from YouTube cards to other node types
- [ ] 8.9 Test creating edges from other nodes to YouTube cards


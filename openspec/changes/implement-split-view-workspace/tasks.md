# Tasks: Implement Split View Workspace

## Phase 1: Layout Core
- [ ] Install `react-resizable-panels` <!-- id: 500 -->
- [ ] Refactor `StudioPageContent` to support Split Layout mode <!-- id: 501 -->
- [ ] Create `ContentDock` component to host viewers <!-- id: 502 -->
- [ ] Implement Dock/Undock actions in `ResourceSidebar` <!-- id: 503 -->

## Phase 2: Viewer Migration
- [ ] Refactor `PDFPreviewModal` into `PDFViewerPanel` (remove modal wrapper) <!-- id: 504 -->
- [ ] Create `VideoPlayerPanel` with `TranscriptList` component <!-- id: 505 -->
- [ ] Implement Bilibili/YouTube timestamp synchronization <!-- id: 506 -->

## Phase 3: Bi-directional Linking
- [ ] Implement Drag-and-Drop from Transcript to Canvas to create Nodes <!-- id: 507 -->
- [ ] Implement "Click Node -> Scroll Content" logic for Video/PDF <!-- id: 508 -->
- [ ] Implement "Select Content -> Highlight Node" logic <!-- id: 509 -->

## Phase 4: Polish
- [ ] Add smooth transitions for Panel opening/closing <!-- id: 510 -->
- [ ] Persist panel sizes and open state <!-- id: 511 -->

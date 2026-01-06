# Tasks: Adopt Chakra UI with Warm Gray Theme

## Phase 1: Foundation
- [x] 1.1 Install Chakra UI dependencies
- [x] 1.2 Create `theme/theme.ts` with warm palette
- [x] 1.3 Set up ChakraProvider in layout
- [x] 1.4 Update `globals.css` CSS variables (--background, --foreground)
- [x] 1.5 Update `colors.ts` primary palette (Indigo → Teal)

## Phase 2: High-Visibility Components
- [x] 2.1 Fix `GlobalSidebar.tsx` (logo gradient, user avatar)
- [x] 2.2 Fix `ProjectCard.tsx` (projectColors array)
- [x] 2.3 Fix page-level bgcolor values (inbox, studio)

## Phase 3: PDF Viewer Components
- [x] 3.1 Update `PDFPreviewModal.tsx` Tailwind classes
- [x] 3.2 Update `AnnotationToolbar.tsx` bg colors
- [x] 3.3 Update `CommentsPanel.tsx` button colors
- [x] 3.4 Update `PageThumbnailSidebar.tsx` backgrounds
- [x] 3.5 Update `HighlightOverlay.tsx` white backgrounds

## Phase 4: Studio Components
- [x] 4.1 Update `KonvaCanvas.tsx` node/canvas colors
- [x] 4.2 Update mindmap components (Node, Edge, Rich)
- [ ] 4.3 Update `InspirationDock.tsx`, `AssistantPanel.tsx`
- [ ] 4.4 Update `ResourceSidebar.tsx`, `SummaryCard.tsx`
- [x] 4.5 Update `GridBackground.tsx` dot color

## Phase 5: Inbox Components
- [x] 5.1 Update inbox component backgrounds
- [x] 5.2 Update `TagChip.tsx` colors

## Phase 6: Verification
- [ ] 6.1 Run `npm run build`
- [ ] 6.2 Visual verification all pages
- [ ] 6.3 Test PDF highlighting functionality
- [ ] 6.4 Test canvas/mindmap interactions

## 6. Documentation
- [ ] 6.1 Update `project.md` styling conventions to mention Chakra
- [x] 6.2 Add comment in theme.ts explaining warm gray rationale

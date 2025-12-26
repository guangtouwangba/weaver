## 1. Setup & Abstraction Layer
- [x] 1.1 Install `@mui/icons-material` package
- [x] 1.2 Create `components/ui/icons/types.ts` with `IconProps` interface
- [x] 1.3 Create `components/ui/icons/Icon.tsx` with `createIcon` helper
- [x] 1.4 Create `components/ui/icons/index.ts` exporting all icons
- [x] 1.5 Remove old `IconWrapper` component

## 2. Migrate Components (Studio)
- [x] 2.1 Migrate `MindMapEditor.tsx`
- [x] 2.2 Migrate `MindMapViews.tsx`
- [x] 2.3 Migrate `KonvaCanvas.tsx`
- [x] 2.4 Migrate `InspirationDock.tsx`
- [x] 2.5 Migrate `MindMapCanvasNode.tsx`
- [x] 2.6 Migrate `SummaryCanvasNode.tsx`
- [x] 2.7 Migrate `ResourceSidebar.tsx`
- [x] 2.8 Migrate `CanvasContextMenu.tsx`
- [x] 2.9 Migrate `CanvasToolbar.tsx`
- [x] 2.10 Migrate `SummaryCard.tsx`
- [x] 2.11 Migrate `ImportSourceDropzone.tsx`
- [x] 2.12 Migrate `CanvasControls.tsx`
- [x] 2.13 Migrate `ChatOverlay.tsx`
- [x] 2.14 Migrate `ThinkingPathGenerator.tsx`
- [x] 2.15 Migrate `NodeDetailPanel.tsx`
- [x] 2.16 Migrate `CanvasSidebar.tsx`
- [x] 2.17 Migrate `AssistantPanel.tsx`
- [x] 2.18 Migrate `SourcePanel.tsx`
- [x] 2.19 Migrate `CanvasPanel.tsx`

## 3. Migrate Components (Other)
- [x] 3.1 Migrate `GlobalSidebar.tsx`
- [x] 3.2 Migrate `CreateProjectDialog.tsx`
- [x] 3.3 Migrate `ImportSourceDialog.tsx`
- [x] 3.4 Migrate `ProjectCard.tsx`
- [x] 3.5 Migrate `PDFViewer.tsx`
- [x] 3.6 Migrate `SelectionToolbar.tsx`
- [x] 3.7 Migrate `HighlightOverlay.tsx`
- [x] 3.8 Migrate `StrategyCard.tsx`
- [x] 3.9 Migrate `StrategyTooltip.tsx`

## 4. Migrate Pages
- [x] 4.1 Migrate `app/studio/[projectId]/page.tsx`
- [x] 4.2 Migrate `app/studio/page.tsx`
- [x] 4.3 Migrate `app/dashboard/page.tsx`
- [x] 4.4 Migrate `app/settings/page.tsx`

## 5. Cleanup & Verification
- [x] 5.1 Remove `lucide-react` from `package.json`
- [x] 5.2 Run `npm install` to update lock file
- [x] 5.3 Run ESLint to catch any missed imports
- [x] 5.4 Verify build succeeds (`npm run build`)
- [x] 5.5 Visual verification of icon rendering in browser

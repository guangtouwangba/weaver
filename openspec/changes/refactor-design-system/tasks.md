# Tasks: Refactor Design System

## 1. Token Foundation (P0)
- [x] 1.1 Create `ui/tokens/colors.ts` with semantic color palette. @frontend
- [x] 1.2 Create `ui/tokens/spacing.ts` with scale (4, 8, 12, 16, 24, 32, 48). @frontend
- [x] 1.3 Create `ui/tokens/typography.ts` with font families, sizes, weights. @frontend
- [x] 1.4 Create `ui/tokens/shadows.ts` with elevation levels. @frontend
- [x] 1.5 Create `ui/tokens/radii.ts` with border-radius scale. @frontend
- [x] 1.6 Create barrel export `ui/tokens/index.ts`. @frontend

## 2. Core Primitives (P0)
- [x] 2.1 Create `Stack` component (`ui/primitives/Stack.tsx`). @frontend
- [x] 2.2 Create `Text` component (`ui/primitives/Text.tsx`). @frontend
- [x] 2.3 Create `Button` component (`ui/primitives/Button.tsx`). @frontend
- [x] 2.4 Create `IconButton` component (`ui/primitives/IconButton.tsx`). @frontend
- [x] 2.5 Create `Surface` component (`ui/primitives/Surface.tsx`). @frontend
- [x] 2.6 Create `Tooltip` wrapper (`ui/primitives/Tooltip.tsx`). @frontend
- [x] 2.7 Create `Spinner` component (`ui/primitives/Spinner.tsx`). @frontend
- [x] 2.8 Create `Collapse` wrapper (`ui/primitives/Collapse.tsx`). @frontend
- [x] 2.9 Create `Skeleton` wrapper (`ui/primitives/Skeleton.tsx`). @frontend
- [x] 2.10 Create barrel export `ui/primitives/index.ts`. @frontend
- [x] 2.11 Create top-level `ui/index.ts` barrel. @frontend

## 3. Pilot Migration (P1)
- [x] 3.1 Migrate `dashboard/TemplateCard.tsx` to use primitives. @frontend
- [x] 3.2 Migrate `inbox/TagChip.tsx` to use primitives. @frontend
- [x] 3.3 Migrate `studio/CanvasControls.tsx` to use primitives. @frontend
- [x] 3.4 Migrate `layout/GlobalSidebar.tsx` to use primitives. @frontend
- [x] 3.5 Visual spot-check of migrated components. @frontend

## 4. Composite Components (P1)
- [x] 4.1 Create `Card` composite (`ui/composites/Card.tsx`). @frontend
- [x] 4.2 Create `Dialog` composite (`ui/composites/Dialog.tsx`). @frontend
- [x] 4.3 Create `Menu` / `ContextMenu` composite. @frontend
- [x] 4.4 Create `Input` / `TextField` composite. @frontend
- [x] 4.5 Create barrel export `ui/composites/index.ts`. @frontend

## 5. Studio Migration (P2)

### 5.1 Simple Components (low MUI, quick wins)
- [x] 5.1.1 `CanvasSidebar.tsx` - View switcher (Box, Tooltip). @frontend
- [x] 5.1.2 `ChatOverlay.tsx` - Chat input overlay (Box, TextField, IconButton). @frontend
- [x] 5.1.3 `ImportSourceDropzone.tsx` - Dropzone (Box, Typography). @frontend
- [x] 5.1.4 `CanvasToolbar.tsx` - Left toolbar (Paper, ToggleButton, Tooltip). @frontend
- [x] 5.1.5 `CanvasContextMenu.tsx` - Right-click menu (Paper, MenuItem). @frontend
- [ ] 5.1.6 `CanvasSection.tsx` - Konva Group (no MUI, skip). @frontend

### 5.2 Medium Components (moderate MUI usage)
- [x] 5.2.1 `DocumentPreviewCard.tsx` - Already uses Tailwind (no MUI, skip). @frontend
- [x] 5.2.2 `SummaryCard.tsx` - Summary card (Paper, Modal, Chip, Button). @frontend
- [x] 5.2.3 `CanvasPanel.tsx` - Canvas container (Box, Paper). @frontend
- [x] 5.2.4 `CanvasPanelKonva.tsx` - Konva wrapper (Box). @frontend
- [x] 5.2.5 `GenerationOutputsOverlay.tsx` - AI outputs (Box, Paper, Chip). @frontend
- [x] 5.2.6 `ThinkingPathGenerator.tsx` - Generator UI (Box, Paper, Button). @frontend

### 5.3 Large Components (heavy MUI, complex)
- [x] 5.3.1 `NodeDetailPanel.tsx` (531 lines) - Slide-over panel (Box, Typography, Button, Chip, TextField). @frontend
- [x] 5.3.2 `ResourceSidebar.tsx` (338 lines) - Already partially migrated, finish remaining MUI. @frontend
- [ ] 5.3.3 `InspirationDock.tsx` (17KB) - Dock panel (Box, Paper, Tabs). @frontend
- [ ] 5.3.4 `SourcePanel.tsx` (35KB) - Source viewer (Box, Paper, Tabs, IconButton). @frontend
- [ ] 5.3.5 `AssistantPanel.tsx` (32KB) - Chat panel (Box, Paper, TextField, IconButton). @frontend
- [ ] 5.3.6 `KonvaCanvas.tsx` (119KB) - Main canvas (Box only, mostly Konva). @frontend

### 5.4 Canvas Subdirectory
- [x] 5.4.1 `canvas/GridBackground.tsx` - Grid pattern (no MUI, skip). @frontend
- [x] 5.4.2 `canvas/NodeEditor.tsx` - Node editor (Box, TextField). @frontend
- [x] 5.4.3 `canvas/SynthesisModeMenu.tsx` - Menu (Box, Paper, MenuItem). @frontend

### 5.5 Canvas-Nodes Subdirectory
- [x] 5.5.1 `canvas-nodes/MindMapCanvasNode.tsx` - MindMap node (Box, Paper). @frontend
- [x] 5.5.2 `canvas-nodes/SummaryCanvasNode.tsx` - Summary node (Box, Paper, Chip). @frontend

### 5.6 MindMap Subdirectory
- [x] 5.6.1 `mindmap/AIInsightBadge.tsx` - Badge (Konva only, no MUI, skip). @frontend
- [x] 5.6.2 `mindmap/CurvedMindMapEdge.tsx` - Edge (no MUI, skip). @frontend
- [x] 5.6.3 `mindmap/MindMapEdge.tsx` - Edge (no MUI, skip). @frontend
- [x] 5.6.4 `mindmap/MindMapNode.tsx` - Node (Konva only, no MUI, skip). @frontend
- [x] 5.6.5 `mindmap/MindMapViews.tsx` - Views (Modal wrapper). @frontend
- [x] 5.6.6 `mindmap/RichMindMapNode.tsx` (16KB) - Rich node (Konva only, no MUI, skip). @frontend
- [ ] 5.6.7 `mindmap/MindMapEditor.tsx` (33KB) - Editor (Box, Paper, Button). @frontend
- [x] 5.6.8 `mindmap/layoutAlgorithms.ts` - Pure TS (no MUI, skip). @frontend

## 6. Other Directories Migration (P2)
- [ ] 6.1 Migrate `inbox/` components (7 files). @frontend
- [ ] 6.2 Migrate `pdf/` components (13 files). @frontend
- [ ] 6.3 Migrate `dashboard/` components (2 files). @frontend
- [ ] 6.4 Migrate `dialogs/` components (2 files). @frontend
- [ ] 6.5 Migrate `settings/` components (2 files). @frontend
- [ ] 6.6 Migrate `layout/` components (4 files). @frontend

## 7. Icon Refactor (P2)
- [ ] 7.1 Decouple `Icon.tsx` from MUI `SvgIcon`. @frontend
- [ ] 7.2 Re-export icons using pure SVG or Lucide. @frontend
- [ ] 7.3 Validate all icon usages still work. @frontend

## 8. Cleanup (Future)
- [ ] 8.1 Remove direct `@mui/material` imports from feature code. @frontend
- [ ] 8.2 Audit and remove unused MUI packages from `package.json`. @frontend

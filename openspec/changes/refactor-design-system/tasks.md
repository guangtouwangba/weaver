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

## 5. Systematic Migration (P2)
- [ ] 5.1 Migrate remaining `studio/` components (25+ files). @frontend
- [ ] 5.2 Migrate `inbox/` components (7 files). @frontend
- [ ] 5.3 Migrate `pdf/` components (13 files). @frontend
- [ ] 5.4 Migrate `dashboard/` components (2 files). @frontend
- [ ] 5.5 Migrate `dialogs/` components (2 files). @frontend
- [ ] 5.6 Migrate `settings/` components (2 files). @frontend
- [ ] 5.7 Migrate `layout/` components (4 files). @frontend

## 6. Icon Refactor (P2)
- [ ] 6.1 Decouple `Icon.tsx` from MUI `SvgIcon`. @frontend
- [ ] 6.2 Re-export icons using pure SVG or Lucide. @frontend
- [ ] 6.3 Validate all icon usages still work. @frontend

## 7. Cleanup (Future)
- [ ] 7.1 Remove direct `@mui/material` imports from feature code. @frontend
- [ ] 7.2 Audit and remove unused MUI packages from `package.json`. @frontend

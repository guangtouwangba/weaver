# Proposal: Refactor Design System

## Why
The current frontend has deep coupling to MUI's component library, making future design updates costly and limiting visual differentiation. To enable a cohesive, custom design system without rewriting the entire application, we need to:
1. Abstract commonly used UI primitives behind internal wrappers.
2. Establish a design token system (colors, spacing, typography) that is library-agnostic.
3. Gradually migrate feature components to use internal primitives.

## What Changes

### 1. Design Token Foundation
Establish a centralized token system (`ui/tokens`) for colors, spacing, typography, shadows, and radii. These tokens become the source of truth for all styling:
-   **File**: `src/components/ui/tokens/index.ts`
-   **Exports**: `colors`, `spacing`, `typography`, `shadows`, `radii`.
-   Tokens align with Tailwind CSS v4 variables when possible.

### 2. Core UI Primitives (P0)
Create abstraction components that wrap MUI (initially) but expose a stable, library-agnostic API:

| Component      | Wraps MUI         | Notes                                      |
|----------------|-------------------|--------------------------------------------|
| `Stack`        | `Box`             | Flexbox container with gap/direction props |
| `Text`         | `Typography`      | Semantic text with variant + token colors  |
| `Button`       | `Button`          | Primary/Secondary/Ghost variants            |
| `IconButton`   | `IconButton`      | Inherits icon abstraction                  |
| `Surface`      | `Paper`           | Elevated container with token shadows      |
| `Tooltip`      | `Tooltip`         | Consistent hover hints                     |
| `Spinner`      | `CircularProgress`| Loading indicator                          |
| `Collapse`     | `Collapse`        | Animated show/hide                         |
| `Skeleton`     | `Skeleton`        | Loading placeholder                        |

These components go in `src/components/ui/primitives/`.

### 3. Composite Components (P1)
Build higher-level components from primitives for recurring patterns:
-   `Card` (Surface + header/body layout)
-   `Dialog` (Modal wrapper)
-   `Menu` / `ContextMenu`
-   `Input`, `TextField`, `Select`
-   `Tabs`, `Chip`, `Badge`

### 4. Migration Strategy (P2)
Incrementally update feature components (studio, dashboard, inbox, pdf, dialogs) to import from `@/components/ui` instead of `@mui/material`:
1. Start with leaf components (e.g., `TemplateCard`, `TagChip`).
2. Move up to container components.
3. Validate each batch with visual regression or manual spot checks.

### 5. Extend Icon Abstraction
Decouple `ui/icons/Icon.tsx` from `SvgIcon` by rendering raw `<svg>` elements or integrating with a headless icon set (e.g., Lucide, Radix Icons). This removes the transitive MUI dependency from icons.

## Goals
1. **Library Independence**: All feature code imports from `@/components/ui`, enabling future swaps (shadcn/ui, Radix, custom) without widespread changes.
2. **Design Consistency**: A single source of truth (tokens) ensures visual coherence.
3. **Maintainability**: Clear separation of "design system" vs. "product features".
4. **Incremental Adoption**: Existing MUI usage continues to work during migration.

## Risks
-   **Migration Scope**: 40+ files currently import MUI directly; full migration is large.
-   **API Mismatch**: Internal component APIs must be expressive enough to cover edge cases currently handled by MUI props.
-   **Bundle Size**: If MUI is not tree-shaken properly during transition, bundle may grow.

## Out of Scope
-   Full visual redesign (tokens and components initially mirror MUI's look).
-   Backend changes.
-   Removal of MUI from dependencies (happens in a later phase once migration is complete).

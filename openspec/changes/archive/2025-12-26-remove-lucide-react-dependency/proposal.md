# Change: Remove lucide-react dependency and create Icon abstraction layer

## Why
1. The project uses both `lucide-react` for icons and MUI for components - unnecessary duplication
2. **Future-proofing**: The design system may change in the future. An abstraction layer ensures only one place needs updating when switching icon libraries
3. Consolidating to a single source reduces bundle size and maintains visual consistency

## What Changes
- **Create icon abstraction layer** at `components/ui/icons/`
  - Single entry point (`index.ts`) exporting all icons
  - Abstract `Icon` component with consistent props interface
  - Easy to swap underlying implementation later
- Replace all direct `lucide-react` imports with abstraction layer imports
- Initially implement with `@mui/icons-material` as the underlying library
- Remove `lucide-react` from `package.json`

## Impact
- Affected specs: studio (icon system)
- Affected code: 25 files in `app/frontend/src/`
  - `components/studio/` (15 files)
  - `components/layout/` (1 file)
  - `components/dialogs/` (2 files)
  - `components/dashboard/` (1 file)
  - `components/pdf/` (3 files)
  - `components/settings/` (2 files)
  - `components/ui/` (IconWrapper → new icons/ folder)
  - `app/` pages (3 files)
- **New files**: `components/ui/icons/index.ts`, `components/ui/icons/Icon.tsx`


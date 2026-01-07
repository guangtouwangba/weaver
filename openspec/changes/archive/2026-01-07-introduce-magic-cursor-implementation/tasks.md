# Tasks: Introduce Magic Cursor

## Spec Phase
- [x] Draft spec deltas for Magic Cursor interactions `openspec/changes/introduce-magic-cursor/specs/studio/spec.md`
- [x] Validate proposal `openspec validate introduce-magic-cursor --strict`
- [x] Submit proposal for review

## Implementation Phase
- [x] Add 'magic' to ToolMode type definition (`CanvasToolbar.tsx`)
- [x] Add Magic Cursor button to toolbar (`CanvasControls.tsx`, `CanvasToolbar.tsx`)
- [x] Add keyboard shortcut M for magic mode (`KonvaCanvas.tsx`)
- [x] Implement MagicSelectionBox with gradient styling (purple gradient border, dashed line)
- [x] Create IntentMenu component (`IntentMenu.tsx`) with Draft Article and Action List options
- [x] Handle magic selection interaction in KonvaCanvas (show Intent Menu on mouse release)
- [x] Add PlaylistAddCheckIcon to icons (`icons/index.ts`)

## Deferred to Separate Proposal
The following tasks are moved to `add-magic-cursor-generation`:
- [ ] Connect Intent Menu actions to backend generation APIs
- [ ] Implement Super Cards (Document Card, Ticket Card) rendering

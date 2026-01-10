# Tasks: Update Design System to Violet Theme

## 1. Core Token Updates (P0)

- [x] 1.1 Update `app/frontend/src/components/ui/tokens/colors.ts`
  - Replace `primary` scale (Sage Green → Violet)
  - Replace `neutral` scale (Warm Stone → Cool Gray)
  - Add new `accent` scale (Rose/Coral)
  - Update `background`, `text`, `border` semantic colors
  - Add `selection` and `tab` semantic colors

- [x] 1.2 Update `app/frontend/src/theme/theme.ts`
  - Replace `brand` colors with Violet scale
  - Replace `gray` overrides with Cool Gray scale
  - Update global body styles (white background)
  - Add `accent` color scale
  - Update focus ring to violet

- [x] 1.3 Update `app/frontend/src/components/ui/tokens/mindmap.ts`
  - Update card, status, text, tags colors to use new palette
  - Add `selection` style tokens with dashed border

## 2. Selection State Implementation (P0)

- [x] 2.1 Add selection style tokens to `colors.ts`
  - Dashed border style config
  - Selected background (#F5F3FF)
  - Focus ring colors (#C4B5FD)

- [x] 2.2 Update canvas selection states in `KonvaCanvas.tsx`
  - Node selection: dashed purple border (`dash={[6, 4]}`)
  - Selection color: #7C3AED
  - Selection shadow: violet-tinted

## 3. Component Updates (P1)

- [x] 3.1 Update `CommandPalette.tsx`
  - Comment updated to reference Violet theme
  - Uses tokens which now reference violet colors

- [x] 3.2 `Chip.tsx` already uses token references
  - Automatically updated via `colors.primary` tokens

- [x] 3.3 Update `ProjectCard.tsx`
  - Replace Teal palette entry with Violet

- [x] 3.4 Sidebar/navigation components
  - Uses Chakra theme which is now violet

## 4. Hardcoded Color Cleanup (P1)

- [x] 4.1 Search and replace hardcoded green values
  - `#388E3C`, `#2E7D32`, `#1B5E20` → `#7C3AED`

- [x] 4.2 Search and replace hardcoded teal values
  - `#0D9488`, `#0F766E`, `#2DD4BF` → `#7C3AED`, `#A78BFA`

- [x] 4.3 Files updated:
  - `KonvaCanvas.tsx` - node styles, selection
  - `SummaryCard.tsx` - gradient, shadows
  - `dashboard/page.tsx` - tab active states
  - `InspirationDock.tsx` - project color
  - `DocumentPreviewCard.tsx` - active states
  - `ProjectCard.tsx` - palette entry

## 5. Tab/Button Active States (P1)

- [x] 5.1 Tab active state in theme.ts
  - Active: Violet text (#7C3AED)
  - Hover: Violet-400 (#A78BFA)
  - Inactive: Gray text

- [x] 5.2 Dashboard page tabs updated
  - Uses #7C3AED for active state

## 6. Accent Color Integration (P2)

- [x] 6.1 Added `accent` scale to colors.ts
  - Rose/Coral palette for hearts, likes

- [x] 6.2 Added `accent` to theme.ts
  - Available for future use

## 7. Validation (P0)

- [x] 7.1 Linter check passed
  - No errors in updated files

- [ ] 7.2 Visual regression check
  - Manual verification needed

- [ ] 7.3 Cross-browser verification
  - Manual verification needed

## Files Modified

| File | Changes |
|------|---------|
| `colors.ts` | Primary, neutral, accent, selection, tab tokens |
| `theme.ts` | Brand, gray, accent colors, body bg, focus ring |
| `mindmap.ts` | Card tokens, tags, selection styles |
| `KonvaCanvas.tsx` | Node styles, selection dash, colors |
| `SummaryCard.tsx` | Gradient, shadows to violet |
| `dashboard/page.tsx` | Tab active state |
| `InspirationDock.tsx` | Project color |
| `DocumentPreviewCard.tsx` | Active state colors |
| `ProjectCard.tsx` | Palette entry |
| `CommandPalette.tsx` | Comment update |

## Summary

- **Primary**: Sage Green → Violet (#7C3AED)
- **Neutral**: Warm Stone → Cool Gray  
- **Selection**: Solid border → Dashed purple border
- **Tab Active**: Teal → Violet
- **Background**: Warm white → Pure white
- **Accent**: New Rose/Coral scale for interactive elements

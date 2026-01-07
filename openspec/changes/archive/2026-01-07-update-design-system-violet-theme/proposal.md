# Proposal: Update Design System to Violet Theme

## Change ID
`update-design-system-violet-theme`

## Summary
Update the application's design system from Sage Green + Warm Stone to Violet + Cool Gray, creating a more modern, clean aesthetic inspired by contemporary productivity tools.

## Background

### Current State
- **Primary Color**: Sage Green (#388E3C) - natural, matte feel
- **Neutral Palette**: Warm Stone (brown/yellow undertones) for paper-like reading
- **Background**: Warm white (#FAFAF9)
- **Selection State**: Solid green borders

### Target State (Reference Design)
- **Primary Color**: Soft Violet (#7C3AED) - modern, approachable
- **Neutral Palette**: Cool Gray (neutral undertones) for clean, crisp UI
- **Background**: Pure white (#FFFFFF)
- **Selection State**: Purple dashed borders (distinctive, playful)
- **Accent Colors**: Coral/Pink for interactive elements (likes, hearts)

## Motivation
1. **Modernization**: Violet is currently more on-trend for productivity/knowledge tools
2. **Differentiation**: Purple dashed selection is a unique visual signature
3. **Clarity**: Cool grays with pure white provide higher perceived clarity
4. **Brand Identity**: Violet conveys creativity and intelligence - fitting for a "thinking assistant"

## Scope

### In Scope
- Update `colors.ts` primary palette (Green → Violet)
- Update `colors.ts` neutral palette (Warm Stone → Cool Gray)
- Update `theme.ts` Chakra brand colors
- Update `mindmap.ts` card tokens
- Update selection/highlight states to use dashed purple borders
- Add accent color for interactive elements (hearts, active tabs)
- Update any hardcoded color values in components

### Out of Scope
- Dark mode (deferred to future iteration)
- Component restructuring
- New components or layouts

## Design Decisions

### 1. Primary Palette: Violet
```
50:  #F5F3FF  (very light violet)
100: #EDE9FE
200: #DDD6FE
300: #C4B5FD
400: #A78BFA
500: #7C3AED  (main brand color)
600: #6D28D9
700: #5B21B6
800: #4C1D95
900: #3B0764
```

### 2. Neutral Palette: Cool Gray
```
50:  #F9FAFB  (background)
100: #F3F4F6
200: #E5E7EB  (borders)
300: #D1D5DB
400: #9CA3AF
500: #6B7280  (secondary text)
600: #4B5563
700: #374151
800: #1F2937  (primary text)
900: #111827
```

### 3. Accent Colors
- **Coral/Pink** for hearts, likes: `#F43F5E` (Rose-500)
- **Tab Active**: Violet-500 (`#7C3AED`) instead of red

### 4. Selection State
- Dashed border: `2px dashed #7C3AED`
- Light violet background: `#F5F3FF` or `#EDE9FE`

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing component styles | Use centralized tokens; grep for hardcoded colors |
| Accessibility contrast issues | Validate with WCAG contrast checker |
| Inconsistent updates | Comprehensive component audit in tasks |

## Success Criteria
1. All components use updated color tokens
2. No hardcoded old colors remain
3. Selection states use dashed purple borders
4. WCAG AA contrast compliance maintained

## Related Changes
- None (standalone design update)


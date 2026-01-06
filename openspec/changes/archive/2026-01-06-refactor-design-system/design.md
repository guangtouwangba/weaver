# Design: Refactor Design System

## Architecture Overview

```
src/components/
├── ui/
│   ├── tokens/           # NEW: Design tokens
│   │   ├── colors.ts
│   │   ├── spacing.ts
│   │   ├── typography.ts
│   │   ├── shadows.ts
│   │   └── index.ts
│   ├── primitives/       # NEW: Core component wrappers
│   │   ├── Stack.tsx
│   │   ├── Text.tsx
│   │   ├── Button.tsx
│   │   ├── IconButton.tsx
│   │   ├── Surface.tsx
│   │   ├── Tooltip.tsx
│   │   ├── Spinner.tsx
│   │   ├── Collapse.tsx
│   │   ├── Skeleton.tsx
│   │   └── index.ts
│   ├── composites/       # NEW: Higher-level components
│   │   ├── Card.tsx
│   │   ├── Dialog.tsx
│   │   ├── Menu.tsx
│   │   ├── Input.tsx
│   │   └── index.ts
│   ├── icons/            # EXISTING: Already abstracted
│   │   ├── Icon.tsx      # Refactor to remove SvgIcon dep
│   │   ├── types.ts
│   │   └── index.ts
│   └── index.ts          # Barrel export
├── dashboard/
├── studio/
├── inbox/
└── ...
```

## Token System Design

Tokens are plain TypeScript objects, not CSS-in-JS theme providers, enabling usage in both React and CSS:

```typescript
// tokens/colors.ts
export const colors = {
  primary: { 500: '#6366F1', 600: '#4F46E5', ... },
  neutral: { 50: '#FAFAFA', 100: '#F5F5F5', ... },
  success: { 500: '#10B981', ... },
  error: { 500: '#EF4444', ... },
} as const;
```

Can be synced to Tailwind CSS v4 via `@theme` directive or CSS custom properties.

## Component API Design

### Stack
```tsx
<Stack direction="row" gap={4} align="center" justify="between">
  <Text>Left</Text>
  <Button variant="primary">Right</Button>
</Stack>
```

### Text
```tsx
<Text variant="h1" color="primary">Heading</Text>
<Text variant="body" color="muted">Paragraph text</Text>
```

Variants: `h1`, `h2`, `h3`, `body`, `caption`, `label`, `overline`.

### Button
```tsx
<Button variant="primary" size="md" loading>Save</Button>
<Button variant="ghost" icon={<AddIcon />} />
```

Variants: `primary`, `secondary`, `ghost`, `danger`.

### Surface
```tsx
<Surface elevation={1} padding={4} radius="md">
  Content
</Surface>
```

## Migration Path

1. **Phase 1 (P0)**: Create `tokens/` and `primitives/` with internal exports.
2. **Phase 2 (P1)**: Migrate 5 pilot components (e.g., `TemplateCard`, `TagChip`, `CanvasControls`) to validate API.
3. **Phase 3 (P1)**: Build `composites/` (Card, Dialog, Menu).
4. **Phase 4 (P2)**: Systematic migration of remaining 35+ files.
5. **Phase 5 (P2)**: Swap icon implementation to headless SVG.
6. **Phase 6 (Future)**: Remove MUI dependency entirely.

## Trade-offs

| Approach                | Pros                             | Cons                                    |
|-------------------------|----------------------------------|-----------------------------------------|
| Wrap MUI (chosen)       | Fast, low risk, leverages stable API | Still depends on MUI internally         |
| Build from scratch      | Full control, smaller bundle     | High effort, must reimplement a11y       |
| Use shadcn/ui or Radix  | Modern, headless                 | Requires paradigm shift, learning curve |

**Decision**: Start by wrapping MUI for quick wins; swap internals to Radix/headless later.

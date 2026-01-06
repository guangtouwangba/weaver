# Design: Adopt Chakra UI with Warm Gray Theme

## Context
当前项目使用 Tailwind CSS v4 + 自定义 tokens 构建 UI。此前已完成将 MUI 解耦为 `ui/primitives` 抽象层的重构。本次变更利用该抽象层，将底层实现替换为 Chakra UI，同时引入暖灰色主题改善阅读体验。

**Constraints:**
- Solo developer - must be incrementally adoptable
- Canvas rendering (Konva) continues using Tailwind/raw CSS
- Existing primitives API must remain stable

## Goals / Non-Goals

**Goals:**
- Install and configure Chakra UI with custom warm gray theme
- Update `ui/tokens/colors.ts` to warm gray palette
- Migrate primitives to use Chakra components internally
- Maintain backward compatibility with existing feature code

**Non-Goals:**
- Full visual redesign beyond color temperature
- Migrate Konva canvas styling (remains Tailwind/CSS)
- Remove Tailwind (coexists with Chakra for layout utilities)

## Decisions

### 1. Chakra UI v2 vs v3
**Decision:** Use Chakra UI v2 (stable)
- v3 is still in RC, v2 has mature ecosystem
- TypeScript support is excellent
- Theme extension API is well-documented

### 2. Color Palette Source
**Decision:** Use Stone palette from Tailwind as warm gray base
- Stone (`#FAFAF9`, `#F5F5F4`, `#E7E5E4`...) has subtle yellow/brown undertones
- Matches Miro/Notion warmth without being too yellow
- Semantic colors (success, error, warning) remain unchanged

### 3. Integration Strategy
**Decision:** Dual-layer approach
```
Feature Code → ui/primitives (stable API) → Chakra Components (internal)
             → ui/tokens (colors/spacing) → Chakra theme.ts
```
- Feature code never imports from `@chakra-ui` directly
- Primitives expose stable props (variant, size, colorScheme)
- Chakra theme consumes tokens for consistency

### 4. Provider Setup
**Decision:** Single ChakraProvider at app root
- Located in `app/layout.tsx` or new `providers.tsx`
- Theme extends Chakra defaults with warm colors
- `ColorModeScript` for SSR hydration

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Bundle size increase (~30-50KB gzipped) | Tree-shaking, code-split Chakra components |
| Tailwind + Chakra redundancy | Chakra for components, Tailwind for layout/canvas |
| Learning curve | Chakra docs are excellent; primitives hide complexity |

## Migration Plan

### Phase 1: Foundation (This Change)
1. Install Chakra dependencies
2. Create theme.ts with warm gray palette
3. Set up ChakraProvider
4. Update `ui/tokens/colors.ts` to warm values
5. Verify existing UI renders correctly

### Phase 2: Primitives Migration (Future)
- Migrate one primitive at a time (Button → Text → Surface...)
- Each primitive switches internal implementation to Chakra
- No API changes to primitives

### Rollback
- Remove ChakraProvider wrapper
- Revert colors.ts to cold grays
- No feature code changes needed

## Open Questions
1. Should we add a dark mode toggle immediately, or defer?
   - **Recommendation:** Defer to keep scope minimal
2. Override Chakra's focus ring to match warm theme?
   - **Recommendation:** Yes, use `brand.500` for focus indicators

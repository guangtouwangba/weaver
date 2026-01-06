# Change: Adopt Chakra UI with Warm Gray Theme

## Why
长时间阅读知识管理类应用需要视觉舒适度。当前设计使用冷灰色 (neutral grays)，与 Notion/Miro/Substack 这类"纸张感"产品相比缺乏温暖人文气质。Chakra UI 提供完善的主题系统和无障碍支持，配合自定义暖灰色板可显著提升阅读体验。

## What Changes

### 1. Install Chakra UI
- Add `@chakra-ui/react` and peer dependencies to `package.json`
- Create `ChakraProvider` wrapper in app root

### 2. Warm Gray Color System
Replace neutral grays with warm grays (Stone palette):
| Token | Current | New (Warm) | Usage |
|-------|---------|------------|-------|
| `gray.50` | `#FAFAFA` | `#FAFAF9` | Canvas background |
| `gray.100` | `#F5F5F5` | `#F5F5F4` | Panel/Sidebar |
| `gray.200` | `#E5E5E5` | `#E7E5E4` | Borders |
| `gray.800` | `#262626` | `#292524` | Primary text |

### 3. Brand Accent Colors
- Primary (Teal): `brand.500: #0D9488`, `brand.600: #0F766E`
- Selection highlight: `teal.400`

### 4. Global Styles
- Body background: `gray.50`
- Body text: `gray.800`
- Reduced contrast for eye comfort

### 5. Component Decoupling
- Keep existing `ui/primitives` as abstraction layer
- Primitives internally switch to Chakra components
- Feature code continues importing from `@/components/ui`

## Impact
- **Affected specs**: `frontend`, `design-system`
- **Affected code**: `ui/tokens/colors.ts`, `ui/primitives/*`, app layout providers
- **Breaking changes**: None (primitives API unchanged)

## Goals
1. **Warm visual identity** - Paper-like reading experience
2. **Maintainability** - Chakra's theme system simplifies token management
3. **Decoupled architecture** - Easy to swap design system later
4. **Accessibility** - Chakra's built-in a11y features

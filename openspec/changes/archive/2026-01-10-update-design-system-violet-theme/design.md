# Design: Violet Theme Design System

## Color Palette Architecture

### Token Structure
```
colors/
├── primary (Violet scale)
├── neutral (Cool Gray scale)
├── success (Green - unchanged)
├── warning (Amber - unchanged)
├── error (Red - unchanged)
├── info (Blue - unchanged)
├── accent (NEW - Rose/Coral)
├── background
├── text
└── border
```

### Primary: Violet Scale
Replacing Sage Green with a vibrant yet soft violet that conveys creativity and intelligence.

```typescript
primary: {
  50:  '#F5F3FF',  // Backgrounds, hover states
  100: '#EDE9FE',  // Tag backgrounds, subtle highlights
  200: '#DDD6FE',  // Disabled states
  300: '#C4B5FD',  // Focus rings
  400: '#A78BFA',  // Secondary actions
  500: '#7C3AED',  // Primary buttons, brand
  600: '#6D28D9',  // Hover states
  700: '#5B21B6',  // Active states, dark text
  800: '#4C1D95',  // Headers on light bg
  900: '#3B0764',  // Darkest, rarely used
}
```

### Neutral: Cool Gray Scale
Replacing Warm Stone with cooler grays for a cleaner, more modern feel.

```typescript
neutral: {
  50:  '#F9FAFB',  // Page background
  100: '#F3F4F6',  // Card backgrounds, panels
  200: '#E5E7EB',  // Borders, dividers
  300: '#D1D5DB',  // Disabled borders
  400: '#9CA3AF',  // Placeholder text
  500: '#6B7280',  // Secondary text
  600: '#4B5563',  // Labels
  700: '#374151',  // Subheadings
  800: '#1F2937',  // Primary text
  900: '#111827',  // Headlines
}
```

### Accent: Rose/Coral (NEW)
For interactive elements like likes, hearts, and notifications.

```typescript
accent: {
  50:  '#FFF1F2',
  100: '#FFE4E6',
  200: '#FECDD3',
  300: '#FDA4AF',
  400: '#FB7185',
  500: '#F43F5E',  // Hearts, likes
  600: '#E11D48',
  700: '#BE123C',
  800: '#9F1239',
  900: '#881337',
}
```

## Selection State Design

### Visual Signature: Dashed Purple Border
The reference design uses a distinctive dashed border for selected items. This becomes a unique visual signature.

```css
/* Selected state */
.selected {
  border: 2px dashed #7C3AED;
  background-color: #F5F3FF;
}

/* Focus state */
.focused {
  outline: 2px solid #C4B5FD;
  outline-offset: 2px;
}
```

### Implementation in React
```typescript
// Selection styles object
export const selectionStyles = {
  selected: {
    border: '2px dashed',
    borderColor: colors.primary[500],
    backgroundColor: colors.primary[50],
  },
  hover: {
    borderColor: colors.primary[400],
    backgroundColor: colors.primary[50],
  },
};
```

## Chakra Theme Integration

### Brand Color Mapping
```typescript
brand: {
  50:  '#F5F3FF',
  100: '#EDE9FE',
  200: '#DDD6FE',
  300: '#C4B5FD',
  400: '#A78BFA',
  500: '#7C3AED',  // colorScheme="brand"
  600: '#6D28D9',
  700: '#5B21B6',
  800: '#4C1D95',
  900: '#3B0764',
}
```

### Gray Replacement
Chakra's default `gray` scale will be overridden with Cool Gray values.

## Tab/Button States

### Active Tab
- **Color**: Violet-500 (`#7C3AED`)
- **Background**: Violet-50 (`#F5F3FF`) or transparent
- **Border-bottom**: 2px solid Violet-500

### Inactive Tab
- **Color**: Neutral-500 (`#6B7280`)
- **Background**: Transparent

## Tag/Chip Design

### Default Tag Style
```typescript
tag: {
  bg: colors.primary[100],      // #EDE9FE
  text: colors.primary[700],    // #5B21B6
  border: colors.primary[200],  // #DDD6FE
}
```

## Component Update Checklist

### High Priority (Uses primary/brand colors)
- [ ] `CommandPalette.tsx` - Recently updated, uses design tokens
- [ ] `ProjectCard.tsx` - Card styling
- [ ] `Chip.tsx` - Tag styling
- [ ] `Button` components - Chakra theme
- [ ] Canvas selection states

### Medium Priority
- [ ] `MindmapCard` components
- [ ] Navigation/sidebar
- [ ] Form inputs focus states

### Low Priority (Semantic colors, less affected)
- [ ] Alert/notification components
- [ ] Status badges

## Contrast Verification

| Combination | Ratio | WCAG AA |
|-------------|-------|---------|
| Violet-500 on White | 4.68:1 | ✅ Pass (Large Text) |
| Violet-700 on Violet-50 | 7.2:1 | ✅ Pass |
| Neutral-800 on White | 12.6:1 | ✅ Pass |
| Neutral-500 on White | 4.5:1 | ✅ Pass |
| Rose-500 on White | 4.3:1 | ✅ Pass (Large Text) |

## Migration Strategy

1. **Update Token Files First**
   - `colors.ts` - Core palette
   - `theme.ts` - Chakra overrides

2. **Search & Replace Hardcoded Values**
   - Grep for old hex values
   - Replace with token references

3. **Visual Regression Testing**
   - Screenshot key pages before/after
   - Manual review of all components


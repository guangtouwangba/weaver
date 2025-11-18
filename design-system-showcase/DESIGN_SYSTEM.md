# Design System - Complete Implementation

This document outlines the complete design system implementation based on `design.json` specifications.

## 🎨 Design Language: Playful Productivity Workspace UI

A light, optimistic, and friendly design system optimized for day-to-day productivity tools.

---

## 📐 Core Design Tokens

### Color System

#### Surface Colors
- `page`: #F5F6F9 - Very light neutral gray canvas
- `card`: #FFFFFF - White cards and panels
- `subtle`: #F9FAFB - Subtle backgrounds

#### Text Colors
- `primary`: #111827 - Main content
- `secondary`: #4B5563 - Supporting text
- `muted`: #9CA3AF - Tertiary information
- `on-accent`: #FFFFFF - Text on colored backgrounds
- `on-warning`: #1F2933 - Text on warning backgrounds
- `on-positive`: #064E3B - Text on success backgrounds

#### Border Colors
- `subtle`: #E5E7EB - Light borders and dividers
- `strong`: #D1D5DB - Prominent borders
- `focus`: #2563EB - Focus indicators

#### Primary Colors
- `strong`: #3B82F6 - Main call-to-action
- `soft`: #E0ECFF - Light background for primary elements
- `hover`: #2563EB - Hover state
- `pressed`: #1D4ED8 - Active/pressed state

#### Semantic Colors
- **Emerald**: success states (#10B981 strong, #D1FAE5 soft)
- **Orange**: warnings (#F97316 strong, #FFEDD5 soft)
- **Yellow**: pending states (#FACC15 strong, #FEF9C3 soft)
- **Red**: errors and alerts (#F97373 strong, #FEE2E2 soft)
- **Secondary**: indigo, purple, pink for accents

### Spacing Scale
- `xxs`: 4px - Minimal gaps
- `xs`: 8px - Between inline elements
- `sm`: 12px - Internal component spacing
- `md`: 16px - Standard padding
- `lg`: 24px - Between sections
- `xl`: 32px - Major section separation
- `xxl`: 40px - Large vertical rhythm

### Border Radius
- `xs`: 4px - Subtle rounding
- `sm`: 8px - Inputs and small containers
- `md`: 12px - Medium containers
- `lg`: 16px - Cards and primary panels
- `pill`: 999px - Fully rounded buttons and chips

### Elevation (Shadows)
- `soft`: 0 4px 16px rgba(15, 23, 42, 0.08) - Cards and modals
- `medium`: 0 8px 24px rgba(15, 23, 42, 0.12) - Elevated overlays

### Typography Scale

| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|--------|
| display-lg | 32px | 1.25 | 600 | Top-level page titles |
| display-md | 24px | 1.3 | 600 | Important section headings |
| title | 20px | 1.3 | 600 | Card titles and key labels |
| subtitle | 16px | 1.4 | 500 | Subheadings, supporting labels |
| body | 14px | 1.5 | 400 | Main body copy, descriptions |
| body-bold | 14px | 1.5 | 600 | Emphasized text |
| caption | 12px | 1.5 | 400 | Secondary and meta information |
| label | 11px | 1.4 | 600 | Button labels, tags, chips |

### Motion
- **Fast**: 120ms - Quick transitions
- **Normal**: 180ms - Standard animations
- **Slow**: 240ms - Deliberate movements
- **Easing**: cubic-bezier(0.2, 0.8, 0.2, 1) - Standard easing

---

## 🧩 Components

### 1. Button
**Variants:** Primary, Secondary, Ghost, Tiny

#### Primary Button
- Height: 40px
- Padding: 20px horizontal
- Background: primary-strong (#3B82F6)
- Text: white
- Border radius: pill (999px)
- Hover: Darker background + soft shadow
- Active: Pressed state, shadow removed

#### Secondary Button
- Height: 36px
- Padding: 18px horizontal
- Background: white with strong border
- Hover: Subtle background fill

#### Ghost Button
- Height: 32px
- Transparent background
- Minimal hover effect

#### Tiny Button
- Height: 24px
- Padding: 12px horizontal
- Compact for dense interfaces

**States:** Default, Hover, Active, Focus (2px ring), Disabled (40% opacity)

---

### 2. Chip / Tag
**Height:** 24px | **Padding:** 10px horizontal | **Shape:** Pill

#### Semantic Variants
- **Active**: Blue background (#E0ECFF), blue text
- **Pending**: Yellow background (#FEF9C3), dark text
- **Confirmed**: Emerald background (#D1FAE5), emerald text
- **Alert**: Red background (#FEE2E2), red text
- **Closed**: Subtle background, muted text

#### Features
- Optional avatar on left (20px circular)
- Optional remove button (16px circular close icon)
- Support for person chips with avatars

---

### 3. Card
**Background:** White | **Padding:** 20px | **Corner radius:** 16px | **Shadow:** Soft

#### Structure
- **Header**: Title (left) + actions (right), 12px bottom spacing
- **Body**: 8px spacing between rows
- **Footer**: Optional, 12px top spacing, 1px divider

#### Usage
- Group related information
- Maintain consistent internal spacing
- Visually distinct from page background

---

### 4. Input
**Height:** 40px | **Padding:** 12px horizontal | **Border radius:** 8–12px

#### Features
- Label with caption style
- Optional icon on left (with proper padding)
- Placeholder text in muted color
- Helper text below
- Error state with red border and text
- Focus state: border-focus + 2px ring

---

### 5. TokenizedInput (NEW)
**As specified in design.json**

#### Features
- Multi-select field with token chips inside
- Height: 44px minimum
- Padding: 10px horizontal, 8px vertical
- 2px border, rounded 12px
- Focus: border switches to primary color + ring
- Tokens display with 8px inline gap, 4px row gap
- Max visible rows: 2 (scrollable)
- Backspace removes last token
- Enter adds new token

#### Person Chip Subtype
- 20px circular avatar on left
- 6px spacing from label
- Remove icon on right

---

### 6. Select / Dropdown
Custom-styled select component with:
- Dropdown animation (slideDown 180ms)
- Selected state highlighting
- Keyboard navigation support
- Max height with scroll

---

### 7. Toggle Switch
- Width: 44px, Height: 24px
- Track: Rounded pill, subtle background
- Knob: 20px circle, white with shadow
- Checked: Primary blue track
- Focus: 2px ring
- Transition: 180ms

---

### 8. Tabs / Segmented Controls
**Height:** 32px | **Padding:** 14px horizontal | **Gap:** 8px

#### Active State
- Background: primary-strong
- Text: white, bold

#### Inactive State
- Background: subtle
- Text: secondary color

#### Usage
- Limit to 3–5 options
- Clear visual dominance for active tab

---

### 9. Modal
#### Structure
- Backdrop: 50% opacity black overlay
- Container: White card, rounded 16px, shadow-medium
- Animation: fadeIn 180ms + slideUp
- ESC key to close
- Click outside to close

#### Sizes
- sm: max-w-md (448px)
- md: max-w-lg (512px)
- lg: max-w-2xl (672px)
- xl: max-w-4xl (896px)

---

### 10. Banner / Notification
**Layout:** Horizontal strip with icon, message, optional action/close

#### Variants
- **Info**: Blue background (#E0ECFF), blue text
- **Success**: Emerald background (#D1FAE5), emerald text
- **Warning**: Orange background (#FFEDD5), dark text
- **Error**: Red background (#FEE2E2), dark text

---

### 11. Progress Bar
**Height:** 6px | **Corner radius:** Pill | **Track:** Subtle background

#### Colors
- Primary blue
- Emerald for success
- Orange for warnings
- Red for critical

---

### 12. Avatar
**Shapes:** Circle | **Sizes:** 24px (sm), 32px (md), 40px (lg)

#### Avatar Group
- Overlapping circles with 8px negative spacing
- Ring: 2px white border
- "+N" indicator for overflow
- Max visible: configurable (default 3)

---

### 13. List Item
**Height:** 56px | **Padding:** 16px horizontal

#### Structure
- Avatar/icon on left
- Text stack in middle (title + subtitle)
- Status chip or actions on right
- Subtle dividers between items

---

### 14. Empty State
**Layout:** Centered content

#### Structure
- Icon or illustration
- Brief headline (subtitle style)
- Short supporting text (body)
- Single primary CTA
- Encouraging and positive tone

---

### 15. MetricCard
Display key metrics with:
- Large number (display-md, 24px, bold)
- Label (caption)
- Optional change indicator (↑/↓ with color)
- Optional icon

---

### 16. ChatBox (NEW)
Full messaging interface with:
- Header: participants, status, actions
- Messages area: scrollable, auto-scroll
- Message bubbles: rounded corners, aligned left/right
- Input area: integrated emoji, attachment, send button
- Character counter
- Keyboard shortcuts

---

### 17. PersonalCenter (NEW)
Comprehensive user profile with:
- Profile header with avatar, stats (4-column grid)
- Tabbed navigation (Profile, Settings, Activity, Preferences)
- Edit mode toggle
- Progress indicators
- Privacy toggles
- Appearance settings
- Activity timeline

---

## 🎯 Icon System (NEW)

**Style:** Simple, geometric line icons
**Stroke Weight:** 1.5px
**Cap Style:** Rounded
**Sizes:** sm (16px), md (20px), lg (24px)

### Icon Categories
1. **Navigation**: menu, close, chevrons, arrows
2. **Communication**: send, mail, chat
3. **Files & Media**: attachment, image, camera, download
4. **Interface**: search, settings, bell, user, heart, star
5. **Status**: check, info, warning, error
6. **Content**: plus, minus, edit, trash, copy
7. **More**: moreVertical, moreHorizontal

---

## 📱 Responsive Behavior

### Grid System
- 12-column grid
- Gutter: 24px
- Max content width: 1280px
- Containers snap to 4-column or 6-column groupings

### Breakpoints
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

---

## ♿ Accessibility

### Contrast
- All text meets WCAG AA standards
- Status chips use sufficiently dark text on light backgrounds

### Keyboard Navigation
- All interactive components keyboard accessible
- Focus states clearly visible (2px ring)
- Logical tab order

### Hit Targets
- Minimum 40x40px for interactive elements
- Adequate padding around icon buttons

### Screen Readers
- Descriptive labels for icons
- Proper ARIA labels
- Semantic HTML structure

---

## 🚀 Implementation Notes

### CSS Framework
- **Tailwind CSS v3** with custom theme extension
- All design tokens mapped to Tailwind config
- Custom animations defined in index.css

### Component Library
- **React** components with consistent API
- Props-driven customization
- TypeScript-ready (prop types included)

### File Structure
```
src/
├── components/
│   ├── Button.jsx
│   ├── Chip.jsx
│   ├── Card.jsx
│   ├── Input.jsx
│   ├── TokenizedInput.jsx
│   ├── Select.jsx
│   ├── Toggle.jsx
│   ├── Modal.jsx
│   ├── Dropdown.jsx
│   ├── Icon.jsx
│   ├── ChatBox.jsx
│   ├── PersonalCenter.jsx
│   └── ... (15+ components)
├── App.jsx (Showcase)
└── index.css (Animations + global styles)
```

---

## ✅ Design.json Compliance Checklist

- [x] All color tokens implemented
- [x] Typography scale exact match
- [x] Spacing scale (xxs to xxl)
- [x] Border radius scale
- [x] Shadow system (soft, medium)
- [x] Motion timing (120ms, 180ms, 240ms)
- [x] Button specifications (all 4 variants)
- [x] Chip/Tag with all semantic variants
- [x] TokenizedInput field (full spec)
- [x] Card layout (header, body, footer)
- [x] Input states (default, focus, error)
- [x] Toggle switch (44x24px, animated)
- [x] Tabs and segmented controls
- [x] Modal with animations
- [x] Banner notifications
- [x] Progress bars
- [x] Avatar and avatar groups
- [x] List items
- [x] Empty states
- [x] Icon library (1.5px stroke, rounded caps)
- [x] ChatBox component
- [x] PersonalCenter component

---

## 📖 Usage Guidelines

### Do's
✅ Use generous white space  
✅ Maintain consistent spacing between sections  
✅ Use primary blue for main CTAs  
✅ Pair semantic colors with appropriate icons  
✅ Keep interactions shallow and responsive  
✅ Show summaries by default, details on demand  

### Don'ts
❌ Don't flood large areas with accent colors  
❌ Don't use heavy or harsh shadows  
❌ Don't stack multiple primary buttons  
❌ Don't rely solely on color for information  
❌ Don't use dense nesting of components  
❌ Don't crowd content - err on more whitespace  

---

## 🎓 Best Practices

1. **Consistency**: Use the same patterns across all interfaces
2. **Clarity**: Prioritize scannability and clear hierarchy
3. **Feedback**: Provide clear visual feedback for all interactions
4. **Performance**: Keep animations smooth (180ms standard)
5. **Accessibility**: Test with keyboard and screen readers
6. **Responsive**: Ensure components work on all screen sizes

---

## 📞 Support

For questions about this design system:
- Review `design.json` for the source specifications
- Check component examples in the showcase app
- Reference COMPONENTS.md for detailed usage examples

**Version:** 1.0.0  
**Last Updated:** November 2025  
**Status:** ✅ Complete Implementation


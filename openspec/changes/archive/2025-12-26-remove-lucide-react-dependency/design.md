## Context
The frontend currently uses two icon libraries:
- `lucide-react` (^0.554.0) - Used in 25 files for ~60 unique icons
- MUI components via `@mui/material` - Used for all UI components

This creates unnecessary bundle bloat and visual inconsistency. Additionally, the design system may change in the future, requiring a flexible abstraction layer.

## Goals / Non-Goals
- **Goals:**
  - **Abstraction layer** for easy design system swapping
  - Single icon library for consistency
  - Reduced bundle size
  - Maintained visual quality and accessibility
  
- **Non-Goals:**
  - Changing icon appearances drastically
  - Adding new icons beyond what's currently used

## Decisions

### Decision 1: Create Icon Abstraction Layer
**Rationale:**
- Future-proof: When design system changes, only update one folder
- Consistent API across all components
- Centralized icon management

**Architecture:**
```
components/ui/icons/
├── index.ts          # Re-exports all icons + Icon component
├── Icon.tsx          # Base Icon component with standard props
├── types.ts          # IconProps interface
└── mappings.ts       # Icon name to component mapping (optional)
```

### Decision 2: Use @mui/icons-material as Initial Implementation
**Rationale:** 
- Already using MUI for components, so design language is consistent
- Tree-shakeable: only imports used icons into bundle
- Well-maintained with TypeScript support
- Most lucide icons have direct MUI equivalents

### Alternatives Considered
1. **Direct MUI imports without abstraction**: Simpler but locks us to MUI
2. **Custom SVG sprites**: More efficient but requires manual SVG management
3. **heroicons/react**: Clean icons but introduces yet another design system

## Icon Mapping Strategy

| Lucide Icon | MUI Equivalent |
|-------------|----------------|
| X | Close |
| Check | Check |
| Plus | Add |
| ArrowUp | ArrowUpward |
| ArrowRight | ArrowForward |
| ChevronLeft | ChevronLeft |
| ChevronRight | ChevronRight |
| ChevronDown | ExpandMore |
| ChevronUp | ExpandLess |
| Maximize2 | Fullscreen |
| ZoomIn | ZoomIn |
| ZoomOut | ZoomOut |
| FileText | Description |
| FolderOpen | FolderOpen |
| FolderPlus | CreateNewFolder |
| Home | Home |
| Search | Search |
| Settings | Settings |
| Settings2 | Tune |
| Layout | Dashboard |
| Layers | Layers |
| Network | AccountTree |
| Brain | Psychology |
| Sparkles | AutoAwesome |
| Zap | Bolt |
| AlertCircle | Error |
| AlertTriangle | Warning |
| HelpCircle | HelpOutline |
| Copy | ContentCopy |
| Trash2 | Delete |
| Edit2 | Edit |
| Share2 | Share |
| RefreshCw | Refresh |
| Move | OpenWith |
| GripVertical | DragIndicator |
| MoreVertical | MoreVert |
| Link / Link2 | Link |
| CloudUpload | CloudUpload |
| FileUp | UploadFile |
| StickyNote | StickyNote2 |
| CreditCard | CreditCard |
| Mic | Mic |
| TrendingUp | TrendingUp |
| Users | People |
| DollarSign | AttachMoney |
| Target | GpsFixed |
| LayoutGrid | GridView |
| List | ViewList |
| History | History |
| Grid2x2 | Grid4x4 |
| ScanSearch | ImageSearch |
| PlusCircle | AddCircle |
| Dock | Dock |
| ParkingCircle | LocalParking |

## Abstraction Layer API Design

### IconProps Interface
```typescript
// components/ui/icons/types.ts
export interface IconProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  color?: 'inherit' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' | 'disabled';
  className?: string;
  style?: React.CSSProperties;
  onClick?: () => void;
}
```

### Usage Pattern
```typescript
// Before (lucide-react)
import { Plus, X, Sparkles } from 'lucide-react';
<Plus size={20} />

// After (abstraction layer)
import { AddIcon, CloseIcon, SparklesIcon } from '@/components/ui/icons';
<AddIcon size="md" />
```

### Icon Component Example
```typescript
// components/ui/icons/Icon.tsx
import { SvgIcon, SvgIconProps } from '@mui/material';

const sizeMap = {
  xs: 12,
  sm: 16,
  md: 20,
  lg: 24,
  xl: 32,
};

export function createIcon(MuiIcon: typeof SvgIcon) {
  return function Icon({ size = 'md', color = 'inherit', ...props }: IconProps) {
    const fontSize = typeof size === 'number' ? size : sizeMap[size];
    return <MuiIcon sx={{ fontSize, color }} {...props} />;
  };
}
```

## Risks / Trade-offs
- **Visual differences**: Some MUI icons may look slightly different than lucide equivalents
  - Mitigation: Review each replacement visually, document any that need custom SVG
- **Migration effort**: 25 files need updates
  - Mitigation: Systematic file-by-file approach with linting
- **Abstraction overhead**: Slight indirection
  - Mitigation: Minimal runtime cost, huge future maintenance benefit

## Migration Plan
1. Install `@mui/icons-material`
2. Create abstraction layer (`components/ui/icons/`)
3. Define `IconProps` interface and `createIcon` helper
4. Create icon exports with consistent naming (`XIcon` → `CloseIcon`)
5. Migrate imports file-by-file to use abstraction layer
6. Remove `lucide-react` from dependencies
7. Delete old `IconWrapper` component
8. Verify no runtime errors or visual regressions

## Open Questions
- None currently - straightforward replacement


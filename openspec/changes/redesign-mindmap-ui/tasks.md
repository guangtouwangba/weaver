## 1. Asset & Theme Preparation

- [x] 1.1 Define Card Theme Tokens
  - Colors: `card-bg: #FFFFFF`, `card-border-active: #4F46E5`, `card-border-dashed: #94A3B8`
  - Status: `status-success: #22C55E`, `status-processing: #3B82F6`
  - Shadows: `shadow-card: 0 4px 12px rgba(0,0,0,0.08)`

## 2. Component Implementation (MindMapNode)

- [x] 2.1 Create new `RichMindMapNode.tsx` component
  - Use Konva `Group` with `Rect` background + rounded corners (12px)
  - Support node variants: `root`, `generating`, `complete`, `pending`
  - Add drop shadow using Konva filters or extra Rect layer

- [x] 2.2 Implement "Root" variant
  - Larger size (280x160), centered AI brain icon (Lucide `Brain`)
  - Title text below icon, bold 18px
  - "PROCESSING CONTEXT" status bar with animated dots (3 circles, opacity loop)
  - Blue border glow (strokeWidth: 2, stroke: #4F46E5)

- [x] 2.3 Implement "Skeleton/Generating" variant
  - Dashed border: `dash: [8, 4]`, stroke: #4F46E5
  - Skeleton bars: 2-3 animated rectangles (gray, opacity pulse 0.3-0.7)
  - Reduced overall opacity: 0.8

- [x] 2.4 Implement "Completed" variant
  - White background, subtle shadow
  - Title (bold, #1F2937) + Content (regular, #6B7280)
  - Green checkmark icon in top-right (16px circle with check)

- [x] 2.5 Implement "Pending/Ghost" variant
  - Gray dashed border: `dash: [6, 4]`, stroke: #D1D5DB
  - Three-dot loading indicator (animated)
  - Overall opacity: 0.5

- [x] 2.6 Implement Tags/Chips rendering
  - Detect content with comma-separated items or array
  - Render as pill-shaped tags (Rect with full corner radius)
  - Light blue background (#EFF6FF), dark text (#1E40AF)

## 3. Edge & Connection Styling

- [x] 3.1 Create `CurvedMindMapEdge.tsx` component
  - Replace straight lines with Bezier curves (`bezierCurveTo`)
  - Calculate control points for smooth S-curves
  - Stroke width: 2px, color matches source node state

- [x] 3.2 Add connection anchor dots
  - Small filled circles (6px) at edge start/end points
  - Color: same as edge stroke
  - Position at node boundary (center-right for parent, center-left for child)

## 4. AI Insight Badge

- [x] 4.1 Create `AIInsightBadge.tsx` component
  - Dark background (#1F2937), rounded rectangle
  - Sparkle icon (✨) + text in white
  - Diamond connector pointing down to target node
  - Position above and left of target node

## 5. Integration & Testing

- [x] 5.1 Update MindMapEditor to use new components
  - Replace existing node/edge rendering
  - Add state mapping from backend `status` to visual variant

- [x] 5.2 Performance verification
  - Test with 21 nodes (default max)
  - Ensure 30+ FPS with shadows and animations
  - Disable expensive effects at low zoom levels (LOD)

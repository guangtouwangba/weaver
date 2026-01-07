# Design: Unify Canvas Node Model

## Architecture Overview

```
Current State:
┌─────────────────────────────────────────────────────────┐
│ StudioContext                                           │
│ ┌─────────────────────┐  ┌─────────────────────────────┐│
│ │ canvasNodes[]       │  │ generationTasks Map         ││
│ │ - notes             │  │ - mindmap (pending/complete)││
│ │ - super_article     │  │ - summary (pending/complete)││
│ │ - super_action_list │  └─────────────────────────────┘│
│ └─────────────────────┘                                 │
└─────────────────────────────────────────────────────────┘
            │                        │
            ▼                        ▼
┌─────────────────────┐    ┌─────────────────────────────┐
│ KonvaCanvas         │    │ GenerationOutputsOverlay    │
│ (Konva Stage)       │    │ (HTML Overlay)              │
│ - Spatial Index ✓   │    │ - No Spatial Index ✗        │
│ - Box Selection ✓   │    │ - Not selectable ✗          │
└─────────────────────┘    └─────────────────────────────┘

Target State:
┌─────────────────────────────────────────────────────────┐
│ StudioContext                                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ canvasNodes[] (unified)                             │ │
│ │ - notes, super_article, super_action_list          │ │
│ │ - mindmap, summary                                  │ │
│ │ - (future: podcast, quiz, timeline, etc.)          │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ pendingGenerations Map (only loading states)       │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│ KonvaCanvas                                             │
│ - All node types rendered                               │
│ - Unified Spatial Index                                 │
│ - Magic Cursor selects everything                       │
└─────────────────────────────────────────────────────────┘
```

## Data Model Changes

### Extended CanvasNode Interface

```typescript
interface CanvasNode {
  id: string;
  type: 'note' | 'source' | 'thinking_step' | 'thinking_branch' 
      | 'super_article' | 'super_action_list'
      | 'mindmap' | 'summary';  // NEW types
  
  // ... existing fields ...
  
  // Generation output metadata (for mindmap, summary, etc.)
  outputId?: string;        // Backend output ID for persistence
  outputData?: {
    // For mindmap
    nodes?: MindmapNode[];
    edges?: MindmapEdge[];
    // For summary
    sections?: SummarySection[];
    keyPoints?: string[];
    // Generic JSON for future types
    [key: string]: unknown;
  };
  generatedFrom?: {
    documentIds?: string[];
    nodeIds?: string[];      // Source nodes for Magic Cursor generation
    snapshotContext?: { x: number; y: number; width: number; height: number };
  };
}
```

### Simplified GenerationTask (Pending Only)

```typescript
interface PendingGeneration {
  id: string;
  type: GenerationType;
  status: 'pending' | 'generating';  // Only loading states
  position: { x: number; y: number };
  createdAt: Date;
}
```

## Component Changes

### KnowledgeNode Component

Extend to handle `mindmap` and `summary` types:

```typescript
// In KnowledgeNode render logic
if (node.type === 'mindmap') {
  return <MindmapKonvaCard node={node} ... />;
}
if (node.type === 'summary') {
  return <SummaryKonvaCard node={node} ... />;
}
```

### MindmapKonvaCard (New)

Renders a compact mindmap preview in Konva:
- Shows root node + first level children
- "N nodes" indicator
- Click to expand (opens MindMapEditor modal)
- Uses HTML Group for text rendering (existing pattern)

### SummaryKonvaCard (New)

Renders a compact summary preview in Konva:
- Shows title + first paragraph
- Section count indicator
- Click to expand (opens SummaryViewer modal)

## Migration Flow

### On Project Load

```typescript
// In StudioContext loadData
const outputsRes = await outputsApi.list(projectId);

// Convert outputs to CanvasNodes
const outputNodes: CanvasNode[] = outputsRes.outputs
  .filter(o => o.status === 'complete')
  .map(output => ({
    id: output.id,
    type: output.output_type as CanvasNodeType,
    title: output.title || `${output.output_type} output`,
    content: '', // Summary in metadata
    x: output.position?.x ?? calculateDefaultPosition(index).x,
    y: output.position?.y ?? calculateDefaultPosition(index).y,
    width: getDefaultWidth(output.output_type),
    height: getDefaultHeight(output.output_type),
    viewType: 'free',
    outputId: output.id,
    outputData: output.data,
    generatedFrom: output.source_info,
  }));

// Merge with regular nodes
setCanvasNodes(prev => [...prev, ...outputNodes]);
```

### On Generation Complete

```typescript
// In useOutputWebSocket or generation handler
const handleGenerationComplete = (output: OutputResponse) => {
  // Create CanvasNode from completed output
  const newNode: CanvasNode = {
    id: output.id,
    type: output.output_type,
    // ... map fields ...
  };
  
  // Add to canvas
  addNodeToCanvas(newNode);
  
  // Remove pending generation
  removePendingGeneration(taskId);
};
```

## Performance Considerations

### Mindmap Rendering in Konva
- Full mindmap with many nodes is expensive in Konva
- Solution: Render preview (root + 1 level) on canvas
- Full mindmap opens in modal with dedicated MindMapEditor

### Spatial Index
- `useSpatialIndex` already handles all nodes
- No changes needed - mindmap/summary nodes have x/y/width/height

### Viewport Culling
- `useViewportCulling` automatically culls off-screen nodes
- Works for all node types

## Backward Compatibility

### Legacy GenerationTask Consumers
- `InspirationDock`: Update to check both canvasNodes and pendingGenerations
- `GenerationOutputsOverlay`: Keep for pending states only
- `useCanvasActions`: No changes (already uses canvasNodes)

### Database
- No schema changes - `outputs` table already stores position and data
- Canvas state continues to work as-is

## Alternatives Considered

### Alternative: Extend Spatial Index to Include GenerationTasks
- Pros: Minimal code changes
- Cons: Two rendering systems, ongoing maintenance burden, inconsistent UX

### Alternative: Render GenerationTasks in Konva Without Data Model Unification
- Pros: Quick fix for selection
- Cons: Data inconsistency, complex sync logic, tech debt


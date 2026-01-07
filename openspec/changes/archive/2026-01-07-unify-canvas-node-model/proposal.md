# Proposal: Unify Canvas Node Model

## Why

Currently, the canvas has two parallel data models for visual elements:

| Model | Storage | Rendered By | Magic Cursor Selectable |
|-------|---------|-------------|-------------------------|
| `CanvasNode[]` | StudioContext.canvasNodes | KonvaCanvas | ✅ Yes |
| `GenerationTask` Map | StudioContext.generationTasks | GenerationOutputsOverlay (HTML) | ❌ No |

This bifurcation causes:

1. **Magic Cursor cannot select Mindmaps/Summaries** - They exist in `generationTasks`, not in the spatial index used by box selection.
2. **Inconsistent interaction patterns** - Notes, Super Cards (article/action_list) behave differently from Mindmaps/Summaries.
3. **Duplicate rendering logic** - Two separate systems for positioning, dragging, and displaying canvas items.
4. **Complex state synchronization** - Data flows differently for generated outputs vs. user-created content.

## What Changes

### 1. Extend `CanvasNode` Types
Add new node types to represent generation outputs:
- `type: 'mindmap'` - Mindmap generation result
- `type: 'summary'` - Summary generation result
- (Future: `podcast`, `quiz`, `timeline`, etc.)

### 2. Migrate `GenerationTask` to `CanvasNode`
When a generation completes:
- Convert the result to a `CanvasNode` with appropriate type
- Add it to `canvasNodes` array
- Remove the temporary `GenerationTask`

### 3. Render All Node Types in KonvaCanvas
- `KnowledgeNode` component already handles `super_article` and `super_action_list`
- Extend to handle `mindmap` and `summary` types
- Use Konva Portal or HTML Group for complex content (existing pattern)

### 4. Deprecate `GenerationOutputsOverlay`
- Keep only for loading/pending states during generation
- Completed outputs move to `CanvasNode` system

### 5. Unified Spatial Indexing
All node types (notes, mindmaps, summaries, super cards) will be:
- Indexed in `useSpatialIndex`
- Selectable by Magic Cursor
- Usable as generation input

## Impact

### Benefits
- **Unified selection** - Magic Cursor works on all content types
- **Consistent interactions** - Drag, edit, delete work the same everywhere
- **Simpler architecture** - One data model, one rendering path
- **Future-proof** - New generation types automatically support selection

### Risks
- **Migration complexity** - Existing saved outputs need conversion
- **Rendering performance** - Complex content (mindmaps) in Konva may need optimization
- **Breaking changes** - Components depending on `generationTasks` need updates

### Migration Strategy
- Backend already stores outputs with position data
- Frontend migration: on load, convert outputs to CanvasNodes
- No database schema changes required

## Scope

- **In Scope:**
  - Extend `CanvasNode` interface for generation outputs
  - Migrate mindmap/summary rendering to KonvaCanvas
  - Update `useSpatialIndex` to include all node types
  - Update Magic Cursor selection logic
  - Deprecate HTML overlay rendering for completed outputs

- **Out of Scope:**
  - Backend API changes (outputs API remains the same)
  - New generation types (podcast, quiz, etc.)
  - UI redesign of mindmap/summary appearance


# Magic Cursor Generation Design

## Context
The Magic Cursor feature enables users to select multiple canvas nodes and trigger AI-powered content generation. This design covers the full flow from user intent selection to result display.

## Goals
- Seamless integration with existing output generation infrastructure
- Real-time streaming of generation progress
- Minimal new abstractions - reuse existing patterns

## Non-Goals
- PDF export functionality (future phase)
- Calendar/Todoist integration (future phase)
- Snapshot Context refresh (future phase)

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  IntentMenu     │────▶│  outputsApi      │────▶│  /outputs/      │
│  (Frontend)     │     │  .generate()     │     │  generate API   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Super Card     │◀────│  WebSocket       │◀────│  ArticleAgent   │
│  (Canvas Node)  │     │  Events          │     │  ActionListAgent│
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Data Flow

### 1. User Triggers Generation
```typescript
// IntentMenu.tsx
onSelect('draft_article') → handleIntentAction('draft_article')
```

### 2. Frontend Prepares Request
```typescript
// KonvaCanvas.tsx
const nodeContent = selectedNodes.map(n => ({
  id: n.id,
  title: n.title,
  content: n.content,
}));

await outputsApi.generate(projectId, 'article', [], title, {
  mode: 'from_canvas_nodes',
  node_data: nodeContent,
  snapshot_context: magicSelection.rect, // For future refresh
});
```

### 3. Backend Processes Request
```python
# output_generation_service.py
if output_type == "article":
    await self._run_article_generation(...)
elif output_type == "action_list":
    await self._run_action_list_generation(...)
```

### 4. Agent Generates Content
```python
# article_agent.py
class ArticleAgent(BaseOutputAgent):
    """Generates structured articles from node content."""
    
    async def generate(self, node_content: str, **kwargs):
        # 1. Analyze themes and structure
        # 2. Generate outline
        # 3. Write sections with citations
        # 4. Yield streaming events
```

### 5. Result Displayed
- WebSocket pushes events to frontend
- New "Super Card" node created on canvas
- Card displays with article/checklist styling

## Agent Designs

### ArticleAgent
**Input:** Node content (titles + content combined)
**Output:** Structured markdown document with sections

**Prompt Strategy:**
1. Extract key themes from input nodes
2. Create logical outline
3. Generate each section with proper headings
4. Include source attribution to original nodes

**Output Format:**
```json
{
  "title": "Generated Article Title",
  "sections": [
    { "heading": "Introduction", "content": "..." },
    { "heading": "Key Insights", "content": "..." }
  ],
  "source_refs": [{ "node_id": "...", "quote": "..." }]
}
```

### ActionListAgent
**Input:** Node content
**Output:** Structured action items with status

**Prompt Strategy:**
1. Identify action items, tasks, TODOs
2. Categorize by priority/theme
3. Format as checklist

**Output Format:**
```json
{
  "title": "Action Items",
  "items": [
    { "id": "1", "text": "Review proposal", "done": false, "priority": "high" },
    { "id": "2", "text": "Schedule meeting", "done": false, "priority": "medium" }
  ],
  "source_refs": [{ "node_id": "...", "quote": "..." }]
}
```

## Frontend Implementation

### Loading State
While generating, show:
1. Magic selection box remains visible with pulsing animation
2. Small "Generating..." indicator near the selection
3. Intent Menu closes immediately on action selection

### Result Display
New node created with type `super-card`:
- **Article:** White background, document styling, expandable sections
- **Action List:** Checklist with interactive checkboxes

## Decisions

### Use Existing Output Infrastructure
**Decision:** Route through existing `outputsApi.generate()` and `OutputGenerationService`  
**Rationale:** Reuses streaming, persistence, and WebSocket infrastructure. Less new code.

### Pass Node Data via Options
**Decision:** Send node content in `options.node_data` rather than document_ids  
**Rationale:** Magic Cursor operates on canvas nodes, not uploaded documents.

### Store Snapshot Context
**Decision:** Include selection coordinates in output metadata for future refresh  
**Rationale:** Enables "Refresh" feature in Super Cards later.

## Risks / Mitigations

| Risk | Mitigation |
|------|------------|
| Large node selections → LLM token limits | Truncate/summarize if total content > 8000 tokens |
| Generation fails | Show error toast, keep selection visible for retry |
| WebSocket disconnection during generation | Implement polling fallback (already exists) |

## Decisions (Confirmed)

### Result Node Position
**Decision:** Offset from selection box (bottom-right corner + 20px padding)  
**Rationale:** Avoids overlapping with source nodes, maintains visual connection to selection area.

### Maximum Node Selection
**Decision:** Maximum 50 nodes per generation  
**Rationale:** Balances usability with LLM token limits. Beyond 50 nodes, content becomes too large for coherent synthesis.


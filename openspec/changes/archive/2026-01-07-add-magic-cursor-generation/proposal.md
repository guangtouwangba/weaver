# Add Magic Cursor Generation Logic

## Why
The Magic Cursor feature allows users to select canvas nodes and trigger AI generation. Currently, the Intent Menu displays "Draft Article" and "Action List" options but has no backend implementation. Users need the ability to generate polished documents and actionable task lists from their selected content.

## What Changes

### Backend
- Add `ARTICLE` and `ACTION_LIST` to `OutputType` enum
- Create `ArticleAgent` for generating structured documents from node content
- Create `ActionListAgent` for extracting tasks and action items
- Both agents use existing `BaseOutputAgent` pattern for streaming

### Frontend
- Connect `IntentMenu` actions to `outputsApi.generate()` API
- Pass selected node IDs and their content as generation context
- Display generation results as new canvas nodes (Super Cards)
- Add loading state during generation

## Impact

### Affected Specs
- `studio` - New requirements for Magic Cursor generation flow

### Affected Code
- **Backend:**
  - `domain/entities/output.py` - Add new OutputType values
  - `domain/agents/article_agent.py` - New agent (create)
  - `domain/agents/action_list_agent.py` - New agent (create)
  - `application/services/output_generation_service.py` - Route new types to agents
- **Frontend:**
  - `components/studio/KonvaCanvas.tsx` - Connect intent menu to API
  - `components/studio/IntentMenu.tsx` - Add loading state
  - `lib/api.ts` - Extend outputsApi type definitions

## User Review Required
- Should the generated Article/Action List appear as a new node on the canvas or open in a modal editor?
- Should we support regeneration (re-running with same context)?


# Change: Fix Output Persistence After Page Refresh

## Why
Summary and mindmap data disappear after page refresh despite being correctly saved to the database. The backend stores outputs successfully, but the frontend never fetches existing outputs on page load. This breaks user expectations that generated content should persist across sessions.

## What Changes
- **Frontend Data Loading**: Add `outputsApi.list()` call to `StudioContext.tsx` during initial data load to fetch saved outputs from the database.
- **State Restoration**: Restore the most recent complete summary and mindmap to React state (`summaryResult`, `mindmapResult`) when the page loads.
- **Overlay Behavior**: Keep overlays closed by default after restore; users click to view previously generated outputs.

## Impact
- **Specs**: `studio` capability will be updated with output persistence requirement.
- **Code**:
  - `app/frontend/src/contexts/StudioContext.tsx` - Add outputs fetch in `loadData()`, restore summary/mindmap state
  - `app/frontend/src/lib/api.ts` - No changes needed (API already exists)


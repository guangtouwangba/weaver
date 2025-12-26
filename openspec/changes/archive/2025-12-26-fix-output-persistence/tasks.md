## 1. Frontend Implementation

- [x] 1.1 Update `StudioContext.tsx` to fetch outputs on mount
  - Add `outputsApi.list(projectId)` to the `loadData()` function
  - Import `outputsApi` from `@/lib/api`
  - Handle 404/empty responses gracefully

- [x] 1.2 Restore summary state from fetched outputs
  - Filter outputs for `output_type === 'summary'` and `status === 'complete'`
  - Select the most recent output (first in list, already sorted by `created_at DESC`)
  - Call `setSummaryResult({ data: output.data, title: output.title })`
  - Keep `setShowSummaryOverlay(false)` to not auto-show

- [x] 1.3 Restore mindmap state from fetched outputs
  - Filter outputs for `output_type === 'mindmap'` and `status === 'complete'`
  - Select the most recent output (first in list, already sorted by `created_at DESC`)
  - Call `setMindmapResult({ data: output.data, title: output.title })`
  - Keep `setShowMindmapOverlay(false)` to not auto-show

## 2. Testing

- [x] 2.1 Manual verification
  - Generate a summary, refresh page, verify data persists
  - Generate a mindmap, refresh page, verify data persists
  - Open Inspiration Dock, click to view restored outputs
  - Test with no existing outputs (new project)


# Tasks: Add Knowledge Export Module

- [ ] Implement `ClipboardService` <!-- id: 1 -->
    - [ ] Create `app/frontend/src/lib/clipboard.ts`
    - [ ] Implement `sortNodesSpatially` (Z-Pattern logic) function
    - [ ] Implement `convertNodeToMarkdown` function for Text, Mindmap, and Source nodes
    - [ ] Implement `generateClipboardContent` main entry point
- [ ] Integrate with `KonvaCanvas` <!-- id: 2 -->
    - [ ] Add `useEffect` hook in `KonvaCanvas.tsx` to listen for `Ctrl+C` / `Cmd+C`
    - [ ] On copy, get `selectedNodeIds`, filter `nodes`, and call `generateClipboardContent`
    - [ ] Write result to `navigator.clipboard`
    - [ ] Show success toast notification
- [ ] Verification Actions <!-- id: 3 -->
    - [ ] Verify sorting accuracy with mixed-layout nodes
    - [ ] Verify mindmap hierarchy preservation
    - [ ] Verify video timestamps and links are correct

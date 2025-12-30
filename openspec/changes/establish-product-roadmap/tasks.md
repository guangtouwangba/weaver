# tasks.md

## Phase 1: Consolidation (Migration from `web`)
- [ ] **Studio Migration**
    - [ ] Port `KonvaCanvas` to `app/frontend/src/components/studio/Canvas`.
    - [ ] Port `GraphView` to `app/frontend/src/components/studio/Graph`.
    - [ ] Port `WriterView` and `PodcastView`.
    - [ ] Integrate `useCanvasWebSocket` hook with real backend.
- [ ] **Cleanup**
    - [ ] Verify all `web` features exist in `app/frontend`.
    - [ ] Delete `web` directory.

## Phase 2: New Features
- [ ] **Chrome Extension**
    - [ ] Scaffold extension project.
    - [ ] Implement capture to `POST /api/v1/inbox/collect`.
- [ ] **Deep Research**
    - [ ] Connect Frontend "Deep Think" button to Backend `ThinkingPath` API.

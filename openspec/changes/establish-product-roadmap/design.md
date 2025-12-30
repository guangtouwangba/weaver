# Design: Product Roadmap 2025

## Development Strategy
The roadmap follows a "Core -> Intelligence -> Multi-user" progression, focused entirely on the production stack (`app/frontend` and `app/backend`).

## Phasing Strategy

### Phase 1: Studio Core (Spatial & Visual Thinking)
*   **Goal**: Establish the primary workspace for knowledge work.
*   **Scope**:
    *   **KonvaCanvas**: Implement a high-performance spatial workbench in `app/frontend`.
    *   **GraphView**: Force-directed visualization of project entities.
    *   **Real-time Sync**: Full WebSocket integration between Frontend Canvas and Backend state.
    *   **Drag-to-Focus**: Interaction model to pull items from the Project sidebar into the Canvas.

### Phase 2: Intelligent Workflows (Synthesis & Capture)
*   **Goal**: Close the loop between ingestion and creation.
*   **Scope**:
    *   **Collection Ecosystem**: Release the Chrome Extension for structured web capture to `Inbox`.
    *   **Deep Research Integration**: Connect the Frontend "Deep Think" interface to the Backend `ThinkingPath` agent.
    *   **Synthesis Engines**: 
        *   **WriterMode**: AI-assisted structured document generation.
        *   **PodcastMode**: Audio summary generation and playback interface.

### Phase 3: Production Foundation
*   **Goal**: Scalable and collaborative foundation.
*   **Scope**:
    *   **Identity**: Auth & User Profiles via Supabase.
    *   **Persistence**: Robust multi-project state management.
    *   **Collaboration**: Real-time collaborative canvas (CRDTs).

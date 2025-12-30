# Design: Product Roadmap 2025

## Current State Analysis
*   **Prototype (`web`)**: Contains advanced features (Canvas, Graph View, Writer Mode, Podcast Mode) but relies on mock data and monolithic structure.
*   **Implementation (`app/frontend` + `app/backend`)**:
    *   **Frontend**: Clean Next.js 15 App Router structure. Implemented `Dashboard`, `Inbox`, `Settings`. `Studio` is partial.
    *   **Backend**: Robust modular monolith. Supports RAG, Canvas ops, Document processing.

## Phasing Strategy

### Phase 1: Consolidation (The "Great Migration")
*   **Goal**: Retire `web` directory.
*   **Scope**:
    *   Migrate `Studio` features:
        *   **Canvas**: Port Konva-based canvas with real WebSocket sync.
        *   **Graph View**: Port force-directed graph (Cosmos/D3).
        *   **Writer/Podcast**: Port these views as sub-routes or modals in Studio.
    *   Verify `Brain` logic is moved to Backend `ThinkingPath` service.
    *   Delete `web`.

### Phase 2: Core Loop Refinement
*   **Goal**: Seamless "Collect -> Analyze -> Create" loop.
*   **Scope**:
    *   **Collection**: Chrome Extension (using existing API).
    *   **Analysis**: "Deep Research" agent integration (Backend ready).
    *   **Creation**: Structured output generation (Reports, Slide decks).

### Phase 3: Ecosystem & Scale
*   **Goal**: Multi-user & Production.
*   **Scope**:
    *   Auth (Supabase).
    *   Multi-project/Multi-user support.
    *   Deployment templates.

## Context
The current RAG implementation in `rag_graph.py` uses a simple `chat_history` list and a `transform_query` node that rewrites queries using an LLM. While it supports basic history, it lacks structured awareness of "entities" (like a specific uploaded video or document) that are the subject of conversation.

## Goals / Non-Goals
- **Goals**: 
    - Accurately resolve "this video/document" to the correct ID/Title.
    - filter retrieval by specific document IDs when context implies it.
    - Persist entity focus across turns in a session.
- **Non-Goals**: 
    - Full-blown multi-modal understanding (we rely on metadata).
    - Complex coreference resolution beyond simple entities and document focus.

## Decisions
- **Decision**: Extend `GraphState` to include `active_entities` and `current_focus`.
    - **Rationale**: Keeps the state explicit in the graph flow, making it easy for nodes (`transform_query`, `retrieve`) to access and modify.
    
- **Decision**: Implement type-specific resolution priority.
    - **Rationale**: If user says "the PDF", search history for last accessed PDF, ignoring more recent but irrelevant entities (like a Video). Current focus should support a stack or typed-history map.

- **Decision**: Store focus in `ChatMessage` metadata (persisted).
    - **Rationale**: Allows resuming context if the graph state is lost (e.g., new request).

## Risks / Trade-offs
- **Risk**: Stale context (user switches topic but system still focuses on old video).
    - **Mitigation**: Intent classification should detect topic shifts and clear/update focus.

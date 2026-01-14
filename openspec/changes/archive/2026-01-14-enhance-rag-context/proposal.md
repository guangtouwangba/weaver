# Change: Context-Aware RAG with Entity Tracking

## Why
Users frequently use natural language references like "this video", "that document", or "it" when continuing a conversation. The current system relies on basic history concatenation or simple rewriting which often fails to resolve these references accurately to specific entities (documents, videos) in the context. This leads to poor retrieval results and frustrating user experience.

## What Changes
- **Context Management**: Introduce explicit tracking of "entities" (videos, documents) and "current focus" in the conversation context.
- **Smart Resolution**: Enhance query rewriting to resolve pronouns ("this", "that") to specific entity metadata (titles, IDs) using the tracked context.
- **Contextual Retrieval**: Inject resolved entity filters into the retrieval step to narrow down search space.
- **Proactive Clarification**: Add logic to ask clarifying questions when references are ambiguous (design/framework only).

## Impact
- **Affected Specs**: `rag`
- **Affected Code**: 
  - `backend/src/research_agent/application/graphs/rag_graph.py` (GraphState, Transform Query)
  - `backend/src/research_agent/application/dto/chat.py` (Context models)
  - `backend/src/research_agent/domain/services/retrieval_service.py` (Filtering)

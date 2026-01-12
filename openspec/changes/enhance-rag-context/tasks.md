## 1. Core Logic Implementation
- [ ] 1.1 Update `GraphState` in `rag_graph.py` to include `entities` and `current_focus`.
- [ ] 1.2 Implement `ConversationContext` helper class/logic to manage history and entity extraction.
- [ ] 1.3 Update `transform_query` in `rag_graph.py` to use `ConversationContext` for resolving references.
- [ ] 1.4 Update `retrieve` node to accept and use entity filters (e.g., `video_id`).

## 2. API & Data Integration
- [ ] 2.1 Update `StreamMessageInput` and `SendMessageInput` to pass initial context/metadata.
- [ ] 2.2 Ensure `ChatMessage` persistence includes context metadata updates.

## 3. Verification
- [ ] 3.1 Unit test `resolve_reference` logic with sample dialogues.
- [ ] 3.2 Integration test: Simulate a 3-turn conversation (Upload -> Ask general -> Ask specific "this video") and verify distinct retrieval filters.

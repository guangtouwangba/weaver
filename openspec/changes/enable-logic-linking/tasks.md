## 1. Implementation
- [ ] 1.1 **Frontend**: Implement "Drag to Connect" interaction in `MindMapEditor`.
    - Handle drag start from node (or dedicated handle).
    - Draw temporary line during drag.
    - Hit testing for target node.
- [ ] 1.2 **Frontend**: Create `LinkTypeDialog` component.
    - Options: "Structural (Parent/Child)", "Support (Green)", "Contradict (Red)", "Related (Dashed)".
- [ ] 1.3 **Backend**: Update `MindmapEdge` schema.
    - Add `relation_type` (enum) and `metadata` (json) fields.
    - Update `create_edge` and `update_edge` endpoints.
- [ ] 1.4 **Frontend**: specific rendering for Edge Types.
    - Update `MindMapEdge` to render different strokes/colors/arrows based on `relation_type`.
- [ ] 1.5 **Frontend**: Implement AI Verification Trigger.
    - Add "Verify Relation" action to Context Menu when an edge or 2 connected nodes are selected.
- [ ] 1.6 **Backend**: Implement Relation Verification Endpoint.
    - New endpoint `POST /api/mindmap/verify-relation`.
    - Input: source node content, target node content, relation type.
    - Logic: LLM check "Does A support/contradict B?".
    - Output: { valid: boolean, reasoning: string, confidence: number }.

## 2. Validation
- [ ] 2.1 **Manual**: Drag connect two nodes -> Dialog appears -> Select "Support" -> Verify Green Line.
- [ ] 2.2 **Manual**: Select the two nodes -> Trigger Verification -> Verify AI response works.

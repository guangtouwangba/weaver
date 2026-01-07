## 1. Implementation
- [x] 1.1 **Frontend**: Implement "Drag to Connect" interaction in `KonvaCanvas` (Generic Canvas).
    - [x] Handle drag start from node (or dedicated handle) via Connect Modes.
    - [x] Draw temporary line during drag.
    - [x] Hit testing for target node.
- [x] 1.2 **Frontend**: Create `LinkTypeDialog` component.
    - [x] Options: "Support (Green)", "Contradict (Red)", "Correlates (Blue)", "Causes (Orange)".
- [x] 1.3 **Backend**: Update `CanvasEdge` schema.
    - [x] Add `relationType`, `label`, and `metadata` to `CanvasEdgeDTO` and `CanvasEdge` interface.
- [x] 1.4 **Frontend**: specific rendering for Edge Types.
    - [x] `KonvaCanvas` already supports rendering styles based on `relationType`.
- [x] 1.5 **Frontend**: Implement AI Verification Trigger.
    - [x] Add "Verify Relation" action to `KonvaCanvas` Context Menu when 2 connected nodes are selected.
- [x] 1.6 **Backend**: Implement Relation Verification Endpoint.
    - [x] New endpoint `POST /api/v1/canvas/verify-relation`.
    - [x] Input: source content, target content, relation type.
    - [x] Logic: LLM check.
    - [x] Output: { valid, reasoning, confidence }.

## 2. Validation
- [ ] 2.1 **Manual**: Switch to "Logic Connect" tool -> Click Source -> Click/Drag to Target -> Dialog appears -> Select "Support" -> Verify Edge Created.
- [ ] 2.2 **Manual**: Select the two nodes -> Right Click -> "Verify Relation" -> Verify AI reasoning alert.

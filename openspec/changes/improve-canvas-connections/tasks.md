# Tasks: Improve Canvas Connections

## 1. Core Implementation (P0)
- [ ] 1.1 **Data Model**: Update `Edge` and `Node` types to support anchors and routing preferences. @frontend
- [ ] 1.2 **Anchors**: Implement `getAnchorPoint` and visual highlights for N/S/E/W anchors. @frontend
- [ ] 1.3 **Routing**: Implement `getStraightPath` algorithm. @frontend
- [ ] 1.4 **Rendering**: Update `renderEdge` to support basic styling (color, width) and straight lines. @frontend
- [ ] 1.5 **Behavior**: Ensure connections update efficiently when nodes are dragged. @frontend

## 2. Advanced Features (P1)
- [ ] 2.1 **Routing**: Implement Orthogonal routing with basic heuristic (Manhattan). @frontend
- [ ] 2.2 **Avoidance**: Add simple obstacle avoidance to orthogonal routing. @frontend
- [ ] 2.3 **Interaction**: Implement drag-to-reconnect for edge endpoints. @frontend
- [ ] 2.4 **Styling**: Add support for dashed lines and arrowheads (SVG markers). @frontend
- [ ] 2.5 **Labels**: Implement editable text labels on connections. @frontend

## 3. Polish & Future (P2)
- [ ] 3.1 **Routing**: Implement Curved routing (Bezier). @frontend
- [ ] 3.2 **Anchors**: Implement auto-selection logic based on relative node positions. @frontend
- [ ] 3.3 **Validation**: Prevent self-loops (if desired) or invalid connections. @frontend

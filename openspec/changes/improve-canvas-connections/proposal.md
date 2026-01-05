# Proposal: Improve Canvas Connections

## 1. Background
The current whiteboard connection implementation is basic, supporting only simple Bezier curves between node centers. To match industry standards like draw.io and Excalidraw, we need a robust connection system that supports multiple routing types, smart anchoring, and rich interactions.

## 2. Goals
- **Advanced Routing**: Support Straight, Orthogonal (with obstacle avoidance), and Curved paths.
- **Smart Anchors**: Auto-selecting anchors based on node relative positions, plus explicit fixed anchors.
- **Rich Interaction**: Allow users to reconnect edges, edit waypoints, and manipulate connections easily.
- **Visual Customization**: Full control over stroke, color, style (dashed), and markers (arrowheads).

## 3. Scope
- **Frontend**: `web/src` (Canvas components).
- **Functionality**:
    - **P0**: Straight routing, Basic/Auto anchors, Node follow, Basic styling.
    - **P1**: Orthogonal routing (w/ avoidance), Reconnection, Labels, Dashed styles.
    - **P2**: Curved routing, Sketch style, Custom anchors.

## 4. Risks
- **Performance**: Orthogonal routing with obstacle avoidance (A* or similar) can be expensive with many nodes. We must optimize or use simplified heuristics.
- **Complexity**: Handling Z-index and complex reconnections might introduce edge cases in state management.

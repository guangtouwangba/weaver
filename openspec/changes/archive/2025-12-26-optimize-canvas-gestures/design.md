## Context
Users on trackpads expect two-finger scroll to pan and pinch to zoom. Currently, `KonvaCanvas` maps all wheel events to zoom, preventing panning without a mouse drag or specific mode switch.

## Decisions
- **Event Mapping**:
    - `WheelEvent` (no modifier) -> Pan (update viewport x, y).
    - `WheelEvent + CtrlKey` -> Zoom (update viewport scale).
    - This aligns with standard browser behavior where "pinch" gestures emit `wheel` events with `ctrlKey: true`.

## Risks
- **Mouse Users**: Users with standard mouse wheels (without touch) are used to "wheel to scroll/pan" or "wheel to zoom". We need to ensure mouse wheel behavior is intuitive.
    - Standard mouse wheel usually scrolls vertical page. In canvas, it typically pans vertically or zooms.
    - To support "Zoom on Wheel" for mouse users, they might need to hold Ctrl. Alternatively, we could keep "Mouse Wheel -> Zoom" but detect if it's a trackpad. (Detecting trackpad is hard/unreliable).
    - Decision: We will strictly follow the Modifier key pattern. Mouse wheel -> Pan (Vertical). Shift+Wheel -> Pan (Horizontal). Ctrl+Wheel -> Zoom. This is consistent with Figma/Miro behavior.


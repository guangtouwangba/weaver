# Optimize Canvas Gestures

## Context
Currently, the canvas treats all `wheel` events as zoom commands. This makes navigation on trackpads difficult, as two-finger scrolling (panning) triggers zoom instead of movement. Users expect standard trackpad behaviors: two-finger drag to pan, and pinch to zoom.

## Goal
Update the `KonvaCanvas` component to support distinct gesture operations:
1. **Pan**: Two-finger scroll (standard wheel event without modifiers).
2. **Zoom**: Pinch gesture (mapped to `wheel` event with `ctrlKey` on most browsers/OSs).

## Non-Goals
- Touch event handling for mobile devices (focus is on trackpad/mouse wheel).
- altering drag-to-pan behavior (spacebar + drag).


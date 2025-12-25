1. Refactor `handleWheel` in `KonvaCanvas.tsx` to distinguish between zoom and pan intents.
2. Implement panning logic using `deltaX` and `deltaY` when `ctrlKey` is false.
3. Restrict zoom logic to execute only when `ctrlKey` is true (Pinch).
4. Verify sensitivity/speed for both panning and zooming to ensure smooth UX.


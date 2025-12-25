# Add Inspiration Dock Toggle

## Context
Users find the Inspiration Dock useful but intrusive when they want to focus on the canvas. Currently, it cannot be closed or hidden.

## Goal
Allow users to toggle the visibility of the Inspiration Dock.
1. Add a "Close" button to the dock itself.
2. Add a toggle button (Sparkles icon) to the Canvas Toolbar to re-open it.
3. Persist the visibility state in `StudioContext`.

## Non-Goals
- Persistence across sessions (refreshing resets state for now, per user preference "Permanently (until page refresh)").

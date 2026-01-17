# Proposal: Add FPS Monitor for Development

## Summary
Add a floating FPS monitor widget using stats.js during development mode to help debug performance issues, especially on the canvas-heavy Studio page.

## Motivation
- The Studio page uses Konva for canvas rendering, which can be performance-sensitive
- During development, it's important to monitor frame rates to catch performance regressions early
- stats.js is the industry-standard lightweight performance monitoring library (created by Three.js author)

## Scope
- Install stats.js dependency
- Create a development-only FPS monitor component
- Integrate it into the app layout (only visible in development mode)
- Position it in a non-intrusive location (top-left corner)

## Out of Scope
- Production performance monitoring
- Memory or render time panels (FPS panel only for simplicity)
- User-configurable display settings

## Technical Approach
1. Install `stats.js` via npm
2. Create a `DevFpsMonitor` component that:
   - Only renders when `process.env.NODE_ENV === 'development'`
   - Initializes stats.js on mount
   - Uses `requestAnimationFrame` for continuous updates
   - Positions the widget fixed in the top-left corner
3. Add the component to the root layout or providers

## Dependencies
- stats.js (npm package)

## Risks
- None significant; dev-only feature with zero production impact

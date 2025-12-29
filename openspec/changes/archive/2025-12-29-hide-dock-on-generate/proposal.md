# Hide Inspiration Dock on Generate

**Status:** Proposed  
**Created:** 2025-12-29

## Problem

When the canvas is empty and `availableFiles` exist, an "Inspiration Dock" UI appears with Summary/Mindmap options. When the user clicks "Summary", a generation loading overlay appears **but the dock remains visible behind it**, creating a confusing UI overlap.

![Issue Screenshot](/Users/siqiuchen/.gemini/antigravity/brain/7b762616-435d-46dd-8006-43a6a8cccb23/uploaded_image_1766991098674.png)

## Expected Behavior

Once the user clicks an action on the Inspiration Dock:
1. The dock should immediately hide
2. Only the generation loading state should be visible

## Root Cause Analysis

In [InspirationDock.tsx L249-250](file:///Users/siqiuchen/Documents/opensource/research-agent-rag/app/frontend/src/components/studio/InspirationDock.tsx#L249-L250):

```tsx
{/* Dock UI - Always visible (not hidden during generation) */}
{!showSummaryOverlay && !showMindmapOverlay && (
```

The comment explicitly states the dock is **not hidden during generation**. The condition only hides the dock once `showSummaryOverlay` or `showMindmapOverlay` is `true` (which happens **after** generation completes).

The `hasActiveGenerations` check exists (from `StudioContext`) but is not used to hide the dock.

## Proposed Fix

Modify the dock visibility condition to also hide when generation is in progress:

```tsx
{!showSummaryOverlay && !showMindmapOverlay && !hasActiveGenerations() && (
```

# Change: Add Web Page Content Preview

## Why
When users import web pages via URL, they need to preview the extracted content before and after adding it to the canvas. Currently, YouTube videos have a rich preview experience (player modal, sidebar preview), but generic web pages lack equivalent functionality. Users cannot easily view article content, check extraction quality, or understand what was imported without adding it to the canvas first.

## What Changes
- Add sidebar preview panel for web page content (article text, metadata, thumbnail)
- Enhance canvas WebPageCard with consistent styling matching YouTube cards
- Add "Read Article" modal for immersive reading experience
- Support double-click on web cards to open article reader
- Add "Add to Canvas" button in sidebar preview

## Impact
- Affected specs: `studio` (ADDED Requirements)
- Affected code:
  - Frontend: New `WebPagePreviewPanel.tsx` component for sidebar
  - Frontend: New `WebPageReaderModal.tsx` for article reading
  - Frontend: Update `ResourceSidebar.tsx` to handle web URL clicks
  - Frontend: Update `SourcePanel.tsx` to show web page preview
  - Frontend: Enhance `WebPageCard` in `KonvaCanvas.tsx`


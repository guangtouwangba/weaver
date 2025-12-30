# Refine AssistantPanel to Match Design Specifications

I will refine the `AssistantPanel` implementation to strictly follow the visual design provided in the image, ensuring all "sidebar" legacy styles are removed and the "floating" aesthetic is perfected.

## 1. Visual Refinements
**File:** `app/frontend/src/components/studio/AssistantPanel.tsx`

### File Card (Top)
- **Position**: Ensure it floats clearly at the top.
- **Style**: 
  - Pure white background with subtle shadow.
  - Red PDF icon (ensure color is correct).
  - Text layout: Filename on top (bold), Size below (gray).
  - Rounded corners: `borderRadius: 12px` (or similar).

### Recent Context Card (Middle)
- **Position**: Floating below the file card, above the input.
- **Style**:
  - "RECENT CONTEXT" header: Small caps, letter spacing, gray text.
  - Max height: Limit height so it doesn't fill the screen like a sidebar (e.g., `maxHeight: '400px'`).
  - Glassmorphism: Ensure backdrop blur and semi-transparent background.
  - Chat Bubbles: Ensure distinct separation between AI and User messages.

### Input Pill (Bottom)
- **Position**: Floating at the bottom.
- **Style**:
  - Full width pill shape (`borderRadius: 50px`).
  - **Border**: Dashed blue/purple border to indicate "Drop Zone" (as seen in design "Drop to analyze...").
  - **Icons**:
    - Left: Sparkle/Lightning icon (Blue/Purple gradient or solid color).
    - Right: Blue circular button with "+" icon.
  - **Placeholder**: "Drop to analyze..." (ensure text color is light gray).

## 2. Layout Adjustments
- **Container**: Ensure the main container is truly transparent and allows clicks through to the canvas in empty spaces (`pointerEvents: 'none'`).
- **Spacing**: Adjust gaps between floating elements to look "airy" and not stacked like a sidebar.

## 3. Implementation Plan
- Modify `AssistantPanel.tsx` to apply these specific styles.
- Verify `Box` and `Paper` props match the "floating" intent.

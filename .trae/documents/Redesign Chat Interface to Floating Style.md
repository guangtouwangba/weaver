# Redesign Chat Interface

I will redesign the chat interface (`AssistantPanel`) to match the provided design, moving away from the sidebar layout to a floating/overlay style.

## 1. Update Layout in `StudioPage`
**File:** `app/frontend/src/app/studio/[projectId]/page.tsx`
- Move `<AssistantPanel />` from the main flex container to be a child of the canvas wrapper `Box`.
- This allows the panel to overlay the canvas instead of shrinking it.

## 2. Redesign `AssistantPanel` Component
**File:** `app/frontend/src/components/studio/AssistantPanel.tsx`
- **Container Style**: Change from a fixed-height sidebar to a floating column positioned on the right.
- **Visuals**:
  - Remove standard borders and gray backgrounds.
  - Implement a transparent background for the main container.
- **New Components/Sections**:
  - **File Card**: A floating card at the top displaying the active file (icon, name, size).
  - **Context Card**: Style the message list area as a "Recent Context" card with rounded corners and shadow.
  - **Input Area**: Transform the input field into a floating "pill" shape at the bottom with:
    - "Drop to analyze..." placeholder.
    - Sparkle/Flash icon on the left.
    - "+" (Add) button on the right.
    - Dashed border styling for the drop zone feel.

## 3. Implementation Details
- Ensure the panel is toggleable (visible/hidden).
- Maintain existing drag-and-drop functionality but updated to the new visual targets.
- Reuse existing logic for chat messages and state, only changing the presentation layer.

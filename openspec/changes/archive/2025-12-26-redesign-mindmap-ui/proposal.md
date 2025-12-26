# Change: Redesign Mindmap UI to Rich Cards

## Why
The current mindmap nodes are simple shapes with text. The user wants a modern, "Glassmorphism" or card-based design that clearly communicates node states (processing, generating, completed) and displays rich content (icons, descriptions, AI badges). This improves the "Visual Thinking Assistant" experience by making the process transparent and visually engaging.

## What Changes
- **Frontend Node Rendering**: Replace simple shapes with complex "Card" groups in Konva.
- **Node States**: Implement visual states for:
  - `Root`: Prominent, glowing, "Processing Context" animation.
  - `Generating`: Dashed border, skeleton loading lines, pulsing effect.
  - `Completed`: Clean card with checkmark icon and description.
  - `Pending`: Faded/Ghost style.
- **Visuals**: Add drop shadows, rounded corners, connection anchors, and dot-grid background.
- **Data Model**: Frontend-only mapping of backend status to visual states.

## Impact
- **Specs**: `studio` capability updated with Rich Node visualization requirements.
- **Code**:
  - `MindMapNode.tsx`: Complete rewrite to render Card-based layout.
  - `MindMapEdge.tsx`: Update to match new node styling (dotted lines for pending).
  - `theme/`: Add new colors/styles for the card system.


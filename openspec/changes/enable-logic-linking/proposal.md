# Change: Enable Mind Map Logic Linking

## Why
Currently, mind map connections are purely structural (parent-child). Research users need to define *semantic* and *logical* relationships (e.g., "Evidence A supports Conclusion B") to build rigorous arguments. The current simple linking does not capitalization on the "connecting" action as a strong intent signal for logic definition.

## What Changes
- **Interactive Linking:** Users can drag from one node to another to create a connection (distinct from auto-parenting).
- **Link Types:** Introduce "Relation" types (Support, Contradict, Relates To) in addition to structural links.
- **Visual Distinction:** Logic links use distinct styles (e.g., solid color-coded lines).
- **AI Verification:** Enable users to verify the defined relationship using AI (e.g., "Does this evidence actually support this conclusion?").

## Impact
- **Specs:** `studio` (Mind Map capabilities).
- **Frontend:** `MindMapEditor.tsx`, `MindMapEdge.tsx`, new `LinkTypeDialog`.
- **Backend:** Update `MindmapEdge` model to store `relationType` and `metadata`.

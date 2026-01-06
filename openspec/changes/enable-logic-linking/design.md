## Context
Users use the whiteboard not just for organizing clips, but for *thinking*. Defining the relationship between pieces of information (Evidence vs Conclusion) is a critical part of the research process.

## Goals
- Allow explicit definition of edge semantics.
- Visual feedback for different logical flows.
- AI-assisted validation of these logical steps.

## Data Model Changes
### MindmapEdge
```typescript
interface MindmapEdge {
  id: string;
  source: string;
  target: string;
  // New fields
  relationType?: 'structural' | 'support' | 'contradict' | 'correlates';
  // metadata for future proofing (e.g. AI verification result)
  metadata?: {
    verified?: boolean;
    reasoning?: string; 
    customLabel?: string;
  };
}
```

## AI Verification Strategy
- **Trigger**: Explicit user action (Context Menu) to avoid auto-spamming tokens.
- **Prompting**: "Given Context A: [Content] and Context B: [Content]. The user claims A supports B. Analyze this claim..."
- **Feedback**: Displayed as a Popover or Side Panel (Assistant) message.

## Edge Visuals
- **Support**: Green, Solid, Arrow at target.
- **Contradict**: Red, Solid, Arrow at target, crosshatch mark maybe?
- **Correlates**: Blue, Dashed, Arrowless (or double arrow).

# Design: Canvas Node Editing & ID Fix

## 1. Unique ID Generation

### Current State
Nodes receive IDs like `node-{Date.now()}-{random}`. This is susceptible to collision on bulk operations or rapid creation.

### Proposed Change
Use the standard Web Crypto API.

```typescript
// app/frontend/src/contexts/StudioContext.tsx
const generateNodeId = () => `node-${crypto.randomUUID()}`;
```

## 2. Node Editing Experience

### UI Component: `NodeEditor`
A React component overlaid on top of the Konva Canvas layer. It is an HTML `textarea` that perfectly matches the position and style of the node being edited.

- **Props**: `node: CanvasNode`, `onSave: (newContent: string) => void`, `onCancel: () => void`.
- **Behavior**:
    - Auto-focus on mount.
    - Autosize height based on content.
    - `Enter` (without Shift) -> Save (for sticky notes/titles).
    - `Shift+Enter` -> New line.
    - `Escape` -> Cancel.
    - `Blur` -> Save.

### Interaction Logic (`KonvaCanvas.tsx`)
1.  **Double Click**:
    - If Node is `source` (PDF): Call `onOpenSource` (existing).
    - If Node is `sticky`, `thinking`, etc.: Set `editingNodeId`.
2.  **Context Menu**:
    - Add "Edit" item.
    - Clicking it sets `editingNodeId`.

### State Management
- `KonvaCanvas` needs state:
  ```typescript
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null);
  ```
- Pass `onEdit` callback to `KnowledgeNode`.
- Render `NodeEditor` only when `editingNodeId` is present.

## 3. Data Flow
1.  User updates text in `NodeEditor`.
2.  `onSave` triggers `updateNode(id, { content: newText })`.
3.  Canvas updates via Optimistic UI.
4.  Change is persisted to backend via existing API.

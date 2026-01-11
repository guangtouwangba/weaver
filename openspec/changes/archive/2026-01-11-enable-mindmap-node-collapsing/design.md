# Design: Mindmap Node Collapsing

## Visibility Logic
A node $N$ is visible if and only if for all ancestors $A$ of $N$, $A$ is not collapsed.

```typescript
function isNodeVisible(nodeId: string, nodes: MindmapNode[], collapsedIds: Set<string>): boolean {
  const node = nodes.find(n => n.id === nodeId);
  if (!node || !node.parentId) return true;
  if (collapsedIds.has(node.parentId)) return false;
  return isNodeVisible(node.parentId, nodes, collapsedIds);
}
```

## State Management
The `collapsed` state will be stored directly on the `MindmapNode` object in the frontend. This allows it to be serialised and persisted via the existing `updateOutput` API.

## UI Components
- **RichMindMapNode**: Will show a toggle icon at the connection point where child edges originate.
- **CurvedMindMapEdge**: Will check visibility of both source and target before rendering.

## Performance Considerations
For large graphs, calculating visibility recursively for every render might be expensive. We can pre-calculate a `hiddenNodeIds` set whenever the `collapsedNodeIds` changes.

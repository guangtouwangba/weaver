# Specification: Canvas Actions

## Summary

Defines a unified action system for programmatic canvas manipulation. All canvas operations are expressed as typed actions that can be dispatched, logged, and reversed.

## ADDED Requirements

### Requirement: Action Type Definition
All canvas operations MUST be represented as discriminated union types.

#### Scenario: Adding a node via action
Given a dispatch function
When `dispatch({ type: 'addNode', payload: { type: 'sticky', x: 100, y: 100, content: 'New' } })` is called
Then a new sticky node appears at position (100, 100)

#### Scenario: Deleting multiple nodes
Given selected node IDs `['node-1', 'node-2']`
When `dispatch({ type: 'deleteNodes', payload: { nodeIds: ['node-1', 'node-2'] } })` is called
Then both nodes and their connected edges are removed

---

### Requirement: Action Dispatcher Hook
A `useCanvasDispatch` hook MUST be provided for executing actions.

#### Scenario: Dispatching from any component
Given a component using `useCanvasDispatch`
When an action is dispatched
Then the canvas state updates accordingly

---

### Requirement: Batch Actions
Multiple actions SHOULD be batchable into a single operation.

#### Scenario: Creating a node with edges
Given an action batch containing `addNode` and `addEdge`
When the batch is dispatched
Then all operations apply atomically

---

## Action Types Reference

| Action Type | Payload | Description |
|-------------|---------|-------------|
| `addNode` | `Partial<CanvasNode>` | Creates a new node |
| `updateNode` | `{ nodeId, updates }` | Updates node properties |
| `deleteNode` | `{ nodeId }` | Removes a node and its edges |
| `moveNode` | `{ nodeId, x, y }` | Changes node position |
| `addEdge` | `Partial<CanvasEdge>` | Creates a connection |
| `updateEdge` | `{ edgeId, updates }` | Updates edge properties |
| `deleteEdge` | `{ edgeId }` | Removes a connection |
| `selectNodes` | `{ nodeIds }` | Sets selection |
| `clearSelection` | `{}` | Clears all selection |
| `panTo` | `{ x, y }` | Pans viewport to position |
| `zoomTo` | `{ scale }` | Sets zoom level |

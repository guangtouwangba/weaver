/**
 * Canvas Actions - Unified action system for programmatic canvas manipulation
 * 
 * All canvas operations are expressed as typed actions that can be dispatched,
 * logged, and potentially reversed.
 */

import { CanvasNode, CanvasEdge } from './api';

// ============================================================================
// Node Actions
// ============================================================================

export interface AddNodeAction {
  type: 'addNode';
  payload: Partial<CanvasNode> & { x?: number; y?: number };
}

export interface UpdateNodeAction {
  type: 'updateNode';
  payload: {
    nodeId: string;
    updates: Partial<CanvasNode>;
  };
}

export interface DeleteNodeAction {
  type: 'deleteNode';
  payload: {
    nodeId: string;
  };
}

export interface DeleteNodesAction {
  type: 'deleteNodes';
  payload: {
    nodeIds: string[];
  };
}

export interface MoveNodeAction {
  type: 'moveNode';
  payload: {
    nodeId: string;
    x: number;
    y: number;
  };
}

// ============================================================================
// Edge Actions
// ============================================================================

export interface AddEdgeAction {
  type: 'addEdge';
  payload: {
    source: string;
    target: string;
    label?: string;
    relationType?: CanvasEdge['relationType'];
  };
}

export interface UpdateEdgeAction {
  type: 'updateEdge';
  payload: {
    edgeId: string;
    updates: Partial<CanvasEdge>;
  };
}

export interface DeleteEdgeAction {
  type: 'deleteEdge';
  payload: {
    edgeId: string;
  };
}

export interface ReconnectEdgeAction {
  type: 'reconnectEdge';
  payload: {
    edgeId: string;
    newSource?: string;
    newTarget?: string;
  };
}

// ============================================================================
// Selection Actions
// ============================================================================

export interface SelectNodesAction {
  type: 'selectNodes';
  payload: {
    nodeIds: string[];
  };
}

export interface SelectEdgeAction {
  type: 'selectEdge';
  payload: {
    edgeId: string;
  };
}

export interface ClearSelectionAction {
  type: 'clearSelection';
  payload: Record<string, never>;
}

export interface SelectAllAction {
  type: 'selectAll';
  payload: Record<string, never>;
}

// ============================================================================
// Viewport Actions
// ============================================================================

export interface PanToAction {
  type: 'panTo';
  payload: {
    x: number;
    y: number;
  };
}

export interface ZoomToAction {
  type: 'zoomTo';
  payload: {
    scale: number;
  };
}

export interface ZoomInAction {
  type: 'zoomIn';
  payload: Record<string, never>;
}

export interface ZoomOutAction {
  type: 'zoomOut';
  payload: Record<string, never>;
}

export interface FitToContentAction {
  type: 'fitToContent';
  payload: Record<string, never>;
}

// ============================================================================
// Generation Actions
// ============================================================================

export interface SynthesizeNodesAction {
  type: 'synthesizeNodes';
  payload: {
    nodeIds: string[];
    mode: 'connect' | 'inspire' | 'debate';
  };
}

export interface GenerateContentAction {
  type: 'generateContent';
  payload: {
    contentType: 'mindmap' | 'summary' | 'flashcards' | 'action_list' | 'article';
    position?: { x: number; y: number };
  };
}

// ============================================================================
// Batch Action
// ============================================================================

export interface BatchAction {
  type: 'batch';
  payload: {
    actions: CanvasAction[];
  };
}

// ============================================================================
// Union Type
// ============================================================================

export type CanvasAction =
  // Node actions
  | AddNodeAction
  | UpdateNodeAction
  | DeleteNodeAction
  | DeleteNodesAction
  | MoveNodeAction
  // Edge actions
  | AddEdgeAction
  | UpdateEdgeAction
  | DeleteEdgeAction
  | ReconnectEdgeAction
  // Selection actions
  | SelectNodesAction
  | SelectEdgeAction
  | ClearSelectionAction
  | SelectAllAction
  // Viewport actions
  | PanToAction
  | ZoomToAction
  | ZoomInAction
  | ZoomOutAction
  | FitToContentAction
  // Generation actions
  | SynthesizeNodesAction
  | GenerateContentAction
  // Batch action
  | BatchAction;

// ============================================================================
// Action Result
// ============================================================================

export interface ActionResult {
  success: boolean;
  error?: string;
  data?: unknown;
}

// ============================================================================
// Dispatcher Type
// ============================================================================

export type CanvasDispatch = (action: CanvasAction) => ActionResult;


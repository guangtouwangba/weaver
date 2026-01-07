/**
 * useActionHistory - Undo/Redo stack for canvas actions
 * 
 * Tracks action history and provides undo/redo capabilities.
 * Uses a simple stack-based approach with snapshots.
 */

import { useState, useCallback, useRef } from 'react';
import { CanvasNode, CanvasEdge } from '@/lib/api';

interface CanvasSnapshot {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  timestamp: number;
}

interface UseActionHistoryOptions {
  maxHistorySize?: number;
}

interface UseActionHistoryResult {
  /** Push current state to history (call before making changes) */
  pushState: (nodes: CanvasNode[], edges: CanvasEdge[]) => void;
  /** Undo to previous state */
  undo: () => CanvasSnapshot | null;
  /** Redo to next state */
  redo: () => CanvasSnapshot | null;
  /** Check if undo is available */
  canUndo: boolean;
  /** Check if redo is available */
  canRedo: boolean;
  /** Clear all history */
  clear: () => void;
  /** Get history stats */
  historySize: number;
}

export function useActionHistory(
  options: UseActionHistoryOptions = {}
): UseActionHistoryResult {
  const { maxHistorySize = 50 } = options;
  
  // Past states (for undo)
  const [undoStack, setUndoStack] = useState<CanvasSnapshot[]>([]);
  // Future states (for redo)
  const [redoStack, setRedoStack] = useState<CanvasSnapshot[]>([]);
  
  // Debounce ref to avoid too frequent snapshots
  const lastPushTime = useRef<number>(0);
  const DEBOUNCE_MS = 100;

  const pushState = useCallback((nodes: CanvasNode[], edges: CanvasEdge[]) => {
    const now = Date.now();
    
    // Debounce rapid changes
    if (now - lastPushTime.current < DEBOUNCE_MS) {
      return;
    }
    lastPushTime.current = now;

    const snapshot: CanvasSnapshot = {
      nodes: JSON.parse(JSON.stringify(nodes)), // Deep clone
      edges: JSON.parse(JSON.stringify(edges)),
      timestamp: now,
    };

    setUndoStack(prev => {
      const newStack = [...prev, snapshot];
      // Limit history size
      if (newStack.length > maxHistorySize) {
        return newStack.slice(-maxHistorySize);
      }
      return newStack;
    });

    // Clear redo stack when new action is performed
    setRedoStack([]);
  }, [maxHistorySize]);

  const undo = useCallback((): CanvasSnapshot | null => {
    if (undoStack.length === 0) {
      return null;
    }

    const lastState = undoStack[undoStack.length - 1];
    
    setUndoStack(prev => prev.slice(0, -1));
    setRedoStack(prev => [...prev, lastState]);

    // Return the previous state (or null if this was the first)
    return undoStack.length > 1 ? undoStack[undoStack.length - 2] : null;
  }, [undoStack]);

  const redo = useCallback((): CanvasSnapshot | null => {
    if (redoStack.length === 0) {
      return null;
    }

    const nextState = redoStack[redoStack.length - 1];
    
    setRedoStack(prev => prev.slice(0, -1));
    setUndoStack(prev => [...prev, nextState]);

    return nextState;
  }, [redoStack]);

  const clear = useCallback(() => {
    setUndoStack([]);
    setRedoStack([]);
  }, []);

  return {
    pushState,
    undo,
    redo,
    canUndo: undoStack.length > 0,
    canRedo: redoStack.length > 0,
    clear,
    historySize: undoStack.length,
  };
}


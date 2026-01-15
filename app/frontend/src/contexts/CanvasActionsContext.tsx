'use client';

/**
 * CanvasActionsContext - Provides global access to canvas dispatch function
 * 
 * This context wraps the useCanvasDispatch hook and makes it available
 * to any component in the tree without prop drilling.
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { useCanvasDispatch } from '@/hooks/useCanvasDispatch';
import { CanvasDispatch } from '@/lib/canvasActions';

interface CanvasActionsContextValue {
  dispatch: CanvasDispatch;
  selectedNodeIds: string[];
  selectedEdgeId: string | null;
}

const CanvasActionsContext = createContext<CanvasActionsContextValue | null>(null);

interface CanvasActionsProviderProps {
  children: ReactNode;
  onOpenImport?: () => void;
}

export function CanvasActionsProvider({
  children,
  onOpenImport,
}: CanvasActionsProviderProps) {
  const canvasActions = useCanvasDispatch({ onOpenImport });

  return (
    <CanvasActionsContext.Provider value={canvasActions}>
      {children}
    </CanvasActionsContext.Provider>
  );
}

/**
 * Hook to access canvas dispatch function from anywhere in the component tree
 */
export function useCanvasActionsContext(): CanvasActionsContextValue {
  const context = useContext(CanvasActionsContext);
  
  if (!context) {
    throw new Error(
      'useCanvasActionsContext must be used within a CanvasActionsProvider'
    );
  }
  
  return context;
}

/**
 * Convenience hook that returns just the dispatch function
 */
export function useDispatch(): CanvasDispatch {
  const { dispatch } = useCanvasActionsContext();
  return dispatch;
}

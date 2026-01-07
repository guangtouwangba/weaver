/**
 * useCanvasDispatch - Unified dispatcher hook for canvas actions
 * 
 * Provides a centralized dispatch function that handles all canvas operations.
 * Integrates with StudioContext for state management.
 */

import { useCallback } from 'react';
import { useStudio, GenerationType } from '@/contexts/StudioContext';
import { CanvasNode, CanvasEdge, canvasApi, outputsApi } from '@/lib/api';
import {
  CanvasAction,
  ActionResult,
  CanvasDispatch,
} from '@/lib/canvasActions';

interface UseCanvasDispatchOptions {
  onOpenImport?: () => void;
}

export function useCanvasDispatch(options: UseCanvasDispatchOptions = {}): {
  dispatch: CanvasDispatch;
  // Selection state (read-only)
  selectedNodeIds: string[];
  selectedEdgeId: string | null;
} {
  const {
    projectId,
    canvasNodes,
    setCanvasNodes,
    canvasEdges,
    setCanvasEdges,
    canvasViewport,
    setCanvasViewport,
    addNodeToCanvas,
    startGeneration,
    documents,
    selectedDocumentIds,
  } = useStudio();

  // Selection state - managed locally since StudioContext doesn't have it
  // In a full implementation, this would be lifted to context
  // For now, we'll return empty arrays and let components manage their own selection
  const selectedNodeIds: string[] = [];
  const selectedEdgeId: string | null = null;

  const dispatch = useCallback((action: CanvasAction): ActionResult => {
    try {
      switch (action.type) {
        // ====================================================================
        // Node Actions
        // ====================================================================
        case 'addNode': {
          const { x, y, ...nodeData } = action.payload;
          const centerX = x ?? (-canvasViewport.x + 400) / canvasViewport.scale;
          const centerY = y ?? (-canvasViewport.y + 300) / canvasViewport.scale;
          
          const newNode: Omit<CanvasNode, 'id'> = {
            type: nodeData.type || 'sticky',
            title: nodeData.title || 'New Note',
            content: nodeData.content || '',
            x: centerX,
            y: centerY,
            width: nodeData.width || 200,
            height: nodeData.height || 200,
            color: nodeData.color || '#fef3c7',
            tags: nodeData.tags || [],
            viewType: 'free',
            ...nodeData,
          };
          
          addNodeToCanvas(newNode);
          return { success: true };
        }

        case 'updateNode': {
          const { nodeId, updates } = action.payload;
          setCanvasNodes((prev: CanvasNode[]) =>
            prev.map(n => n.id === nodeId ? { ...n, ...updates } : n)
          );
          return { success: true };
        }

        case 'deleteNode': {
          const { nodeId } = action.payload;
          setCanvasNodes((prev: CanvasNode[]) => prev.filter(n => n.id !== nodeId));
          setCanvasEdges((prev: CanvasEdge[]) =>
            prev.filter(e => e.source !== nodeId && e.target !== nodeId)
          );
          
          // Also delete from backend if projectId exists
          if (projectId) {
            canvasApi.deleteNode(projectId, nodeId).catch(err => {
              console.error('Failed to delete node from backend:', err);
            });
          }
          return { success: true };
        }

        case 'deleteNodes': {
          const { nodeIds } = action.payload;
          const nodeIdSet = new Set(nodeIds);
          
          setCanvasNodes((prev: CanvasNode[]) =>
            prev.filter(n => !nodeIdSet.has(n.id))
          );
          setCanvasEdges((prev: CanvasEdge[]) =>
            prev.filter(e => !nodeIdSet.has(e.source) && !nodeIdSet.has(e.target))
          );
          
          // Delete from backend
          if (projectId) {
            nodeIds.forEach(nodeId => {
              canvasApi.deleteNode(projectId, nodeId).catch(err => {
                console.error('Failed to delete node from backend:', err);
              });
            });
          }
          return { success: true };
        }

        case 'moveNode': {
          const { nodeId, x, y } = action.payload;
          setCanvasNodes((prev: CanvasNode[]) =>
            prev.map(n => n.id === nodeId ? { ...n, x, y } : n)
          );
          return { success: true };
        }

        // ====================================================================
        // Edge Actions
        // ====================================================================
        case 'addEdge': {
          const { source, target, label, relationType } = action.payload;
          
          // Check for duplicate
          const exists = canvasEdges.some(
            e => (e.source === source && e.target === target) ||
                 (e.source === target && e.target === source)
          );
          
          if (exists) {
            return { success: false, error: 'Edge already exists between these nodes' };
          }
          
          const newEdge: CanvasEdge = {
            id: `edge-${crypto.randomUUID()}`,
            source,
            target,
            label: label || '',
            relationType: relationType || 'related',
          };
          
          setCanvasEdges((prev: CanvasEdge[]) => [...prev, newEdge]);
          return { success: true, data: { edgeId: newEdge.id } };
        }

        case 'updateEdge': {
          const { edgeId, updates } = action.payload;
          setCanvasEdges((prev: CanvasEdge[]) =>
            prev.map(e => e.id === edgeId ? { ...e, ...updates } : e)
          );
          return { success: true };
        }

        case 'deleteEdge': {
          const { edgeId } = action.payload;
          setCanvasEdges((prev: CanvasEdge[]) =>
            prev.filter(e => e.id !== edgeId)
          );
          return { success: true };
        }

        case 'reconnectEdge': {
          const { edgeId, newSource, newTarget } = action.payload;
          setCanvasEdges((prev: CanvasEdge[]) =>
            prev.map(e => {
              if (e.id !== edgeId) return e;
              return {
                ...e,
                source: newSource ?? e.source,
                target: newTarget ?? e.target,
              };
            })
          );
          return { success: true };
        }

        // ====================================================================
        // Selection Actions
        // ====================================================================
        case 'selectNodes':
        case 'selectEdge':
        case 'clearSelection':
        case 'selectAll': {
          // Selection is managed by KonvaCanvas component directly
          // These actions are provided for API completeness but 
          // actual selection state lives in the component
          console.log(`[CanvasDispatch] Selection action: ${action.type}`, action.payload);
          return { success: true };
        }

        // ====================================================================
        // Viewport Actions
        // ====================================================================
        case 'panTo': {
          const { x, y } = action.payload;
          setCanvasViewport({
            ...canvasViewport,
            x: -x * canvasViewport.scale + 400,
            y: -y * canvasViewport.scale + 300,
          });
          return { success: true };
        }

        case 'zoomTo': {
          const { scale } = action.payload;
          const clampedScale = Math.max(0.1, Math.min(5, scale));
          setCanvasViewport({
            ...canvasViewport,
            scale: clampedScale,
          });
          return { success: true };
        }

        case 'zoomIn': {
          const newScale = Math.min(5, canvasViewport.scale * 1.2);
          setCanvasViewport({
            ...canvasViewport,
            scale: newScale,
          });
          return { success: true };
        }

        case 'zoomOut': {
          const newScale = Math.max(0.1, canvasViewport.scale / 1.2);
          setCanvasViewport({
            ...canvasViewport,
            scale: newScale,
          });
          return { success: true };
        }

        case 'fitToContent': {
          if (canvasNodes.length === 0) {
            return { success: true };
          }
          
          // Calculate bounding box of all nodes
          const padding = 50;
          let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
          
          canvasNodes.forEach(node => {
            minX = Math.min(minX, node.x);
            minY = Math.min(minY, node.y);
            maxX = Math.max(maxX, node.x + (node.width || 200));
            maxY = Math.max(maxY, node.y + (node.height || 200));
          });
          
          const contentWidth = maxX - minX + padding * 2;
          const contentHeight = maxY - minY + padding * 2;
          const viewportWidth = 800; // Approximate
          const viewportHeight = 600;
          
          const scaleX = viewportWidth / contentWidth;
          const scaleY = viewportHeight / contentHeight;
          const scale = Math.max(0.1, Math.min(1, Math.min(scaleX, scaleY)));
          
          setCanvasViewport({
            x: -(minX - padding) * scale + (viewportWidth - contentWidth * scale) / 2,
            y: -(minY - padding) * scale + (viewportHeight - contentHeight * scale) / 2,
            scale,
          });
          return { success: true };
        }

        // ====================================================================
        // Generation Actions
        // ====================================================================
        case 'synthesizeNodes': {
          // Synthesis requires async operation - return immediately
          // Actual synthesis is handled elsewhere
          console.log('[CanvasDispatch] Synthesize nodes:', action.payload);
          return { success: true };
        }

        case 'generateContent': {
          const { contentType, position } = action.payload;
          const targetPos = position ?? {
            x: (-canvasViewport.x + 400) / canvasViewport.scale,
            y: (-canvasViewport.y + 300) / canvasViewport.scale,
          };
          
          // Start generation task
          startGeneration(contentType as GenerationType, targetPos);
          return { success: true };
        }

        // ====================================================================
        // Batch Action
        // ====================================================================
        case 'batch': {
          const results: ActionResult[] = [];
          for (const subAction of action.payload.actions) {
            results.push(dispatch(subAction));
          }
          const hasError = results.some(r => !r.success);
          return {
            success: !hasError,
            data: results,
          };
        }

        default: {
          const _exhaustiveCheck: never = action;
          return { success: false, error: `Unknown action type: ${(_exhaustiveCheck as CanvasAction).type}` };
        }
      }
    } catch (error) {
      console.error('[CanvasDispatch] Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }, [
    projectId,
    canvasNodes,
    canvasEdges,
    canvasViewport,
    setCanvasNodes,
    setCanvasEdges,
    setCanvasViewport,
    addNodeToCanvas,
    startGeneration,
  ]);

  return {
    dispatch,
    selectedNodeIds,
    selectedEdgeId,
  };
}


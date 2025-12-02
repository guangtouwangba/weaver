'use client';

/**
 * Canvas Panel with Konva integration
 * Provides the bridge between StudioContext and KonvaCanvas
 */

import { useEffect } from 'react';
import { useStudio } from '@/contexts/StudioContext';
import { canvasApi } from '@/lib/api';
import KonvaCanvas from './KonvaCanvas';

export default function CanvasPanelKonva() {
  const { 
    projectId, 
    canvasNodes, 
    setCanvasNodes,
    canvasEdges,
    setCanvasEdges,
    canvasViewport,
    setCanvasViewport,
    saveCanvas,
    addNodeToCanvas,
  } = useStudio();

  // Auto-save on change (debounced)
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (canvasNodes.length > 0) {
        saveCanvas(); // Update context
        canvasApi.save(projectId, {
          nodes: canvasNodes,
          edges: canvasEdges,
          viewport: canvasViewport
        }).catch(err => console.error("Auto-save failed", err));
      }
    }, 2000);
    return () => clearTimeout(timeout);
  }, [canvasNodes, canvasEdges, canvasViewport, projectId, saveCanvas]);

  return (
    <KonvaCanvas 
      nodes={canvasNodes}
      edges={canvasEdges}
      viewport={canvasViewport}
      onNodesChange={setCanvasNodes}
      onEdgesChange={setCanvasEdges}
      onViewportChange={setCanvasViewport}
      onNodeAdd={addNodeToCanvas}
    />
  );
}


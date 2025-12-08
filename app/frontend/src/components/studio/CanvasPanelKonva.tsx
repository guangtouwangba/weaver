'use client';

/**
 * Canvas Panel with Konva integration
 * Provides the bridge between StudioContext and KonvaCanvas
 */

import { useEffect } from 'react';
import { Box } from '@mui/material';
import { useStudio } from '@/contexts/StudioContext';
import { canvasApi } from '@/lib/api';
import KonvaCanvas from './KonvaCanvas';
import CanvasSidebar from './CanvasSidebar';

export default function CanvasPanelKonva() {
  const { 
    projectId, 
    canvasNodes, 
    setCanvasNodes,
    canvasEdges,
    setCanvasEdges,
    canvasSections,
    canvasViewport,
    setCanvasViewport,
    currentView,
    viewStates,
    saveCanvas,
    addNodeToCanvas,
    highlightedNodeId,
    navigateToMessage,
  } = useStudio();

  // Auto-save on change (debounced)
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (canvasNodes.length > 0 || canvasSections.length > 0) {
        saveCanvas(); // Update context
        canvasApi.save(projectId, {
          nodes: canvasNodes,
          edges: canvasEdges,
          sections: canvasSections,
          viewport: canvasViewport,
          viewStates: viewStates,
        }).catch(err => console.error("Auto-save failed", err));
      }
    }, 2000);
    return () => clearTimeout(timeout);
  }, [canvasNodes, canvasEdges, canvasSections, canvasViewport, viewStates, projectId, saveCanvas]);

  return (
    <Box sx={{ display: 'flex', flexGrow: 1, minWidth: 0, overflow: 'hidden' }}>
      <KonvaCanvas 
        nodes={canvasNodes}
        edges={canvasEdges}
        viewport={canvasViewport}
        currentView={currentView}
        onNodesChange={setCanvasNodes}
        onEdgesChange={setCanvasEdges}
        onViewportChange={setCanvasViewport}
        onNodeAdd={addNodeToCanvas}
        highlightedNodeId={highlightedNodeId}
        onNodeClick={(node) => {
          // Navigate to linked message when clicking on a thinking path node
          if (node.messageIds?.length) {
            navigateToMessage(node.messageIds[0]);
          }
        }}
      />
      <CanvasSidebar />
    </Box>
  );
}


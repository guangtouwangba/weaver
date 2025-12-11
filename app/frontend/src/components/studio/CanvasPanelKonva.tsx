'use client';

/**
 * Canvas Panel with Konva integration
 * Provides the bridge between StudioContext and KonvaCanvas
 */

import { useEffect, useState } from 'react';
import { Box } from '@mui/material';
import { useStudio } from '@/contexts/StudioContext';
import { canvasApi } from '@/lib/api';
import KonvaCanvas from './KonvaCanvas';
import CanvasSidebar from './CanvasSidebar';
import ThinkingPathGenerator from './ThinkingPathGenerator';
import CanvasToolbar, { ToolMode } from './CanvasToolbar';

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
    navigateToSource,  // Phase 1: For opening source documents
  } = useStudio();

  const [toolMode, setToolMode] = useState<ToolMode>('select');

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

  // Keyboard shortcuts for tools (V for Select, H for Hand)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) return;

      if (e.key.toLowerCase() === 'v') {
        setToolMode('select');
      } else if (e.key.toLowerCase() === 'h') {
        setToolMode('hand');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <Box sx={{ display: 'flex', flexGrow: 1, minWidth: 0, overflow: 'hidden', position: 'relative' }}>
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
        onOpenSource={(sourceId, pageNumber) => {
          // Phase 1: Open source document and navigate to page
          navigateToSource(sourceId, pageNumber || 1);
        }}
        toolMode={toolMode}
      />
      
      {/* Canvas Tool Toolbar Overlay */}
      <CanvasToolbar activeTool={toolMode} onChange={setToolMode} />

      <CanvasSidebar />
      <ThinkingPathGenerator />
    </Box>
  );
}

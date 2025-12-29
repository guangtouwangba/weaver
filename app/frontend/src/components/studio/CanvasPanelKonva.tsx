'use client';

/**
 * Canvas Panel with Konva integration
 * Provides the bridge between StudioContext and KonvaCanvas
 */

import { useCallback, useEffect, useState } from 'react';
import { Box, Chip, CircularProgress } from '@mui/material';
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
    isGenerating,
  } = useStudio();



  const [toolMode, setToolMode] = useState<ToolMode>('select');
  const [hasSelection, setHasSelection] = useState(false);

  // Zoom handlers
  const handleZoomIn = useCallback(() => {
    setCanvasViewport(prev => ({
      ...prev,
      scale: Math.min(5, prev.scale * 1.2)
    }));
  }, [setCanvasViewport]);

  const handleZoomOut = useCallback(() => {
    setCanvasViewport(prev => ({
      ...prev,
      scale: Math.max(0.1, prev.scale / 1.2)
    }));
  }, [setCanvasViewport]);

  const handleResetZoom = useCallback(() => {
    setCanvasViewport(prev => ({
      ...prev,
      scale: 1
    }));
  }, [setCanvasViewport]);

  const handleFitView = useCallback(() => {
    // Calculate bounds of all nodes and fit the view
    if (canvasNodes.length === 0) return;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    canvasNodes.forEach(node => {
      minX = Math.min(minX, node.x);
      minY = Math.min(minY, node.y);
      maxX = Math.max(maxX, node.x + (node.width || 280));
      maxY = Math.max(maxY, node.y + (node.height || 200));
    });

    // Add padding
    const padding = 100;
    minX -= padding;
    minY -= padding;
    maxX += padding;
    maxY += padding;

    // Calculate scale to fit (assuming container is ~800x600, this is approximate)
    const contentWidth = maxX - minX;
    const contentHeight = maxY - minY;
    const scale = Math.min(800 / contentWidth, 600 / contentHeight, 1);

    setCanvasViewport({
      x: -minX * scale,
      y: -minY * scale,
      scale: Math.max(0.1, Math.min(1, scale))
    });
  }, [canvasNodes, setCanvasViewport]);

  // Selection change handler (called from KonvaCanvas)
  const handleSelectionChange = useCallback((count: number) => {
    setHasSelection(count > 0);
  }, []);

  // Delete selected nodes handler
  const handleDeleteSelected = useCallback(() => {
    // This is a placeholder - actual deletion is handled in KonvaCanvas via keyboard
    // We could add a ref or callback to trigger deletion from toolbar
  }, []);

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
        onToolChange={setToolMode}
        onSelectionChange={handleSelectionChange}
      />

      {/* Canvas Tool Toolbar Overlay */}
      <CanvasToolbar
        activeTool={toolMode}
        onChange={setToolMode}
        zoom={canvasViewport.scale}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onResetZoom={handleResetZoom}
        onFitView={handleFitView}
        onInsert={() => {/* TODO: implement insert menu */ }}
        onDelete={handleDeleteSelected}
        hasSelection={hasSelection}
      />

      {/* Global Loading Indicator */}
      {isGenerating && (
        <Box
          sx={{
            position: 'absolute',
            top: 20,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1200,
            pointerEvents: 'none'
          }}
        >
          <Chip
            icon={<CircularProgress size={16} color="inherit" />}
            label="Generating content..."
            sx={{
              bgcolor: 'background.paper',
              boxShadow: 3,
              border: '1px solid',
              borderColor: 'divider',
              fontWeight: 500
            }}
          />
        </Box>
      )}

      <CanvasSidebar />
      <ThinkingPathGenerator />
    </Box>
  );
}

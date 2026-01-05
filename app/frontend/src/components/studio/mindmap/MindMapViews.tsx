'use client';

import React, { useMemo } from 'react';
import { Stage, Layer } from 'react-konva';
import { Modal } from '@mui/material';
import { Stack } from '@/components/ui';
import { MindmapData } from '@/lib/api';
import { MindMapNode } from './MindMapNode';
import { MindMapEdge } from './MindMapEdge';
import { MindMapEditor } from './MindMapEditor';
import { applyLayout } from './layoutAlgorithms';

interface MindMapRendererProps {
  data: MindmapData;
  width: number;
  height: number;
  scale?: number;
  onNodeClick?: (nodeId: string) => void;
}

export const MindMapRenderer: React.FC<MindMapRendererProps> = ({
  data,
  width,
  height,
  scale = 1,
  onNodeClick
}) => {
  // Apply layout to ensure nodes are positioned correctly
  // The preview uses a scaled-down view, so we compute layout based on preview dimensions
  const layoutedData = useMemo(() => {
    if (data.nodes.length === 0) return data;

    // Apply balanced layout - use larger canvas for layout calculation
    // then the scale will shrink it down for preview
    const canvasWidth = width / scale;
    const canvasHeight = height / scale;
    const result = applyLayout(data, 'balanced', canvasWidth, canvasHeight);
    return { ...data, nodes: result.nodes };
  }, [data, width, height, scale]);

  return (
    <Stage width={width} height={height} scaleX={scale} scaleY={scale}>
      <Layer>
        {layoutedData.edges.map((edge) => {
          const source = layoutedData.nodes.find((n) => n.id === edge.source);
          const target = layoutedData.nodes.find((n) => n.id === edge.target);
          if (!source || !target) return null;
          return (
            <MindMapEdge
              key={edge.id}
              edge={edge}
              sourceNode={source}
              targetNode={target}
            />
          );
        })}
        {layoutedData.nodes.map((node) => (
          <MindMapNode
            key={node.id}
            node={node}
            onClick={onNodeClick}
          />
        ))}
      </Layer>
    </Stage>
  );
};

// ============================================================================
// MindMap Card (Minimized View)
// @deprecated Use MindMapCanvasNode from './canvas-nodes/MindMapCanvasNode' instead.
// This component is no longer used. MindMapCanvasNode provides:
// - Unified styling across all contexts
// - Full MindMapEditor in expanded view with zoom, pan, editing, export
// - Overlay mode support for centered display
// ============================================================================

// ============================================================================
// MindMap Full View (Interactive Editor)
// ============================================================================

interface MindMapFullViewProps {
  open: boolean;
  data: MindmapData;
  title: string;
  onClose: () => void;
  onDataChange?: (data: MindmapData) => void;
}

export const MindMapFullView: React.FC<MindMapFullViewProps> = ({
  open,
  data,
  title,
  onClose,
  onDataChange,
}) => {
  if (!open) return null;

  return (
    <Modal
      open={open}
      onClose={onClose}
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* 
        MindMapEditor has position: fixed, inset: 0
        We wrap it in a div that doesn't constrain it, or just pass it directly.
        Since it has fixed positioning, it will fill the screen.
        The Modal provides the Portal behavior to break out of parent transforms.
      */}
      <div style={{ width: '100%', height: '100%', outline: 'none' }}>
        <MindMapEditor
          initialData={data}
          title={title}
          onClose={onClose}
          onSave={onDataChange}
        />
      </div>
    </Modal>
  );
};

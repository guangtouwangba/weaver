import React, { useRef, useEffect, useState } from 'react';
import { Stage, Layer, Rect } from 'react-konva';
import { Box, Typography, IconButton, Modal, Paper, CircularProgress } from '@mui/material';
import { X, Maximize2, ZoomIn, ZoomOut } from 'lucide-react';
import { MindmapData } from '@/lib/api';
import { MindMapNode } from './MindMapNode';
import { MindMapEdge } from './MindMapEdge';
import { MindMapEditor } from './MindMapEditor';

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
  // Calculate bounds to center content
  const stageRef = useRef<any>(null);
  
  // Auto-center logic could go here, but for now we rely on the data's coordinates being reasonable
  // or the parent passing a transformed scale/offset.
  
  return (
    <Stage width={width} height={height} scaleX={scale} scaleY={scale}>
      <Layer>
        {data.edges.map((edge) => {
          const source = data.nodes.find((n) => n.id === edge.source);
          const target = data.nodes.find((n) => n.id === edge.target);
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
        {data.nodes.map((node) => (
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
// ============================================================================

interface MindMapCardProps {
  data: MindmapData;
  title: string;
  onClose: () => void;
  onExpand: () => void;
  isStreaming?: boolean;
}

export const MindMapCard: React.FC<MindMapCardProps> = ({ data, title, onClose, onExpand, isStreaming = false }) => {
  const nodeCount = data.nodes.length;
  
  return (
    <Paper
      elevation={8}
      sx={{
        width: 400,
        height: 300,
        borderRadius: 3,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(0,0,0,0.08)',
      }}
    >
      {/* Header */}
      <Box sx={{ 
        p: 1.5, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        borderBottom: '1px solid rgba(0,0,0,0.05)'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, maxWidth: 250 }}>
          {isStreaming && (
            <CircularProgress size={14} sx={{ color: '#10B981' }} />
          )}
          <Typography variant="subtitle2" fontWeight={600} noWrap>
            {title}
          </Typography>
          {isStreaming && nodeCount > 0 && (
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              {nodeCount} node{nodeCount !== 1 ? 's' : ''}
            </Typography>
          )}
        </Box>
        <Box>
          <IconButton size="small" onClick={onExpand} disabled={isStreaming && nodeCount === 0}>
            <Maximize2 size={16} />
          </IconButton>
          <IconButton size="small" onClick={onClose}>
            <X size={16} />
          </IconButton>
        </Box>
      </Box>

      {/* Preview Canvas */}
      <Box sx={{ flexGrow: 1, position: 'relative', bgcolor: '#FAFAFA' }}>
        {nodeCount > 0 ? (
          <MindMapRenderer 
            data={data} 
            width={400} 
            height={250} 
            scale={0.4}
          />
        ) : (
          /* Empty state while waiting for first node */
          <Box sx={{ 
            display: 'flex', 
            flexDirection: 'column',
            alignItems: 'center', 
            justifyContent: 'center', 
            height: '100%',
            gap: 1.5
          }}>
            <CircularProgress size={32} sx={{ color: '#10B981' }} />
            <Typography variant="body2" color="text.secondary">
              Generating mindmap...
            </Typography>
          </Box>
        )}
        
        {/* Overlay to catch clicks for expand (only when we have nodes) */}
        {nodeCount > 0 && (
          <Box 
            onClick={onExpand}
            sx={{ 
              position: 'absolute', 
              inset: 0, 
              cursor: 'pointer',
              '&:hover': { bgcolor: 'rgba(0,0,0,0.02)' }
            }} 
          />
        )}
      </Box>
    </Paper>
  );
};

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
        We wrap it in a Box that doesn't constrain it, or just pass it directly.
        Since it has fixed positioning, it will fill the screen.
        The Modal provides the Portal behavior to break out of parent transforms.
      */}
      <Box sx={{ width: '100%', height: '100%', outline: 'none' }}>
        <MindMapEditor
          initialData={data}
          title={title}
          onClose={onClose}
          onSave={onDataChange}
        />
      </Box>
    </Modal>
  );
};


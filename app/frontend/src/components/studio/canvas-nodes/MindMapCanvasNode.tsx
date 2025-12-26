'use client';

/**
 * MindMapCanvasNode - A compact mindmap card that appears on the canvas
 * Renders as an HTML overlay positioned over the Konva canvas
 */

import React, { useState, useRef } from 'react';
import { Stage, Layer } from 'react-konva';
import { Box, Paper, Typography, IconButton, Modal, Chip, CircularProgress } from '@mui/material';
import { CloseIcon, FullscreenIcon, ZoomInIcon, ZoomOutIcon, AccountTreeIcon, OpenWithIcon } from '@/components/ui/icons';
import { MindmapData } from '@/lib/api';
import { MindMapNode } from '../mindmap/MindMapNode';
import { MindMapEdge } from '../mindmap/MindMapEdge';

interface MindMapCanvasNodeProps {
  id: string;
  title: string;
  data: MindmapData;
  position: { x: number; y: number };
  viewport: { x: number; y: number; scale: number };
  isStreaming?: boolean;
  onClose: () => void;
  onDragStart?: (e: React.MouseEvent) => void;
  onDragEnd?: () => void;
}

// Mini renderer for preview
const MiniMindMapRenderer: React.FC<{ data: MindmapData; width: number; height: number; scale?: number }> = ({
  data,
  width,
  height,
  scale = 1,
}) => {
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
          <MindMapNode key={node.id} node={node} />
        ))}
      </Layer>
    </Stage>
  );
};

// Full renderer with zoom controls
const FullMindMapRenderer: React.FC<{
  data: MindmapData;
  scale: number;
  onNodeClick?: (nodeId: string) => void;
}> = ({ data, scale, onNodeClick }) => {
  return (
    <Box
      sx={{
        minWidth: '100%',
        minHeight: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 4,
      }}
    >
      <Stage width={1600} height={1200} scaleX={scale} scaleY={scale}>
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
    </Box>
  );
};

export default function MindMapCanvasNode({
  id,
  title,
  data,
  position,
  viewport,
  isStreaming = false,
  onClose,
  onDragStart,
  onDragEnd,
}: MindMapCanvasNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [fullScale, setFullScale] = useState(1);

  // Convert canvas coordinates to screen coordinates
  const screenX = position.x * viewport.scale + viewport.x;
  const screenY = position.y * viewport.scale + viewport.y;

  const nodeCount = data.nodes.length;

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target instanceof HTMLElement && e.target.closest('.drag-handle')) {
      setIsDragging(true);
      onDragStart?.(e);
    }
  };

  const handleMouseUp = () => {
    if (isDragging) {
      setIsDragging(false);
      onDragEnd?.();
    }
  };

  return (
    <>
      {/* Compact Card */}
      <Paper
        elevation={0}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        sx={{
          position: 'absolute',
          left: screenX,
          top: screenY,
          width: 340,
          height: 240,
          borderRadius: 3,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          bgcolor: 'rgba(255,255,255,0.98)',
          border: '1px solid',
          borderColor: 'divider',
          boxShadow: isDragging
            ? '0 12px 40px rgba(16, 185, 129, 0.25)'
            : '0 4px 20px rgba(0,0,0,0.08)',
          cursor: isDragging ? 'grabbing' : 'default',
          transition: isDragging ? 'none' : 'box-shadow 0.2s, transform 0.2s',
          transform: `scale(${viewport.scale > 0.5 ? 1 : viewport.scale * 2})`,
          transformOrigin: 'top left',
          zIndex: isDragging ? 1000 : 100,
          '&:hover': {
            boxShadow: '0 6px 24px rgba(0,0,0,0.12)',
          },
          animation: 'popIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
          '@keyframes popIn': {
            from: { opacity: 0, transform: 'scale(0.9)' },
            to: { opacity: 1, transform: 'scale(1)' },
          },
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 1.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(0,0,0,0.05)',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1, minWidth: 0 }}>
            {/* Drag Handle */}
            <Box
              className="drag-handle"
              sx={{
                cursor: 'grab',
                p: 0.5,
                borderRadius: 1,
                color: 'text.disabled',
                flexShrink: 0,
                '&:hover': {
                  color: 'text.secondary',
                  bgcolor: 'grey.100',
                },
                '&:active': { cursor: 'grabbing' },
              }}
            >
              <OpenWithIcon size={14} />
            </Box>

            {/* Icon */}
            <Box
              sx={{
                width: 28,
                height: 28,
                borderRadius: 1.5,
                background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                flexShrink: 0,
              }}
            >
              <AccountTreeIcon size={14} />
            </Box>

            {/* Title */}
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="subtitle2" fontWeight={600} noWrap sx={{ fontSize: '0.85rem' }}>
                {title}
              </Typography>
            </Box>

            {/* Streaming indicator */}
            {isStreaming && <CircularProgress size={14} sx={{ color: '#10B981', flexShrink: 0 }} />}
          </Box>

          {/* Actions */}
          <Box sx={{ display: 'flex', gap: 0.25, flexShrink: 0 }}>
            <IconButton
              size="small"
              onClick={() => setIsExpanded(true)}
              disabled={isStreaming && nodeCount === 0}
              sx={{ p: 0.5 }}
            >
              <FullscreenIcon size={14} />
            </IconButton>
            <IconButton size="small" onClick={onClose} sx={{ p: 0.5 }}>
              <CloseIcon size={14} />
            </IconButton>
          </Box>
        </Box>

        {/* Tags */}
        <Box sx={{ px: 1.5, py: 0.75, display: 'flex', gap: 0.5 }}>
          <Chip
            label="MINDMAP"
            size="small"
            sx={{
              bgcolor: '#ECFDF5',
              color: '#059669',
              fontWeight: 600,
              fontSize: '0.55rem',
              height: 16,
              borderRadius: 0.5,
              '& .MuiChip-label': { px: 0.75 },
            }}
          />
          {nodeCount > 0 && (
            <Chip
              label={`${nodeCount} NODES`}
              size="small"
              sx={{
                bgcolor: '#F3F4F6',
                color: '#6B7280',
                fontWeight: 600,
                fontSize: '0.55rem',
                height: 16,
                borderRadius: 0.5,
                '& .MuiChip-label': { px: 0.75 },
              }}
            />
          )}
        </Box>

        {/* Preview Canvas */}
        <Box sx={{ flexGrow: 1, position: 'relative', bgcolor: '#FAFAFA' }}>
          {nodeCount > 0 ? (
            <MiniMindMapRenderer data={data} width={340} height={150} scale={0.35} />
          ) : (
            /* Empty state while waiting for first node */
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                gap: 1,
              }}
            >
              <CircularProgress size={24} sx={{ color: '#10B981' }} />
              <Typography variant="caption" color="text.secondary">
                Generating mindmap...
              </Typography>
            </Box>
          )}

          {/* Overlay to catch clicks for expand (only when we have nodes) */}
          {nodeCount > 0 && (
            <Box
              onClick={() => setIsExpanded(true)}
              sx={{
                position: 'absolute',
                inset: 0,
                cursor: 'pointer',
                '&:hover': { bgcolor: 'rgba(0,0,0,0.02)' },
              }}
            />
          )}
        </Box>
      </Paper>

      {/* Expanded Modal */}
      <Modal open={isExpanded} onClose={() => setIsExpanded(false)}>
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '90vw',
            height: '90vh',
            bgcolor: 'background.paper',
            borderRadius: 4,
            boxShadow: 24,
            outline: 'none',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <Box
            sx={{
              p: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid',
              borderColor: 'divider',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box
                sx={{
                  width: 36,
                  height: 36,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                }}
              >
                <AccountTreeIcon size={18} />
              </Box>
              <Typography variant="h6" fontWeight={600}>
                {title}
              </Typography>
              <Chip
                label={`${nodeCount} nodes`}
                size="small"
                sx={{ bgcolor: '#ECFDF5', color: '#059669', fontWeight: 600 }}
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <IconButton onClick={() => setFullScale((s) => Math.min(s + 0.1, 2))}>
                <ZoomInIcon size="md" />
              </IconButton>
              <IconButton onClick={() => setFullScale((s) => Math.max(s - 0.1, 0.2))}>
                <ZoomOutIcon size="md" />
              </IconButton>
              <IconButton onClick={() => setIsExpanded(false)} sx={{ ml: 2 }}>
                <CloseIcon size="md" />
              </IconButton>
            </Box>
          </Box>

          {/* Full Canvas */}
          <Box sx={{ flexGrow: 1, overflow: 'auto', bgcolor: '#F3F4F6', position: 'relative' }}>
            <FullMindMapRenderer data={data} scale={fullScale} />
          </Box>
        </Box>
      </Modal>
    </>
  );
}


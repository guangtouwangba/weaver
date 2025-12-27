'use client';

/**
 * MindMapCanvasNode - A compact mindmap card that appears on the canvas
 * Renders as an HTML overlay positioned over the Konva canvas
 * 
 * Features:
 * - Unified visual styling across all display contexts
 * - Full MindMapEditor in expanded view with:
 *   - Free zoom (scroll wheel, pinch, +/- buttons)
 *   - Canvas pan
 *   - Layout switching
 *   - Node editing (add/delete/edit)
 *   - Export (PNG/JSON)
 * 
 * Performance Optimizations:
 * - Wrapped with React.memo to prevent re-renders when other nodes are being dragged
 * - Accepts data-task-id for direct DOM manipulation during drag
 */

import React, { useState, useRef, useEffect, memo } from 'react';
import { Stage, Layer } from 'react-konva';
import { Box, Paper, Typography, IconButton, Modal, Chip, CircularProgress } from '@mui/material';
import { CloseIcon, FullscreenIcon, AccountTreeIcon, OpenWithIcon } from '@/components/ui/icons';
import { MindmapData } from '@/lib/api';
import { MindMapNode } from '../mindmap/MindMapNode';
import { MindMapEdge } from '../mindmap/MindMapEdge';
import { MindMapEditor } from '../mindmap/MindMapEditor';

interface MindMapCanvasNodeProps {
  id: string;
  'data-task-id'?: string;
  title: string;
  data: MindmapData;
  position: { x: number; y: number };
  viewport: { x: number; y: number; scale: number };
  isStreaming?: boolean;
  /** When true, card is centered on screen (overlay mode) without viewport transform */
  isOverlayMode?: boolean;
  onClose: () => void;
  onDragStart?: (e: React.MouseEvent) => void;
  onDragEnd?: () => void;
  /** Callback when mindmap data is saved from editor */
  onDataChange?: (data: MindmapData) => void;
  /** External drag state control from parent (GenerationOutputsOverlay) */
  isDragging?: boolean;
}

// Mini renderer for preview (compact card view)
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

function MindMapCanvasNodeInner({
  id,
  'data-task-id': dataTaskId,
  title,
  data,
  position,
  viewport,
  isStreaming = false,
  isOverlayMode = false,
  onClose,
  onDragStart,
  onDragEnd,
  onDataChange,
  isDragging = false, // Controlled by parent (GenerationOutputsOverlay)
}: MindMapCanvasNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Performance: track renders
  const renderCountRef = useRef(0);
  renderCountRef.current++;
  
  useEffect(() => {
    if (isDragging && renderCountRef.current % 10 === 0) {
      console.log(`[Perf][MindMapNode ${id}] Render count: ${renderCountRef.current}`);
    }
  });

  // Convert canvas coordinates to screen coordinates (only when not in overlay mode)
  const screenX = isOverlayMode ? 0 : position.x * viewport.scale + viewport.x;
  const screenY = isOverlayMode ? 0 : position.y * viewport.scale + viewport.y;

  const nodeCount = data.nodes.length;

  const handleMouseDown = (e: React.MouseEvent) => {
    console.log('[MindMapNode] MouseDown', { 
        target: e.target, 
        isDragHandle: (e.target as HTMLElement).closest('.drag-handle') !== null,
        isButton: (e.target as HTMLElement).closest('button') !== null,
    });
    if (e.target instanceof HTMLElement) {
      // Skip if clicking on buttons (close, expand)
      if (e.target.closest('button') || e.target.closest('.MuiIconButton-root')) {
        return;
      }
      if (e.target.closest('.drag-handle')) {
        console.log('[MindMapNode] Drag handle clicked, calling onDragStart');
        onDragStart?.(e);
      }
    }
  };

  // Note: handleMouseUp is no longer needed here.
  // Parent (GenerationOutputsOverlay) handles mouseup via window event listener,
  // which ensures drag state is properly cleared even when mouse is released outside the card.

  return (
    <>
      {/* Compact Card */}
      <Paper
        elevation={isOverlayMode ? 8 : 0}
        data-task-id={dataTaskId || id}
        onMouseDown={handleMouseDown}
        sx={{
          position: isOverlayMode ? 'relative' : 'absolute',
          left: isOverlayMode ? 'auto' : screenX,
          top: isOverlayMode ? 'auto' : screenY,
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
            : isOverlayMode
              ? '0 8px 32px rgba(0,0,0,0.12)'
              : '0 4px 20px rgba(0,0,0,0.08)',
          cursor: isDragging ? 'grabbing' : 'default',
          transition: isDragging ? 'none' : 'box-shadow 0.2s, transform 0.2s',
          transform: isOverlayMode ? 'none' : `scale(${viewport.scale > 0.5 ? 1 : viewport.scale * 2})`,
          transformOrigin: 'top left',
          zIndex: isDragging ? 1000 : 100,
          '&:hover': {
            boxShadow: isOverlayMode ? '0 10px 40px rgba(0,0,0,0.15)' : '0 6px 24px rgba(0,0,0,0.12)',
          },
          animation: 'popIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
          '@keyframes popIn': {
            from: { opacity: 0, transform: 'scale(0.9)' },
            to: { opacity: 1, transform: 'scale(1)' },
          },
        }}
      >
        {/* Header - entire header is draggable */}
        <Box
          className="drag-handle"
          sx={{
            p: 1.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(0,0,0,0.05)',
            cursor: 'grab',
            '&:active': { cursor: 'grabbing' },
            userSelect: 'none',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1, minWidth: 0 }}>
            {/* Drag Indicator Icon */}
            <Box
              sx={{
                p: 0.5,
                borderRadius: 1,
                color: 'text.disabled',
                flexShrink: 0,
                '&:hover': {
                  color: 'text.secondary',
                  bgcolor: 'grey.100',
                },
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

      {/* Expanded Modal - Uses MindMapEditor for full editing capabilities */}
      <Modal 
        open={isExpanded} 
        onClose={() => setIsExpanded(false)}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* 
          MindMapEditor has position: fixed, inset: 0
          It provides full editing capabilities:
          - Free zoom (scroll wheel, pinch, +/- buttons)
          - Canvas pan (drag background)
          - Layout switching (radial, tree, balanced)
          - Node editing (add, delete, edit label/content)
          - Export (PNG, JSON)
        */}
        <Box sx={{ width: '100%', height: '100%', outline: 'none' }}>
          <MindMapEditor
            initialData={data}
            title={title}
            onClose={() => setIsExpanded(false)}
            onSave={onDataChange}
          />
        </Box>
      </Modal>
    </>
  );
}

/**
 * Memoized MindMapCanvasNode - prevents re-renders when:
 * - Other nodes are being dragged
 * - Parent component updates unrelated state
 * 
 * Only re-renders when this node's props actually change.
 */
const MindMapCanvasNode = memo(MindMapCanvasNodeInner, (prevProps, nextProps) => {
  // Custom equality check - only re-render if this node's data changed
  // During drag of another node, this node's props won't change
  return (
    prevProps.id === nextProps.id &&
    prevProps.title === nextProps.title &&
    prevProps.position.x === nextProps.position.x &&
    prevProps.position.y === nextProps.position.y &&
    prevProps.viewport.x === nextProps.viewport.x &&
    prevProps.viewport.y === nextProps.viewport.y &&
    prevProps.viewport.scale === nextProps.viewport.scale &&
    prevProps.isDragging === nextProps.isDragging &&
    prevProps.isStreaming === nextProps.isStreaming &&
    prevProps.isOverlayMode === nextProps.isOverlayMode &&
    prevProps.data === nextProps.data
  );
});

MindMapCanvasNode.displayName = 'MindMapCanvasNode';

export default MindMapCanvasNode;


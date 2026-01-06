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
import { Surface, Stack, Text, IconButton, Spinner, Modal, Chip } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import { CloseIcon, FullscreenIcon, AccountTreeIcon, OpenWithIcon, DeleteIcon } from '@/components/ui/icons';
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
        {data.edges.map((edge, idx) => {
          const source = data.nodes.find((n) => n.id === edge.source);
          const target = data.nodes.find((n) => n.id === edge.target);
          if (!source || !target) return null;
          return (
            <MindMapEdge
              key={`${edge.id}-${idx}`}
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
      if (e.target.closest('button')) {
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
      <Surface
        elevation={isOverlayMode ? 4 : 0}
        radius="lg"
        bordered
        data-task-id={dataTaskId || id}
        onMouseDown={handleMouseDown}
        style={{
          position: isOverlayMode ? 'relative' : 'absolute',
          left: isOverlayMode ? 'auto' : screenX,
          top: isOverlayMode ? 'auto' : screenY,
          width: 340,
          height: 240,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: 'rgba(255,255,255,0.98)',
          boxShadow: isDragging
            ? '0 12px 40px rgba(20, 184, 166, 0.25)'
            : isOverlayMode
              ? shadows.xl
              : shadows.lg,
          cursor: isDragging ? 'grabbing' : 'default',
          transition: isDragging ? 'none' : 'box-shadow 0.2s, transform 0.2s',
          transform: isOverlayMode ? 'none' : `scale(${viewport.scale > 0.5 ? 1 : viewport.scale * 2})`,
          transformOrigin: 'top left',
          zIndex: isDragging ? 1000 : 100,
        }}
      >
        {/* Header Row */}
        <Stack
          direction="row"
          align="center"
          justify="between"
          style={{
            padding: 12,
            borderBottom: '1px solid rgba(0,0,0,0.05)',
          }}
        >
          {/* Drag Handle Area */}
          <Stack
            direction="row"
            align="center"
            gap={1}
            className="drag-handle"
            style={{
              flex: 1,
              minWidth: 0,
              cursor: 'grab',
              userSelect: 'none',
            }}
          >
            {/* Drag Indicator Icon */}
            <div
              style={{
                padding: 4,
                borderRadius: radii.sm,
                color: colors.text.disabled,
                flexShrink: 0,
              }}
            >
              <OpenWithIcon size={14} />
            </div>

            {/* Icon */}
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: radii.md,
                background: `linear-gradient(135deg, ${colors.success[500]} 0%, ${colors.success[600]} 100%)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                flexShrink: 0,
              }}
            >
              <AccountTreeIcon size={14} />
            </div>

            {/* Title */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <Text variant="label" truncate style={{ fontSize: '0.85rem' }}>
                {title}
              </Text>
            </div>

            {/* Streaming indicator */}
            {isStreaming && <Spinner size="xs" color="secondary" />}
          </Stack>

          {/* Actions - Outside drag-handle */}
          <Stack direction="row" gap={0} style={{ flexShrink: 0 }}>
            <IconButton
              size="sm"
              variant="ghost"
              onClick={() => setIsExpanded(true)}
              disabled={isStreaming && nodeCount === 0}
            >
              <FullscreenIcon size={14} />
            </IconButton>
            <IconButton size="sm" variant="ghost" onClick={onClose} title="Delete">
              <DeleteIcon size={14} />
            </IconButton>
          </Stack>
        </Stack>

        {/* Tags */}
        <Stack direction="row" gap={0} style={{ paddingLeft: 12, paddingRight: 12, paddingTop: 6, paddingBottom: 6, gap: 4 }}>
          <Chip
            label="MINDMAP"
            size="sm"
            style={{
              backgroundColor: colors.success[50],
              color: colors.success[600],
              fontWeight: 600,
              fontSize: '0.55rem',
              height: 16,
              borderRadius: 0.5,
              paddingLeft: 4,
              paddingRight: 4,
            }}
          />
          {nodeCount > 0 && (
            <Chip
              label={`${nodeCount} NODES`}
              size="sm"
              style={{
                backgroundColor: colors.neutral[100],
                color: colors.neutral[500],
                fontWeight: 600,
                fontSize: '0.55rem',
                height: 16,
                borderRadius: 0.5,
                paddingLeft: 4,
                paddingRight: 4,
              }}
            />
          )}
        </Stack>

        {/* Preview Canvas */}
        <div style={{ flexGrow: 1, position: 'relative', backgroundColor: colors.background.subtle }}>
          {nodeCount > 0 ? (
            <MiniMindMapRenderer data={data} width={340} height={150} scale={0.35} />
          ) : (
            /* Empty state while waiting for first node */
            <Stack
              direction="column"
              align="center"
              justify="center"
              gap={1}
              style={{ height: '100%' }}
            >
              <Spinner size="sm" color="secondary" />
              <Text variant="caption" color="secondary">
                Generating mindmap...
              </Text>
            </Stack>
          )}

          {/* Overlay to catch clicks for expand (only when we have nodes) */}
          {nodeCount > 0 && (
            <div
              onClick={() => setIsExpanded(true)}
              style={{
                position: 'absolute',
                inset: 0,
                cursor: 'pointer',
              }}
            />
          )}
        </div>
      </Surface>

      {/* Expanded Modal - Uses MindMapEditor for full editing capabilities */}
      <Modal
        open={isExpanded}
        onClose={() => setIsExpanded(false)}
        style={{
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
        <div style={{ width: '100%', height: '100%', outline: 'none' }}>
          <MindMapEditor
            initialData={data}
            title={title}
            onClose={() => setIsExpanded(false)}
            onSave={onDataChange}
          />
        </div>
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



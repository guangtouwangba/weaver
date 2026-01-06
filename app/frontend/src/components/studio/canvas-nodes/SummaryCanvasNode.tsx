'use client';

/**
 * SummaryCanvasNode - A compact summary card that appears on the canvas
 * Renders as an HTML overlay positioned over the Konva canvas
 * 
 * Performance Optimizations:
 * - Wrapped with React.memo to prevent re-renders when other nodes are being dragged
 * - Accepts data-task-id for direct DOM manipulation during drag
 */

import React, { useState, useRef, useEffect, memo } from 'react';
import { Surface, Stack, Text, IconButton, Button, Chip, Modal } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import { CloseIcon, FullscreenIcon, AutoAwesomeIcon, TrendingUpIcon, PeopleIcon, ArrowForwardIcon, ContentCopyIcon, OpenWithIcon, DeleteIcon } from '@/components/ui/icons';
import { SummaryData, KeyFinding } from '@/lib/api';

interface SummaryCanvasNodeProps {
  id: string;
  'data-task-id'?: string;
  title: string;
  data: SummaryData;
  position: { x: number; y: number };
  viewport: { x: number; y: number; scale: number };
  onClose: () => void;
  onDragStart?: (e: React.MouseEvent) => void;
  onDragEnd?: () => void;
  /** External drag state control from parent (GenerationOutputsOverlay) */
  isDragging?: boolean;
}

function SummaryCanvasNodeInner({
  id,
  'data-task-id': dataTaskId,
  title,
  data,
  position,
  viewport,
  onClose,
  onDragStart,
  onDragEnd,
  isDragging = false, // Controlled by parent (GenerationOutputsOverlay)
}: SummaryCanvasNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Performance: track renders
  const renderCountRef = useRef(0);
  renderCountRef.current++;

  useEffect(() => {
    if (isDragging && renderCountRef.current % 10 === 0) {
      console.log(`[Perf][SummaryNode ${id}] Render count: ${renderCountRef.current}`);
    }
  });

  // Convert canvas coordinates to screen coordinates
  const screenX = position.x * viewport.scale + viewport.x;
  const screenY = position.y * viewport.scale + viewport.y;

  const handleExpand = () => setIsExpanded(true);
  const handleCloseExpanded = () => setIsExpanded(false);

  const handleMouseDown = (e: React.MouseEvent) => {
    console.log('[SummaryNode] MouseDown', {
      target: e.target,
      isDragHandle: (e.target as HTMLElement).closest('.drag-handle') !== null,
      isButton: (e.target as HTMLElement).closest('button') !== null,
    });
    if (e.target instanceof HTMLElement) {
      // Skip if clicking on buttons (close, expand, copy)
      if (e.target.closest('button')) {
        return;
      }
      if (e.target.closest('.drag-handle')) {
        console.log('[SummaryNode] Drag handle clicked, calling onDragStart');
        onDragStart?.(e);
      }
    }
  };

  const handleCopy = () => {
    if (data.summary) {
      navigator.clipboard.writeText(data.summary);
    }
  };

  return (
    <>
      {/* Compact Card */}
      <Surface
        elevation={0}
        radius="lg"
        bordered
        data-task-id={dataTaskId || id}
        onMouseDown={handleMouseDown}
        style={{
          position: 'absolute',
          left: screenX,
          top: screenY,
          width: 320,
          padding: 16,
          boxShadow: isDragging
            ? '0 12px 40px rgba(139, 92, 246, 0.25)'
            : shadows.lg,
          cursor: isDragging ? 'grabbing' : 'default',
          transition: isDragging ? 'none' : 'box-shadow 0.2s, transform 0.2s',
          transform: `scale(${viewport.scale > 0.5 ? 1 : viewport.scale * 2})`,
          transformOrigin: 'top left',
          zIndex: isDragging ? 1000 : 100,
        }}
      >
        {/* Header - entire header is draggable */}
        <Stack
          direction="row"
          align="start"
          className="drag-handle"
          style={{
            marginBottom: 12,
            cursor: 'grab',
            userSelect: 'none',
          }}
        >
          {/* Drag Indicator Icon */}
          <div
            style={{
              padding: 4,
              marginRight: 8,
              borderRadius: radii.sm,
              color: colors.text.disabled,
            }}
          >
            <OpenWithIcon size={14} />
          </div>

          {/* Icon */}
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: radii.md,
              background: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              marginRight: 12,
              flexShrink: 0,
            }}
          >
            <AutoAwesomeIcon size="sm" />
          </div>

          {/* Title Info */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <Text variant="label" truncate style={{ lineHeight: 1.2, marginBottom: 2 }}>
              {title}
            </Text>
            <Text variant="caption" color="secondary" style={{ fontSize: '0.65rem' }}>
              AI Summary
            </Text>
          </div>

          {/* Actions */}
          <Stack direction="row" gap={0} style={{ flexShrink: 0, gap: 2 }}>
            <IconButton size="sm" variant="ghost" onClick={handleCopy}>
              <ContentCopyIcon size={14} />
            </IconButton>
            <IconButton size="sm" variant="ghost" onClick={handleExpand}>
              <FullscreenIcon size={14} />
            </IconButton>
            <IconButton size="sm" variant="ghost" onClick={onClose} title="Delete">
              <DeleteIcon size={14} />
            </IconButton>
          </Stack>
        </Stack>

        {/* Tags */}
        <Stack direction="row" gap={0} style={{ marginBottom: 12, gap: 4 }}>
          <Chip
            label="SUMMARY"
            size="sm"
            color="primary"
            variant="soft"
          />
          <Chip
            label="AI GENERATED"
            size="sm"
            color="primary"
            variant="soft"
          />
        </Stack>

        {/* Content Preview */}
        <Text
          variant="bodySmall"
          color="secondary"
          style={{
            marginBottom: 12,
            fontSize: '0.8rem',
            lineHeight: 1.5,
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden'
          }}
        >
          {data.summary}
        </Text>

        {/* Key Findings Preview */}
        {data.keyFindings && data.keyFindings.length > 0 && (
          <div
            style={{
              padding: 12,
              backgroundColor: colors.background.subtle,
              borderRadius: radii.md,
              marginBottom: 12,
            }}
          >
            {data.keyFindings.slice(0, 2).map((finding, idx) => (
              <Stack key={idx} direction="row" align="start" gap={1} style={{ marginBottom: idx === 0 && data.keyFindings.length > 1 ? 8 : 0 }}>
                <div style={{ marginTop: 2 }}>
                  {idx === 0 ? <TrendingUpIcon size={12} style={{ color: colors.success[500] }} /> : <PeopleIcon size={12} style={{ color: colors.primary[500] }} />}
                </div>
                <Text variant="caption" style={{ fontSize: '0.7rem', lineHeight: 1.4 }}>
                  <span style={{ fontWeight: 600 }}>{finding.label}:</span> {finding.content.slice(0, 60)}...
                </Text>
              </Stack>
            ))}
          </div>
        )}

        {/* Expand Button */}
        <Button
          size="sm"
          onClick={handleExpand}
          endIcon={<ArrowForwardIcon size={14} />}
          style={{ width: '100%' }}
        >
          Read More
        </Button>
      </Surface >

      {/* Expanded Modal */}
      <Modal
        open={isExpanded}
        onClose={handleCloseExpanded}
        size="lg"
        style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
      >
        {/* Modal Header */}
        <Stack
          direction="row"
          align="center"
          justify="between"
          style={{
            padding: 20,
            borderBottom: `1px solid ${colors.border.default}`,
          }}
        >
          <Stack direction="row" align="center" gap={1}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: radii.md,
                background: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
              }}
            >
              <AutoAwesomeIcon size={18} />
            </div>
            <div>
              <Text variant="label">{title}</Text>
              <Text variant="caption" color="secondary">
                AI Generated Summary
              </Text>
            </div>
          </Stack>
          <Stack direction="row" gap={0} style={{ gap: 4 }}>
            <IconButton size="sm" variant="ghost" onClick={handleCopy}>
              <ContentCopyIcon size={18} />
            </IconButton>
            <IconButton size="sm" variant="ghost" onClick={handleCloseExpanded}>
              <CloseIcon size={18} />
            </IconButton>
          </Stack>
        </Stack>

        {/* Modal Content */}
        <div style={{ padding: 24, overflowY: 'auto', flex: 1 }}>
          <Text variant="overline" color="primary" style={{ marginBottom: 8, display: 'block', fontWeight: 700 }}>
            EXECUTIVE SUMMARY
          </Text>
          <Text variant="body" color="secondary" style={{ lineHeight: 1.8, marginBottom: 24 }}>
            {data.summary}
          </Text>

          {data.keyFindings && data.keyFindings.length > 0 && (
            <>
              <Text variant="overline" color="primary" style={{ marginBottom: 16, display: 'block', fontWeight: 700 }}>
                KEY FINDINGS
              </Text>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {data.keyFindings.map((finding, idx) => (
                  <Surface
                    key={idx}
                    elevation={0}
                    radius="md"
                    bordered
                    style={{ padding: 16, backgroundColor: colors.background.subtle }}
                  >
                    <Stack direction="row" align="center" gap={1} style={{ marginBottom: 4 }}>
                      <div
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          backgroundColor: colors.primary[500],
                        }}
                      />
                      <Text variant="label">{finding.label}</Text>
                    </Stack>
                    <Text variant="bodySmall" color="secondary" style={{ lineHeight: 1.6 }}>
                      {finding.content}
                    </Text>
                  </Surface>
                ))}
              </div>
            </>
          )}
        </div>
      </Modal>
    </>
  );
}

/**
 * Memoized SummaryCanvasNode - prevents re-renders when:
 * - Other nodes are being dragged
 * - Parent component updates unrelated state
 * 
 * Only re-renders when this node's props actually change.
 */
const SummaryCanvasNode = memo(SummaryCanvasNodeInner, (prevProps, nextProps) => {
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
    prevProps.data === nextProps.data
  );
});

SummaryCanvasNode.displayName = 'SummaryCanvasNode';

export default SummaryCanvasNode;

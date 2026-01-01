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
import { Box, Paper, Typography, IconButton, Chip, Modal, Fade, Backdrop, Button } from '@mui/material';
import { CloseIcon, FullscreenIcon, AutoAwesomeIcon, TrendingUpIcon, PeopleIcon, ArrowForwardIcon, ContentCopyIcon, DragIndicatorIcon, OpenWithIcon, DeleteIcon } from '@/components/ui/icons';
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
      if (e.target.closest('button') || e.target.closest('.MuiIconButton-root')) {
        return;
      }
      if (e.target.closest('.drag-handle')) {
        console.log('[SummaryNode] Drag handle clicked, calling onDragStart');
        onDragStart?.(e);
      }
    }
  };

  // Note: handleMouseUp is no longer needed here.
  // Parent (GenerationOutputsOverlay) handles mouseup via window event listener,
  // which ensures drag state is properly cleared even when mouse is released outside the card.

  const handleCopy = () => {
    if (data.summary) {
      navigator.clipboard.writeText(data.summary);
    }
  };

  return (
    <>
      {/* Compact Card */}
      <Paper
        elevation={0}
        data-task-id={dataTaskId || id}
        onMouseDown={handleMouseDown}
        sx={{
          position: 'absolute',
          left: screenX,
          top: screenY,
          width: 320,
          p: 2,
          borderRadius: 3,
          border: '1px solid',
          borderColor: 'divider',
          bgcolor: 'white',
          boxShadow: isDragging
            ? '0 12px 40px rgba(139, 92, 246, 0.25)'
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
            to: { opacity: 1, transform: 'scale(1)' }
          }
        }}
      >
        {/* Header - entire header is draggable */}
        <Box
          className="drag-handle"
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            mb: 1.5,
            cursor: 'grab',
            '&:active': { cursor: 'grabbing' },
            userSelect: 'none',
          }}
        >
          {/* Drag Indicator Icon */}
          <Box
            sx={{
              p: 0.5,
              mr: 1,
              borderRadius: 1,
              color: 'text.disabled',
              '&:hover': {
                color: 'text.secondary',
                bgcolor: 'grey.100'
              },
            }}
          >
            <OpenWithIcon size={14} />
          </Box>

          {/* Icon */}
          <Box
            sx={{
              width: 32,
              height: 32,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              mr: 1.5,
              flexShrink: 0
            }}
          >
            <AutoAwesomeIcon size="sm" />
          </Box>

          {/* Title Info */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="subtitle2" fontWeight={700} sx={{ lineHeight: 1.2, mb: 0.25 }} noWrap>
              {title}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
              AI Summary
            </Typography>
          </Box>

          {/* Actions */}
          <Box sx={{ display: 'flex', gap: 0.25, flexShrink: 0 }}>
            <IconButton size="small" onClick={handleCopy} sx={{ color: 'text.secondary', p: 0.5 }}>
              <ContentCopyIcon size={14} />
            </IconButton>
            <IconButton size="small" onClick={handleExpand} sx={{ color: 'text.secondary', p: 0.5 }}>
              <FullscreenIcon size={14} />
            </IconButton>
            <IconButton size="small" onClick={onClose} sx={{ color: 'text.secondary', p: 0.5 }} title="Delete">
              <DeleteIcon size={14} />
            </IconButton>
          </Box>
        </Box>

        {/* Tags */}
        <Box sx={{ display: 'flex', gap: 0.5, mb: 1.5 }}>
          <Chip
            label="SUMMARY"
            size="small"
            sx={{
              bgcolor: '#EEF2FF',
              color: '#4F46E5',
              fontWeight: 600,
              fontSize: '0.6rem',
              height: 18,
              borderRadius: 0.5,
              '& .MuiChip-label': { px: 0.75 }
            }}
          />
          <Chip
            label="AI GENERATED"
            size="small"
            sx={{
              bgcolor: '#F5F3FF',
              color: '#7C3AED',
              fontWeight: 600,
              fontSize: '0.6rem',
              height: 18,
              borderRadius: 0.5,
              '& .MuiChip-label': { px: 0.75 }
            }}
          />
        </Box>

        {/* Content Preview */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 1.5,
            fontSize: '0.8rem',
            lineHeight: 1.5,
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden'
          }}
        >
          {data.summary}
        </Typography>

        {/* Key Findings Preview */}
        {data.keyFindings && data.keyFindings.length > 0 && (
          <Box sx={{ p: 1.5, bgcolor: '#F8FAFC', borderRadius: 1.5, mb: 1.5 }}>
            {data.keyFindings.slice(0, 2).map((finding, idx) => (
              <Box key={idx} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: idx === 0 && data.keyFindings.length > 1 ? 1 : 0 }}>
                <Box sx={{ mt: 0.25 }}>
                  {idx === 0 ? <TrendingUpIcon size={12} sx={{ color: '#10B981' }} /> : <PeopleIcon size={12} sx={{ color: '#3B82F6' }} />}
                </Box>
                <Typography variant="caption" sx={{ fontSize: '0.7rem', lineHeight: 1.4 }}>
                  <Box component="span" fontWeight={600}>{finding.label}:</Box> {finding.content.slice(0, 60)}...
                </Typography>
              </Box>
            ))}
          </Box>
        )}

        {/* Expand Button */}
        <Button
          fullWidth
          size="small"
          onClick={handleExpand}
          sx={{
            bgcolor: '#4F46E5',
            color: 'white',
            borderRadius: 2,
            textTransform: 'none',
            py: 0.75,
            fontSize: '0.75rem',
            '&:hover': {
              bgcolor: '#4338CA'
            }
          }}
          endIcon={<ArrowForwardIcon size={14} />}
        >
          Read More
        </Button>
      </Paper>

      {/* Expanded Modal */}
      <Modal
        open={isExpanded}
        onClose={handleCloseExpanded}
        closeAfterTransition
        slots={{ backdrop: Backdrop }}
        slotProps={{
          backdrop: {
            timeout: 500,
            sx: { bgcolor: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(4px)' }
          },
        }}
      >
        <Fade in={isExpanded}>
          <Box sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '90%',
            maxWidth: 700,
            maxHeight: '85vh',
            bgcolor: 'background.paper',
            borderRadius: 4,
            boxShadow: 24,
            p: 0,
            outline: 'none',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column'
          }}>
            {/* Modal Header */}
            <Box sx={{
              p: 2.5,
              borderBottom: '1px solid',
              borderColor: 'divider',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Box
                  sx={{
                    width: 36,
                    height: 36,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <AutoAwesomeIcon size={18} />
                </Box>
                <Box>
                  <Typography variant="subtitle1" fontWeight={700}>
                    {title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    AI Generated Summary
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                <IconButton size="small" onClick={handleCopy}>
                  <ContentCopyIcon size={18} />
                </IconButton>
                <IconButton size="small" onClick={handleCloseExpanded}>
                  <CloseIcon size={18} />
                </IconButton>
              </Box>
            </Box>

            {/* Modal Content */}
            <Box sx={{ p: 3, overflowY: 'auto', flex: 1 }}>
              <Typography variant="overline" color="primary" fontWeight={700} sx={{ mb: 1, display: 'block' }}>
                EXECUTIVE SUMMARY
              </Typography>
              <Typography variant="body1" paragraph sx={{ lineHeight: 1.8, color: 'text.secondary', mb: 3 }}>
                {data.summary}
              </Typography>

              {data.keyFindings && data.keyFindings.length > 0 && (
                <>
                  <Typography variant="overline" color="primary" fontWeight={700} sx={{ mb: 2, display: 'block' }}>
                    KEY FINDINGS
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                    {data.keyFindings.map((finding, idx) => (
                      <Paper key={idx} elevation={0} sx={{ p: 2, bgcolor: '#F8FAFC', borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
                        <Typography variant="subtitle2" fontWeight={700} gutterBottom sx={{ color: 'text.primary', display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box component="span" sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'primary.main' }} />
                          {finding.label}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                          {finding.content}
                        </Typography>
                      </Paper>
                    ))}
                  </Box>
                </>
              )}
            </Box>
          </Box>
        </Fade>
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


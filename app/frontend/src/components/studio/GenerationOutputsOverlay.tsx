'use client';

/**
 * GenerationOutputsOverlay - Renders loading cards during generation
 * 
 * With the Unified Node Model, completed outputs are now CanvasNodes rendered
 * in KonvaCanvas. This overlay only shows loading placeholders for pending/generating tasks.
 * 
 * Features:
 * - Loading placeholder cards for pending/generating tasks
 * - Viewport-aware positioning
 * - Draggable loading cards
 * 
 * Note: Completed outputs (mindmap, summary, article, action_list) are rendered
 * as CanvasNodes in KonvaCanvas, not here.
 */

import React, { useMemo, useState, useCallback, useRef, useEffect } from 'react';
import { Surface, Stack, Text, Spinner, IconButton } from '@/components/ui';
import { colors, shadows, radii } from '@/components/ui/tokens';
import { useStudio, GenerationType, GenerationTask } from '@/contexts/StudioContext';
import { AutoAwesomeIcon, AccountTreeIcon, OpenWithIcon, CloseIcon, ErrorIcon } from '@/components/ui/icons';

interface GenerationOutputsOverlayProps {
  viewport: { x: number; y: number; scale: number };
}

// Drag state for tracking active drag operation
interface DragState {
  taskId: string;
  startMouseX: number;
  startMouseY: number;
  startPositionX: number;
  startPositionY: number;
}

// Current drag position (separate from DragState for RAF optimization)
interface DragPosition {
  x: number;
  y: number;
}

// Loading or Error placeholder card for generating/failed tasks
function LoadingCard({
  task,
  viewport,
  onDragStart,
  onDismiss,
  isDragging,
}: {
  task: GenerationTask;
  viewport: { x: number; y: number; scale: number };
  onDragStart: (e: React.MouseEvent, taskId: string) => void;
  onDismiss: (taskId: string) => void;
  isDragging: boolean;
}) {
  // Convert canvas coordinates to screen coordinates
  const screenX = task.position.x * viewport.scale + viewport.x;
  const screenY = task.position.y * viewport.scale + viewport.y;

  const isError = task.status === 'error';
  const isMindmap = task.type === 'mindmap';
  const gradientColor = isError
    ? `linear-gradient(135deg, ${colors.error[500]} 0%, ${colors.error[600]} 100%)`
    : isMindmap
      ? `linear-gradient(135deg, ${colors.success[500]} 0%, ${colors.success[600]} 100%)`
      : `linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)`;
  const typeLabel = isMindmap ? 'MINDMAP' : 'SUMMARY';
  const TypeIcon = isMindmap ? AccountTreeIcon : AutoAwesomeIcon;

  const handleMouseDown = (e: React.MouseEvent) => {
    console.log('[LoadingCard] handleMouseDown', {
      isDragHandle: !!(e.target instanceof HTMLElement && e.target.closest('.drag-handle')),
      isButton: !!(e.target instanceof HTMLElement && e.target.closest('button'))
    });
    if (e.target instanceof HTMLElement) {
      // Skip if clicking on buttons
      if (e.target.closest('button') || e.target.closest('.MuiIconButton-root')) {
        return;
      }
      if (e.target.closest('.drag-handle')) {
        onDragStart(e, task.id);
      }
    }
  };

  return (
    <Surface
      elevation={0}
      radius="lg"
      bordered
      data-task-id={task.id}
      onMouseDown={handleMouseDown}
      style={{
        position: 'absolute',
        left: screenX,
        top: screenY,
        width: 320,
        padding: 16,
        cursor: isDragging ? 'grabbing' : 'default',
        transition: isDragging ? 'none' : 'box-shadow 0.2s, transform 0.2s',
        transform: `scale(${viewport.scale > 0.5 ? 1 : viewport.scale * 2})`,
        transformOrigin: 'top left',
        zIndex: isDragging ? 1000 : 100,
        boxShadow: isDragging
          ? '0 12px 40px rgba(139, 92, 246, 0.25)'
          : shadows.lg,
        borderColor: isError ? colors.error[300] : undefined,
      }}
    >
      {/* Header - entire header is draggable */}
      <Stack
        direction="row"
        align="center"
        gap={1}
        className="drag-handle"
        style={{
          marginBottom: 16,
          cursor: isError ? 'default' : 'grab',
          userSelect: 'none',
          overflow: 'hidden',
        }}
      >
        {/* Drag Indicator Icon (hidden for error state) */}
        {!isError && (
          <div
            style={{
              padding: 4,
              borderRadius: radii.sm,
              color: colors.text.disabled,
            }}
          >
            <OpenWithIcon size={14} />
          </div>
        )}

        {/* Icon */}
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: radii.md,
            background: gradientColor,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            flexShrink: 0,
          }}
        >
          {isError ? <ErrorIcon size="sm" /> : <TypeIcon size="sm" />}
        </div>

        <div style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
          <Text
            variant="label"
            truncate
            style={{
              lineHeight: 1.2,
              marginBottom: 2,
              display: 'block',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              color: isError ? colors.error[700] : undefined,
            }}
          >
            {isError ? 'Generation Failed' : (task.title || `Generating ${task.type}...`)}
          </Text>
          <Text variant="overline" color="secondary" style={{ fontSize: '0.65rem' }}>
            {typeLabel}
          </Text>
        </div>

        {/* Close button for error state */}
        {isError && (
          <IconButton
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onDismiss(task.id);
            }}
            style={{
              color: colors.text.secondary,
            }}
          >
            <CloseIcon size={16} />
          </IconButton>
        )}
      </Stack>

      <Stack
        direction="column"
        align="center"
        justify="center"
        gap={1}
        style={{
          paddingTop: isError ? 16 : 32,
          paddingBottom: isError ? 16 : 32,
          backgroundColor: isError ? colors.error[50] : colors.background.subtle,
          borderRadius: radii.md,
        }}
      >
        {isError ? (
          <>
            <Text variant="bodySmall" color="error" style={{ fontWeight: 500, textAlign: 'center' }}>
              {task.error || 'An error occurred'}
            </Text>
            <Text variant="caption" color="secondary" style={{ textAlign: 'center', marginTop: 4 }}>
              Click × to dismiss
            </Text>
          </>
        ) : (
          <>
            <Spinner
              size="md"
              color={isMindmap ? 'secondary' : 'primary'}
            />
            <Text variant="bodySmall" color="secondary" style={{ fontWeight: 500 }}>
              Generating...
            </Text>
            <Text variant="caption" color="disabled">
              This may take a moment
            </Text>
          </>
        )}
      </Stack>
    </Surface>
  );
}

export default function GenerationOutputsOverlay({ viewport }: GenerationOutputsOverlayProps) {
  const {
    generationTasks,
    updateGenerationTaskPosition,
    removeGenerationTask,
  } = useStudio();

  // Drag state - only tracks if drag is active and initial conditions
  const [dragState, setDragState] = useState<DragState | null>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  // === Performance Optimization: Drag position tracked via refs, not state ===
  // This prevents React re-renders during drag
  const dragPositionRef = useRef<DragPosition | null>(null);
  const rafIdRef = useRef<number | null>(null);

  // Render tracking
  const renderCountRef = useRef(0);

  // Log render count periodically (every 10 renders during drag)
  useEffect(() => {
    renderCountRef.current++;
    if (dragState && renderCountRef.current % 10 === 0) {
      console.log(`[Perf] Overlay render count: ${renderCountRef.current}`);
    }
  });

  // Get tasks that should show loading cards (unified node model: completed outputs are now CanvasNodes)
  const renderableTasks = useMemo(() => {
    const tasks: GenerationTask[] = [];
    generationTasks.forEach(task => {
      // Show pending/generating tasks as loading cards
      // Also show error tasks so users can see failures (they'll auto-dismiss or be closable)
      // Completed tasks are now CanvasNodes rendered in KonvaCanvas
      // Note: We don't check !task.result because streaming mindmap updates result during generation
      if (task.status === 'pending' || task.status === 'generating' || task.status === 'error') {
        tasks.push(task);
      }
    });
    console.log('[Overlay] Rendering tasks:', tasks.map(t => `${t.id}(${t.status})`));
    return tasks;
  }, [generationTasks]);

  // Performance tracking
  const frameCountRef = useRef(0);
  const lastFrameTimeRef = useRef(0);
  const dragStartTimeRef = useRef(0);

  // Handle drag start
  const handleDragStart = useCallback((e: React.MouseEvent, taskId: string) => {
    const startTime = performance.now();
    console.log('[Overlay] handleDragStart called', { taskId, clientX: e.clientX, clientY: e.clientY });
    const task = generationTasks.get(taskId);
    if (!task) {
      console.warn('[Overlay] Task not found for dragging', taskId);
      return;
    }

    e.preventDefault();
    e.stopPropagation();

    const newState = {
      taskId,
      startMouseX: e.clientX,
      startMouseY: e.clientY,
      startPositionX: task.position.x,
      startPositionY: task.position.y,
    };
    console.log('[Overlay] Setting drag state', newState);
    setDragState(newState);

    // Initialize drag position ref with current position
    dragPositionRef.current = { x: task.position.x, y: task.position.y };

    // Reset performance counters
    frameCountRef.current = 0;
    lastFrameTimeRef.current = performance.now();
    dragStartTimeRef.current = performance.now();

    console.log(`[Perf] Drag start took ${(performance.now() - startTime).toFixed(2)}ms`);
  }, [generationTasks]);

  // Handle drag move - update DOM directly via CSS transform, not React state
  useEffect(() => {
    if (!dragState) return;

    const handleMouseMove = (e: MouseEvent) => {
      // RAF throttling: skip if we already have a pending frame
      if (rafIdRef.current !== null) return;

      rafIdRef.current = requestAnimationFrame(() => {
        rafIdRef.current = null;
        frameCountRef.current++;

        // Calculate delta in screen pixels
        const deltaScreenX = e.clientX - dragState.startMouseX;
        const deltaScreenY = e.clientY - dragState.startMouseY;

        // Convert screen delta to canvas coordinates (accounting for viewport scale)
        const deltaCanvasX = deltaScreenX / viewport.scale;
        const deltaCanvasY = deltaScreenY / viewport.scale;

        // Calculate new position
        const newX = dragState.startPositionX + deltaCanvasX;
        const newY = dragState.startPositionY + deltaCanvasY;

        // Store position in ref (no React re-render)
        dragPositionRef.current = { x: newX, y: newY };

        // === Direct DOM manipulation for smooth 60fps drag ===
        // Find the dragged element and update its position via CSS transform
        const element = document.querySelector(`[data-task-id="${dragState.taskId}"]`) as HTMLElement;
        if (element) {
          // Convert canvas position to screen position
          const screenX = newX * viewport.scale + viewport.x;
          const screenY = newY * viewport.scale + viewport.y;
          element.style.left = `${screenX}px`;
          element.style.top = `${screenY}px`;
        }

        // Log performance every 30 frames
        if (frameCountRef.current % 30 === 0) {
          const now = performance.now();
          const elapsed = now - lastFrameTimeRef.current;
          const fps = (30 / elapsed) * 1000;
          console.log(`[Perf] Drag FPS: ${fps.toFixed(1)}, Frame ${frameCountRef.current}`);
          lastFrameTimeRef.current = now;
        }
      });
    };

    const handleMouseUp = () => {
      // Cancel any pending RAF
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }

      const totalDragTime = performance.now() - dragStartTimeRef.current;
      const avgFps = (frameCountRef.current / totalDragTime) * 1000;
      console.log(`[Perf] Drag ended. Total frames: ${frameCountRef.current}, Duration: ${totalDragTime.toFixed(0)}ms, Avg FPS: ${avgFps.toFixed(1)}`);
      console.log('[Overlay] Drag end (mouseup)');

      // === Commit final position to React state on drag end ===
      // This is the only state update during the entire drag operation
      if (dragPositionRef.current) {
        updateGenerationTaskPosition(dragState.taskId, dragPositionRef.current);
      }

      dragPositionRef.current = null;
      setDragState(null);
    };

    // Add event listeners to window to capture mouse events outside the overlay
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      // Clean up RAF on unmount
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
    };
  }, [dragState, viewport.scale, viewport.x, viewport.y, updateGenerationTaskPosition]);

  if (renderableTasks.length === 0) {
    return null;
  }

  return (
    <div
      ref={overlayRef}
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none', // Allow click-through to canvas for panning
        zIndex: 50, // Above canvas but below modals
      }}
    >
      <style>{`
        [data-task-id] {
          pointer-events: auto;
        }
      `}</style>
      {/* Render loading cards for pending/generating tasks and error cards for failed tasks */}
      {/* Completed outputs are now CanvasNodes rendered in KonvaCanvas (unified node model) */}
      {renderableTasks.map(task => {
        const isDragging = dragState?.taskId === task.id;
        return (
          <LoadingCard
            key={task.id}
            task={task}
            viewport={viewport}
            onDragStart={handleDragStart}
            onDismiss={removeGenerationTask}
            isDragging={isDragging}
          />
        );
      })}
    </div>
  );
}

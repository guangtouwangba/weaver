'use client';

/**
 * GenerationOutputsOverlay - Renders completed generation tasks as canvas overlays
 * Watches the generationTasks state and renders SummaryCanvasNode or MindMapCanvasNode
 * for each completed task at its captured position.
 * 
 * Features:
 * - Draggable output cards with position persistence
 * - Loading placeholder cards for generating tasks
 * - Viewport-aware positioning
 * 
 * Performance Optimizations (Phase 1):
 * - Drag position tracked via useRef to avoid React state updates during drag
 * - DOM updates via CSS transform during drag (bypasses React reconciliation)
 * - RAF throttling for mouse move handler
 * - Final position committed to state only on drag end
 */

import React, { useMemo, useState, useCallback, useRef, useEffect } from 'react';
import { Box, Paper, Typography, CircularProgress } from '@mui/material';
import { useStudio, GenerationType, GenerationTask } from '@/contexts/StudioContext';
import { SummaryCanvasNode, MindMapCanvasNode } from './canvas-nodes';
import { SummaryData, MindmapData } from '@/lib/api';
import { AutoAwesomeIcon, AccountTreeIcon, OpenWithIcon } from '@/components/ui/icons';

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

// Loading placeholder card for generating tasks
function LoadingCard({ 
  task, 
  viewport,
  onDragStart,
  isDragging,
}: { 
  task: GenerationTask; 
  viewport: { x: number; y: number; scale: number };
  onDragStart: (e: React.MouseEvent, taskId: string) => void;
  isDragging: boolean;
}) {
  // Convert canvas coordinates to screen coordinates
  const screenX = task.position.x * viewport.scale + viewport.x;
  const screenY = task.position.y * viewport.scale + viewport.y;

  const isMindmap = task.type === 'mindmap';
  const gradientColor = isMindmap 
    ? 'linear-gradient(135deg, #10B981 0%, #059669 100%)'
    : 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)';
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
    <Paper
      elevation={0}
      data-task-id={task.id}
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
          alignItems: 'center', 
          gap: 1, 
          mb: 2,
          cursor: 'grab',
          '&:active': { cursor: 'grabbing' },
          userSelect: 'none',
        }}
      >
        {/* Drag Indicator Icon */}
        <Box 
          sx={{ 
            p: 0.5,
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
            background: gradientColor,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            flexShrink: 0
          }}
        >
          <TypeIcon size="sm" />
        </Box>

        {/* Title Info */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="subtitle2" fontWeight={700} sx={{ lineHeight: 1.2, mb: 0.25 }} noWrap>
            {task.title || `Generating ${task.type}...`}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
            {typeLabel}
          </Typography>
        </Box>
      </Box>

      {/* Loading Content */}
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          py: 4,
          bgcolor: '#F8FAFC',
          borderRadius: 2,
          gap: 1.5,
        }}
      >
        <CircularProgress 
          size={32} 
          sx={{ 
            color: isMindmap ? '#10B981' : '#8B5CF6' 
          }} 
        />
        <Typography variant="body2" color="text.secondary" fontWeight={500}>
          Generating...
        </Typography>
        <Typography variant="caption" color="text.disabled">
          This may take a moment
        </Typography>
      </Box>
    </Paper>
  );
}

export default function GenerationOutputsOverlay({ viewport }: GenerationOutputsOverlayProps) {
  const { 
    generationTasks, 
    removeGenerationTask,
    updateGenerationTaskPosition,
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
  renderCountRef.current++;
  
  // Log render count periodically (every 10 renders during drag)
  useEffect(() => {
    if (dragState && renderCountRef.current % 10 === 0) {
      console.log(`[Perf] Overlay render count: ${renderCountRef.current}`);
    }
  });

  // Get all tasks that should be rendered
  const renderableTasks = useMemo(() => {
    const tasks: GenerationTask[] = [];
    generationTasks.forEach(task => {
      // Show completed tasks, generating tasks (for streaming preview), and pending/generating for loading cards
      if (task.status === 'complete' || task.status === 'generating' || task.status === 'pending') {
        tasks.push(task);
      }
    });
    return tasks;
  }, [generationTasks]);

  // Performance tracking
  const frameCountRef = useRef(0);
  const lastFrameTimeRef = useRef(performance.now());
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
    <Box
      ref={overlayRef}
      sx={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none', // Allow click-through to canvas for panning
        zIndex: 50, // Above canvas but below modals
        '& > *': {
          pointerEvents: 'auto', // Enable events on children (output cards)
        },
      }}
    >
      {renderableTasks.map(task => {
        const handleClose = () => removeGenerationTask(task.id);
        const isDragging = dragState?.taskId === task.id;
        
        // Show loading card for pending/generating tasks without result
        if ((task.status === 'pending' || task.status === 'generating') && !task.result) {
          return (
            <LoadingCard
              key={task.id}
              task={task}
              viewport={viewport}
              onDragStart={handleDragStart}
              isDragging={isDragging}
            />
          );
        }
        
        if (task.type === 'summary' && task.result) {
          return (
            <SummaryCanvasNode
              key={task.id}
              id={task.id}
              data-task-id={task.id}
              title={task.title || 'Summary'}
              data={task.result as SummaryData}
              position={task.position}
              viewport={viewport}
              onClose={handleClose}
              onDragStart={(e) => handleDragStart(e, task.id)}
              onDragEnd={() => setDragState(null)}
              isDragging={isDragging}
            />
          );
        }
        
        if (task.type === 'mindmap' && task.result) {
          return (
            <MindMapCanvasNode
              key={task.id}
              id={task.id}
              data-task-id={task.id}
              title={task.title || 'Mind Map'}
              data={task.result as MindmapData}
              position={task.position}
              viewport={viewport}
              isStreaming={task.status === 'generating'}
              onClose={handleClose}
              onDragStart={(e) => handleDragStart(e, task.id)}
              onDragEnd={() => setDragState(null)}
              isDragging={isDragging}
            />
          );
        }
        
        // For other types, we could add more canvas node types here
        // For now, just return null for unsupported types
        return null;
      })}
    </Box>
  );
}


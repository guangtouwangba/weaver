'use client';

/**
 * GenerationOutputsOverlay - Renders completed generation tasks as canvas overlays
 * Watches the generationTasks state and renders SummaryCanvasNode or MindMapCanvasNode
 * for each completed task at its captured position.
 */

import React, { useMemo } from 'react';
import { Box } from '@mui/material';
import { useStudio, GenerationType, GenerationTask } from '@/contexts/StudioContext';
import { SummaryCanvasNode, MindMapCanvasNode } from './canvas-nodes';
import { SummaryData, MindmapData } from '@/lib/api';

interface GenerationOutputsOverlayProps {
  viewport: { x: number; y: number; scale: number };
}

export default function GenerationOutputsOverlay({ viewport }: GenerationOutputsOverlayProps) {
  const { 
    generationTasks, 
    removeGenerationTask 
  } = useStudio();

  // Get all tasks that should be rendered (completed or generating with partial data)
  const renderableTasks = useMemo(() => {
    const tasks: GenerationTask[] = [];
    generationTasks.forEach(task => {
      // Show completed tasks and generating tasks (for streaming preview)
      if (task.status === 'complete' || (task.status === 'generating' && task.result)) {
        tasks.push(task);
      }
    });
    return tasks;
  }, [generationTasks]);

  if (renderableTasks.length === 0) {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none', // Allow click-through to canvas
        zIndex: 50, // Above canvas but below modals
        '& > *': {
          pointerEvents: 'auto', // Enable events on children
        },
      }}
    >
      {renderableTasks.map(task => {
        const handleClose = () => removeGenerationTask(task.id);
        
        if (task.type === 'summary' && task.result) {
          return (
            <SummaryCanvasNode
              key={task.id}
              id={task.id}
              title={task.title || 'Summary'}
              data={task.result as SummaryData}
              position={task.position}
              viewport={viewport}
              onClose={handleClose}
            />
          );
        }
        
        if (task.type === 'mindmap' && task.result) {
          return (
            <MindMapCanvasNode
              key={task.id}
              id={task.id}
              title={task.title || 'Mind Map'}
              data={task.result as MindmapData}
              position={task.position}
              viewport={viewport}
              isStreaming={task.status === 'generating'}
              onClose={handleClose}
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


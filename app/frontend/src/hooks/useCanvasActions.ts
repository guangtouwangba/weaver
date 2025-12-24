import { useCallback } from 'react';
import { useStudio } from '@/contexts/StudioContext';
import { CanvasNode } from '@/lib/api';

interface UseCanvasActionsProps {
  onOpenImport?: () => void;
}

export function useCanvasActions({ onOpenImport }: UseCanvasActionsProps = {}) {
  const { addNodeToCanvas, documents } = useStudio();

  const handleAddNode = useCallback((
    type: 'default' | 'sticky' | 'source' | 'insight', 
    position: { x: number, y: number },
    content: string = 'New Node'
  ) => {
    const node: Omit<CanvasNode, 'id'> = {
      type: type === 'sticky' ? 'sticky' : 'default', // Map to valid types
      title: type === 'sticky' ? 'Sticky Note' : 'New Node',
      content: content,
      x: position.x,
      y: position.y,
      width: type === 'sticky' ? 200 : 280,
      height: type === 'sticky' ? 200 : 160,
      color: type === 'sticky' ? '#fef3c7' : 'white', // Yellow for sticky
    };
    
    addNodeToCanvas(node);
  }, [addNodeToCanvas]);

  const handleGenerateContent = useCallback(async (
    type: 'mindmap' | 'flashcards' | 'summary' | 'podcast' | 'quiz' | 'timeline' | 'compare'
  ) => {
    // Placeholder for future implementation
    console.log(`Generating ${type}...`);
    
    // Example simulation
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        console.log(`${type} generated`);
        resolve();
      }, 1000);
    });
  }, []);

  const handleImportSource = useCallback(() => {
    if (onOpenImport) {
      onOpenImport();
    } else {
      console.warn('Import dialog handler not provided');
    }
  }, [onOpenImport]);

  return {
    handleAddNode,
    handleGenerateContent,
    handleImportSource,
  };
}


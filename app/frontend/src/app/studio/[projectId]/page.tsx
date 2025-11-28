'use client';

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import GlobalLayout from "@/components/layout/GlobalLayout";
import { Box } from "@mui/material";
import { StudioProvider } from "@/contexts/StudioContext";
import SourcePanel from "@/components/studio/SourcePanel";
import AssistantPanel from "@/components/studio/AssistantPanel";
import CanvasPanel from "@/components/studio/CanvasPanel";

// Helper Component
const VerticalResizeHandle = ({ onMouseDown }: { onMouseDown: (e: React.MouseEvent) => void }) => (
  <Box 
    onMouseDown={onMouseDown}
    sx={{
      width: 4,
      cursor: 'col-resize',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      bgcolor: 'transparent',
      zIndex: 50,
      height: '100%',
      flexShrink: 0,
      transition: 'background-color 0.2s',
      '&:hover': { bgcolor: 'primary.main' },
      '&:active': { bgcolor: 'primary.main' }
    }}
  />
);

export default function StudioPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  // --- Layout State ---
  const [leftVisible, setLeftVisible] = useState(true);
  const [centerVisible, setCenterVisible] = useState(true);
  const [leftWidth, setLeftWidth] = useState(380);
  const [centerWidth, setCenterWidth] = useState(380); 
  const [resizingCol, setResizingCol] = useState<'left' | 'center' | null>(null);

  // --- Resize Logic ---
  const handleHorizontalMouseDown = (col: 'left' | 'center') => (e: React.MouseEvent) => {
    e.preventDefault();
    setResizingCol(col);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (resizingCol) {
        const min = 280, max = 600;
        if (resizingCol === 'left') {
          setLeftWidth(Math.max(min, Math.min(e.clientX, max)));
        } else {
          // Calculate center width based on mouse position relative to left panel
          const offset = leftVisible ? leftWidth : 49;
          setCenterWidth(Math.max(min, Math.min(e.clientX - offset, max)));
        }
      }
    };
    
    const handleMouseUp = () => {
      setResizingCol(null);
    };
    
    if (resizingCol) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    };
  }, [resizingCol, leftWidth, leftVisible]);

  // --- Keyboard Shortcuts for Layout ---
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';
      
      if (!isInput) {
        if ((e.metaKey || e.ctrlKey) && e.key === '\\') {
          e.preventDefault();
          setLeftVisible(prev => !prev);
        }
        if ((e.metaKey || e.ctrlKey) && e.key === '.') {
          e.preventDefault();
          setCenterVisible(prev => !prev);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <StudioProvider projectId={projectId}>
      <GlobalLayout>
        <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.paper' }}>
          {/* LEFT: Source Panel */}
          <SourcePanel 
            visible={leftVisible} 
            width={leftWidth} 
            onToggle={() => setLeftVisible(!leftVisible)}
          />
          {leftVisible && <VerticalResizeHandle onMouseDown={handleHorizontalMouseDown('left')} />}

          {/* CENTER: AI Assistant */}
          <AssistantPanel 
            visible={centerVisible}
            width={centerWidth}
            onToggle={() => setCenterVisible(!centerVisible)}
          />
          {centerVisible && <VerticalResizeHandle onMouseDown={handleHorizontalMouseDown('center')} />}
          
          {/* RIGHT: Canvas */}
          <CanvasPanel />
        </Box>
      </GlobalLayout>
    </StudioProvider>
  );
}

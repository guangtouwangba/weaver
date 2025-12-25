'use client';

import { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Chip,
  CircularProgress
} from "@mui/material";
import { 
  Layout, 
  FileText,
  Link as LinkIcon,
} from "lucide-react";
import { useStudio } from '@/contexts/StudioContext';
import { canvasApi } from '@/lib/api';
import { CanvasNode } from '@/lib/api';
import ThinkingPathGenerator from './ThinkingPathGenerator';

export default function CanvasPanel() {
  const { 
    projectId, 
    canvasNodes, setCanvasNodes, 
    canvasEdges, setCanvasEdges,
    canvasViewport: viewport, setCanvasViewport: setViewport,
    saveCanvas,
    addNodeToCanvas,
    isGenerating // Global generation state
  } = useStudio();

  const [isPanning, setIsPanning] = useState(false);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [connectingNodeId, setConnectingNodeId] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string | null>(null);
  const [tempLineEnd, setTempLineEnd] = useState<{ x: number, y: number } | null>(null);
  
  const lastMousePos = useRef({ x: 0, y: 0 });
  const mousePos = useRef({ x: 0, y: 0 });
  const dragStartPos = useRef<{ x: number, y: number } | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);

  // Auto-save on change (debounced)
  useEffect(() => {
    const timeout = setTimeout(() => {
        if (canvasNodes.length > 0) {
            saveCanvas(); // Trigger context save which calls API
            canvasApi.save(projectId, {
                nodes: canvasNodes,
                edges: canvasEdges,
                viewport: viewport
            }).catch(err => console.error("Auto-save failed", err));
        }
    }, 2000);
    return () => clearTimeout(timeout);
  }, [canvasNodes, canvasEdges, viewport, projectId, saveCanvas]);

  // --- Keyboard Shortcuts ---
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';
      
      if (e.code === 'Space' && !e.repeat && !isInput) {
        e.preventDefault(); 
        setIsSpacePressed(true);
      }
      
      // Delete selected node or connection
      if ((e.key === 'Delete' || e.key === 'Backspace') && !isInput) {
        e.preventDefault();
        if (selectedConnectionId) {
          setCanvasEdges(prev => prev.filter(edge => edge.id !== selectedConnectionId));
          setSelectedConnectionId(null);
        } else if (selectedNodeId) {
          setCanvasNodes(prev => prev.filter(node => node.id !== selectedNodeId));
          setCanvasEdges(prev => prev.filter(edge => edge.source !== selectedNodeId && edge.target !== selectedNodeId));
          setSelectedNodeId(null);
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        setIsSpacePressed(false);
        setIsPanning(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [selectedConnectionId, selectedNodeId, setCanvasNodes, setCanvasEdges]);

  // --- Canvas Wheel Handler ---
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      
      if (e.metaKey || e.ctrlKey) {
        const delta = -e.deltaY * 0.001;
        const newScale = Math.min(Math.max(0.1, viewport.scale * (1 + delta)), 5);
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        const cx = (mx - viewport.x) / viewport.scale;
        const cy = (my - viewport.y) / viewport.scale;
        setViewport({ x: mx - cx * newScale, y: my - cy * newScale, scale: newScale });
      } else {
        setViewport({ ...viewport, x: viewport.x - e.deltaX, y: viewport.y - e.deltaY });
      }
    };

    canvas.addEventListener('wheel', handleWheel, { passive: false });
    return () => canvas.removeEventListener('wheel', handleWheel);
  }, [viewport, setViewport]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const rect = canvasRef.current?.getBoundingClientRect();
    if (rect) {
      const x = (e.clientX - rect.left - viewport.x) / viewport.scale;
      const y = (e.clientY - rect.top - viewport.y) / viewport.scale;
      
      // Try to get custom JSON data first
      const jsonData = e.dataTransfer.getData("application/json");
      if (jsonData) {
        try {
            const data = JSON.parse(jsonData);
            if (data.sourceType === 'pdf' && data.content) {
                addNodeToCanvas({
                    type: 'card',
                    title: data.sourceTitle || 'PDF Note',
                    content: data.content,
                    x: x - 140,
                    y: y - 100,
                    width: 280,
                    height: 200,
                    color: 'white',
                    tags: ['#pdf'],
                    sourceId: data.sourceId,
                    sourcePage: data.pageNumber
                });
                return;
            }
            
            // Handle citation drop from AI responses
            if (data.sourceType === 'citation' && data.content) {
                addNodeToCanvas({
                    type: 'card',
                    title: data.sourceTitle || 'Citation',
                    content: data.content,
                    x: x - 140,
                    y: y - 100,
                    width: 280,
                    height: 200,
                    color: 'white',
                    tags: data.tags || ['#citation'],
                    sourceId: data.sourceId,
                    sourcePage: data.pageNumber
                });
                return;
            }
        } catch (e) {
            console.error("Failed to parse drop data", e);
        }
      }

      // Fallback to plain text
      const text = e.dataTransfer.getData("text/plain");
      
      if (text) {
        addNodeToCanvas({
            type: 'card',
            title: 'New Note',
            content: text,
            x: x - 140,
            y: y - 100,
            width: 280,
            height: 200,
            color: 'white',
            tags: []
        });
      }
    }
  };

  return (
    <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative' }}>
      <Box sx={{ height: 48, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', px: 3, justifyContent: 'space-between', bgcolor: '#FAFAFA', flexShrink: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Layout size={14} className="text-gray-500" />
          <Typography variant="subtitle2" fontWeight="600">Canvas</Typography>
          {isGenerating && (
            <Chip 
              size="small" 
              icon={<CircularProgress size={12} />} 
              label="Generating..." 
              sx={{ ml: 2, height: 24, fontSize: '0.75rem' }} 
            />
          )}
        </Box>
        <Typography variant="caption" color="text.disabled">Auto-saved</Typography>
      </Box>
      
      <Box 
        ref={canvasRef}
        sx={{ 
          flexGrow: 1, 
          bgcolor: '#FAFAFA', 
          position: 'relative', 
          overflow: 'hidden',
          cursor: isSpacePressed ? (isPanning ? 'grabbing' : 'grab') : 'default',
          touchAction: 'none',
          userSelect: 'none'
        }}
        onMouseDown={(e) => {
          if (isSpacePressed || e.button === 1) {
            setIsPanning(true);
            lastMousePos.current = { x: e.clientX, y: e.clientY };
          } else if (e.button === 0) {
            setSelectedNodeId(null);
            setSelectedConnectionId(null);
            setIsPanning(true);
            lastMousePos.current = { x: e.clientX, y: e.clientY };
          }
        }}
        onMouseMove={(e) => {
          mousePos.current = { x: e.clientX, y: e.clientY };
          
          if (connectingNodeId && canvasRef.current) {
            const rect = canvasRef.current.getBoundingClientRect();
            const x = (e.clientX - rect.left - viewport.x) / viewport.scale;
            const y = (e.clientY - rect.top - viewport.y) / viewport.scale;
            requestAnimationFrame(() => setTempLineEnd({ x, y }));
            return;
          }
          
          if (draggingNodeId) {
            if (dragStartPos.current) {
              if (Math.abs(e.clientX - dragStartPos.current.x) < 3 && Math.abs(e.clientY - dragStartPos.current.y) < 3) return;
              dragStartPos.current = null;
            }
            const dx = (e.clientX - lastMousePos.current.x) / viewport.scale;
            const dy = (e.clientY - lastMousePos.current.y) / viewport.scale;
            setCanvasNodes(prev => prev.map(n => n.id === draggingNodeId ? { ...n, x: n.x + dx, y: n.y + dy } : n));
            lastMousePos.current = { x: e.clientX, y: e.clientY };
          } else if (isPanning) {
            const dx = e.clientX - lastMousePos.current.x;
            const dy = e.clientY - lastMousePos.current.y;
            setViewport({ ...viewport, x: viewport.x + dx, y: viewport.y + dy });
            lastMousePos.current = { x: e.clientX, y: e.clientY };
          }
        }}
        onMouseUp={() => {
          setIsPanning(false);
          setDraggingNodeId(null);
          dragStartPos.current = null;
          setConnectingNodeId(null);
          setTempLineEnd(null);
        }}
        onMouseLeave={() => {
          setIsPanning(false);
          setDraggingNodeId(null);
          setConnectingNodeId(null);
          setTempLineEnd(null);
          dragStartPos.current = null;
        }}
        onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = "copy"; }}
        onDrop={handleDrop}
      >
        {/* Grid Background */}
        <Box 
          sx={{ 
            position: 'absolute', 
            inset: 0, 
            opacity: 0.5, 
            backgroundImage: 'radial-gradient(#D1D5DB 1px, transparent 1px)', 
            backgroundSize: `${20 * viewport.scale}px ${20 * viewport.scale}px`,
            backgroundPosition: `${viewport.x}px ${viewport.y}px`,
            pointerEvents: 'none'
          }} 
        />
        
        {/* Canvas Content */}
        <Box sx={{ transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.scale})`, transformOrigin: '0 0', position: 'absolute', top: 0, left: 0 }}>
          {/* SVG Connections */}
          <svg style={{ position: 'absolute', top: 0, left: 0, width: 10000, height: 10000, overflow: 'visible', pointerEvents: 'visiblePainted' }}>
            <rect width="10000" height="10000" fill="transparent" style={{ pointerEvents: 'none' }} />
            {canvasEdges.map(edge => {
              const source = canvasNodes.find(n => n.id === edge.source);
              const target = canvasNodes.find(n => n.id === edge.target);
              if (!source || !target) return null;
              
              const x1 = source.x + 280, y1 = source.y + 60; // Simplified anchor points
              const x2 = target.x, y2 = target.y + 60;
              const ctrl = Math.max(Math.abs(x2 - x1) * 0.4, 50);
              const isSelected = selectedConnectionId === edge.id;

              return (
                <g key={edge.id || `${edge.source}-${edge.target}`}>
                  <path 
                    d={`M ${x1} ${y1} C ${x1 + ctrl} ${y1}, ${x2 - ctrl} ${y2}, ${x2} ${y2}`}
                    stroke="transparent" strokeWidth="12" fill="none"
                    style={{ pointerEvents: 'stroke', cursor: 'pointer' }}
                    onClick={(e) => { e.stopPropagation(); setSelectedConnectionId(edge.id || null); setSelectedNodeId(null); }}
                  />
                  <path 
                    d={`M ${x1} ${y1} C ${x1 + ctrl} ${y1}, ${x2 - ctrl} ${y2}, ${x2} ${y2}`}
                    stroke={isSelected ? "#EF4444" : "#94A3B8"} 
                    strokeWidth={isSelected ? 3 : 2}
                    fill="none"
                    style={{ pointerEvents: 'none' }}
                  />
                </g>
              );
            })}

            {/* Temp Connection Line */}
            {connectingNodeId && tempLineEnd && (() => {
              const src = canvasNodes.find(n => n.id === connectingNodeId);
              if (!src) return null;
              const x1 = src.x + 280, y1 = src.y + 50;
              const ctrl = Math.max(Math.abs(tempLineEnd.x - x1) * 0.5, 50);
              return <path d={`M ${x1} ${y1} C ${x1 + ctrl} ${y1}, ${tempLineEnd.x - ctrl} ${tempLineEnd.y}, ${tempLineEnd.x} ${tempLineEnd.y}`} stroke="#3B82F6" strokeWidth="2" fill="none" strokeDasharray="5,5" />;
            })()}
          </svg>

          {/* Nodes */}
          {canvasNodes.map(node => (
            <Paper 
              key={node.id}
              elevation={selectedNodeId === node.id ? 8 : 2} 
              draggable
              onDragStart={(e) => {
                // Set data for dragging to chat input
                const payload = {
                  type: 'canvas_node',
                  id: node.id,
                  title: node.title,
                  content: node.content,
                  sourceMessageId: (node as any).messageIds?.[0] || null // Assuming messageIds might exist on node in future
                };
                e.dataTransfer.setData('application/json', JSON.stringify(payload));
                e.dataTransfer.effectAllowed = 'copy';
                
                // Prevent interfering with internal canvas dragging if needed
                // But for native drag & drop to another component, we need this event
                // We'll let the internal onMouseDown handle the internal dragging
              }}
              onMouseDown={(e) => {
                e.stopPropagation();
                if (!(e.target as HTMLElement).closest('.conn-handle')) {
                  setDraggingNodeId(node.id);
                  setSelectedNodeId(node.id);
                  setSelectedConnectionId(null);
                  lastMousePos.current = { x: e.clientX, y: e.clientY };
                  dragStartPos.current = { x: e.clientX, y: e.clientY };
                }
              }}
              onMouseUp={(e) => {
                e.stopPropagation();
                if (connectingNodeId && connectingNodeId !== node.id) {
                  // Create new edge
                  const newEdge = { source: connectingNodeId, target: node.id, id: `e-${Date.now()}` };
                  setCanvasEdges(prev => [...prev, newEdge]);
                }
                setConnectingNodeId(null);
                setTempLineEnd(null);
                setDraggingNodeId(null);
                dragStartPos.current = null;
              }}
              onMouseEnter={() => setHoveredNodeId(node.id)}
              onMouseLeave={() => setHoveredNodeId(null)}
              sx={{ 
                position: 'absolute', 
                top: node.y, 
                left: node.x, 
                width: 280, 
                borderRadius: 3, 
                border: '2px solid', 
                borderColor: connectingNodeId && connectingNodeId !== node.id ? '#10B981' : (selectedNodeId === node.id ? 'primary.main' : (node.color === 'blue' ? '#3B82F6' : 'transparent')),
                overflow: 'visible',
                cursor: 'grab',
                '&:hover': { boxShadow: 4 }
              }}
            >
              {/* Connection Handle */}
              <Box
                className="conn-handle"
                onMouseDown={(e) => { e.stopPropagation(); setConnectingNodeId(node.id); }}
                sx={{
                  position: 'absolute', right: -6, top: '50%', transform: 'translateY(-50%)',
                  width: 12, height: 12, borderRadius: '50%', bgcolor: '#3B82F6', border: '2px solid white',
                  cursor: 'crosshair', opacity: hoveredNodeId === node.id || connectingNodeId === node.id ? 1 : 0,
                  transition: 'opacity 0.2s', zIndex: 10
                }}
              />
              
              {/* Receiving Handle */}
              {connectingNodeId && connectingNodeId !== node.id && (
                <Box sx={{ position: 'absolute', left: -6, top: '50%', transform: 'translateY(-50%)', width: 12, height: 12, borderRadius: '50%', bgcolor: '#10B981', border: '2px solid white', zIndex: 10 }} />
              )}
              
              {/* Card Content */}
              <Box sx={{ overflow: 'hidden', borderRadius: 2 }}>
                <Box sx={{ height: 4, bgcolor: node.color === 'blue' ? '#3B82F6' : '#E5E7EB' }} />
                <Box sx={{ p: 2 }}>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom>{node.title}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5, mb: 1.5 }}>{node.content}</Typography>
                  {node.tags && (
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {node.tags.map(tag => <Chip key={tag} label={tag} size="small" sx={{ height: 20, fontSize: 10, bgcolor: '#F3F4F6' }} />)}
                    </Box>
                  )}
                </Box>
              </Box>
            </Paper>
          ))}
        </Box>
      </Box>
      <ThinkingPathGenerator />
    </Box>
  );
}


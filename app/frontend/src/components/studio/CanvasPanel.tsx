'use client';

import { useState, useRef, useEffect } from 'react';
import { Chip } from "@/components/ui/primitives";
import {
  Stack,
  Surface,
  Text,
  Spinner,
} from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import {
  DashboardIcon,
} from '@/components/ui/icons';
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
              sourcePage: data.pageNumber,
              viewType: 'free',
              subType: 'source'
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
              sourcePage: data.pageNumber,
              viewType: 'free',
              subType: 'source'
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
          tags: [],
          viewType: 'free',
          subType: 'note'
        });
      }
    }
  };

  return (
    <Stack
      direction="column"
      style={{
        flexGrow: 1,
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {/* Header */}
      <Stack
        direction="row"
        align="center"
        justify="between"
        style={{
          height: 48,
          borderBottom: `1px solid ${colors.border.default}`,
          paddingLeft: 24,
          paddingRight: 24,
          backgroundColor: colors.background.subtle,
          flexShrink: 0,
        }}
      >
        <Stack direction="row" align="center" gap={1}>
          <DashboardIcon size={14} style={{ color: colors.neutral[500] }} />
          <Text variant="label">Canvas</Text>
          {isGenerating && (
            <Chip
              size="sm"
              icon={<Spinner size="xs" color="primary" />}
              label="Generating..."
              style={{ marginLeft: 16, height: 24, fontSize: '0.75rem' }}
            />
          )}
        </Stack>
        <Text variant="caption" color="disabled">Auto-saved</Text>
      </Stack>

      {/* Canvas Area */}
      <div
        ref={canvasRef}
        style={{
          flexGrow: 1,
          backgroundColor: colors.background.subtle,
          position: 'relative',
          overflow: 'hidden',
          cursor: isSpacePressed ? (isPanning ? 'grabbing' : 'grab') : 'default',
          touchAction: 'none',
          userSelect: 'none',
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
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0.5,
            backgroundImage: 'radial-gradient(#D1D5DB 1px, transparent 1px)',
            backgroundSize: `${20 * viewport.scale}px ${20 * viewport.scale}px`,
            backgroundPosition: `${viewport.x}px ${viewport.y}px`,
            pointerEvents: 'none',
          }}
        />

        {/* Canvas Content */}
        <div
          style={{
            transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.scale})`,
            transformOrigin: '0 0',
            position: 'absolute',
            top: 0,
            left: 0,
          }}
        >
          {/* SVG Connections */}
          <svg style={{ position: 'absolute', top: 0, left: 0, width: 10000, height: 10000, overflow: 'visible', pointerEvents: 'visiblePainted' }}>
            <rect width="10000" height="10000" fill="transparent" style={{ pointerEvents: 'none' }} />
            {canvasEdges.map(edge => {
              const source = canvasNodes.find(n => n.id === edge.source);
              const target = canvasNodes.find(n => n.id === edge.target);
              if (!source || !target) return null;

              const x1 = source.x + 280, y1 = source.y + 60;
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
                    stroke={isSelected ? colors.error[500] : colors.neutral[400]}
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
              return <path d={`M ${x1} ${y1} C ${x1 + ctrl} ${y1}, ${tempLineEnd.x - ctrl} ${tempLineEnd.y}, ${tempLineEnd.x} ${tempLineEnd.y}`} stroke={colors.primary[500]} strokeWidth="2" fill="none" strokeDasharray="5,5" />;
            })()}
          </svg>

          {/* Nodes */}
          {canvasNodes.map(node => (
            <Surface
              key={node.id}
              elevation={selectedNodeId === node.id ? 4 : 2}
              radius="lg"
              draggable
              onDragStart={(e: React.DragEvent) => {
                const payload = {
                  type: 'canvas_node',
                  id: node.id,
                  title: node.title,
                  content: node.content,
                  sourceMessageId: (node as any).messageIds?.[0] || null
                };
                e.dataTransfer.setData('application/json', JSON.stringify(payload));
                e.dataTransfer.effectAllowed = 'copy';
              }}
              onMouseDown={(e: React.MouseEvent) => {
                e.stopPropagation();
                if (!(e.target as HTMLElement).closest('.conn-handle')) {
                  setDraggingNodeId(node.id);
                  setSelectedNodeId(node.id);
                  setSelectedConnectionId(null);
                  lastMousePos.current = { x: e.clientX, y: e.clientY };
                  dragStartPos.current = { x: e.clientX, y: e.clientY };
                }
              }}
              onMouseUp={(e: React.MouseEvent) => {
                e.stopPropagation();
                if (connectingNodeId && connectingNodeId !== node.id) {
                  const newEdge = { source: connectingNodeId, target: node.id, id: `e-${crypto.randomUUID()}` };
                  setCanvasEdges(prev => [...prev, newEdge]);
                }
                setConnectingNodeId(null);
                setTempLineEnd(null);
                setDraggingNodeId(null);
                dragStartPos.current = null;
              }}
              onMouseEnter={() => setHoveredNodeId(node.id)}
              onMouseLeave={() => setHoveredNodeId(null)}
              className="canvas-node-surface"
              style={{
                position: 'absolute',
                top: node.y,
                left: node.x,
                width: 280,
                border: '2px solid',
                borderColor: connectingNodeId && connectingNodeId !== node.id
                  ? colors.success[500]
                  : (selectedNodeId === node.id
                    ? colors.primary[500]
                    : (node.color === 'blue' ? colors.primary[500] : 'transparent')),
                overflow: 'visible',
                cursor: 'grab',
              }}
            >
              {/* Connection Handle */}
              <div
                className="conn-handle"
                onMouseDown={(e) => { e.stopPropagation(); setConnectingNodeId(node.id); }}
                style={{
                  position: 'absolute',
                  right: -6,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: colors.primary[500],
                  border: '2px solid white',
                  cursor: 'crosshair',
                  opacity: hoveredNodeId === node.id || connectingNodeId === node.id ? 1 : 0,
                  transition: 'opacity 0.2s',
                  zIndex: 10,
                }}
              />

              {/* Receiving Handle */}
              {connectingNodeId && connectingNodeId !== node.id && (
                <div
                  style={{
                    position: 'absolute',
                    left: -6,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: colors.success[500],
                    border: '2px solid white',
                    zIndex: 10,
                  }}
                />
              )}

              {/* Card Content */}
              <div style={{ overflow: 'hidden', borderRadius: radii.md }}>
                <div
                  style={{
                    height: 4,
                    backgroundColor: node.color === 'blue' ? colors.primary[500] : colors.neutral[200],
                  }}
                />
                <div style={{ padding: 16 }}>
                  <Text variant="label" style={{ marginBottom: 4 }}>{node.title}</Text>
                  <Text variant="bodySmall" color="secondary" style={{ lineHeight: 1.5, marginBottom: 12 }}>{node.content}</Text>
                  {node.tags && (
                    <Stack direction="row" gap={0} style={{ flexWrap: 'wrap', gap: 4 }}>
                      {node.tags.map(tag => (
                        <Chip key={tag} label={tag} size="sm" style={{ height: 20, fontSize: 10, backgroundColor: colors.neutral[100] }} />
                      ))}
                    </Stack>
                  )}
                </div>
              </div>
            </Surface>
          ))}
        </div>
      </div>
      <ThinkingPathGenerator />
      <style>{`
        .canvas-node-surface {
          transition: box-shadow 0.2s;
        }
        .canvas-node-surface:hover {
          box-shadow: ${shadows.lg};
        }
      `}</style>
    </Stack>
  );
}

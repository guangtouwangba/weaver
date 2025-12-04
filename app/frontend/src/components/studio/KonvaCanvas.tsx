'use client';

/**
 * High-performance Konva.js-powered Canvas
 * Replaces DOM-based rendering with HTML5 Canvas for better performance
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { Stage, Layer, Group, Rect, Text, Line, Arrow } from 'react-konva';
import Konva from 'konva';
import { Box, Typography } from '@mui/material';
import { Layout } from 'lucide-react';
import { useStudio } from '@/contexts/StudioContext';

interface CanvasNode {
  id: string;
  type: string;
  title: string;
  content: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  color?: string;
  tags?: string[];
  sourceId?: string;
  sourcePage?: number;
}

interface CanvasEdge {
  id?: string;
  source: string;
  target: string;
}

interface Viewport {
  x: number;
  y: number;
  scale: number;
}

interface KonvaCanvasProps {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  viewport: Viewport;
  onNodesChange: (nodes: CanvasNode[]) => void;
  onEdgesChange: (edges: CanvasEdge[]) => void;
  onViewportChange: (viewport: Viewport) => void;
  onNodeAdd?: (node: Partial<CanvasNode>) => void;
}

// Knowledge Node Component
const KnowledgeNode = ({
  node,
  isSelected,
  onSelect,
  onDragStart,
  onDragEnd,
}: {
  node: CanvasNode;
  isSelected: boolean;
  onSelect: () => void;
  onDragStart: () => void;
  onDragEnd: (e: Konva.KonvaEventObject<DragEvent>) => void;
}) => {
  const width = node.width || 280;
  const height = node.height || 200;
  const nodeColor = node.color === 'blue' ? '#3B82F6' : '#E5E7EB';

  return (
    <Group
      x={node.x}
      y={node.y}
      draggable
      onClick={onSelect}
      onTap={onSelect}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
    >
      {/* Border/Background */}
      <Rect
        width={width}
        height={height}
        fill="white"
        cornerRadius={12}
        stroke={isSelected ? '#3B82F6' : '#E5E7EB'}
        strokeWidth={isSelected ? 3 : 2}
        shadowColor="black"
        shadowBlur={isSelected ? 12 : 8}
        shadowOpacity={isSelected ? 0.15 : 0.08}
        shadowOffsetY={4}
      />

      {/* Top Color Bar */}
      <Rect
        y={0}
        width={width}
        height={4}
        fill={nodeColor}
        cornerRadius={[12, 12, 0, 0]}
      />

      {/* Title */}
      <Text
        x={16}
        y={20}
        width={width - 32}
        text={node.title}
        fontSize={16}
        fontStyle="bold"
        fill="#1F2937"
        wrap="word"
        ellipsis={true}
      />

      {/* Content */}
      <Text
        x={16}
        y={55}
        width={width - 32}
        height={90}
        text={node.content}
        fontSize={14}
        fill="#6B7280"
        wrap="word"
        ellipsis={true}
      />

      {/* Tags (simplified - show first tag only) */}
      {node.tags && node.tags.length > 0 && (
        <>
          <Rect
            x={16}
            y={height - 35}
            width={Math.min(node.tags[0].length * 7 + 16, width - 32)}
            height={20}
            fill="#F3F4F6"
            cornerRadius={4}
          />
          <Text
            x={24}
            y={height - 32}
            text={node.tags[0]}
            fontSize={10}
            fill="#6B7280"
          />
        </>
      )}

      {/* Source info */}
      {node.sourceId && (
        <Text
          x={16}
          y={height - 25}
          width={width - 32}
          text={`📄 ${node.sourceId.substring(0, 8)}${node.sourcePage ? ` • p.${node.sourcePage}` : ''}`}
          fontSize={11}
          fill="#9CA3AF"
        />
      )}
    </Group>
  );
};

export default function KonvaCanvas({
  nodes,
  edges,
  viewport,
  onNodesChange,
  onEdgesChange,
  onViewportChange,
  onNodeAdd,
}: KonvaCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isPanning, setIsPanning] = useState(false);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const lastPosRef = useRef({ x: 0, y: 0 });
  const { dragPreview, setDragPreview, dragContentRef } = useStudio();

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Handle keyboard shortcuts (Space for panning)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';
      
      if (e.code === 'Space' && !e.repeat && !isInput) {
        e.preventDefault();
        setIsSpacePressed(true);
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
  }, []);

  // Handle node drag
  const handleNodeDragStart = useCallback(
    (nodeId: string) => () => {
      setSelectedNodeId(nodeId);
    },
    []
  );

  const handleNodeDragEnd = useCallback(
    (nodeId: string) => (e: Konva.KonvaEventObject<DragEvent>) => {
      const updatedNodes = nodes.map((n) =>
        n.id === nodeId
          ? { ...n, x: e.target.x(), y: e.target.y() }
          : n
      );
      onNodesChange(updatedNodes);
    },
    [nodes, onNodesChange]
  );

  // Handle wheel zoom
  const handleWheel = (e: Konva.KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();
    const stage = stageRef.current;
    if (!stage) return;

    const scaleBy = 1.1;
    const oldScale = viewport.scale;
    const pointer = stage.getPointerPosition();
    
    if (!pointer) return;

    const mousePointTo = {
      x: (pointer.x - viewport.x) / oldScale,
      y: (pointer.y - viewport.y) / oldScale,
    };

    const newScale = e.evt.deltaY > 0 ? oldScale / scaleBy : oldScale * scaleBy;
    const clampedScale = Math.max(0.1, Math.min(5, newScale));

    onViewportChange({
      scale: clampedScale,
      x: pointer.x - mousePointTo.x * clampedScale,
      y: pointer.y - mousePointTo.y * clampedScale,
    });
  };

  // Handle manual panning
  const handleStageMouseDown = (e: Konva.KonvaEventObject<MouseEvent>) => {
    // Only pan when clicking on empty space (Stage or background)
    const clickedOnEmpty = e.target === e.target.getStage() || e.target.getClassName() === 'Rect';
    
    if (clickedOnEmpty) {
      // Left click on empty space = pan, or middle mouse button
      if (e.evt.button === 0 || e.evt.button === 1 || isSpacePressed) {
        setIsPanning(true);
        lastPosRef.current = { x: e.evt.clientX, y: e.evt.clientY };
      }
      // Also deselect when clicking on empty space
      setSelectedNodeId(null);
    }
  };

  const handleStageMouseMove = (e: Konva.KonvaEventObject<MouseEvent>) => {
    if (!isPanning) return;

    const dx = e.evt.clientX - lastPosRef.current.x;
    const dy = e.evt.clientY - lastPosRef.current.y;

    onViewportChange({
      ...viewport,
      x: viewport.x + dx,
      y: viewport.y + dy,
    });

    lastPosRef.current = { x: e.evt.clientX, y: e.evt.clientY };
  };

  const handleStageMouseUp = () => {
    setIsPanning(false);
  };

  // Draw connections
  const renderEdges = () => {
    return edges.map((edge, index) => {
      const source = nodes.find((n) => n.id === edge.source);
      const target = nodes.find((n) => n.id === edge.target);
      
      if (!source || !target) return null;

      const x1 = source.x + (source.width || 280);
      const y1 = source.y + ((source.height || 200) / 2);
      const x2 = target.x;
      const y2 = target.y + ((target.height || 200) / 2);

      const controlOffset = Math.max(Math.abs(x2 - x1) * 0.4, 50);

      return (
        <Line
          key={edge.id || `${edge.source}-${edge.target}-${index}`}
          points={[
            x1, y1,
            x1 + controlOffset, y1,
            x2 - controlOffset, y2,
            x2, y2
          ]}
          stroke="#94A3B8"
          strokeWidth={2}
          tension={0.5}
          bezier
        />
      );
    });
  };

  return (
    <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Header */}
      <Box 
        sx={{ 
          height: 48, 
          borderBottom: '1px solid', 
          borderColor: 'divider', 
          display: 'flex', 
          alignItems: 'center', 
          px: 3, 
          justifyContent: 'space-between', 
          bgcolor: '#FAFAFA',
          zIndex: 100
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Layout size={14} className="text-gray-500" />
          <Typography variant="subtitle2" fontWeight="600">
            Canvas
          </Typography>
        </Box>
        <Typography variant="caption" color="text.disabled">
          Auto-saved • {nodes.length} nodes
        </Typography>
      </Box>

      {/* Canvas Container */}
      <Box
        ref={containerRef}
        sx={{ 
          flexGrow: 1, 
          bgcolor: '#FAFAFA', 
          position: 'relative',
          overflow: 'hidden'
        }}
        onDragOver={(e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'copy';

          // Update drag preview position while dragging AI response
          if (dragContentRef.current && containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect();
            const screenX = e.clientX - rect.left;
            const screenY = e.clientY - rect.top;
            const canvasX = (screenX - viewport.x) / viewport.scale;
            const canvasY = (screenY - viewport.y) / viewport.scale;

            setDragPreview({
              x: canvasX,
              y: canvasY,
              content: dragContentRef.current,
            });
          }
        }}
        onDragLeave={() => {
          setDragPreview(null);
        }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();

          if (!containerRef.current) return;

          const rect = containerRef.current.getBoundingClientRect();
          const screenX = e.clientX - rect.left;
          const screenY = e.clientY - rect.top;
          const canvasX = (screenX - viewport.x) / viewport.scale;
          const canvasY = (screenY - viewport.y) / viewport.scale;

          // Center the card on mouse position (card width: 280, height: 200)
          const cardWidth = 280;
          const cardHeight = 200;
          const centeredX = canvasX - cardWidth / 2;
          const centeredY = canvasY - cardHeight / 2;

          let handled = false;

          const jsonData = e.dataTransfer.getData('application/json');
          if (jsonData && onNodeAdd) {
            try {
              const data = JSON.parse(jsonData);
              if (data.type === 'ai_response') {
                onNodeAdd({
                  type: 'ai_insight',
                  title: data.source?.query || 'AI Insight',
                  content: data.content,
                  x: centeredX,
                  y: centeredY,
                  width: cardWidth,
                  height: cardHeight,
                  color: 'blue',
                  tags: ['#ai'],
                });
                handled = true;
              }
            } catch {
              // ignore JSON parse errors
            }
          }

          if (!handled && onNodeAdd) {
            const text = e.dataTransfer.getData('text/plain');
            if (text) {
              onNodeAdd({
                type: 'card',
                title: 'New Insight',
                content: text,
                x: centeredX,
                y: centeredY,
                width: cardWidth,
                height: cardHeight,
                color: 'blue',
                tags: ['#from-drag'],
              });
            }
          }

          setDragPreview(null);
        }}
      >
        <Stage
          ref={stageRef}
          width={dimensions.width}
          height={dimensions.height}
          x={viewport.x}
          y={viewport.y}
          scaleX={viewport.scale}
          scaleY={viewport.scale}
          onWheel={handleWheel}
          onMouseDown={handleStageMouseDown}
          onMouseMove={handleStageMouseMove}
          onMouseUp={handleStageMouseUp}
          onMouseLeave={handleStageMouseUp}
          style={{ cursor: isPanning ? 'grabbing' : 'default' }}
        >
          {/* Background Layer with Grid */}
          <Layer>
            <Rect
              x={-viewport.x / viewport.scale - 5000}
              y={-viewport.y / viewport.scale - 5000}
              width={10000}
              height={10000}
              fill="#FAFAFA"
            />
          </Layer>

          {/* Content Layer */}
          <Layer>
            {/* Edges */}
            {renderEdges()}

            {/* Nodes */}
            {nodes.map((node) => (
              <KnowledgeNode
                key={node.id}
                node={node}
                isSelected={selectedNodeId === node.id}
                onSelect={() => setSelectedNodeId(node.id)}
                onDragStart={handleNodeDragStart(node.id)}
                onDragEnd={handleNodeDragEnd(node.id)}
              />
            ))}

            {/* Drag Preview for AI Insight */}
            {dragPreview && (
              <Group
                x={dragPreview.x - 140}
                y={dragPreview.y - 100}
                opacity={0.7}
                listening={false}
              >
                <Rect
                  width={280}
                  height={200}
                  fill="white"
                  cornerRadius={12}
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dash={[6, 4]}
                  shadowColor="black"
                  shadowBlur={8}
                  shadowOpacity={0.15}
                  shadowOffsetY={4}
                />
                <Rect
                  y={0}
                  width={280}
                  height={4}
                  fill="#3B82F6"
                  cornerRadius={[12, 12, 0, 0]}
                />
                <Text
                  x={16}
                  y={16}
                  width={280 - 32}
                  text="AI Insight"
                  fontSize={12}
                  fontStyle="bold"
                  fill="#1F2937"
                />
                <Text
                  x={16}
                  y={40}
                  width={280 - 32}
                  height={130}
                  text={dragPreview.content}
                  fontSize={12}
                  fill="#6B7280"
                  wrap="word"
                  ellipsis
                />
              </Group>
            )}
          </Layer>
        </Stage>
      </Box>
    </Box>
  );
}


'use client';

/**
 * High-performance Konva.js-powered Canvas
 * Replaces DOM-based rendering with HTML5 Canvas for better performance
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { Stage, Layer, Group, Rect, Text, Line, Arrow } from 'react-konva';
import Konva from 'konva';
import { Box, Typography, Menu, MenuItem } from '@mui/material';
import { Layout, ArrowUp } from 'lucide-react';
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
  viewType: 'free' | 'thinking';
  sectionId?: string;
  messageIds?: string[];  // Linked chat message IDs
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
  currentView: 'free' | 'thinking';
  onNodesChange: (nodes: CanvasNode[]) => void;
  onEdgesChange: (edges: CanvasEdge[]) => void;
  onViewportChange: (viewport: Viewport) => void;
  onNodeAdd?: (node: Partial<CanvasNode>) => void;
  highlightedNodeId?: string | null;  // Node to highlight (for navigation from chat)
  onNodeClick?: (node: CanvasNode) => void;  // Callback when node is clicked
}

// Node style configuration based on type
const getNodeStyle = (type: string) => {
  const styles: Record<string, { 
    borderColor: string; 
    borderStyle: 'solid' | 'dashed'; 
    bgColor: string; 
    icon: string;
    topBarColor: string;
  }> = {
    knowledge: {
      borderColor: '#E5E7EB',
      borderStyle: 'solid',
      bgColor: '#FFFFFF',
      icon: '📄',
      topBarColor: '#E5E7EB',
    },
    insight: {
      borderColor: '#3B82F6',
      borderStyle: 'solid',
      bgColor: '#EFF6FF',
      icon: '💡',
      topBarColor: '#3B82F6',
    },
    manual: {
      borderColor: '#E5E7EB',
      borderStyle: 'solid',
      bgColor: '#FFFFFF',
      icon: '✏️',
      topBarColor: '#9CA3AF',
    },
    question: {
      borderColor: '#3B82F6',
      borderStyle: 'dashed',
      bgColor: '#EFF6FF',
      icon: '🤔',
      topBarColor: '#3B82F6',
    },
    answer: {
      borderColor: '#10B981',
      borderStyle: 'dashed',
      bgColor: '#F0FDF4',
      icon: '💭',
      topBarColor: '#10B981',
    },
    conclusion: {
      borderColor: '#F59E0B',
      borderStyle: 'dashed',
      bgColor: '#FFFBEB',
      icon: '✨',
      topBarColor: '#F59E0B',
    },
  };
  
  // Default to knowledge style for backward compatibility
  return styles[type] || styles.knowledge;
};

// Knowledge Node Component
const KnowledgeNode = ({
  node,
  isSelected,
  isHighlighted,
  onSelect,
  onClick,
  onDragStart,
  onDragEnd,
  onContextMenu,
}: {
  node: CanvasNode;
  isSelected: boolean;
  isHighlighted?: boolean;
  onSelect: () => void;
  onClick?: () => void;
  onDragStart: () => void;
  onDragEnd: (e: Konva.KonvaEventObject<DragEvent>) => void;
  onContextMenu?: (e: Konva.KonvaEventObject<PointerEvent>) => void;
}) => {
  const width = node.width || 280;
  const height = node.height || 200;
  const style = getNodeStyle(node.type);
  
  // Highlight animation effect
  const highlightStrokeWidth = isHighlighted ? 3 : (isSelected ? 2 : 1);
  const highlightStrokeColor = isHighlighted ? '#3B82F6' : (isSelected ? style.borderColor : style.borderColor);

  return (
    <Group
      x={node.x}
      y={node.y}
      draggable
      onClick={() => {
        onSelect();
        onClick?.();
      }}
      onTap={() => {
        onSelect();
        onClick?.();
      }}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onContextMenu={onContextMenu}
    >
      {/* Border/Background */}
      <Rect
        width={width}
        height={height}
        fill={style.bgColor}
        cornerRadius={12}
        stroke={highlightStrokeColor}
        strokeWidth={highlightStrokeWidth}
        dash={style.borderStyle === 'dashed' ? [8, 4] : undefined}
        shadowColor={isHighlighted ? '#3B82F6' : 'black'}
        shadowBlur={isHighlighted ? 16 : (isSelected ? 12 : 8)}
        shadowOpacity={isHighlighted ? 0.3 : (isSelected ? 0.15 : 0.08)}
        shadowOffsetY={4}
      />

      {/* Top Color Bar */}
      <Rect
        y={0}
        width={width}
        height={4}
        fill={style.topBarColor}
        cornerRadius={[12, 12, 0, 0]}
      />

      {/* Type Icon (top-left) */}
      <Text
        x={12}
        y={12}
        text={style.icon}
        fontSize={16}
      />

      {/* Title (adjust for icon) */}
      <Text
        x={40}
        y={14}
        width={width - 56}
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
        y={48}
        width={width - 32}
        height={95}
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
  currentView,
  onNodesChange,
  onEdgesChange,
  onViewportChange,
  onNodeAdd,
  highlightedNodeId,
  onNodeClick,
}: KonvaCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isPanning, setIsPanning] = useState(false);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId?: string; sectionId?: string } | null>(null);
  const lastPosRef = useRef({ x: 0, y: 0 });
  const { 
    dragPreview, 
    setDragPreview, 
    dragContentRef, 
    promoteNode, 
    deleteSection,
    canvasSections,
    setCanvasSections,
    currentView: studioCurrentView 
  } = useStudio();

  // Filter nodes and sections by current view
  const visibleNodes = nodes.filter(node => node.viewType === currentView);
  const visibleSections = canvasSections.filter(section => section.viewType === currentView);

  // Update dimensions on resize
  useEffect(() => {
    if (!containerRef.current) return;

    // Set initial dimensions (ensure minimum 1x1 to avoid canvas errors)
    const initialWidth = containerRef.current.offsetWidth || 800;
    const initialHeight = containerRef.current.offsetHeight || 600;
    setDimensions({
      width: Math.max(1, initialWidth),
      height: Math.max(1, initialHeight),
    });

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect) {
          // Ensure minimum 1x1 dimensions to prevent drawImage errors
          const width = Math.max(1, entry.contentRect.width);
          const height = Math.max(1, entry.contentRect.height);
          setDimensions({ width, height });
        }
      }
    });

    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
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

  // Draw connections (only for visible nodes)
  const renderEdges = () => {
    return edges.map((edge, index) => {
      const source = visibleNodes.find((n) => n.id === edge.source);
      const target = visibleNodes.find((n) => n.id === edge.target);
      
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
    <Box sx={{ flexGrow: 1, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
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
          zIndex: 100,
          flexShrink: 0
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Layout size={14} className="text-gray-500" />
          <Typography variant="subtitle2" fontWeight="600">
            Canvas
          </Typography>
        </Box>
        <Typography variant="caption" color="text.disabled">
          Auto-saved • {visibleNodes.length} nodes ({currentView === 'free' ? '自由画布' : '思考路径'})
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
        {/* Context Menu */}
        {contextMenu && (
          <Menu
            open={Boolean(contextMenu)}
            onClose={() => setContextMenu(null)}
            anchorReference="anchorPosition"
            anchorPosition={
              contextMenu ? { top: contextMenu.y, left: contextMenu.x } : undefined
            }
          >
            {contextMenu.nodeId && studioCurrentView === 'thinking' && (
              <MenuItem
                onClick={() => {
                  if (contextMenu.nodeId) {
                    promoteNode(contextMenu.nodeId);
                  }
                  setContextMenu(null);
                }}
                sx={{ fontSize: 14 }}
              >
                <ArrowUp size={14} style={{ marginRight: 8 }} />
                提升到自由画布
              </MenuItem>
            )}
            {contextMenu.nodeId && (
              <MenuItem
                onClick={() => {
                  if (contextMenu.nodeId) {
                    onNodesChange(nodes.filter(n => n.id !== contextMenu.nodeId));
                  }
                  setContextMenu(null);
                }}
                sx={{ fontSize: 14, color: 'error.main' }}
              >
                删除节点
              </MenuItem>
            )}
            {contextMenu.sectionId && (
              <>
                <MenuItem
                  onClick={() => {
                    if (contextMenu.sectionId) {
                      // Toggle collapse
                      setCanvasSections(prev =>
                        prev.map(s =>
                          s.id === contextMenu.sectionId
                            ? { ...s, isCollapsed: !s.isCollapsed }
                            : s
                        )
                      );
                    }
                    setContextMenu(null);
                  }}
                  sx={{ fontSize: 14 }}
                >
                  折叠/展开Section
                </MenuItem>
                <MenuItem
                  onClick={() => {
                    if (contextMenu.sectionId) {
                      deleteSection(contextMenu.sectionId);
                    }
                    setContextMenu(null);
                  }}
                  sx={{ fontSize: 14, color: 'error.main' }}
                >
                  删除Section
                </MenuItem>
              </>
            )}
          </Menu>
        )}
        
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
            {/* Sections (render before nodes for proper layering) */}
            {visibleSections.map((section) => {
              const sectionNodes = visibleNodes.filter(n => n.sectionId === section.id);
              
              // Calculate section bounds
              if (sectionNodes.length === 0) return null;
              
              let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
              sectionNodes.forEach(node => {
                minX = Math.min(minX, node.x);
                minY = Math.min(minY, node.y);
                maxX = Math.max(maxX, node.x + (node.width || 280));
                maxY = Math.max(maxY, node.y + (node.height || 200));
              });
              
              const headerHeight = 48;
              const padding = 16;
              const contentWidth = maxX - minX + padding * 2;
              const contentHeight = maxY - minY + padding * 2;
              const totalHeight = headerHeight + (section.isCollapsed ? 0 : contentHeight);

              return (
                <Group
                  key={section.id}
                  x={section.x || minX - padding}
                  y={section.y || minY - padding - headerHeight}
                  onContextMenu={(e) => {
                    e.evt.preventDefault();
                    setContextMenu({
                      x: e.evt.clientX,
                      y: e.evt.clientY,
                      sectionId: section.id,
                    });
                  }}
                >
                  {/* Section Background */}
                  <Rect
                    width={contentWidth}
                    height={totalHeight}
                    fill="#F3F4F6"
                    cornerRadius={12}
                    stroke="#E5E7EB"
                    strokeWidth={1}
                    shadowColor="black"
                    shadowBlur={8}
                    shadowOpacity={0.08}
                    shadowOffsetY={2}
                  />

                  {/* Header */}
                  <Rect
                    width={contentWidth}
                    height={headerHeight}
                    fill="#FFFFFF"
                    cornerRadius={[12, 12, 0, 0]}
                    onClick={() => {
                      setCanvasSections(prev =>
                        prev.map(s =>
                          s.id === section.id ? { ...s, isCollapsed: !s.isCollapsed } : s
                        )
                      );
                    }}
                  />

                  {/* Icon */}
                  <Text x={16} y={16} text="🌱" fontSize={18} />

                  {/* Title */}
                  <Text
                    x={48}
                    y={18}
                    width={contentWidth - 100}
                    text={section.title}
                    fontSize={14}
                    fontStyle="bold"
                    fill="#1F2937"
                    ellipsis
                  />

                  {/* Collapse icon */}
                  <Text
                    x={contentWidth - 40}
                    y={18}
                    text={section.isCollapsed ? '▶' : '▼'}
                    fontSize={12}
                    fill="#6B7280"
                  />
                </Group>
              );
            })}

            {/* Edges */}
            {renderEdges()}

            {/* Nodes (filtered by current view, excluding ones in sections when collapsed) */}
            {visibleNodes.map((node) => {
              // Skip nodes in collapsed sections
              if (node.sectionId) {
                const section = visibleSections.find(s => s.id === node.sectionId);
                if (section?.isCollapsed) return null;
              }
              
              return (
              <KnowledgeNode
                key={node.id}
                node={node}
                isSelected={selectedNodeId === node.id}
                isHighlighted={highlightedNodeId === node.id}
                onSelect={() => setSelectedNodeId(node.id)}
                onClick={() => onNodeClick?.(node)}
                onDragStart={handleNodeDragStart(node.id)}
                onDragEnd={handleNodeDragEnd(node.id)}
                onContextMenu={(e) => {
                  e.evt.preventDefault();
                  setContextMenu({
                    x: e.evt.clientX,
                    y: e.evt.clientY,
                    nodeId: node.id,
                  });
                }}
              />
            );
            })}

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


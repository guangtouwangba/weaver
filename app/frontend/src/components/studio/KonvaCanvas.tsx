'use client';

/**
 * High-performance Konva.js-powered Canvas
 * Replaces DOM-based rendering with HTML5 Canvas for better performance
 */

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { Stage, Layer, Group, Rect, Text, Line, Circle, Image, Path } from 'react-konva';


const URLImage = ({ src, x, y, width, height, opacity, cornerRadius }: any) => {
  const [image, setImage] = useState<HTMLImageElement | undefined>(undefined);

  useEffect(() => {
    if (!src) {
      console.log('[DEBUG] URLImage no src');
      return;
    }
    console.log('[DEBUG] URLImage loading:', src);
    const img = new window.Image();
    img.src = src;
    img.crossOrigin = 'Anonymous';
    img.onload = () => {
      console.log('[DEBUG] URLImage loaded:', src);
      setImage(img);
    };
    img.onerror = (e) => {
      console.error('[DEBUG] URLImage error:', src, e);
    };
  }, [src]);

  return image ? <Image x={x} y={y} width={width} height={height} image={image} opacity={opacity} cornerRadius={cornerRadius} /> : null;
};

import Konva from 'konva';
import { Menu, MenuItem, TextField } from '@/components/ui/composites';
import { Chip, IconButton, Button, Spinner, Stack, Surface, Text as UiText } from '@/components/ui/primitives';
import { colors } from '@/components/ui/tokens';
import {
  ArrowUpwardIcon, CloseIcon, CheckIcon, LayersIcon, AutoAwesomeIcon, SearchIcon,
  EditIcon, DeleteIcon,
} from '@/components/ui/icons';
import { useStudio } from '@/contexts/StudioContext';
import { useCanvasActions } from '@/hooks/useCanvasActions';
import { ToolMode } from './CanvasToolbar';
import InspirationDock from './InspirationDock';
import CanvasContextMenu from './CanvasContextMenu';
import GenerationOutputsOverlay from './GenerationOutputsOverlay';
import { CanvasNode, CanvasEdge } from '@/lib/api';
import {
  getAnchorPoint,
  resolveAnchor,
  getStraightPath,
  getBezierPath,
  getOrthogonalPath,
  getArrowPoints,
  getAllAnchorPoints,
  AnchorDirection,
} from '@/lib/connectionUtils';
import { useSpatialIndex, SpatialItem } from '@/hooks/useSpatialIndex';
import { useViewportCulling } from '@/hooks/useViewportCulling';
import GridBackground from './canvas/GridBackground';
import SynthesisModeMenu, { SynthesisMode } from './canvas/SynthesisModeMenu';
import NodeEditor from './canvas/NodeEditor';
import useOutputWebSocket from '@/hooks/useOutputWebSocket';

interface Viewport {
  x: number;
  y: number;
  scale: number;
}

interface KonvaCanvasProps {
  nodes?: CanvasNode[];
  edges?: CanvasEdge[];
  viewport?: Viewport;
  currentView?: 'free' | 'thinking';
  onNodesChange?: (nodes: CanvasNode[]) => void;
  onEdgesChange?: (edges: CanvasEdge[]) => void;
  onViewportChange?: (viewport: Viewport) => void;
  onNodeAdd?: (node: Partial<CanvasNode>) => void;
  highlightedNodeId?: string | null;  // Node to highlight (for navigation from chat)
  onNodeClick?: (node: CanvasNode) => void;  // Callback when node is clicked
  onNodeDoubleClick?: (node: CanvasNode) => void;  // Phase 1: Callback for drill-down (opening source)
  onOpenSource?: (sourceId: string, pageNumber?: number) => void;  // Phase 1: Navigate to source document
  toolMode?: ToolMode; // New prop
  onToolChange?: (tool: ToolMode) => void; // Callback to change tool mode
  onOpenImport?: () => void; // For Context Menu Import
  onSelectionChange?: (count: number) => void; // Callback when selection changes
}

// Node style configuration based on type
const getNodeStyle = (type: string, subType?: string, fileType?: string, isDraft?: boolean, branchType?: string) => {
  const styles: Record<string, {
    borderColor: string;
    borderStyle: 'solid' | 'dashed';
    bgColor: string;
    icon: string;
    topBarColor: string;
  }> = {
    // === Source Node Types (The Portal) ===
    source_pdf: {
      borderColor: '#DC2626',  // Red - PDF documents
      borderStyle: 'solid',
      bgColor: '#FEF2F2',      // Light red
      icon: '📕',              // Book/PDF icon
      topBarColor: '#DC2626',
    },
    source_markdown: {
      borderColor: '#2563EB',  // Blue - Markdown
      borderStyle: 'solid',
      bgColor: '#EFF6FF',      // Light blue
      icon: '📝',              // Markdown/Note icon
      topBarColor: '#2563EB',
    },
    source_web: {
      borderColor: '#059669',  // Teal - Web pages
      borderStyle: 'solid',
      bgColor: '#ECFDF5',      // Light teal
      icon: '🌐',              // Globe icon
      topBarColor: '#059669',
    },
    source_text: {
      borderColor: '#6B7280',  // Gray - Plain text
      borderStyle: 'solid',
      bgColor: '#F9FAFB',      // Light gray
      icon: '📄',              // Document icon
      topBarColor: '#6B7280',
    },
    // === Thinking Path Node Types (User Conversation Visualization) ===
    question: {
      borderColor: '#3B82F6',  // Blue
      borderStyle: 'dashed',
      bgColor: '#EFF6FF',      // Light blue
      icon: '❓',              // Question mark
      topBarColor: '#3B82F6',
    },
    answer: {
      borderColor: '#10B981',  // Green
      borderStyle: 'solid',
      bgColor: '#F0FDF4',      // Light green
      icon: '💬',              // Chat bubble
      topBarColor: '#10B981',
    },
    insight: {
      borderColor: '#F59E0B',  // Yellow/Gold
      borderStyle: 'solid',
      bgColor: '#FFFBEB',      // Light yellow
      icon: '💡',              // Lightbulb
      topBarColor: '#F59E0B',
    },
    // === Thinking Graph Node Types (Dynamic Mind Map) ===
    thinking_step: {
      borderColor: '#3B82F6',  // Blue for finalized
      borderStyle: 'solid',
      bgColor: '#EFF6FF',      // Light blue
      icon: '🧠',              // Brain icon
      topBarColor: '#3B82F6',
    },
    thinking_step_draft: {
      borderColor: '#8B5CF6',  // Purple for draft
      borderStyle: 'dashed',
      bgColor: '#F5F3FF',      // Light purple
      icon: '⏳',              // Hourglass for pending
      topBarColor: '#8B5CF6',
    },
    thinking_branch: {
      borderColor: '#F59E0B',  // Yellow/Gold for branches
      borderStyle: 'solid',
      bgColor: '#FFFBEB',      // Light yellow
      icon: '🔀',              // Branch icon
      topBarColor: '#F59E0B',
    },
    thinking_branch_question: {
      borderColor: '#3B82F6',  // Blue for question branches
      borderStyle: 'dashed',
      bgColor: '#EFF6FF',      // Light blue
      icon: '❓',              // Question mark
      topBarColor: '#3B82F6',
    },
    thinking_branch_alternative: {
      borderColor: '#10B981',  // Green for alternative branches
      borderStyle: 'solid',
      bgColor: '#F0FDF4',      // Light green
      icon: '🔄',              // Alternative icon
      topBarColor: '#10B981',
    },
    thinking_branch_counterargument: {
      borderColor: '#EF4444',  // Red for counterargument branches
      borderStyle: 'solid',
      bgColor: '#FEF2F2',      // Light red
      icon: '⚡',              // Counterargument icon
      topBarColor: '#EF4444',
    },
    // === Generated Output Node Types ===
    summary_output: {
      borderColor: '#8B5CF6',  // Purple for AI outputs
      borderStyle: 'solid',
      bgColor: '#FAF5FF',      // Light purple
      icon: '⚡',              // Zap icon for summary
      topBarColor: '#8B5CF6',
    },
    mindmap_output: {
      borderColor: '#10B981',  // Green for mindmap
      borderStyle: 'solid',
      bgColor: '#ECFDF5',      // Light green
      icon: '🔀',              // Network icon for mindmap
      topBarColor: '#10B981',
    },
    // === Other Node Types ===
    knowledge: {
      borderColor: '#E5E7EB',
      borderStyle: 'solid',
      bgColor: '#FFFFFF',
      icon: '📄',
      topBarColor: '#E5E7EB',
    },
    manual: {
      borderColor: '#E5E7EB',
      borderStyle: 'solid',
      bgColor: '#FFFFFF',
      icon: '✏️',
      topBarColor: '#9CA3AF',
    },
    conclusion: {
      borderColor: '#8B5CF6',  // Purple
      borderStyle: 'solid',
      bgColor: '#F5F3FF',      // Light purple
      icon: '✨',
      topBarColor: '#8B5CF6',
    },
    // === Inspiration Dock Generated Types ===
    podcast: {
      borderColor: '#8B5CF6',  // Purple
      borderStyle: 'solid',
      bgColor: '#F5F3FF',      // Light purple
      icon: '🎙️',
      topBarColor: '#8B5CF6',
    },
    quiz: {
      borderColor: '#F97316',  // Orange
      borderStyle: 'solid',
      bgColor: '#FFF7ED',      // Light orange
      icon: '❓',
      topBarColor: '#F97316',
    },
    timeline: {
      borderColor: '#EC4899',  // Pink
      borderStyle: 'solid',
      bgColor: '#FDF2F8',      // Light pink
      icon: '📅',
      topBarColor: '#EC4899',
    },
    compare: {
      borderColor: '#10B981',  // Green
      borderStyle: 'solid',
      bgColor: '#ECFDF5',      // Light green
      icon: '⚖️',
      topBarColor: '#10B981',
    },
    // === Sticky Note ===
    sticky: {
      borderColor: '#FCD34D', // Amber 300
      borderStyle: 'solid',
      bgColor: '#FEF3C7', // Amber 100
      icon: '📝',
      topBarColor: '#FCD34D',
    }
  };

  // Handle source nodes with specific file types
  if (subType === 'source' && fileType) {
    const sourceKey = `source_${fileType}`;
    if (styles[sourceKey]) {
      return styles[sourceKey];
    }
    // Fallback for unknown source types
    return styles.source_text;
  }

  // Handle thinking_step nodes with draft status
  if (type === 'thinking_step') {
    if (isDraft) {
      return styles.thinking_step_draft;
    }
    return styles.thinking_step;
  }

  // Handle thinking_branch nodes with branch type
  if (type === 'thinking_branch') {
    if (branchType === 'question') {
      return styles.thinking_branch_question;
    }
    if (branchType === 'alternative') {
      return styles.thinking_branch_alternative;
    }
    if (branchType === 'counterargument') {
      return styles.thinking_branch_counterargument;
    }
    return styles.thinking_branch;
  }

  // Default to knowledge style for backward compatibility
  return styles[type] || styles.knowledge;
};

// --- PDF Icon Paths ---
const PDF_ICON_BODY = "M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z";
const PDF_ICON_FOLD = "M14 2V8H20";

// --- Source Preview Card (Canvas Implementation of the UI) ---
const SourcePreviewCard = ({
  node,
  width,
  height,
  isSelected,
  isHighlighted,
  isActiveThinking,
}: {
  node: CanvasNode;
  width: number;
  height: number;
  isSelected: boolean;
  isHighlighted?: boolean;
  isActiveThinking?: boolean;
}) => {
  const thumbUrl = node.fileMetadata?.thumbnailUrl;
  const strokeColor = isActiveThinking ? '#8B5CF6' : (isHighlighted ? '#3B82F6' : (isSelected ? '#6366F1' : '#E5E7EB'));
  const strokeWidth = isSelected || isHighlighted ? 2 : 1;
  const shadowBlur = isSelected ? 12 : 4;
  const shadowOpacity = isSelected ? 0.15 : 0.05;

  // Enforce minimum height for proper layout of "Beautiful Card"
  const displayHeight = Math.max(height, 320);

  return (
    <Group>
      {/* 1. Main Card Container */}
      <Rect
        width={width}
        height={displayHeight}
        fill="white"
        cornerRadius={12}
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        shadowColor="black"
        shadowBlur={shadowBlur}
        shadowOpacity={shadowOpacity}
        shadowOffsetY={4}
      />

      {/* 2. Header (Top 40px) */}
      <Group x={12} y={12}>
        <Group scaleX={0.7} scaleY={0.7}>
          <Path data={PDF_ICON_BODY} fill="#EF4444" />
          <Path data={PDF_ICON_FOLD} fill="#B91C1C" fillOpacity={0.5} />
        </Group>
        <Text
          x={24}
          y={2}
          text="PDF Document"
          fontSize={12}
          fontStyle="bold"
          fill="#6B7280"
          fontFamily="Inter, sans-serif"
        />
      </Group>

      {/* Header Separator */}
      <Line points={[0, 40, width, 40]} stroke="#F3F4F6" strokeWidth={1} />

      {/* 3. Body (Preview Area) */}
      <Rect
        x={1}
        y={40}
        width={width - 2}
        height={displayHeight - 90}
        fill="#FFF7ED" // Orange-50 equivalent
        opacity={0.5}
      />

      {/* Thumbnail Logic */}
      {thumbUrl ? (
        <Group x={(width - 120) / 2} y={55}>
          {/* Shadow for Paper */}
          <Rect
            x={4}
            y={4}
            width={120}
            height={150} // Aspect ratio approx
            fill="black"
            opacity={0.1}
            cornerRadius={2}
            blurRadius={4}
          />
          {/* White Paper Bg */}
          <Rect
            width={120}
            height={150}
            fill="white"
            cornerRadius={2}
          />
          {/* Image */}
          <URLImage
            src={thumbUrl}
            width={120}
            height={150}
            cornerRadius={2}
          />
        </Group>
      ) : (
        /* Placeholder */
        <Group x={(width - 100) / 2} y={60}>
          <Rect width={100} height={130} fill="white" stroke="#E5E7EB" dash={[4, 4]} cornerRadius={4} />
          <Text x={10} y={60} text="No Preview" fontSize={12} fill="#9CA3AF" />
        </Group>
      )}

      {/* 4. Footer */}
      <Line points={[0, displayHeight - 50, width, displayHeight - 50]} stroke="#F3F4F6" strokeWidth={1} />

      <Group x={12} y={displayHeight - 38}>
        {/* Icon Box */}
        <Rect width={28} height={28} fill="#FEF2F2" cornerRadius={6} />
        <Group x={6} y={6} scaleX={0.7} scaleY={0.7}>
          <Path data={PDF_ICON_BODY} fill="#DC2626" />
        </Group>

        {/* Text Info */}
        <Group x={36} y={-2}>
          <Text
            text={node.title}
            width={width - 60}
            ellipsis={true}
            fontSize={13}
            fontStyle="bold"
            fill="#111827"
            height={20}
          />
          <Text
            y={18}
            text={node.fileMetadata?.pageCount ? `${node.fileMetadata.pageCount} pages` : 'Unknown size'}
            fontSize={10}
            fill="#6B7280"
          />
        </Group>
      </Group>
    </Group>
  );
};

// Knowledge Node Component
const KnowledgeNode = ({
  node,
  isSelected,
  isHighlighted,
  isMergeTarget,
  isHovered,
  isConnecting,
  isConnectTarget,
  isActiveThinking,
  onSelect,
  onClick,
  onDoubleClick,
  onLinkBack,
  onDragStart,
  onDragMove,
  onDragEnd,
  onContextMenu,
  onConnectionStart,
  onMouseEnter,
  onMouseLeave,
  isDraggable = true,
  isSynthesisSource = false,
}: {
  node: CanvasNode;
  isSelected: boolean;
  isHighlighted?: boolean;
  isMergeTarget?: boolean;            // Synthesis: Show merge target highlight
  isHovered?: boolean;              // Phase 2: Show connection handles
  isConnecting?: boolean;           // Phase 2: Currently dragging a connection from this node
  isConnectTarget?: boolean;        // Phase 2: Currently a potential connection target
  isActiveThinking?: boolean;       // Thinking Graph: Is this the active thinking node (fork point)
  isSynthesisSource?: boolean;      // Synthesis: This node is being used as input for synthesis
  isDraggable?: boolean;            // Controls whether the node can be dragged
  onSelect: (e: Konva.KonvaEventObject<MouseEvent | TouchEvent>) => void;
  onClick?: () => void;
  onDoubleClick?: () => void;       // Phase 1: Drill-down
  onLinkBack?: () => void;          // Phase 1: Navigate to source
  onDragStart: (e: Konva.KonvaEventObject<DragEvent>) => void;
  onDragMove?: (e: Konva.KonvaEventObject<DragEvent>) => void;
  onDragEnd: (e: Konva.KonvaEventObject<DragEvent>) => void;
  onContextMenu?: (e: Konva.KonvaEventObject<PointerEvent>) => void;
  onConnectionStart?: () => void;   // Phase 2: Start dragging connection
  onMouseEnter?: () => void;        // Phase 2: For hover state
  onMouseLeave?: () => void;        // Phase 2: For hover state
}) => {


  const width = node.width || 280;
  const height = node.height || 200;
  const style = getNodeStyle(node.type, node.subType, node.fileMetadata?.fileType, node.isDraft, node.branchType);

  // Thinking Graph: Check if this is a thinking step or branch node
  const isThinkingStep = node.type === 'thinking_step';
  const isThinkingBranch = node.type === 'thinking_branch';

  // Highlight animation effect
  const highlightStrokeWidth = isActiveThinking ? 4 : (isMergeTarget ? 3 : (isHighlighted ? 3 : (isSelected ? 2 : 1)));
  const highlightStrokeColor = isActiveThinking ? '#8B5CF6' : (isMergeTarget ? '#8B5CF6' : (isHighlighted ? '#3B82F6' : (isSelected ? style.borderColor : style.borderColor)));
  const highlightShadowColor = isMergeTarget ? '#8B5CF6' : (isActiveThinking ? '#8B5CF6' : (isHighlighted ? '#3B82F6' : 'black'));
  const highlightShadowBlur = isMergeTarget ? 24 : (isActiveThinking ? 20 : (isHighlighted ? 16 : (isSelected ? 12 : 8)));

  // Check if this is a source node (for visual distinction)
  const isSourceNode = node.subType === 'source';
  // Check if this node has a source reference (for link-back feature)
  const hasSourceRef = !isSourceNode && node.sourceId;

  // Calculate opacity: reduce if this node is being used as synthesis input
  const nodeOpacity = isSynthesisSource ? 0.4 : 1;

  return (
    <Group
      id={`node-${node.id}`} // Assign ID for finding during bulk drag
      x={node.x}
      y={node.y}
      opacity={nodeOpacity}
      draggable={isDraggable}
      onClick={(e) => {
        onSelect(e);
        onClick?.();
      }}
      onTap={(e) => {
        onSelect(e);
        onClick?.();
      }}
      onDblClick={() => onDoubleClick?.()}
      onDblTap={() => onDoubleClick?.()}
      onDragStart={onDragStart}
      onDragMove={onDragMove}
      onDragEnd={onDragEnd}
      onContextMenu={onContextMenu}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* Use SourcePreviewCard for PDF Source Nodes */}
      {isSourceNode ? (
        <SourcePreviewCard
          node={node}
          width={width}
          height={height}
          isSelected={isSelected}
          isHighlighted={isHighlighted}
          isActiveThinking={isActiveThinking}
        />
      ) : (
        <>
          {/* Standard Node Rendering */}

          {/* Border/Background */}
          <Rect
            width={width}
            height={height}
            fill={style.bgColor}
            cornerRadius={12}
            stroke={highlightStrokeColor}
            strokeWidth={highlightStrokeWidth}
            dash={style.borderStyle === 'dashed' ? [8, 4] : undefined}
            shadowColor={isActiveThinking ? '#8B5CF6' : (isHighlighted ? '#3B82F6' : 'black')}
            shadowBlur={isActiveThinking ? 20 : (isHighlighted ? 16 : (isSelected ? 12 : 8))}
            shadowOpacity={isActiveThinking ? 0.4 : (isHighlighted ? 0.3 : (isSelected ? 0.15 : 0.08))}
            shadowOffsetY={4}
          />

          {/* Top Color Bar - thicker for source nodes */}
          <Rect
            y={0}
            width={width}
            height={isSourceNode ? 6 : 4}
            fill={style.topBarColor}
            cornerRadius={[12, 12, 0, 0]}
          />

          {/* Type Icon (top-left) */}
          <Text
            x={12}
            y={isSourceNode ? 14 : 12}
            text={style.icon}
            fontSize={isSourceNode ? 18 : 16}
          />

          {/* Title (adjust for icon) */}
          <Text
            x={40}
            y={isSourceNode ? 16 : 14}
            width={width - (hasSourceRef ? 80 : 56) - (isThinkingStep ? 60 : 0)}
            text={node.title}
            fontSize={isSourceNode ? 15 : 16}
            fontStyle="bold"
            fill="#1F2937"
            wrap="word"
            ellipsis={true}
          />

          {/* Thinking Graph: Step Index Badge */}
          {isThinkingStep && node.thinkingStepIndex && (
            <>
              <Rect
                x={width - 45}
                y={12}
                width={36}
                height={20}
                fill={node.isDraft ? '#8B5CF6' : '#3B82F6'}
                cornerRadius={10}
              />
              <Text
                x={width - 42}
                y={15}
                text={`#${node.thinkingStepIndex}`}
                fontSize={11}
                fontStyle="bold"
                fill="#FFFFFF"
              />
            </>
          )}

          {/* Thinking Graph: Active Context Badge */}
          {isActiveThinking && (
            <>
              <Rect
                x={width - 52}
                y={35}
                width={44}
                height={16}
                fill="#F3E8FF"
                cornerRadius={8}
              />
              <Text
                x={width - 48}
                y={37}
                text="Active"
                fontSize={9}
                fontStyle="bold"
                fill="#7C3AED"
              />
            </>
          )}

          {/* Thinking Graph: Draft Badge */}
          {node.isDraft && (
            <>
              <Rect
                x={width - (isActiveThinking ? 100 : 52)}
                y={35}
                width={40}
                height={16}
                fill="#FEF3C7"
                cornerRadius={8}
              />
              <Text
                x={width - (isActiveThinking ? 96 : 48)}
                y={37}
                text="Draft"
                fontSize={9}
                fontStyle="bold"
                fill="#D97706"
              />
            </>
          )}

          {/* Source Node: File metadata badge */}
          {isSourceNode && node.fileMetadata && (
            <>
              <Rect
                x={width - 60}
                y={14}
                width={48}
                height={18}
                fill={style.topBarColor}
                cornerRadius={4}
                opacity={0.2}
              />
              <Text
                x={width - 56}
                y={17}
                text={node.fileMetadata.fileType?.toUpperCase() || 'FILE'}
                fontSize={10}
                fontStyle="bold"
                fill={style.topBarColor}
              />
            </>
          )}

          {/* Link-Back Icon (top-right) for nodes with source reference */}
          {hasSourceRef && (
            <Group
              x={width - 32}
              y={12}
              onClick={(e) => {
                e.cancelBubble = true;
                onLinkBack?.();
              }}
              onTap={(e) => {
                e.cancelBubble = true;
                onLinkBack?.();
              }}
            >
              <Rect
                width={24}
                height={24}
                fill="#E0E7FF"
                cornerRadius={6}
              />
              <Text
                x={4}
                y={4}
                text="🔗"
                fontSize={14}
              />
            </Group>
          )}

          {/* Content */}
          <Text
            x={16}
            y={isSourceNode ? 50 : 48}
            width={width - 32}
            height={isSourceNode ? 85 : 95}
            text={node.content}
            fontSize={14}
            fill="#6B7280"
            wrap="word"
            ellipsis={true}
            visible={!(isSourceNode && node.fileMetadata?.thumbnailUrl)}
          />
          {isSourceNode && node.fileMetadata?.thumbnailUrl && (
            <URLImage
              src={node.fileMetadata.thumbnailUrl}
              x={16}
              y={50}
              width={width - 32}
              height={isSourceNode ? 85 : 95}
              cornerRadius={8}
            />
          )}

          {/* Source Node: Page count info */}
          {isSourceNode && node.fileMetadata?.pageCount && (
            <Text
              x={16}
              y={height - 50}
              text={`${node.fileMetadata.pageCount} pages`}
              fontSize={11}
              fill="#9CA3AF"
            />
          )}

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

          {/* Source info (for non-source nodes that reference a source) */}
          {hasSourceRef && (
            <Text
              x={16}
              y={height - 25}
              width={width - 32}
              text={`📄 ${node.sourceId!.substring(0, 8)}${node.sourcePage ? ` • p.${node.sourcePage}` : ''}`}
              fontSize={11}
              fill="#9CA3AF"
            />
          )}

          {/* Double-click hint for source nodes */}
          {isSourceNode && isSelected && (
            <Text
              x={16}
              y={height - 18}
              text="Double-click to open"
              fontSize={10}
              fill="#6B7280"
              fontStyle="italic"
            />
          )}

          {/* Phase 2: Connection Handle (Right side - output) */}
          {(isHovered || isSelected || isConnecting) && (
            <Group
              x={width}
              y={height / 2}
              onMouseDown={(e) => {
                e.cancelBubble = true;
                onConnectionStart?.();
              }}
              onTouchStart={(e) => {
                e.cancelBubble = true;
                onConnectionStart?.();
              }}
            >
              <Rect
                x={-8}
                y={-8}
                width={16}
                height={16}
                fill={isConnecting ? '#3B82F6' : '#FFFFFF'}
                stroke="#3B82F6"
                strokeWidth={2}
                cornerRadius={8}
              />
            </Group>
          )}

          {/* Phase 2: Connection Target Handle (Left side - input) */}
          {isConnectTarget && (
            <Group x={0} y={height / 2}>
              <Rect
                x={-8}
                y={-8}
                width={16}
                height={16}
                fill="#10B981"
                stroke="#059669"
                strokeWidth={2}
                cornerRadius={8}
              />
            </Group>
          )}
        </>
      )}
    </Group>
  );
};

export default function KonvaCanvas({
  nodes: propNodes,
  edges: propEdges,
  viewport: propViewport,
  currentView: propCurrentView,
  onNodesChange: propOnNodesChange,
  onEdgesChange: propOnEdgesChange,
  onViewportChange: propOnViewportChange,
  onNodeAdd,
  highlightedNodeId,
  onNodeClick,
  onNodeDoubleClick,
  onOpenSource,
  toolMode = 'select', // Default to select
  onToolChange,
  onOpenImport,
  onSelectionChange,
}: KonvaCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const lastWheelTimeRef = useRef(0); // For wheel event throttling
  const WHEEL_THROTTLE_MS = 16; // ~60fps throttle for smooth scrolling
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Selection State
  const [selectedNodeIds, setSelectedNodeIds] = useState<Set<string>>(new Set());

  // Notify parent when selection changes
  useEffect(() => {
    onSelectionChange?.(selectedNodeIds.size);
  }, [selectedNodeIds, onSelectionChange]);

  const [selectionRect, setSelectionRect] = useState<{
    startX: number; startY: number; x: number; y: number; width: number; height: number
  } | null>(null);

  const [isPanning, setIsPanning] = useState(false);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId?: string; sectionId?: string } | null>(null);

  // Phase 2: Manual Connection State
  const [connectingFromNodeId, setConnectingFromNodeId] = useState<string | null>(null);
  const [connectingLineEnd, setConnectingLineEnd] = useState<{ x: number; y: number } | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [edgeLabelDialog, setEdgeLabelDialog] = useState<{
    edge: CanvasEdge;
    position: { x: number; y: number };
  } | null>(null);

  // P1: Edge Selection & Reconnection
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [reconnectingEdge, setReconnectingEdge] = useState<{
    edgeId: string;
    type: 'source' | 'target';
    x?: number;
    y?: number;
  } | null>(null);

  // Merge/Synthesis State
  const [mergeTargetNodeId, setMergeTargetNodeId] = useState<string | null>(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);
  const [pendingSynthesisResult, setPendingSynthesisResult] = useState<{
    id: string;
    title: string;
    content: string;
    recommendation?: string;
    keyRisk?: string;
    confidence?: 'high' | 'medium' | 'low';
    themes?: string[];
    sourceNodeIds?: string[];
    mode: 'connect' | 'inspire' | 'debate';
    position: { x: number; y: number };
  } | null>(null);

  // Node Editing State
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null);

  // Refs for Drag/Pan
  const lastPosRef = useRef({ x: 0, y: 0 });
  const draggedNodeRef = useRef<string | null>(null);
  const lastDragPosRef = useRef<{ x: number, y: number } | null>(null);

  const {
    dragPreview,
    setDragPreview,
    projectId, // Get projectId for WebSocket connection
    dragContentRef,
    promoteNode,
    deleteSection,
    addSection,
    canvasSections,
    setCanvasSections,
    currentView: studioCurrentView,
    activeThinkingId,
    setActiveThinkingId,
    setCrossBoundaryDragNode,
    documents, // Get documents for Inspiration Dock
    generationTasks, // Get generation tasks to check for completed outputs
    // Get canvas state from context as fallback
    canvasNodes: contextNodes,
    canvasEdges: contextEdges,
    canvasViewport: contextViewport,
    setCanvasNodes: contextSetNodes,
    setCanvasEdges: contextSetEdges,
    setCanvasViewport: contextSetViewport,
  } = useStudio();

  const {
    handleDeleteNode,
    handleSynthesizeNodes: synthesizeNodes,
    handleGenerateContent,
    handleGenerateContentConcurrent,
    getViewportCenterPosition,
    handleImportSource
  } = useCanvasActions({ onOpenImport });

  // Use props if provided, otherwise fall back to context values
  const nodes = propNodes ?? contextNodes ?? [];
  const edges = propEdges ?? contextEdges ?? [];
  const viewport = propViewport ?? contextViewport ?? { x: 0, y: 0, scale: 1 };
  const currentView = propCurrentView ?? studioCurrentView ?? 'free';
  const onNodesChange = propOnNodesChange ?? contextSetNodes ?? (() => { });
  const onEdgesChange = propOnEdgesChange ?? contextSetEdges ?? (() => { });
  const onViewportChange = propOnViewportChange ?? contextSetViewport ?? (() => { });

  // Filter nodes and sections by current view
  const visibleNodes = (nodes || []).filter(node => node.viewType === currentView);
  const visibleSections = (canvasSections || []).filter(section => section.viewType === currentView);

  // Spatial index for O(log N) box selection queries
  const spatialIndex = useSpatialIndex(visibleNodes);

  // Viewport culling - only render nodes within visible viewport (+ padding)
  const culledNodes = useViewportCulling(
    viewport,
    dimensions,
    spatialIndex,
    visibleNodes,
    300 // Extra padding to prevent pop-in during fast panning
  );

  // Check if there are any completed generation outputs on the canvas
  const hasCompletedOutputs = useMemo(() => {
    return Array.from(generationTasks.values()).some(task => task.status === 'complete');
  }, [generationTasks]);

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

  // Pan to highlighted node when navigating from chat
  useEffect(() => {
    if (!highlightedNodeId) return;

    const node = nodes.find(n => n.id === highlightedNodeId);
    if (!node) return;

    // Calculate center of the node
    const nodeWidth = node.width || 280;
    const nodeHeight = node.height || 200;
    const nodeCenterX = node.x + nodeWidth / 2;
    const nodeCenterY = node.y + nodeHeight / 2;

    // Calculate new viewport position to center the node on screen
    const scale = viewport.scale;
    const newX = dimensions.width / 2 - nodeCenterX * scale;
    const newY = dimensions.height / 2 - nodeCenterY * scale;

    // Update viewport to center on the node
    onViewportChange({
      scale,
      x: newX,
      y: newY,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightedNodeId]); // Only trigger when highlightedNodeId changes

  // Handle keyboard shortcuts (Space for panning, Delete for deletion, Cmd+A for Select All)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';

      if (isInput) return;

      // Space for Pan
      if (e.code === 'Space' && !e.repeat) {
        e.preventDefault();
        setIsSpacePressed(true);
      }

      // Delete / Backspace - Delete selected nodes or edges
      if (e.key === 'Delete' || e.key === 'Backspace') {
        let deleted = false;

        if (selectedNodeIds.size > 0) {
          e.preventDefault();
          // Delete each selected node via API (handles optimistic updates and rollback)
          selectedNodeIds.forEach(nodeId => {
            handleDeleteNode(nodeId).catch(err => {
              console.error('Failed to delete node:', err);
            });
          });
          setSelectedNodeIds(new Set());
          deleted = true;
        }

        if (selectedEdgeId) {
          e.preventDefault();
          if (onEdgesChange) {
            onEdgesChange(edges.filter(edge => edge.id !== selectedEdgeId));
          }
          setSelectedEdgeId(null);
          setEdgeLabelDialog(null);
          deleted = true;
        }
      }

      // Cmd+A / Ctrl+A for Select All
      if ((e.metaKey || e.ctrlKey) && e.key === 'a') {
        e.preventDefault();
        // Select all VISIBLE nodes
        const allVisibleIds = visibleNodes.map(n => n.id);
        setSelectedNodeIds(new Set(allVisibleIds));
      }

      // Tool Shortcuts (V for Select, H for Hand)
      if (e.key.toLowerCase() === 'v') {
        onToolChange?.('select');
      }
      if (e.key.toLowerCase() === 'h') {
        onToolChange?.('hand');
      }

      // Cmd+D / Ctrl+D for Duplicate
      if ((e.metaKey || e.ctrlKey) && e.key === 'd') {
        e.preventDefault();
        if (selectedNodeIds.size > 0) {
          const nodesToDuplicate = nodes.filter(n => selectedNodeIds.has(n.id));
          const newNodes = nodesToDuplicate.map(node => ({
            ...node,
            id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            x: node.x + 20,
            y: node.y + 20,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }));

          onNodesChange([...nodes, ...newNodes]);
          // Select the new nodes
          setSelectedNodeIds(new Set(newNodes.map(n => n.id)));
        }
      }

      // Nudge (Arrow Keys)
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        if (selectedNodeIds.size > 0) {
          e.preventDefault();
          const step = e.shiftKey ? 10 : 1;
          const dx = e.key === 'ArrowLeft' ? -step : (e.key === 'ArrowRight' ? step : 0);
          const dy = e.key === 'ArrowUp' ? -step : (e.key === 'ArrowDown' ? step : 0);

          const updatedNodes = nodes.map(n => {
            if (selectedNodeIds.has(n.id)) {
              return { ...n, x: n.x + dx, y: n.y + dy };
            }
            return n;
          });
          onNodesChange(updatedNodes);
        }
      }

      // Group (Cmd+G / Ctrl+G)
      if ((e.metaKey || e.ctrlKey) && e.key === 'g') {
        e.preventDefault();
        const selectedNodes = visibleNodes.filter(n => selectedNodeIds.has(n.id));

        if (selectedNodes.length >= 2) {
          let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
          selectedNodes.forEach(node => {
            minX = Math.min(minX, node.x);
            minY = Math.min(minY, node.y);
            maxX = Math.max(maxX, node.x + (node.width || 280));
            maxY = Math.max(maxY, node.y + (node.height || 200));
          });

          const padding = 24;
          const headerHeight = 48;
          const sectionId = `section-${crypto.randomUUID()}`;

          const newSection = {
            id: sectionId,
            title: `Group (${selectedNodes.length})`,
            viewType: currentView as 'free' | 'thinking',
            isCollapsed: false,
            nodeIds: Array.from(selectedNodeIds),
            x: minX - padding,
            y: minY - padding - headerHeight,
            width: maxX - minX + padding * 2,
            height: maxY - minY + padding * 2 + headerHeight,
          };

          addSection(newSection);

          const updatedNodes = nodes.map(node =>
            selectedNodeIds.has(node.id)
              ? { ...node, sectionId }
              : node
          );
          onNodesChange(updatedNodes);
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
  }, [selectedNodeIds, nodes, visibleNodes, onNodesChange, addSection, currentView, onToolChange]);

  // Handle Node Selection Logic
  const handleNodeSelect = useCallback((nodeId: string, e: Konva.KonvaEventObject<MouseEvent | TouchEvent>) => {
    // In Hand mode or holding space, let event bubble to Stage for panning
    if (toolMode === 'hand' || isSpacePressed) return;

    e.cancelBubble = true; // Prevent stage click (only in select mode)

    const isShift = e.evt.shiftKey || e.evt.ctrlKey || e.evt.metaKey;
    const isSelected = selectedNodeIds.has(nodeId);

    if (isShift) {
      // Toggle selection
      const newSet = new Set(selectedNodeIds);
      if (isSelected) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      setSelectedNodeIds(newSet);
    } else {
      if (!isSelected) {
        setSelectedNodeIds(new Set([nodeId]));
      }
    }
  }, [selectedNodeIds, toolMode, isSpacePressed]);

  // Handle Bulk Drag
  const handleNodeDragStart = useCallback((nodeId: string) => (e: Konva.KonvaEventObject<DragEvent>) => {
    // Prevent drag if in hand mode (though draggable prop should control this)
    if (toolMode === 'hand') {
      e.target.stopDrag();
      return;
    }

    e.cancelBubble = true;
    draggedNodeRef.current = nodeId;
    lastDragPosRef.current = e.target.position();

    // Enable cross-boundary drag (to Chat)
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      setCrossBoundaryDragNode({
        id: node.id,
        title: node.title,
        content: node.content,
        sourceMessageId: node.sourceMessageId
      });
    }

    // Ensure dragging node is selected and determine effective selection
    let effectiveSelectionIds = new Set(selectedNodeIds);
    if (!selectedNodeIds.has(nodeId)) {
      if (!e.evt.shiftKey) {
        effectiveSelectionIds = new Set([nodeId]);
        setSelectedNodeIds(effectiveSelectionIds);
      } else {
        effectiveSelectionIds.add(nodeId);
        setSelectedNodeIds(new Set(effectiveSelectionIds));
      }
    }

    // Alt + Drag: Leave a copy behind (Duplicate)
    if (e.evt.altKey) {
      const nodesToClone = nodes.filter(n => effectiveSelectionIds.has(n.id));

      const newStaticNodes = nodesToClone.map(node => ({
        ...node,
        id: `node-${crypto.randomUUID()}-copy`,
        // Keep original position (this will be the "left behind" copy)
        x: node.x,
        y: node.y,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        // Clear selection for the copy, as we are dragging the original
      }));

      // Add static copies to canvas
      onNodesChange([...nodes, ...newStaticNodes]);
      // Selection stays on the moving nodes (original IDs), which is what we want.
    }

  }, [selectedNodeIds, toolMode, nodes, setCrossBoundaryDragNode]);

  const handleNodeDragMove = useCallback((nodeId: string) => (e: Konva.KonvaEventObject<DragEvent>) => {
    e.cancelBubble = true;
    if (!lastDragPosRef.current) return;

    const newPos = e.target.position();
    const dx = newPos.x - lastDragPosRef.current.x;
    const dy = newPos.y - lastDragPosRef.current.y;

    lastDragPosRef.current = newPos;

    // Move other selected nodes
    const stage = stageRef.current;
    if (!stage) return;

    selectedNodeIds.forEach(id => {
      if (id === nodeId) return; // Skip self
      const node = stage.findOne(`#node-${id}`);
      if (node) {
        node.x(node.x() + dx);
        node.y(node.y() + dy);
      }
    });
  }, [selectedNodeIds]);

  const handleNodeDragEnd = useCallback((nodeId: string) => (e: Konva.KonvaEventObject<DragEvent>) => {
    e.cancelBubble = true;
    draggedNodeRef.current = null;
    lastDragPosRef.current = null;

    // Check if mouse is outside the canvas container (cross-boundary drag)
    const container = containerRef.current;
    const mouseX = e.evt.clientX;
    const mouseY = e.evt.clientY;
    const stage = stageRef.current;

    if (container) {
      const rect = container.getBoundingClientRect();
      const isOutsideCanvas = mouseX < rect.left || mouseX > rect.right ||
        mouseY < rect.top || mouseY > rect.bottom;

      if (isOutsideCanvas) {
        // Cross-boundary drag: Reset node position back to original (from state)
        // This keeps the node visible in canvas while also adding it as context
        if (stage) {
          selectedNodeIds.forEach(id => {
            const originalNode = nodes.find(n => n.id === id);
            const konvaNode = stage.findOne(`#node-${id}`);
            if (originalNode && konvaNode) {
              konvaNode.x(originalNode.x);
              konvaNode.y(originalNode.y);
            }
          });
        }

        // Clear crossBoundaryDragNode after a short delay to allow AssistantPanel to detect it
        setTimeout(() => setCrossBoundaryDragNode(null), 100);
        return;
      }
    }

    // Clear cross-boundary drag state since we're dropping inside canvas
    setCrossBoundaryDragNode(null);

    // Sync all selected nodes positions to state
    if (!stage) return;

    const updatedNodes = nodes.map(n => {
      if (selectedNodeIds.has(n.id)) {
        // If it's the dragged node, use event target
        if (n.id === nodeId) {
          return { ...n, x: e.target.x(), y: e.target.y() };
        }
        // For others, look up by ID
        const nodeNode = stage.findOne(`#node-${n.id}`);
        if (nodeNode) {
          return { ...n, x: nodeNode.x(), y: nodeNode.y() };
        }
      }
      return n;
    });

    onNodesChange(updatedNodes);
  }, [nodes, selectedNodeIds, onNodesChange, setCrossBoundaryDragNode]);

  // Handle wheel zoom and pan (with throttling for smooth Mac trackpad scrolling)
  const handleWheel = (e: Konva.KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();

    // Throttle wheel events to prevent stuttering on Mac trackpad
    const now = Date.now();
    if (now - lastWheelTimeRef.current < WHEEL_THROTTLE_MS) {
      return;
    }
    lastWheelTimeRef.current = now;

    const stage = stageRef.current;
    if (!stage) return;

    // Zoom Logic (Ctrl + Wheel / Pinch)
    if (e.evt.ctrlKey) {
      const scaleBy = 1.05;
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
    } else {
      // Pan Logic (Trackpad scroll / Mouse wheel scroll)
      const dx = -e.evt.deltaX;
      const dy = -e.evt.deltaY;

      onViewportChange({
        ...viewport,
        x: viewport.x + dx,
        y: viewport.y + dy,
      });
    }
  };

  // Handle Stage Interaction (Pan vs Box Select)
  const handleStageMouseDown = (e: Konva.KonvaEventObject<MouseEvent>) => {
    // Check if we are in Pan mode (Hand tool or Spacebar)
    // In Hand mode/Spacebar, we ALWAYS pan, regardless of what was clicked (node or stage)
    const isHandMode = toolMode === 'hand' || isSpacePressed;

    if (isHandMode) {
      if (e.evt.button === 0) { // Left click only for primary pan
        setIsPanning(true);
        lastPosRef.current = { x: e.evt.clientX, y: e.evt.clientY };
        return; // Stop here, do not process selection
      }
    }

    // Existing "Clicked on Empty" check for Select Mode behaviors
    const clickedOnEmpty = e.target === e.target.getStage() || e.target.getClassName() === 'Rect';

    if (clickedOnEmpty) {
      // Left click
      if (e.evt.button === 0) {
        // If NOT Hand/Space (already handled above), then it's Box Selection
        if (!isHandMode) {
          // Box Selection mode
          const stage = e.target.getStage();
          const pointer = stage?.getPointerPosition();
          if (pointer) {
            const x = (pointer.x - viewport.x) / viewport.scale;
            const y = (pointer.y - viewport.y) / viewport.scale;
            setSelectionRect({
              startX: x, startY: y,
              x, y, width: 0, height: 0
            });
          }
          // Clear selection if not Shift
          if (!e.evt.shiftKey) {
            setSelectedNodeIds(new Set());
            setSelectedEdgeId(null);
          }
        }
      } else if (e.evt.button === 1) {
        // Middle click pan (always works)
        setIsPanning(true);
        lastPosRef.current = { x: e.evt.clientX, y: e.evt.clientY };
      }
    }
  };

  const handleStageMouseMove = (e: Konva.KonvaEventObject<MouseEvent>) => {
    // Phase 2: Handle Connection Line dragging
    if (connectingFromNodeId) {
      const stage = e.target.getStage();
      const pointer = stage?.getPointerPosition();
      if (pointer) {
        const canvasX = (pointer.x - viewport.x) / viewport.scale;
        const canvasY = (pointer.y - viewport.y) / viewport.scale;
        setConnectingLineEnd({ x: canvasX, y: canvasY });
      }
      return;
    }

    // Handle Pan
    if (isPanning) {
      const dx = e.evt.clientX - lastPosRef.current.x;
      const dy = e.evt.clientY - lastPosRef.current.y;

      onViewportChange({
        ...viewport,
        x: viewport.x + dx,
        y: viewport.y + dy,
      });

      lastPosRef.current = { x: e.evt.clientX, y: e.evt.clientY };
      return;
    }

    // Handle Box Selection
    if (selectionRect) {
      const stage = e.target.getStage();
      const pointer = stage?.getPointerPosition();
      if (pointer) {
        const currentX = (pointer.x - viewport.x) / viewport.scale;
        const currentY = (pointer.y - viewport.y) / viewport.scale;

        const startX = selectionRect.startX;
        const startY = selectionRect.startY;

        setSelectionRect({
          ...selectionRect,
          x: Math.min(startX, currentX),
          y: Math.min(startY, currentY),
          width: Math.abs(currentX - startX),
          height: Math.abs(currentY - startY)
        });
      }
    }
  };

  // --- Merge Handlers (Synthesis) ---
  const MERGE_PROXIMITY_THRESHOLD = 150; // pixels

  // Helper to get raw node ID from event target (traversing up to parent Group if needed)
  // WebSocket for Synthesis
  const [synthesisTaskId, setSynthesisTaskId] = useState<string | null>(null);

  useOutputWebSocket({
    projectId: projectId || '',
    taskId: synthesisTaskId,
    enabled: !!projectId && !!synthesisTaskId,
    onNodeAdded: (nodeId, nodeData) => {
      console.log('[KonvaCanvas] onNodeAdded:', nodeId, nodeData);

      // Since we are scoped to the task_id, any node added is likely our result.
      // But we still check if we have a pending result to update.
      if (pendingSynthesisResult) {
        // Extract synthesis specific fields from metadata if available
        const metadata = nodeData.metadata || {};

        // Parse content field which contains Markdown formatted insight
        // We might want to keep the raw parts if available, but for now we have the full content string
        // The synthesis agent returns a formatted markdown string in nodeData.content

        setPendingSynthesisResult(prev => {
          if (!prev) return null;
          return {
            ...prev,
            // Update with real data
            id: nodeId, // Use server-generated ID
            title: nodeData.label || prev.title,
            content: nodeData.content || prev.content,
            // Try to extract structured data if we can, otherwise these might stay as defaults
            // The Agent puts them in metadata themes/confidence
            confidence: (metadata.confidence as any) || 'medium',
            themes: (metadata.themes as string[]) || [],
            // Clear the "Processing..." state
            recommendation: metadata.themes ? undefined : prev.recommendation, // If we have themes, assume real data
            keyRisk: undefined,
          };
        });

        // Clear task ID to satisfy "one-off" synthesis
        setSynthesisTaskId(null);
        setIsSynthesizing(false);
      }
    },
    onGenerationError: (error) => {
      console.error('Synthesis error:', error);
      setPendingSynthesisResult(prev => prev ? { ...prev, content: `Error: ${error}` } : null);
      setSynthesisTaskId(null);
      setIsSynthesizing(false);
    }
  });

  const getNodeIdFromEvent = (e: Konva.KonvaEventObject<DragEvent>) => {
    // The drag event target might be a child element (e.g., Rect inside Group)
    // We need to traverse up to find the Group with the node-{uuid} ID
    let target = e.target;
    while (target) {
      const id = target.id();
      if (id && id.startsWith('node-')) {
        return id.replace('node-', '');
      }
      target = target.parent as Konva.Node;
    }
    // Fallback: use target directly (shouldn't reach here normally)
    const id = e.target.id();
    return id.startsWith('node-') ? id.replace('node-', '') : id;
  };



  const handleNodeDragMoveWithMerge = useCallback(
    (e: Konva.KonvaEventObject<DragEvent>) => {
      const nodeId = getNodeIdFromEvent(e);
      if (!nodeId) {
        console.warn('[Merge] Could not get nodeId from event');
        return;
      }

      const draggedNode = nodes.find((n) => n.id === nodeId);
      if (!draggedNode) {
        console.warn('[Merge] Could not find node:', nodeId);
        return;
      }

      const draggedWidth = draggedNode.width || 280;
      const draggedHeight = draggedNode.height || 200;

      // Find the draggable Group element to get its actual position
      // The event target might be this Group or we need to find the parent Group
      let groupNode = e.target;
      while (groupNode && !groupNode.id()?.startsWith('node-')) {
        groupNode = groupNode.parent as Konva.Node;
      }

      const x = groupNode ? groupNode.x() : e.target.x();
      const y = groupNode ? groupNode.y() : e.target.y();

      const draggedCenterX = x + draggedWidth / 2;
      const draggedCenterY = y + draggedHeight / 2;

      let closestNodeId: string | null = null;
      let closestDistance = Infinity;

      for (const node of nodes) {
        if (node.id === nodeId) continue;

        const nodeWidth = node.width || 280;
        const nodeHeight = node.height || 200;
        const nodeCenterX = node.x + nodeWidth / 2;
        const nodeCenterY = node.y + nodeHeight / 2;

        const distance = Math.sqrt(
          Math.pow(draggedCenterX - nodeCenterX, 2) +
          Math.pow(draggedCenterY - nodeCenterY, 2)
        );

        if (distance < closestDistance && distance < MERGE_PROXIMITY_THRESHOLD) {
          closestDistance = distance;
          closestNodeId = node.id;
        }
      }

      if (closestNodeId && closestNodeId !== mergeTargetNodeId) {
        console.log('[Merge] Potential merge detected:', nodeId, '->', closestNodeId, 'dist:', Math.round(closestDistance));
      }

      setMergeTargetNodeId(closestNodeId);
      if (closestNodeId) setDraggedNodeId(nodeId);
    },
    [nodes, mergeTargetNodeId]
  );

  const handleNodeDragEndWithMerge = useCallback(
    (e: Konva.KonvaEventObject<DragEvent>) => {
      const nodeId = getNodeIdFromEvent(e);
      const x = e.target.x();
      const y = e.target.y();

      // Check for merge
      if (mergeTargetNodeId && draggedNodeId === nodeId) {
        // Merge detected - keep state for prompt
      } else {
        setDraggedNodeId(null);
        setMergeTargetNodeId(null);
      }

      // Always update position
      const targetNode = nodes.find((n) => n.id === nodeId);
      if (targetNode && onNodesChange) {
        const updatedNodes = nodes.map((n) =>
          n.id === nodeId ? { ...n, x, y } : n
        );
        onNodesChange(updatedNodes);
      }
    },
    [nodes, onNodesChange, mergeTargetNodeId, draggedNodeId]
  );

  // P1: Edge Reconnection Handlers
  const handleEdgeHandleDragMove = useCallback((e: Konva.KonvaEventObject<DragEvent>, edgeId: string, type: 'source' | 'target') => {
    // Current pointer position relative to canvas
    const stage = e.target.getStage();
    const pointer = stage?.getPointerPosition();
    if (!pointer) return;

    const canvasX = (pointer.x - viewport.x) / viewport.scale;
    const canvasY = (pointer.y - viewport.y) / viewport.scale;

    setReconnectingEdge({ edgeId, type, x: canvasX, y: canvasY });

    // Check for drop target (node) under cursor
    const targetNode = visibleNodes.find(node => {
      const nodeWidth = node.width || 280;
      const nodeHeight = node.height || 200;
      return (
        canvasX >= node.x &&
        canvasX <= node.x + nodeWidth &&
        canvasY >= node.y &&
        canvasY <= node.y + nodeHeight
      );
    });

    setHoveredNodeId(targetNode ? targetNode.id : null);
  }, [viewport, visibleNodes]);

  const handleEdgeHandleDragEnd = useCallback((e: Konva.KonvaEventObject<DragEvent>, edge: CanvasEdge, type: 'source' | 'target') => {
    setReconnectingEdge(null);
    setHoveredNodeId(null);

    // Reset handle position visually (Konva keeps it at drop location otherwise)
    e.target.position({ x: 0, y: 0 });

    const stage = e.target.getStage();
    const pointer = stage?.getPointerPosition();
    if (!pointer) return;

    const canvasX = (pointer.x - viewport.x) / viewport.scale;
    const canvasY = (pointer.y - viewport.y) / viewport.scale;

    // Find target node
    const targetNode = visibleNodes.find(node => {
      const nodeWidth = node.width || 280;
      const nodeHeight = node.height || 200;
      return (
        canvasX >= node.x &&
        canvasX <= node.x + nodeWidth &&
        canvasY >= node.y &&
        canvasY <= node.y + nodeHeight
      );
    });

    if (targetNode) {
      // Don't allow self-loops if source===target (unless we want to support self-loops, but P2 says 'Prevent self-loops')
      // Actually P2.3 says 'Validation: Prevent self-loops (if desired)'
      // For now let's allow basic reconnect.

      const newEdge = { ...edge };

      if (type === 'source') {
        if (targetNode.id === edge.target) return; // No change
        newEdge.source = targetNode.id;
        newEdge.sourceAnchor = 'auto'; // Reset anchor to auto
      } else {
        if (targetNode.id === edge.source) return; // No change
        newEdge.target = targetNode.id;
        newEdge.targetAnchor = 'auto'; // Reset anchor to auto
      }

      // Check for duplicates
      const exists = edges.some(e =>
        e.id !== edge.id &&
        ((e.source === newEdge.source && e.target === newEdge.target) ||
          (e.source === newEdge.target && e.target === newEdge.source))
      );

      if (!exists && onEdgesChange) {
        onEdgesChange(edges.map(e => e.id === edge.id ? newEdge : e));
      }
    }
  }, [viewport, visibleNodes, edges, onEdgesChange]);

  const handleCancelMerge = () => {
    setMergeTargetNodeId(null);
    setDraggedNodeId(null);
  };

  const handleSynthesize = async (mode: SynthesisMode) => {
    if (!draggedNodeId || !mergeTargetNodeId) return;

    const sourceNodeIds = [draggedNodeId, mergeTargetNodeId];
    setIsSynthesizing(true);

    try {
      const targetNode = nodes.find(n => n.id === mergeTargetNodeId);
      const draggedNode = nodes.find(n => n.id === draggedNodeId);

      // Calculate position for result card (between the two nodes) - CANVAS coordinates
      const midX = targetNode && draggedNode
        ? (targetNode.x + draggedNode.x + (draggedNode.width || 280)) / 2
        : 400;
      const maxY = targetNode && draggedNode
        ? Math.max(targetNode.y + (targetNode.height || 200), draggedNode.y + (draggedNode.height || 200)) + 50
        : 300;

      // Use canvas coordinates directly (not screen coords) for Konva rendering
      const resultPosition = { x: midX, y: maxY };

      // Call the synthesis API and get task_id (returned by synthesizeNodes)
      // The backend will generate the result and we poll/wait for it
      // For now, we'll extract content from the source nodes and create a mock pending result
      // This will be replaced with proper WebSocket handling

      const sourceContents = sourceNodeIds.map(id => {
        const node = nodes.find(n => n.id === id);
        return { title: node?.title || '', content: node?.content || '' };
      });

      // Start synthesis via API
      const response = await synthesizeNodes(sourceNodeIds, resultPosition, mode);

      // Set task ID to enable WebSocket listening
      if (response && response.task_id) {
        console.log('[Canvas] Synthesis task started:', response.task_id);
        setSynthesisTaskId(response.task_id);
      }

      // Create a pending result to show immediately 
      // In production, this would come from WebSocket NODE_ADDED event
      const modeLabels = {
        connect: 'Connection Found',
        inspire: 'New Perspective',
        debate: 'Key Tension Identified',
      };

      setPendingSynthesisResult({
        id: `synthesis-${crypto.randomUUID()}`,
        title: modeLabels[mode],
        content: `Analyzing "${sourceContents[0].title}" and "${sourceContents[1].title}" to find ${mode === 'connect' ? 'connections' : mode === 'inspire' ? 'new perspectives' : 'tensions'}...`,
        recommendation: 'Processing...',
        keyRisk: 'Processing...',
        confidence: 'medium',
        themes: [],
        sourceNodeIds,
        mode,
        position: resultPosition,
      });

      // Note: In full implementation, WebSocket would update this with actual LLM result
      // For demo, we'll keep the loading state until user discards or adds

    } catch (e) {
      console.error(e);
      setPendingSynthesisResult(null);
    } finally {
      setIsSynthesizing(false);
      setMergeTargetNodeId(null);
      setDraggedNodeId(null);
    }
  };

  const handleNodeSave = (nodeId: string, updates: { title?: string; content?: string }) => {
    if (onNodesChange) {
      const updatedNodes = nodes.map((n) =>
        n.id === nodeId ? { ...n, ...updates } : n
      );
      onNodesChange(updatedNodes);
    }
    setEditingNodeId(null);
  };

  const handleNodeEditCancel = () => {
    setEditingNodeId(null);
  };

  const handleStageMouseUp = (e: Konva.KonvaEventObject<MouseEvent>) => {
    // Phase 2: Handle Connection creation
    if (connectingFromNodeId && connectingLineEnd) {
      const stage = e.target.getStage();
      const pointer = stage?.getPointerPosition();
      if (pointer) {
        const canvasX = (pointer.x - viewport.x) / viewport.scale;
        const canvasY = (pointer.y - viewport.y) / viewport.scale;

        // Find target node under the mouse
        const targetNode = visibleNodes.find(node => {
          const nodeWidth = node.width || 280;
          const nodeHeight = node.height || 200;
          return (
            canvasX >= node.x &&
            canvasX <= node.x + nodeWidth &&
            canvasY >= node.y &&
            canvasY <= node.y + nodeHeight &&
            node.id !== connectingFromNodeId
          );
        });

        if (targetNode) {
          // Check if edge already exists
          const edgeExists = edges.some(
            e => (e.source === connectingFromNodeId && e.target === targetNode.id) ||
              (e.source === targetNode.id && e.target === connectingFromNodeId)
          );

          if (!edgeExists) {
            // Create new edge with default label
            const newEdge: CanvasEdge = {
              id: `edge-${crypto.randomUUID()}`,
              source: connectingFromNodeId,
              target: targetNode.id,
              label: '',
              relationType: 'related',
            };
            onEdgesChange([...edges, newEdge]);

            // Show label dialog
            const sourceNode = visibleNodes.find(n => n.id === connectingFromNodeId);
            if (sourceNode) {
              const midX = ((sourceNode.x + (sourceNode.width || 280)) + targetNode.x) / 2;
              const midY = ((sourceNode.y + (sourceNode.height || 200) / 2) + (targetNode.y + (targetNode.height || 200) / 2)) / 2;
              // Convert to screen coordinates
              const screenX = midX * viewport.scale + viewport.x;
              const screenY = midY * viewport.scale + viewport.y;
              setEdgeLabelDialog({ edge: newEdge, position: { x: screenX, y: screenY } });
            }
          }
        }
      }
      setConnectingFromNodeId(null);
      setConnectingLineEnd(null);
      return;
    }

    if (isPanning) {
      setIsPanning(false);
    }

    if (selectionRect) {
      // Calculate Intersection using spatial index O(log N) query
      const box = selectionRect;
      // Optimization: only check intersection if box has size
      if (box.width > 0 || box.height > 0) {
        const newSelection = new Set(selectedNodeIds);

        // Use spatial index for efficient box selection
        const intersectingItems = spatialIndex.search({
          minX: box.x,
          minY: box.y,
          maxX: box.x + box.width,
          maxY: box.y + box.height
        });

        intersectingItems.forEach((item: SpatialItem) => {
          newSelection.add(item.nodeId);
        });

        setSelectedNodeIds(newSelection);
      }
      setSelectionRect(null);
    }
  };

  // Determine Cursor Style
  const getCursorStyle = () => {
    if (isPanning) return 'grabbing';
    if (toolMode === 'hand' || isSpacePressed) return 'grab';
    if (selectionRect) return 'crosshair';
    if (hoveredNodeId && toolMode === 'select') return 'move';
    return 'default';
  };

  // Edge style configuration for different relation types
  interface EdgeStyleConfig {
    color: string;
    bgColor: string;
    strokeWidth: number;
    dash?: number[];
    icon?: string;  // Icon name for edge midpoint
  }

  const EDGE_STYLES: Record<string, EdgeStyleConfig> = {
    // Core Q&A relationships
    answers: { color: '#10B981', bgColor: '#ECFDF5', strokeWidth: 2, icon: '✓' },           // Green - check
    prompts_question: { color: '#8B5CF6', bgColor: '#F5F3FF', strokeWidth: 2, dash: [8, 4], icon: '?' },  // Violet - question
    derives: { color: '#F59E0B', bgColor: '#FFFBEB', strokeWidth: 2, icon: '💡' },          // Amber - lightbulb

    // Logical relationships
    causes: { color: '#EF4444', bgColor: '#FEF2F2', strokeWidth: 3, icon: '→' },           // Red - arrow
    compares: { color: '#3B82F6', bgColor: '#EFF6FF', strokeWidth: 2, dash: [4, 4], icon: '⇆' },  // Blue - bidirectional
    supports: { color: '#059669', bgColor: '#ECFDF5', strokeWidth: 2, icon: '+' },           // Green - plus
    contradicts: { color: '#DC2626', bgColor: '#FEF2F2', strokeWidth: 2, icon: '×' },           // Red - cross

    // Evolution relationships
    revises: { color: '#EC4899', bgColor: '#FCE7F3', strokeWidth: 2, dash: [12, 6], icon: '✎' }, // Pink - edit
    extends: { color: '#06B6D4', bgColor: '#ECFEFF', strokeWidth: 2, icon: '↗' },           // Cyan - extend

    // Organization
    parks: { color: '#9CA3AF', bgColor: '#F3F4F6', strokeWidth: 1.5, dash: [4, 8], icon: '⏸' }, // Gray - pause
    groups: { color: '#7C3AED', bgColor: '#F5F3FF', strokeWidth: 1.5, dash: [2, 2], icon: '▢' }, // Purple - group
    belongs_to: { color: '#7C3AED', bgColor: '#F5F3FF', strokeWidth: 2 },                       // Purple (legacy)
    related: { color: '#6B7280', bgColor: '#F3F4F6', strokeWidth: 2 },                       // Gray (legacy)

    // User-defined
    custom: { color: '#6B7280', bgColor: '#F3F4F6', strokeWidth: 2 },                       // Gray

    // Thinking Path edge types (for styling compatibility)
    branch: { color: '#F59E0B', bgColor: '#FFFBEB', strokeWidth: 2.5, icon: '↳' },         // Amber - branch from insight
    progression: { color: '#8B5CF6', bgColor: '#F5F3FF', strokeWidth: 2.5, dash: [8, 4], icon: '→' }, // Violet - topic follow-up
  };

  // Get edge style with fallback
  const getEdgeStyle = (relationType?: string, edgeType?: string): EdgeStyleConfig => {
    // Check edge type first (for thinking path edges), then relation type
    if (edgeType && EDGE_STYLES[edgeType]) {
      return EDGE_STYLES[edgeType];
    }
    return EDGE_STYLES[relationType || 'related'] || EDGE_STYLES.related;
  };

  // Legacy function for backwards compatibility
  const getEdgeLabelStyle = (relationType?: string, edgeType?: string) => {
    const style = getEdgeStyle(relationType, edgeType);
    return { color: style.color, bgColor: style.bgColor };
  };

  // Draw connections with labels and relation-specific styling
  const renderEdges = () => {
    return edges.map((edge, index) => {
      const source = visibleNodes.find((n) => n.id === edge.source);
      const target = visibleNodes.find((n) => n.id === edge.target);

      if (!source || !target) return null;

      const isSelected = selectedEdgeId === edge.id;
      const isReconnecting = reconnectingEdge?.edgeId === edge.id;

      // === P0: Dynamic anchor selection ===
      const sourceAnchorDir = resolveAnchor(edge, source, target, 'source');
      const targetAnchorDir = resolveAnchor(edge, source, target, 'target');

      let sourceAnchor = getAnchorPoint(source, sourceAnchorDir);
      let targetAnchor = getAnchorPoint(target, targetAnchorDir);

      // === P1: Reconnection Live Preview ===
      // If we are dragging an endpoint, use the cursor position instead of the anchor
      if (isReconnecting && reconnectingEdge.x !== undefined && reconnectingEdge.y !== undefined) {
        if (reconnectingEdge.type === 'source') {
          // Keep direction for now, or calculate based on relative pos
          sourceAnchor = { x: reconnectingEdge.x, y: reconnectingEdge.y, direction: sourceAnchorDir };
        } else {
          targetAnchor = { x: reconnectingEdge.x, y: reconnectingEdge.y, direction: targetAnchorDir };
        }
      }

      // === P0: Routing type selection ===
      const routingType = edge.routingType || 'bezier'; // Default to bezier for backwards compatibility

      let pathPoints: number[] = [];
      if (routingType === 'straight') {
        pathPoints = getStraightPath(sourceAnchor, targetAnchor);
      } else if (routingType === 'orthogonal') {
        // P1: Orthogonal routing
        // For now pass empty obstacles, will add collision detection later
        pathPoints = getOrthogonalPath(sourceAnchor, targetAnchor, []);
      } else {
        pathPoints = getBezierPath(sourceAnchor, targetAnchor);
      }

      // Calculate midpoint for label/icon placement
      const midX = (sourceAnchor.x + targetAnchor.x) / 2;
      const midY = (sourceAnchor.y + targetAnchor.y) / 2;

      // Get edge style configuration
      const baseEdgeStyle = getEdgeStyle(edge.relationType, edge.type);

      // Apply overrides from edge data
      const edgeStyle = {
        color: edge.color || baseEdgeStyle.color,
        bgColor: baseEdgeStyle.bgColor, // Background usually doesn't need override, but could add if needed
        strokeWidth: edge.strokeWidth || baseEdgeStyle.strokeWidth,
        dash: edge.strokeDash || baseEdgeStyle.dash,
        icon: baseEdgeStyle.icon
      };

      const hasLabel = edge.label && edge.label.trim().length > 0;

      // Determine if this edge should have special styling
      const hasRelationType = !!edge.relationType && edge.relationType !== 'related' && edge.relationType !== 'custom';
      const isThinkingPathEdge = edge.type === 'branch' || edge.type === 'progression';
      const hasCustomStyle = !!edge.color || !!edge.strokeWidth || !!edge.strokeDash;

      const shouldHighlight = hasLabel || hasRelationType || isThinkingPathEdge || hasCustomStyle || isSelected;

      // Check for bidirectional edge (compares)
      const isBidirectional = edge.direction === 'bidirectional' || edge.relationType === 'compares';

      // === P0: Dynamic arrow points ===
      // If reconnecting target, arrow should follow cursor
      const targetArrowPoints = getArrowPoints(targetAnchor);
      const sourceArrowPoints = isBidirectional ? getArrowPoints(sourceAnchor) : null;

      return (
        <Group
          key={edge.id || `${edge.source}-${edge.target}-${index}`}
          onClick={(e) => {
            e.cancelBubble = true;
            setSelectedEdgeId(edge.id);
          }}
          onTap={(e) => {
            e.cancelBubble = true;
            setSelectedEdgeId(edge.id);
          }}
        >
          {/* Hit area for easier selection - invisible wide stroke */}
          <Line
            points={pathPoints}
            stroke="transparent"
            strokeWidth={20}
            tension={routingType === 'bezier' ? 0.5 : 0}
            bezier={routingType === 'bezier'}
          />

          {/* Selection Halo */}
          {isSelected && (
            <Line
              points={pathPoints}
              stroke="#3B82F6"
              strokeWidth={(edgeStyle.strokeWidth || 2) + 4}
              opacity={0.3}
              tension={routingType === 'bezier' ? 0.5 : 0}
              bezier={routingType === 'bezier'}
            />
          )}

          {/* Main edge line */}
          <Line
            points={pathPoints}
            stroke={shouldHighlight ? edgeStyle.color : "#94A3B8"}
            strokeWidth={edgeStyle.strokeWidth}
            dash={edgeStyle.dash}
            tension={routingType === 'bezier' ? 0.5 : 0}
            bezier={routingType === 'bezier'}
          />

          {/* Arrow at target end */}
          <Line
            points={targetArrowPoints}
            stroke={shouldHighlight ? edgeStyle.color : "#94A3B8"}
            strokeWidth={edgeStyle.strokeWidth}
            lineCap="round"
            lineJoin="round"
          />

          {/* Arrow at source end for bidirectional edges */}
          {isBidirectional && sourceArrowPoints && (
            <Line
              points={sourceArrowPoints}
              stroke={edgeStyle.color}
              strokeWidth={edgeStyle.strokeWidth}
              lineCap="round"
              lineJoin="round"
            />
          )}

          {/* Edge Label (AI-generated or user-defined) */}
          {(hasLabel || edgeStyle.icon) && (
            <Group
              x={midX}
              y={midY}
              onClick={(e) => {
                e.cancelBubble = true;
                const stage = e.target.getStage();
                const pointer = stage?.getPointerPosition();

                // If the edge selection bubble didn't happen first, we ensure it's selected
                setSelectedEdgeId(edge.id);

                if (pointer) {
                  setEdgeLabelDialog({
                    edge,
                    position: pointer // Use screen coords or stage coords? Dialog uses fixed div position, likely needs client position.
                    // IMPORTANT: The existing code for setEdgeLabelDialog expects screen coordinates because the dialog is an HTML overlay.
                    // pointer is {x, y} relative to stage container? No, getPointerPosition is relative to stage container.
                    // The dialog is positioned with position: absolute LEFT/TOP.
                    // If the dialog is inside a container, we need coords relative to that container.
                    // Looking at existing usage (line 1785), it receives event properties.
                    // Let's use `e.evt.clientX` / `e.evt.clientY` which are screen coords if possible.
                    // Konva event `e.evt` is the native MouseEvent.
                  });
                }
              }}
            >
              {hasLabel ? (
                <>
                  <Rect
                    x={-edge.label!.length * 4 - 10}
                    y={-12}
                    width={edge.label!.length * 8 + 20}
                    height={24}
                    fill={edgeStyle.bgColor}
                    stroke={edgeStyle.color}
                    strokeWidth={1}
                    cornerRadius={12}
                    shadowColor="rgba(0,0,0,0.1)"
                    shadowBlur={4}
                    shadowOffsetY={2}
                  />
                  {edgeStyle.icon && (
                    <Text
                      x={-edge.label!.length * 4 - 6}
                      y={-8}
                      text={edgeStyle.icon}
                      fontSize={12}
                      fill={edgeStyle.color}
                    />
                  )}
                  <Text
                    x={edgeStyle.icon ? -edge.label!.length * 4 + 8 : -edge.label!.length * 4}
                    y={-7}
                    text={edge.label}
                    fontSize={11}
                    fill={edgeStyle.color}
                    fontStyle="600"
                  />
                </>
              ) : (
                <>
                  <Circle
                    radius={12}
                    fill={edgeStyle.bgColor}
                    stroke={edgeStyle.color}
                    strokeWidth={1}
                  />
                  <Text
                    x={-6}
                    y={-7}
                    text={edgeStyle.icon}
                    fontSize={12}
                    fill={edgeStyle.color}
                    align="center"
                  />
                </>
              )}
            </Group>
          )}

          {/* P1: Reconnection Handles (only if selected) */}
          {isSelected && (
            <>
              {/* Source Handle */}
              <Circle
                x={sourceAnchor.x}
                y={sourceAnchor.y}
                radius={6}
                fill="#3B82F6"
                stroke="white"
                strokeWidth={2}
                draggable
                onDragMove={(e) => handleEdgeHandleDragMove(e, edge.id, 'source')}
                onDragEnd={(e) => handleEdgeHandleDragEnd(e, edge, 'source')}
                onMouseEnter={() => {
                  const container = stageRef.current?.container();
                  if (container) container.style.cursor = 'crosshair';
                }}
                onMouseLeave={() => {
                  const container = stageRef.current?.container();
                  if (container) container.style.cursor = 'default';
                }}
              />
              {/* Target Handle */}
              <Circle
                x={targetAnchor.x}
                y={targetAnchor.y}
                radius={6}
                fill="#3B82F6"
                stroke="white"
                strokeWidth={2}
                draggable
                onDragMove={(e) => handleEdgeHandleDragMove(e, edge.id, 'target')}
                onDragEnd={(e) => handleEdgeHandleDragEnd(e, edge, 'target')}
                onMouseEnter={() => {
                  const container = stageRef.current?.container();
                  if (container) container.style.cursor = 'crosshair';
                }}
                onMouseLeave={() => {
                  const container = stageRef.current?.container();
                  if (container) container.style.cursor = 'default';
                }}
              />
            </>
          )}
        </Group>
      );
    });
  };

  return (
    <div
      style={{ flexGrow: 1, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
    >
      {/* Canvas Container */}
      <div
        ref={containerRef}
        style={{
          flexGrow: 1,
          backgroundColor: '#FAFAFA',
          position: 'relative',
          overflow: 'hidden'
        }}
        onContextMenu={(e) => {
          // Prevent browser default context menu at container level
          // The Konva Stage's onContextMenu will handle showing our custom menu
          e.preventDefault();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'copy';
          if (dragContentRef.current && containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect();
            const screenX = e.clientX - rect.left;
            const screenY = e.clientY - rect.top;
            const canvasX = (screenX - viewport.x) / viewport.scale;
            const canvasY = (screenY - viewport.y) / viewport.scale;
            setDragPreview({ x: canvasX, y: canvasY, content: dragContentRef.current });
          }
        }}
        onDragLeave={() => setDragPreview(null)}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          if (!containerRef.current) return;
          const rect = containerRef.current.getBoundingClientRect();
          const screenX = e.clientX - rect.left;
          const screenY = e.clientY - rect.top;
          const canvasX = (screenX - viewport.x) / viewport.scale;
          const canvasY = (screenY - viewport.y) / viewport.scale;

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
              // Handle document drops from sidebar
              if (data.type === 'document') {
                const nodeData = {
                  type: 'knowledge',

                  title: data.title,
                  content: '', // Will be populated with summary if available
                  x: centeredX,
                  y: centeredY,
                  width: cardWidth,
                  height: cardHeight,
                  color: 'red',
                  tags: ['#source'],
                  sourceId: data.documentId,
                  fileMetadata: {
                    fileType: data.fileType || 'pdf',
                    pageCount: data.pageCount,
                    thumbnailUrl: data.thumbnailUrl,
                  },
                  viewType: 'free' as const,
                  subType: 'source' as const,
                };
                onNodeAdd(nodeData);
                handled = true;
              }
            } catch (err) {
              console.error('[KonvaCanvas] onDrop - Error parsing JSON:', err);
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
        {/* Context Menu for Canvas Background */}
        {contextMenu && !contextMenu.nodeId && !contextMenu.sectionId && (
          <CanvasContextMenu
            open={true}
            x={contextMenu.x}
            y={contextMenu.y}
            onClose={() => setContextMenu(null)}
            onOpenImport={onOpenImport || (() => { })}
            viewport={viewport}
            canvasContainerRef={containerRef}
          />
        )}

        {/* Existing Menu for Nodes/Sections */}
        {contextMenu && (contextMenu.nodeId || contextMenu.sectionId) && (
          <Menu
            open={Boolean(contextMenu)}
            onClose={() => setContextMenu(null)}
            anchorReference="anchorPosition"
            anchorPosition={contextMenu ? { top: contextMenu.y, left: contextMenu.x } : undefined}
          >
            {contextMenu.nodeId && (
              <MenuItem
                onClick={() => {
                  setEditingNodeId(contextMenu.nodeId!);
                  setContextMenu(null);
                }}
                style={{ fontSize: 14 }}
              >
                <EditIcon size={16} style={{ marginRight: 8 }} />
                Edit
              </MenuItem>
            )}

            {contextMenu.nodeId && studioCurrentView === 'thinking' && (
              <MenuItem
                onClick={() => {
                  if (contextMenu.nodeId) promoteNode(contextMenu.nodeId);
                  setContextMenu(null);
                }}
                style={{ fontSize: 14 }}
              >
                <ArrowUpwardIcon size={14} style={{ marginRight: 8 }} />
                提升到自由画布
              </MenuItem>
            )}
            {/* Phase 4: Extract Insights for Source Nodes */}
            {contextMenu.nodeId && (() => {
              const node = visibleNodes.find(n => n.id === contextMenu.nodeId);
              return node?.subType === 'source';
            })() && (
                <MenuItem
                  onClick={() => {
                    const sourceNode = visibleNodes.find(n => n.id === contextMenu.nodeId);
                    if (!sourceNode) return;

                    // Generate mock insights with radial layout
                    const insights = [
                      { title: '核心概念 1', content: `从 "${sourceNode.title}" 中提取的核心概念。这是一个自动生成的洞察点。` },
                      { title: '核心概念 2', content: '另一个重要的知识点。代表文档中的关键论述或结论。' },
                      { title: '关联主题', content: '与主题相关的延伸内容。可用于进一步探索。' },
                      { title: '待验证观点', content: '需要进一步确认的内容。建议查阅更多资料。' },
                      { title: '总结', content: `"${sourceNode.title}" 的主要贡献和价值总结。` },
                    ];

                    // Radial layout calculation
                    const centerX = sourceNode.x + (sourceNode.width || 280) / 2;
                    const centerY = sourceNode.y + (sourceNode.height || 200) / 2;
                    const radius = 350; // Distance from center
                    const angleStep = (2 * Math.PI) / insights.length;
                    const startAngle = -Math.PI / 2; // Start from top

                    const newNodes: typeof nodes = [];
                    const newEdges: CanvasEdge[] = [];

                    insights.forEach((insight, index) => {
                      const angle = startAngle + angleStep * index;
                      const nodeWidth = 240;
                      const nodeHeight = 160;

                      const nodeId = `insight-${crypto.randomUUID()}-${index}`;
                      const x = centerX + radius * Math.cos(angle) - nodeWidth / 2;
                      const y = centerY + radius * Math.sin(angle) - nodeHeight / 2;

                      newNodes.push({
                        id: nodeId,
                        type: 'insight',
                        title: insight.title,
                        content: insight.content,
                        x,
                        y,
                        width: nodeWidth,
                        height: nodeHeight,
                        color: 'yellow',
                        tags: ['#extracted'],
                        sourceId: sourceNode.sourceId || sourceNode.id,
                        viewType: currentView as 'free' | 'thinking',
                      });

                      // Create edge from source to this insight
                      newEdges.push({
                        id: `edge-${crypto.randomUUID()}-${index}`,
                        source: sourceNode.id,
                        target: nodeId,
                        label: index === insights.length - 1 ? '总结' : '',
                        relationType: index === insights.length - 1 ? 'belongs_to' : 'related',
                      });
                    });

                    // Add all new nodes and edges
                    onNodesChange([...nodes, ...newNodes]);
                    onEdgesChange([...edges, ...newEdges]);

                    setContextMenu(null);
                  }}
                  style={{ fontSize: 14 }}
                >
                  <AutoAwesomeIcon size={14} style={{ marginRight: 8 }} />
                  提取洞察 (Extract Insights)
                </MenuItem>
              )}
            {/* Phase 3: Create Group from Selection */}
            {selectedNodeIds.size >= 2 && contextMenu.nodeId && selectedNodeIds.has(contextMenu.nodeId) && (
              <MenuItem
                onClick={() => {
                  // Get all selected nodes
                  const selectedNodes = visibleNodes.filter(n => selectedNodeIds.has(n.id));
                  if (selectedNodes.length < 2) return;

                  // Calculate bounding box
                  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                  selectedNodes.forEach(node => {
                    minX = Math.min(minX, node.x);
                    minY = Math.min(minY, node.y);
                    maxX = Math.max(maxX, node.x + (node.width || 280));
                    maxY = Math.max(maxY, node.y + (node.height || 200));
                  });

                  const padding = 24;
                  const headerHeight = 48;

                  // Create new section
                  const sectionId = `section-${crypto.randomUUID()}`;
                  const newSection = {
                    id: sectionId,
                    title: `组 (${selectedNodes.length} 个节点)`,
                    viewType: currentView as 'free' | 'thinking',
                    isCollapsed: false,
                    nodeIds: Array.from(selectedNodeIds),
                    x: minX - padding,
                    y: minY - padding - headerHeight,
                    width: maxX - minX + padding * 2,
                    height: maxY - minY + padding * 2 + headerHeight,
                  };

                  addSection(newSection);

                  // Update nodes with sectionId
                  const updatedNodes = nodes.map(node =>
                    selectedNodeIds.has(node.id)
                      ? { ...node, sectionId }
                      : node
                  );
                  onNodesChange(updatedNodes);

                  setContextMenu(null);
                }}
                style={{ fontSize: 14 }}
              >
                <LayersIcon size={14} style={{ marginRight: 8 }} />
                创建分组 ({selectedNodeIds.size})
              </MenuItem>
            )}
            {contextMenu.nodeId && (
              <MenuItem
                onClick={() => {
                  if (contextMenu.nodeId) {
                    // If the right-clicked node is in selection, delete all selected via API
                    // If not, delete only this one
                    if (selectedNodeIds.has(contextMenu.nodeId)) {
                      // Delete all selected nodes via API
                      selectedNodeIds.forEach(nodeId => {
                        handleDeleteNode(nodeId).catch(err => {
                          console.error('Failed to delete node:', err);
                          alert(`Failed to delete node: ${err instanceof Error ? err.message : 'Unknown error'}`);
                        });
                      });
                      setSelectedNodeIds(new Set());
                    } else {
                      // Delete single node via API
                      handleDeleteNode(contextMenu.nodeId).catch(err => {
                        console.error('Failed to delete node:', err);
                        alert(`Failed to delete node: ${err instanceof Error ? err.message : 'Unknown error'}`);
                      });
                    }
                  }
                  setContextMenu(null);
                }}
                style={{ fontSize: 14, color: '#DC2626' }}
              >
                <DeleteIcon size={14} style={{ marginRight: 8 }} />
                Delete Node {selectedNodeIds.size > 1 && selectedNodeIds.has(contextMenu.nodeId!) ? `(${selectedNodeIds.size})` : ''}
              </MenuItem>
            )}
            {contextMenu.sectionId && (
              <>
                <MenuItem
                  onClick={() => {
                    if (contextMenu.sectionId) {
                      setCanvasSections(prev =>
                        prev.map(s => s.id === contextMenu.sectionId ? { ...s, isCollapsed: !s.isCollapsed } : s)
                      );
                    }
                    setContextMenu(null);
                  }}
                  style={{ fontSize: 14 }}
                >
                  折叠/展开Section
                </MenuItem>
                <MenuItem
                  onClick={() => {
                    if (contextMenu.sectionId) deleteSection(contextMenu.sectionId);
                    setContextMenu(null);
                  }}
                  style={{ fontSize: 14, color: '#DC2626' }}
                >
                  删除Section
                </MenuItem>
              </>
            )}
          </Menu>
        )}

        {/* Phase 2: Edge Label Dialog */}
        {edgeLabelDialog && (
          <Surface
            elevation={4}
            radius="md"
            style={{
              position: 'absolute',
              left: edgeLabelDialog.position.x,
              top: edgeLabelDialog.position.y,
              transform: 'translate(-50%, -50%)',
              padding: 16,
              minWidth: 240,
              zIndex: 1100,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <UiText variant="h6" style={{ fontWeight: 600 }}>
                连接关系
              </UiText>
              <div style={{ display: 'flex', gap: 4 }}>
                <IconButton
                  size="sm"
                  color="danger"
                  variant="ghost"
                  onClick={() => {
                    if (onEdgesChange) {
                      onEdgesChange(edges.filter(e => e.id !== edgeLabelDialog.edge.id));
                    }
                    setEdgeLabelDialog(null);
                    setSelectedEdgeId(null);
                  }}
                  title="删除连接 (Delete Connection)"
                >
                  <DeleteIcon size={16} />
                </IconButton>
                <IconButton
                  size="sm"
                  variant="ghost"
                  onClick={() => setEdgeLabelDialog(null)}
                >
                  <CloseIcon size={16} />
                </IconButton>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'row', gap: 4, flexWrap: 'wrap', marginBottom: 12 }}>
              {[
                { type: 'supports', label: '支持', color: '#059669' },
                { type: 'contradicts', label: '反对', color: '#DC2626' },
                { type: 'causes', label: '导致', color: '#D97706' },
                { type: 'belongs_to', label: '属于', color: '#7C3AED' },
                { type: 'related', label: '相关', color: '#6B7280' },
              ].map(({ type, label, color }) => (
                <Chip
                  key={type}
                  label={label}
                  size="sm"
                  onClick={() => {
                    const updatedEdges = edges.map(e =>
                      e.id === edgeLabelDialog.edge.id
                        ? { ...e, label, relationType: type as CanvasEdge['relationType'] }
                        : e
                    );
                    onEdgesChange(updatedEdges);
                    setEdgeLabelDialog(null);
                  }}
                  style={{
                    borderColor: color,
                    color: color,
                    cursor: 'pointer',
                  }}
                  variant="outlined"
                />
              ))}
            </div>

            <TextField
              value=""
              placeholder="自定义标签..."
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const value = (e.currentTarget.value).trim();
                  if (value) {
                    const updatedEdges = edges.map(edge =>
                      edge.id === edgeLabelDialog.edge.id
                        ? { ...edge, label: value, relationType: 'custom' as const }
                        : edge
                    );
                    onEdgesChange(updatedEdges);
                  }
                  setEdgeLabelDialog(null);
                }
              }}
              style={{ fontSize: 13 }}
            />
          </Surface>
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
          onDblClick={(e) => {
            // Check if clicked on empty stage
            const clickedOnEmpty = e.target === e.target.getStage();
            if (clickedOnEmpty && onNodeAdd) {
              const stage = e.target.getStage();
              const pointer = stage?.getPointerPosition();
              if (pointer) {
                const x = (pointer.x - viewport.x) / viewport.scale;
                const y = (pointer.y - viewport.y) / viewport.scale;

                onNodeAdd({
                  type: 'sticky', // Default to sticky note
                  title: '',
                  content: 'New Note',
                  x: x - 100, // Center approx (width/2)
                  y: y - 75,  // Center approx (height/2)
                  width: 200,
                  height: 150,
                  color: 'yellow',
                  tags: [],
                });
              }
            }
          }}
          onMouseLeave={() => {
            handleStageMouseUp({} as Konva.KonvaEventObject<MouseEvent>);
            // Clear connection state on mouse leave
            setConnectingFromNodeId(null);
            setConnectingLineEnd(null);
          }}
          onContextMenu={(e) => {
            // Handle context menu for Stage (empty space)
            // Prevent default context menu
            e.evt.preventDefault();

            // If we are over a node or section, that handler will have fired first and called stopPropagation?
            // Actually, Konva event bubbling: Node -> Group -> Layer -> Stage.
            // If Node/Group handler calls cancelBubble, Stage handler won't see it?
            // Correct.

            // So this handler is for when we clicked on Stage background.
            setContextMenu({ x: e.evt.clientX, y: e.evt.clientY });
          }}
          style={{ cursor: getCursorStyle() }}
        >
          {/* Background Layer */}
          <Layer>
            <Rect
              x={-viewport.x / viewport.scale - 5000}
              y={-viewport.y / viewport.scale - 5000}
              width={10000}
              height={10000}
              fill="#FAFAFA"
            />
            {/* Infinite Dot Grid - Optimized with single Shape */}
            <GridBackground viewport={viewport} dimensions={dimensions} />
          </Layer>

          {/* Content Layer */}
          <Layer>
            {/* Sections */}
            {visibleSections.map((section) => {
              const sectionNodes = visibleNodes.filter(n => n.sectionId === section.id);
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
                    e.cancelBubble = true; // Stop propagation to stage
                    setContextMenu({ x: e.evt.clientX, y: e.evt.clientY, sectionId: section.id });
                  }}
                >
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
                  <Rect
                    width={contentWidth}
                    height={headerHeight}
                    fill="#FFFFFF"
                    cornerRadius={[12, 12, 0, 0]}
                    onClick={() => {
                      setCanvasSections(prev =>
                        prev.map(s => s.id === section.id ? { ...s, isCollapsed: !s.isCollapsed } : s)
                      );
                    }}
                  />
                  <Text x={16} y={16} text="🌱" fontSize={18} />
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

            {/* Phase 2: Temporary Connection Line */}
            {connectingFromNodeId && connectingLineEnd && (() => {
              const sourceNode = visibleNodes.find(n => n.id === connectingFromNodeId);
              if (!sourceNode) return null;

              const x1 = sourceNode.x + (sourceNode.width || 280);
              const y1 = sourceNode.y + ((sourceNode.height || 200) / 2);
              const x2 = connectingLineEnd.x;
              const y2 = connectingLineEnd.y;
              const controlOffset = Math.max(Math.abs(x2 - x1) * 0.4, 50);

              return (
                <Line
                  points={[x1, y1, x1 + controlOffset, y1, x2 - controlOffset, y2, x2, y2]}
                  stroke="#3B82F6"
                  strokeWidth={2}
                  tension={0.5}
                  bezier
                  dash={[8, 4]}
                  listening={false}
                />
              );
            })()}

            {/* Nodes - Using culledNodes for viewport culling optimization */}
            {culledNodes.map((node) => {
              if (node.sectionId) {
                const section = visibleSections.find(s => s.id === node.sectionId);
                if (section?.isCollapsed) return null;
              }

              return (
                <KnowledgeNode
                  key={node.id}
                  node={node}

                  isSelected={selectedNodeIds.has(node.id)}
                  isHighlighted={highlightedNodeId === node.id}
                  isMergeTarget={mergeTargetNodeId === node.id}
                  isHovered={hoveredNodeId === node.id}
                  isConnecting={connectingFromNodeId === node.id}
                  isConnectTarget={connectingFromNodeId !== null && connectingFromNodeId !== node.id}
                  isActiveThinking={activeThinkingId === node.id}
                  isSynthesisSource={pendingSynthesisResult?.sourceNodeIds?.includes(node.id) ?? false}
                  isDraggable={toolMode === 'select' && !isSpacePressed}
                  onSelect={(e) => handleNodeSelect(node.id, e)}
                  onClick={() => {
                    // Thinking Graph: Set as active thinking node when clicked
                    if (node.type === 'thinking_step' || node.type === 'thinking_branch') {
                      setActiveThinkingId(node.id);
                    }
                    onNodeClick?.(node);
                  }}
                  onDoubleClick={() => {
                    // Phase 1: Handle double-click for source nodes (drill-down)
                    if (node.subType === 'source' && node.sourceId) {
                      onOpenSource?.(node.sourceId, node.sourcePage);
                    } else {
                      setEditingNodeId(node.id);
                    }
                    onNodeDoubleClick?.(node);
                  }}
                  onLinkBack={() => {
                    // Phase 1: Navigate to source document
                    if (node.sourceId) {
                      onOpenSource?.(node.sourceId, node.sourcePage);
                    }
                  }}
                  onDragStart={handleNodeDragStart(node.id)}
                  onDragMove={(e) => {
                    handleNodeDragMove(node.id)(e);
                    handleNodeDragMoveWithMerge(e);
                  }}
                  onDragEnd={(e) => {
                    handleNodeDragEnd(node.id)(e);
                    handleNodeDragEndWithMerge(e);
                  }}
                  onContextMenu={(e) => {
                    e.evt.preventDefault();
                    e.cancelBubble = true; // Stop propagation to stage
                    setContextMenu({ x: e.evt.clientX, y: e.evt.clientY, nodeId: node.id });
                  }}
                  onConnectionStart={() => {
                    // Phase 2: Start connection drag
                    setConnectingFromNodeId(node.id);
                  }}
                  onMouseEnter={() => setHoveredNodeId(node.id)}
                  onMouseLeave={() => setHoveredNodeId(null)}
                />
              );
            })}

            {/* Selection Box */}
            {selectionRect && (
              <Rect
                x={selectionRect.x}
                y={selectionRect.y}
                width={selectionRect.width}
                height={selectionRect.height}
                fill="rgba(59, 130, 246, 0.1)"
                stroke="#3B82F6"
                strokeWidth={1}
                listening={false}
              />
            )}

            {/* Drag Preview */}
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
                <Rect y={0} width={280} height={4} fill="#3B82F6" cornerRadius={[12, 12, 0, 0]} />
                <Text x={16} y={16} width={280 - 32} text="AI Insight" fontSize={12} fontStyle="bold" fill="#1F2937" />
                <Text x={16} y={40} width={280 - 32} height={130} text={dragPreview.content} fontSize={12} fill="#6B7280" wrap="word" ellipsis />
              </Group>
            )}
          </Layer>

          {/* Synthesis Connection Lines */}
          {pendingSynthesisResult && pendingSynthesisResult.sourceNodeIds && (
            <Layer>
              {pendingSynthesisResult.sourceNodeIds.map(sourceId => {
                const sourceNode = nodes.find(n => n.id === sourceId);
                if (!sourceNode) return null;

                // Position is now in canvas coordinates directly
                const targetX = pendingSynthesisResult.position.x;
                const targetY = pendingSynthesisResult.position.y;

                // Source center
                const sourceX = sourceNode.x + (sourceNode.width || 280) / 2;
                const sourceY = sourceNode.y + (sourceNode.height || 200) / 2;

                return (
                  <Line
                    key={`synthesis-line-${sourceId}`}
                    points={[sourceX, sourceY, targetX + 160, targetY]}
                    stroke="#6366F1"
                    strokeWidth={2}
                    dash={[10, 10]}
                    opacity={0.6}
                    listening={false}
                  />
                );
              })}

              {/* Konva Synthesis Node */}
              <Group
                x={pendingSynthesisResult.position.x}
                y={pendingSynthesisResult.position.y}
                draggable
                onDragEnd={(e) => {
                  setPendingSynthesisResult(prev => prev ? {
                    ...prev,
                    position: { x: e.target.x(), y: e.target.y() }
                  } : null);
                }}
              >
                {/* Card Background */}
                <Rect
                  width={320}
                  height={220}
                  fill="white"
                  cornerRadius={16}
                  stroke="#6366F1"
                  strokeWidth={2}
                  shadowColor="rgba(99, 102, 241, 0.3)"
                  shadowBlur={20}
                  shadowOffsetY={8}
                />

                {/* Top Accent Bar */}
                <Rect
                  y={0}
                  width={320}
                  height={6}
                  fill="#6366F1"
                  cornerRadius={[16, 16, 0, 0]}
                />

                {/* AI Icon Background */}
                <Rect
                  x={16}
                  y={16}
                  width={36}
                  height={36}
                  fill="#EEF2FF"
                  cornerRadius={8}
                />
                <Text
                  x={22}
                  y={22}
                  text="✨"
                  fontSize={18}
                />

                {/* Header Text */}
                <Text
                  x={60}
                  y={18}
                  text="Consolidated Insight"
                  fontSize={14}
                  fontStyle="bold"
                  fill="#1F2937"
                />
                <Text
                  x={60}
                  y={35}
                  text="AI GENERATED"
                  fontSize={10}
                  fill="#6366F1"
                  fontStyle="600"
                />

                {/* Confidence Badge */}
                <Rect
                  x={220}
                  y={20}
                  width={90}
                  height={24}
                  fill="transparent"
                  stroke={pendingSynthesisResult.confidence === 'high' ? '#059669' : '#D97706'}
                  strokeWidth={1}
                  cornerRadius={12}
                />
                <Text
                  x={230}
                  y={26}
                  text={`${(pendingSynthesisResult.confidence || 'medium').charAt(0).toUpperCase()}${(pendingSynthesisResult.confidence || 'medium').slice(1)} Conf.`}
                  fontSize={10}
                  fill={pendingSynthesisResult.confidence === 'high' ? '#059669' : '#D97706'}
                />

                {/* Title */}
                <Text
                  x={16}
                  y={65}
                  width={288}
                  text={pendingSynthesisResult.title}
                  fontSize={15}
                  fontStyle="bold"
                  fill="#1F2937"
                  wrap="word"
                />

                {/* Content */}
                <Text
                  x={16}
                  y={90}
                  width={288}
                  height={80}
                  text={pendingSynthesisResult.content}
                  fontSize={12}
                  fill="#4B5563"
                  wrap="word"
                  ellipsis
                />

                {/* Footer */}
                <Rect
                  y={180}
                  width={320}
                  height={40}
                  fill="#F9FAFB"
                  cornerRadius={[0, 0, 16, 16]}
                />
                <Text
                  x={16}
                  y={193}
                  text={`📄 Synthesized from ${pendingSynthesisResult.sourceNodeIds?.length || 2} sources`}
                  fontSize={11}
                  fill="#6B7280"
                />
              </Group>
            </Layer>
          )}
        </Stage>

        {/* Merge Prompt Overlay */}
        {/* Merge Prompt Overlay - Replaced with SynthesisModeMenu */}
        {/* Merge Prompt Overlay */}
        {mergeTargetNodeId && draggedNodeId && (() => {
          const targetNode = nodes.find(n => n.id === mergeTargetNodeId);
          const draggedNode = nodes.find(n => n.id === draggedNodeId);

          let menuPosition;
          if (targetNode && draggedNode) {
            // Calculate midpoint top
            const targetCenterX = targetNode.x + (targetNode.width || 280) / 2;
            const draggedCenterX = draggedNode.x + (draggedNode.width || 280) / 2;
            const midX = (targetCenterX + draggedCenterX) / 2;

            // Use the higher (smaller Y) of the two nodes as the anchor for top
            const minY = Math.min(targetNode.y, draggedNode.y);

            // Convert to screen coordinates
            const screenX = midX * viewport.scale + viewport.x;
            const screenY = minY * viewport.scale + viewport.y - 20; // 20px padding above

            menuPosition = { x: screenX, y: screenY };
          }

          return (
            <SynthesisModeMenu
              isSynthesizing={isSynthesizing}
              onSelect={handleSynthesize}
              onCancel={handleCancelMerge}
              position={menuPosition}
            />
          );
        })()}

        {/* Node Editor Overlay */}
        {editingNodeId && (() => {
          const node = nodes.find(n => n.id === editingNodeId);
          if (!node) return null;
          return (
            <NodeEditor
              key={node.id}
              node={node}
              viewport={viewport}
              onSave={handleNodeSave}
              onCancel={handleNodeEditCancel}
            />
          );
        })()}

        {/* Loading Overlay for Synthesis */}
        {isSynthesizing && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundColor: 'rgba(255,255,255,0.6)',
              backdropFilter: 'blur(2px)',
              zIndex: 1900,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Spinner size="lg" style={{ color: '#8B5CF6' }} />
          </div>
        )}

        {/* Generation Outputs Overlay - Renders completed generation tasks at their positions */}
        <GenerationOutputsOverlay viewport={viewport} />

        {/* Inspiration Dock - Shown when canvas is empty, no outputs exist, but documents are uploaded */}
        {visibleNodes.length === 0 && documents.length > 0 && !hasCompletedOutputs && (
          <InspirationDock />
        )}

        {/* Synthesis Connection Lines - Moved inside Stage */}

        {/* Synthesis Action Buttons - Floating overlay anchored to Konva node */}
        {pendingSynthesisResult && (() => {
          // Convert canvas position to screen position
          const screenX = pendingSynthesisResult.position.x * viewport.scale + viewport.x;
          const screenY = (pendingSynthesisResult.position.y + 220) * viewport.scale + viewport.y; // Below the 220px tall card

          return (
            <div
              style={{
                position: 'absolute',
                left: screenX,
                top: screenY + 8,
                transform: 'translateX(-50%)',
                display: 'flex',
                gap: 8,
                zIndex: 2100,
                backgroundColor: 'white',
                padding: 8,
                borderRadius: 8,
                boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
              }}
            >
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setPendingSynthesisResult(null)}
                style={{ color: colors.text.secondary }}
              >
                Discard
              </Button>
              <Button
                size="sm"
                variant="primary"
                onClick={() => {
                  // Create a new canvas node from the synthesis result
                  const newNode: CanvasNode = {
                    id: pendingSynthesisResult.id,
                    type: 'synthesis',
                    title: pendingSynthesisResult.title,
                    content: pendingSynthesisResult.content +
                      (pendingSynthesisResult.recommendation ? `\n\n**Recommendation:** ${pendingSynthesisResult.recommendation}` : '') +
                      (pendingSynthesisResult.keyRisk ? `\n\n**Key Risk:** ${pendingSynthesisResult.keyRisk}` : ''),
                    x: pendingSynthesisResult.position.x,
                    y: pendingSynthesisResult.position.y,
                    width: 320,
                    height: 220,
                    color: '#EEF2FF',
                    tags: pendingSynthesisResult.themes || [],
                    viewType: 'free',
                    subType: 'insight',
                  };

                  if (onNodesChange) {
                    onNodesChange([...nodes, newNode]);
                  }
                  setPendingSynthesisResult(null);
                }}
                style={{
                  textTransform: 'none',
                  backgroundColor: '#6366F1',
                  borderRadius: 8,
                }}
              >
                Add to Board
              </Button>
            </div>
          );
        })()}
      </div>
    </div>
  );
}

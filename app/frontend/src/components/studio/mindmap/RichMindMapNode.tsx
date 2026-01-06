/**
 * RichMindMapNode - Rich Card-based Mind Map Node
 * 
 * Features:
 * - Multiple visual states: root, generating, complete, pending
 * - Animated status indicators
 * - Drop shadows and rounded corners
 * - Tags/chips rendering for categorical data
 * - Performance optimizations with LOD
 */

import React, { useEffect, useRef, useMemo } from 'react';
import { Group, Rect, Text, Circle, Line } from 'react-konva';
import Konva from 'konva';
import { MindmapNode as MindmapNodeType } from '@/lib/api';
import { mindmapCardTokens as tokens } from '@/components/ui/tokens';

// ============================================================================
// Types
// ============================================================================

export type NodeVariant = 'root' | 'generating' | 'complete' | 'pending';

interface RichMindMapNodeProps {
  node: MindmapNodeType;
  isSelected?: boolean;
  lodLevel?: 'full' | 'labels' | 'simple';
  shouldAnimate?: boolean;
  onDoubleClick?: (nodeId: string) => void;
  onClick?: (nodeId: string, e: Konva.KonvaEventObject<MouseEvent>) => void;
  onDragEnd?: (nodeId: string, x: number, y: number) => void;
}

// ============================================================================
// Helper Components
// ============================================================================

/**
 * Animated processing dots (3 dots with staggered opacity)
 */
const ProcessingDots: React.FC<{ x: number; y: number; color: string }> = ({ x, y, color }) => {
  const dot1Ref = useRef<Konva.Circle>(null);
  const dot2Ref = useRef<Konva.Circle>(null);
  const dot3Ref = useRef<Konva.Circle>(null);

  useEffect(() => {
    const animate = (ref: React.RefObject<Konva.Circle | null>, delay: number) => {
      if (!ref.current) return;

      const anim = () => {
        ref.current?.to({
          opacity: 0.3,
          duration: tokens.animation.dots,
          easing: Konva.Easings.EaseInOut,
          onFinish: () => {
            ref.current?.to({
              opacity: 1,
              duration: tokens.animation.dots,
              easing: Konva.Easings.EaseInOut,
              onFinish: anim,
            });
          },
        });
      };

      setTimeout(anim, delay * 1000);
    };

    animate(dot1Ref, 0);
    animate(dot2Ref, tokens.animation.dots);
    animate(dot3Ref, tokens.animation.dots * 2);
  }, []);

  return (
    <Group x={x} y={y}>
      <Circle ref={dot1Ref} x={0} y={0} radius={3} fill={color} />
      <Circle ref={dot2Ref} x={10} y={0} radius={3} fill={color} />
      <Circle ref={dot3Ref} x={20} y={0} radius={3} fill={color} />
    </Group>
  );
};

/**
 * Skeleton loading bars for generating state
 */
const SkeletonBars: React.FC<{ x: number; y: number; width: number }> = ({ x, y, width }) => {
  const bar1Ref = useRef<Konva.Rect>(null);
  const bar2Ref = useRef<Konva.Rect>(null);

  useEffect(() => {
    const animate = (ref: React.RefObject<Konva.Rect | null>) => {
      if (!ref.current) return;

      const pulse = () => {
        ref.current?.to({
          opacity: 0.3,
          duration: tokens.animation.skeleton / 2,
          easing: Konva.Easings.EaseInOut,
          onFinish: () => {
            ref.current?.to({
              opacity: 0.7,
              duration: tokens.animation.skeleton / 2,
              easing: Konva.Easings.EaseInOut,
              onFinish: pulse,
            });
          },
        });
      };
      pulse();
    };

    animate(bar1Ref);
    setTimeout(() => animate(bar2Ref), 200);
  }, []);

  return (
    <Group x={x} y={y}>
      <Rect
        ref={bar1Ref}
        x={0}
        y={0}
        width={width * 0.7}
        height={12}
        fill="#E5E7EB"
        cornerRadius={4}
        opacity={0.7}
      />
      <Rect
        ref={bar2Ref}
        x={0}
        y={20}
        width={width * 0.5}
        height={10}
        fill="#E5E7EB"
        cornerRadius={4}
        opacity={0.5}
      />
    </Group>
  );
};

/**
 * Checkmark icon for completed state
 */
const CheckmarkIcon: React.FC<{ x: number; y: number; size?: number }> = ({ x, y, size = 16 }) => {
  return (
    <Group x={x} y={y}>
      <Circle
        x={size / 2}
        y={size / 2}
        radius={size / 2}
        fill={tokens.status.success}
      />
      <Line
        points={[
          size * 0.25, size * 0.5,
          size * 0.45, size * 0.7,
          size * 0.75, size * 0.3,
        ]}
        stroke={tokens.text.onDark}
        strokeWidth={2}
        lineCap="round"
        lineJoin="round"
      />
    </Group>
  );
};

/**
 * Brain icon for root node (simplified)
 */
const BrainIcon: React.FC<{ x: number; y: number; size?: number; color?: string }> = ({
  x, y, size = 32, color = tokens.root.iconColor
}) => {
  // Simplified brain icon using basic shapes
  return (
    <Group x={x} y={y}>
      {/* Left hemisphere */}
      <Circle x={size * 0.35} y={size * 0.4} radius={size * 0.3} stroke={color} strokeWidth={2} />
      <Circle x={size * 0.3} y={size * 0.6} radius={size * 0.2} stroke={color} strokeWidth={2} />
      {/* Right hemisphere */}
      <Circle x={size * 0.65} y={size * 0.4} radius={size * 0.3} stroke={color} strokeWidth={2} />
      <Circle x={size * 0.7} y={size * 0.6} radius={size * 0.2} stroke={color} strokeWidth={2} />
      {/* Center connection */}
      <Line
        points={[size * 0.5, size * 0.15, size * 0.5, size * 0.85]}
        stroke={color}
        strokeWidth={2}
        lineCap="round"
      />
    </Group>
  );
};

/**
 * Tag/Chip component for categorical data
 */
const TagChip: React.FC<{
  x: number;
  y: number;
  text: string;
  maxWidth?: number;
}> = ({ x, y, text, maxWidth = 80 }) => {
  const displayText = text.length > 12 ? text.slice(0, 10) + '...' : text;
  const chipWidth = Math.min(displayText.length * 7 + 16, maxWidth);

  return (
    <Group x={x} y={y}>
      <Rect
        width={chipWidth}
        height={20}
        fill={tokens.tags.bg}
        stroke={tokens.tags.border}
        strokeWidth={1}
        cornerRadius={10}
      />
      <Text
        x={8}
        y={4}
        text={displayText}
        fontSize={10}
        fill={tokens.tags.text}
        fontStyle="500"
      />
    </Group>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export const RichMindMapNode: React.FC<RichMindMapNodeProps> = ({
  node,
  isSelected = false,
  lodLevel = 'full',
  shouldAnimate = true,
  onDoubleClick,
  onClick,
  onDragEnd,
}) => {
  const groupRef = useRef<Konva.Group>(null);
  const glowRef = useRef<Konva.Rect>(null);

  const width = node.width || 200;
  const height = node.height || 80;
  const isRoot = node.depth === 0;

  // Determine node variant based on status and depth
  const variant: NodeVariant = useMemo(() => {
    if (isRoot) return 'root';
    switch (node.status) {
      case 'generating': return 'generating';
      case 'complete': return 'complete';
      case 'error': return 'complete'; // Show as complete with error indication
      default: return 'pending';
    }
  }, [isRoot, node.status]);

  // Root node dimensions
  const rootWidth = 280;
  const rootHeight = 160;
  const finalWidth = isRoot ? rootWidth : width;
  const finalHeight = isRoot ? rootHeight : height;

  // Parse tags from content (comma-separated)
  const tags = useMemo(() => {
    if (!node.content || variant !== 'complete') return [];
    const items = node.content.split(',').map(s => s.trim()).filter(Boolean);
    // Only treat as tags if there are multiple short items
    if (items.length >= 2 && items.every(item => item.length < 30)) {
      return items.slice(0, 4); // Max 4 tags
    }
    return [];
  }, [node.content, variant]);

  // Growth animation on mount
  useEffect(() => {
    if (!groupRef.current || !shouldAnimate) return;

    groupRef.current.scale({ x: 0, y: 0 });
    groupRef.current.to({
      scaleX: 1,
      scaleY: 1,
      duration: 0.4,
      easing: Konva.Easings.BackEaseOut,
    });
  }, [shouldAnimate]);

  // Root node glow animation
  useEffect(() => {
    if (variant !== 'root' || !glowRef.current || !shouldAnimate) return;

    const pulseGlow = () => {
      glowRef.current?.to({
        shadowOpacity: 0.5,
        duration: tokens.animation.pulse / 2,
        easing: Konva.Easings.EaseInOut,
        onFinish: () => {
          glowRef.current?.to({
            shadowOpacity: 0.2,
            duration: tokens.animation.pulse / 2,
            easing: Konva.Easings.EaseInOut,
            onFinish: pulseGlow,
          });
        },
      });
    };
    pulseGlow();
  }, [variant, shouldAnimate]);

  // Get variant-specific styles
  const getVariantStyles = () => {
    switch (variant) {
      case 'root':
        return {
          fill: tokens.card.bgRoot,
          stroke: tokens.card.borderActive,
          strokeWidth: 3,
          dash: undefined,
          opacity: 1,
          shadowBlur: 20,
          shadowColor: tokens.root.glowColor,
          shadowOpacity: 0.3,
        };
      case 'generating':
        return {
          fill: tokens.card.bg,
          stroke: tokens.card.borderActive,
          strokeWidth: 2,
          dash: [8, 4],
          opacity: 0.85,
          shadowBlur: 8,
          shadowColor: 'black',
          shadowOpacity: 0.08,
        };
      case 'complete':
        return {
          fill: tokens.card.bg,
          stroke: '#E5E7EB',
          strokeWidth: 1,
          dash: undefined,
          opacity: 1,
          shadowBlur: 12,
          shadowColor: 'black',
          shadowOpacity: 0.08,
        };
      case 'pending':
        return {
          fill: tokens.card.bg,
          stroke: tokens.card.borderPending,
          strokeWidth: 2,
          dash: [6, 4],
          opacity: 0.5,
          shadowBlur: 4,
          shadowColor: 'black',
          shadowOpacity: 0.04,
        };
    }
  };

  const styles = getVariantStyles();

  // Simple render for low LOD
  if (lodLevel === 'simple') {
    return (
      <Group
        ref={groupRef}
        x={node.x}
        y={node.y}
        draggable
        onClick={(e) => onClick?.(node.id, e)}
        onTap={(e) => onClick?.(node.id, e)}
        onDragEnd={(e) => onDragEnd?.(node.id, e.target.x(), e.target.y())}
      >
        <Rect
          width={finalWidth}
          height={finalHeight}
          fill={styles.fill}
          stroke={styles.stroke}
          strokeWidth={styles.strokeWidth}
          cornerRadius={tokens.card.cornerRadius}
          opacity={styles.opacity}
        />
      </Group>
    );
  }

  return (
    <Group
      ref={groupRef}
      x={node.x}
      y={node.y}
      draggable
      onClick={(e) => onClick?.(node.id, e)}
      onTap={(e) => onClick?.(node.id, e)}
      onDblClick={() => onDoubleClick?.(node.id)}
      onDblTap={() => onDoubleClick?.(node.id)}
      onDragEnd={(e) => onDragEnd?.(node.id, e.target.x(), e.target.y())}
    >

      {/* Selection indicator */}
      {isSelected && (
        <Rect
          x={-4}
          y={-4}
          width={finalWidth + 8}
          height={finalHeight + 8}
          stroke={tokens.card.borderActive}
          strokeWidth={2}
          cornerRadius={tokens.card.cornerRadius + 4}
          dash={[8, 4]}
        />
      )}

      {/* Card background with shadow */}
      <Rect
        ref={variant === 'root' ? glowRef : undefined}
        width={finalWidth}
        height={finalHeight}
        fill={styles.fill}
        stroke={styles.stroke}
        strokeWidth={styles.strokeWidth}
        dash={styles.dash}
        cornerRadius={tokens.card.cornerRadius}
        opacity={styles.opacity}
        shadowColor={styles.shadowColor}
        shadowBlur={styles.shadowBlur}
        shadowOpacity={styles.shadowOpacity}
        shadowOffsetY={4}
      />

      {/* ============ ROOT VARIANT ============ */}
      {variant === 'root' && (
        <>
          {/* Brain icon */}
          <BrainIcon
            x={(finalWidth - 40) / 2}
            y={24}
            size={40}
            color={tokens.root.iconColor}
          />

          {/* Title */}
          <Text
            x={16}
            y={74}
            width={finalWidth - 32}
            text={node.label}
            fontSize={18}
            fontStyle="bold"
            fill={tokens.text.title}
            align="center"
            wrap="word"
            ellipsis
          />

          {/* Status bar */}
          <Rect
            x={16}
            y={finalHeight - 36}
            width={finalWidth - 32}
            height={24}
            fill={
              node.status === 'error' ? tokens.status.errorBg :
                node.status === 'complete' ? tokens.status.successBg :
                  tokens.status.processingBg
            }
            cornerRadius={6}
          />
          <Text
            x={32}
            y={finalHeight - 31}
            text={
              node.status === 'error' ? 'ERROR' :
                node.status === 'complete' ? 'READY' :
                  'PROCESSING'
            }
            fontSize={10}
            fontStyle="600"
            fill={
              node.status === 'error' ? tokens.status.error :
                node.status === 'complete' ? tokens.status.success :
                  tokens.status.processing
            }
            letterSpacing={0.5}
          />
          {node.status !== 'complete' && node.status !== 'error' && (
            <ProcessingDots
              x={finalWidth - 56}
              y={finalHeight - 24}
              color={tokens.status.processing}
            />
          )}
        </>
      )}

      {/* ============ GENERATING VARIANT ============ */}
      {variant === 'generating' && (
        <>
          <SkeletonBars x={16} y={16} width={finalWidth - 32} />

          {/* Small generating indicator */}
          <Text
            x={16}
            y={finalHeight - 20}
            text="Generating..."
            fontSize={10}
            fill={tokens.text.muted}
            fontStyle="italic"
          />
        </>
      )}

      {/* ============ COMPLETE VARIANT ============ */}
      {variant === 'complete' && (
        <>
          {/* Checkmark icon */}
          <CheckmarkIcon x={finalWidth - 24} y={8} size={16} />

          {/* Title */}
          <Text
            x={16}
            y={16}
            width={finalWidth - 48}
            text={node.label}
            fontSize={14}
            fontStyle="bold"
            fill={tokens.text.title}
            wrap="word"
            ellipsis
          />

          {/* Content or Tags */}
          {tags.length > 0 ? (
            <Group x={16} y={lodLevel === 'labels' ? 40 : 44}>
              {tags.map((tag, idx) => (
                <TagChip
                  key={idx}
                  x={(idx % 2) * 85}
                  y={Math.floor(idx / 2) * 24}
                  text={tag}
                  maxWidth={80}
                />
              ))}
            </Group>
          ) : (
            lodLevel === 'full' && node.content && (
              <Text
                x={16}
                y={40}
                width={finalWidth - 32}
                height={finalHeight - 56}
                text={node.content}
                fontSize={11}
                fill={tokens.text.content}
                wrap="word"
                ellipsis
              />
            )
          )}
        </>
      )}

      {/* ============ PENDING VARIANT ============ */}
      {variant === 'pending' && (
        <>
          {/* Title placeholder */}
          <Text
            x={16}
            y={finalHeight / 2 - 16}
            width={finalWidth - 32}
            text={node.label || 'Waiting...'}
            fontSize={12}
            fill={tokens.text.muted}
            align="center"
          />

          {/* Loading dots */}
          <ProcessingDots
            x={(finalWidth - 20) / 2}
            y={finalHeight / 2 + 8}
            color={tokens.text.muted}
          />
        </>
      )}
    </Group>
  );
};

export default RichMindMapNode;


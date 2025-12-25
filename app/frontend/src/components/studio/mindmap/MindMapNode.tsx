import React, { useEffect, useRef } from 'react';
import { Group, Rect, Text, Circle } from 'react-konva';
import Konva from 'konva';
import { MindmapNode as MindmapNodeType } from '@/lib/api';

interface MindMapNodeProps {
  node: MindmapNodeType;
  onClick?: (nodeId: string) => void;
}

export const MindMapNode: React.FC<MindMapNodeProps> = ({ node, onClick }) => {
  const groupRef = useRef<Konva.Group>(null);

  useEffect(() => {
    if (groupRef.current) {
      // Growth animation on mount
      groupRef.current.scale({ x: 0, y: 0 });
      groupRef.current.to({
        scaleX: 1,
        scaleY: 1,
        duration: 0.5,
        easing: Konva.Easings.BackEaseOut,
      });
    }
  }, []);

  const isRoot = node.depth === 0;
  const width = node.width || 200;
  const height = node.height || 80;
  
  // Color mapping based on node color/depth
  const getColors = (color: string) => {
    switch (color) {
      case 'primary': return { fill: '#EFF6FF', stroke: '#3B82F6', text: '#1E3A8A' }; // Blue
      case 'blue': return { fill: '#EFF6FF', stroke: '#3B82F6', text: '#1E3A8A' };
      case 'green': return { fill: '#ECFDF5', stroke: '#10B981', text: '#064E3B' };
      case 'orange': return { fill: '#FFF7ED', stroke: '#F97316', text: '#7C2D12' };
      case 'purple': return { fill: '#F5F3FF', stroke: '#8B5CF6', text: '#4C1D95' };
      case 'pink': return { fill: '#FDF2F8', stroke: '#EC4899', text: '#831843' };
      default: return { fill: '#FFFFFF', stroke: '#9CA3AF', text: '#374151' };
    }
  };

  const colors = getColors(node.color);

  return (
    <Group
      ref={groupRef}
      x={node.x}
      y={node.y}
      width={width}
      height={height}
      onClick={() => onClick?.(node.id)}
      onTap={() => onClick?.(node.id)}
    >
      {/* Node Shape */}
      <Rect
        width={width}
        height={height}
        fill={colors.fill}
        stroke={colors.stroke}
        strokeWidth={isRoot ? 3 : 2}
        cornerRadius={12}
        shadowColor="black"
        shadowBlur={10}
        shadowOpacity={0.1}
        shadowOffsetY={4}
      />

      {/* Label */}
      <Text
        x={16}
        y={16}
        width={width - 32}
        text={node.label}
        fontSize={isRoot ? 16 : 14}
        fontStyle="bold"
        fill={colors.text}
        wrap="word"
        ellipsis={true}
      />

      {/* Content Preview (truncated) */}
      {!isRoot && node.content && (
        <Text
          x={16}
          y={40}
          width={width - 32}
          height={height - 48}
          text={node.content}
          fontSize={11}
          fill={colors.text}
          opacity={0.8}
          wrap="word"
          ellipsis={true}
        />
      )}

      {/* Status Indicator (if generating) */}
      {node.status === 'generating' && (
        <Circle
          x={width - 12}
          y={12}
          radius={4}
          fill={colors.stroke}
          opacity={0.5}
        />
      )}
    </Group>
  );
};

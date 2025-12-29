'use client';

/**
 * Canvas Section Component (Konva.Group)
 * Represents a container for grouping related nodes
 */

import { Group, Rect, Text } from 'react-konva';
import Konva from 'konva';
import { CanvasSection as CanvasSectionType, CanvasNode } from '@/lib/api';

interface CanvasSectionComponentProps {
  section: CanvasSectionType;
  nodes: CanvasNode[];
  isSelected: boolean;
  onSelect: () => void;
  onDragEnd: (e: Konva.KonvaEventObject<DragEvent>) => void;
  onToggleCollapse: () => void;
  renderNode: (node: CanvasNode, offsetX: number, offsetY: number) => React.ReactNode;
}

export default function CanvasSectionComponent({
  section,
  nodes,
  isSelected,
  onSelect,
  onDragEnd,
  onToggleCollapse,
  renderNode,
}: CanvasSectionComponentProps) {
  // Calculate section bounds from nodes
  const sectionNodes = nodes.filter(n => section.nodeIds.includes(n.id));
  
  // Header dimensions
  const headerHeight = 48;
  const padding = 16;
  
  // Calculate content bounds
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  sectionNodes.forEach(node => {
    minX = Math.min(minX, node.x);
    minY = Math.min(minY, node.y);
    maxX = Math.max(maxX, node.x + (node.width || 280));
    maxY = Math.max(maxY, node.y + (node.height || 200));
  });
  
  const contentWidth = sectionNodes.length > 0 ? maxX - minX + padding * 2 : 400;
  const contentHeight = sectionNodes.length > 0 ? maxY - minY + padding * 2 : 100;
  const totalHeight = headerHeight + (section.isCollapsed ? 0 : contentHeight);

  return (
    <Group
      x={section.x}
      y={section.y}
      draggable
      onDragEnd={onDragEnd}
      onClick={onSelect}
      onTap={onSelect}
    >
      {/* Section Background */}
      <Rect
        width={contentWidth}
        height={totalHeight}
        fill="#F3F4F6"
        cornerRadius={12}
        stroke={isSelected ? '#3B82F6' : '#E5E7EB'}
        strokeWidth={isSelected ? 2 : 1}
        shadowColor="black"
        shadowBlur={8}
        shadowOpacity={0.08}
        shadowOffsetY={2}
      />

      {/* Header Background */}
      <Rect
        width={contentWidth}
        height={headerHeight}
        fill="#FFFFFF"
        cornerRadius={[12, 12, 0, 0]}
        onClick={onToggleCollapse}
        onTap={onToggleCollapse}
      />

      {/* Section Icon */}
      <Text
        x={16}
        y={16}
        text={section.viewType === 'thinking' ? '🌱' : '📁'}
        fontSize={18}
      />

      {/* Section Title */}
      <Text
        x={48}
        y={18}
        width={contentWidth - 120}
        text={section.title}
        fontSize={14}
        fontStyle="bold"
        fill="#1F2937"
        wrap="word"
        ellipsis
      />

      {/* Collapse/Expand Icon */}
      <Text
        x={contentWidth - 40}
        y={18}
        text={section.isCollapsed ? '▶' : '▼'}
        fontSize={12}
        fill="#6B7280"
        onClick={onToggleCollapse}
        onTap={onToggleCollapse}
      />

      {/* Node Count */}
      <Text
        x={16}
        y={headerHeight - 20}
        text={`${section.nodeIds.length} 个节点`}
        fontSize={11}
        fill="#9CA3AF"
      />

      {/* Content (only render when expanded) */}
      {!section.isCollapsed && sectionNodes.length > 0 && (
        <Group y={headerHeight}>
          {sectionNodes.map((node) => {
            // Calculate relative position within section
            const offsetX = node.x - minX + padding;
            const offsetY = node.y - minY + padding;
            return renderNode(node, offsetX, offsetY);
          })}
        </Group>
      )}
    </Group>
  );
}

























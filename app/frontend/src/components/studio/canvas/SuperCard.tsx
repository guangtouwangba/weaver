'use client';

/**
 * Super Card Components for Magic Cursor Generation Results
 * 
 * These are distinct result containers that appear on the canvas after
 * Magic Cursor generation completes:
 * - DocumentCard: For articles with expandable sections
 * - TicketCard: For action lists with interactive checkboxes
 */

import React, { useCallback } from 'react';
import { Group, Rect, Text, Circle } from 'react-konva';
import Konva from 'konva';
import { ArticleData, ActionListData, ActionItem } from '@/lib/api';

// ============================================================================
// Shared Types & Constants
// ============================================================================

export interface SuperCardPosition {
  x: number;
  y: number;
}

const CARD_STYLES = {
  document: {
    headerBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    headerColor: '#667eea',
    borderColor: '#667eea',
    bgColor: '#FAFBFF',
    iconBg: '#667eea',
    width: 320,
    minHeight: 160,
  },
  ticket: {
    headerBg: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
    headerColor: '#f59e0b',
    borderColor: '#f59e0b',
    bgColor: '#FFFCF5',
    iconBg: '#f59e0b',
    width: 280,
    minHeight: 140,
  },
};

// ============================================================================
// Document Card (Article Output)
// ============================================================================

interface DocumentCardProps {
  data: ArticleData;
  position: SuperCardPosition;
  isSelected?: boolean;
  onClick?: () => void;
  onDragMove?: (pos: SuperCardPosition) => void;
  onDragEnd?: (pos: SuperCardPosition) => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  data,
  position,
  isSelected = false,
  onClick,
  onDragMove,
  onDragEnd,
}) => {
  const style = CARD_STYLES.document;
  
  // Calculate height based on content
  const headerHeight = 48;
  const sectionPreviewHeight = 28;
  const padding = 12;
  const sectionsToShow = Math.min(data.sections.length, 3);
  const contentHeight = sectionsToShow * sectionPreviewHeight + (sectionsToShow > 0 ? padding : 0);
  const totalHeight = Math.max(headerHeight + contentHeight + padding, style.minHeight);
  
  const handleDragEnd = useCallback((e: Konva.KonvaEventObject<DragEvent>) => {
    const node = e.target;
    onDragEnd?.({ x: node.x(), y: node.y() });
  }, [onDragEnd]);
  
  const handleDragMove = useCallback((e: Konva.KonvaEventObject<DragEvent>) => {
    const node = e.target;
    onDragMove?.({ x: node.x(), y: node.y() });
  }, [onDragMove]);

  return (
    <Group
      x={position.x}
      y={position.y}
      draggable
      onDragEnd={handleDragEnd}
      onDragMove={handleDragMove}
      onClick={onClick}
      onTap={onClick}
    >
      {/* Shadow */}
      <Rect
        x={4}
        y={4}
        width={style.width}
        height={totalHeight}
        fill="rgba(0,0,0,0.08)"
        cornerRadius={12}
      />
      
      {/* Card Background */}
      <Rect
        x={0}
        y={0}
        width={style.width}
        height={totalHeight}
        fill={style.bgColor}
        stroke={isSelected ? style.borderColor : 'rgba(102, 126, 234, 0.3)'}
        strokeWidth={isSelected ? 2 : 1}
        cornerRadius={12}
      />
      
      {/* Header Bar */}
      <Rect
        x={0}
        y={0}
        width={style.width}
        height={headerHeight}
        fill={style.headerColor}
        cornerRadius={[12, 12, 0, 0]}
      />
      
      {/* Document Icon */}
      <Circle
        x={24}
        y={headerHeight / 2}
        radius={14}
        fill="rgba(255,255,255,0.2)"
      />
      <Text
        x={16}
        y={headerHeight / 2 - 8}
        text="📄"
        fontSize={14}
      />
      
      {/* Title */}
      <Text
        x={48}
        y={14}
        width={style.width - 60}
        text={data.title || 'Generated Article'}
        fontSize={14}
        fontStyle="bold"
        fill="#FFFFFF"
        ellipsis={true}
        wrap="none"
      />
      
      {/* Section Previews */}
      {data.sections.slice(0, 3).map((section, index) => (
        <React.Fragment key={index}>
          <Text
            x={padding}
            y={headerHeight + padding + index * sectionPreviewHeight}
            width={style.width - padding * 2}
            text={`• ${section.heading}`}
            fontSize={12}
            fill="#4B5563"
            ellipsis={true}
            wrap="none"
          />
        </React.Fragment>
      ))}
      
      {/* More sections indicator */}
      {data.sections.length > 3 && (
        <Text
          x={padding}
          y={headerHeight + padding + 3 * sectionPreviewHeight}
          text={`+${data.sections.length - 3} more sections`}
          fontSize={11}
          fill="#9CA3AF"
          fontStyle="italic"
        />
      )}
      
      {/* Click hint */}
      <Text
        x={style.width - 70}
        y={totalHeight - 20}
        text="Click to open"
        fontSize={10}
        fill="#9CA3AF"
      />
    </Group>
  );
};

// ============================================================================
// Ticket Card (Action List Output)
// ============================================================================

interface TicketCardProps {
  data: ActionListData;
  position: SuperCardPosition;
  isSelected?: boolean;
  onClick?: () => void;
  onToggleItem?: (itemId: string, done: boolean) => void;
  onDragMove?: (pos: SuperCardPosition) => void;
  onDragEnd?: (pos: SuperCardPosition) => void;
}

export const TicketCard: React.FC<TicketCardProps> = ({
  data,
  position,
  isSelected = false,
  onClick,
  onToggleItem,
  onDragMove,
  onDragEnd,
}) => {
  const style = CARD_STYLES.ticket;
  
  // Calculate height based on items
  const headerHeight = 44;
  const itemHeight = 26;
  const padding = 10;
  const itemsToShow = Math.min(data.items.length, 5);
  const contentHeight = itemsToShow * itemHeight + (itemsToShow > 0 ? padding : 0);
  const totalHeight = Math.max(headerHeight + contentHeight + padding, style.minHeight);
  
  const completedCount = data.items.filter(item => item.done).length;
  
  const handleDragEnd = useCallback((e: Konva.KonvaEventObject<DragEvent>) => {
    const node = e.target;
    onDragEnd?.({ x: node.x(), y: node.y() });
  }, [onDragEnd]);
  
  const handleDragMove = useCallback((e: Konva.KonvaEventObject<DragEvent>) => {
    const node = e.target;
    onDragMove?.({ x: node.x(), y: node.y() });
  }, [onDragMove]);
  
  const handleCheckboxClick = useCallback((item: ActionItem, e: Konva.KonvaEventObject<MouseEvent>) => {
    e.cancelBubble = true; // Prevent card click
    onToggleItem?.(item.id, !item.done);
  }, [onToggleItem]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#EF4444';
      case 'medium': return '#F59E0B';
      case 'low': return '#10B981';
      default: return '#6B7280';
    }
  };

  return (
    <Group
      x={position.x}
      y={position.y}
      draggable
      onDragEnd={handleDragEnd}
      onDragMove={handleDragMove}
      onClick={onClick}
      onTap={onClick}
    >
      {/* Shadow */}
      <Rect
        x={4}
        y={4}
        width={style.width}
        height={totalHeight}
        fill="rgba(0,0,0,0.08)"
        cornerRadius={10}
      />
      
      {/* Card Background */}
      <Rect
        x={0}
        y={0}
        width={style.width}
        height={totalHeight}
        fill={style.bgColor}
        stroke={isSelected ? style.borderColor : 'rgba(245, 158, 11, 0.3)'}
        strokeWidth={isSelected ? 2 : 1}
        cornerRadius={10}
      />
      
      {/* Header Bar */}
      <Rect
        x={0}
        y={0}
        width={style.width}
        height={headerHeight}
        fill={style.headerColor}
        cornerRadius={[10, 10, 0, 0]}
      />
      
      {/* Checklist Icon */}
      <Circle
        x={22}
        y={headerHeight / 2}
        radius={12}
        fill="rgba(255,255,255,0.2)"
      />
      <Text
        x={14}
        y={headerHeight / 2 - 7}
        text="✓"
        fontSize={13}
        fill="#FFFFFF"
        fontStyle="bold"
      />
      
      {/* Title & Count */}
      <Text
        x={42}
        y={10}
        width={style.width - 60}
        text={data.title || 'Action Items'}
        fontSize={13}
        fontStyle="bold"
        fill="#FFFFFF"
        ellipsis={true}
        wrap="none"
      />
      <Text
        x={42}
        y={26}
        text={`${completedCount}/${data.items.length} completed`}
        fontSize={10}
        fill="rgba(255,255,255,0.8)"
      />
      
      {/* Action Items */}
      {data.items.slice(0, 5).map((item, index) => {
        const y = headerHeight + padding + index * itemHeight;
        return (
          <React.Fragment key={item.id}>
            {/* Checkbox */}
            <Rect
              x={padding}
              y={y + 2}
              width={16}
              height={16}
              fill={item.done ? '#10B981' : '#FFFFFF'}
              stroke={item.done ? '#10B981' : '#D1D5DB'}
              strokeWidth={1.5}
              cornerRadius={3}
              onClick={(e) => handleCheckboxClick(item, e)}
              onTap={(e) => handleCheckboxClick(item, e)}
            />
            {item.done && (
              <Text
                x={padding + 2}
                y={y + 2}
                text="✓"
                fontSize={12}
                fill="#FFFFFF"
                fontStyle="bold"
              />
            )}
            
            {/* Priority indicator */}
            <Circle
              x={padding + 26}
              y={y + 10}
              radius={4}
              fill={getPriorityColor(item.priority)}
            />
            
            {/* Item text */}
            <Text
              x={padding + 38}
              y={y + 3}
              width={style.width - padding * 2 - 50}
              text={item.text}
              fontSize={11}
              fill={item.done ? '#9CA3AF' : '#374151'}
              textDecoration={item.done ? 'line-through' : 'none'}
              ellipsis={true}
              wrap="none"
            />
          </React.Fragment>
        );
      })}
      
      {/* More items indicator */}
      {data.items.length > 5 && (
        <Text
          x={padding}
          y={headerHeight + padding + 5 * itemHeight}
          text={`+${data.items.length - 5} more items`}
          fontSize={10}
          fill="#9CA3AF"
          fontStyle="italic"
        />
      )}
    </Group>
  );
};

// ============================================================================
// Super Card Factory (for dynamic rendering)
// ============================================================================

export type SuperCardData = 
  | { type: 'article'; data: ArticleData }
  | { type: 'action_list'; data: ActionListData };

interface SuperCardProps {
  cardData: SuperCardData;
  position: SuperCardPosition;
  isSelected?: boolean;
  onClick?: () => void;
  onToggleItem?: (itemId: string, done: boolean) => void;
  onDragMove?: (pos: SuperCardPosition) => void;
  onDragEnd?: (pos: SuperCardPosition) => void;
}

export const SuperCard: React.FC<SuperCardProps> = ({
  cardData,
  position,
  isSelected,
  onClick,
  onToggleItem,
  onDragMove,
  onDragEnd,
}) => {
  if (cardData.type === 'article') {
    return (
      <DocumentCard
        data={cardData.data}
        position={position}
        isSelected={isSelected}
        onClick={onClick}
        onDragMove={onDragMove}
        onDragEnd={onDragEnd}
      />
    );
  }
  
  return (
    <TicketCard
      data={cardData.data}
      position={position}
      isSelected={isSelected}
      onClick={onClick}
      onToggleItem={onToggleItem}
      onDragMove={onDragMove}
      onDragEnd={onDragEnd}
    />
  );
};

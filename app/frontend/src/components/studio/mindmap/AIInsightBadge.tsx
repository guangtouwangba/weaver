/**
 * AIInsightBadge - Floating AI Insight Decoration
 * 
 * Features:
 * - Dark background badge with sparkle icon
 * - Diamond connector pointing to target node
 * - Positioned above and left of target node
 */

import React from 'react';
import { Group, Rect, Text, Line, RegularPolygon } from 'react-konva';
import { mindmapCardTokens as tokens } from '@/theme/theme';

interface AIInsightBadgeProps {
  x: number;
  y: number;
  text: string;
  targetX: number;
  targetY: number;
}

/**
 * Sparkle icon (✨ simplified)
 */
const SparkleIcon: React.FC<{ x: number; y: number; size?: number }> = ({ 
  x, y, size = 14 
}) => {
  const center = size / 2;
  const points = [
    // Vertical line
    center, 0,
    center, size,
    // Horizontal line
    0, center,
    size, center,
  ];
  
  return (
    <Group x={x} y={y}>
      {/* Main star cross */}
      <Line
        points={[center, 2, center, size - 2]}
        stroke={tokens.aiBadge.accent}
        strokeWidth={2}
        lineCap="round"
      />
      <Line
        points={[2, center, size - 2, center]}
        stroke={tokens.aiBadge.accent}
        strokeWidth={2}
        lineCap="round"
      />
      {/* Small diagonal sparkles */}
      <Line
        points={[4, 4, size - 4, size - 4]}
        stroke={tokens.aiBadge.accent}
        strokeWidth={1.5}
        lineCap="round"
        opacity={0.6}
      />
      <Line
        points={[size - 4, 4, 4, size - 4]}
        stroke={tokens.aiBadge.accent}
        strokeWidth={1.5}
        lineCap="round"
        opacity={0.6}
      />
    </Group>
  );
};

export const AIInsightBadge: React.FC<AIInsightBadgeProps> = ({
  x,
  y,
  text,
  targetX,
  targetY,
}) => {
  const displayText = text.length > 40 ? text.slice(0, 37) + '...' : text;
  const badgeWidth = Math.min(Math.max(displayText.length * 7 + 40, 100), 200);
  const badgeHeight = 28;
  const connectorSize = 8;
  
  // Badge position (offset from provided x, y)
  const badgeX = x;
  const badgeY = y;
  
  // Diamond connector position
  const diamondX = badgeX + badgeWidth / 2;
  const diamondY = badgeY + badgeHeight + connectorSize / 2;

  return (
    <Group>
      {/* Badge background */}
      <Rect
        x={badgeX}
        y={badgeY}
        width={badgeWidth}
        height={badgeHeight}
        fill={tokens.aiBadge.bg}
        cornerRadius={6}
        shadowColor="black"
        shadowBlur={8}
        shadowOpacity={0.2}
        shadowOffsetY={2}
      />
      
      {/* Sparkle icon */}
      <SparkleIcon x={badgeX + 8} y={badgeY + 7} size={14} />
      
      {/* Text */}
      <Text
        x={badgeX + 26}
        y={badgeY + 8}
        width={badgeWidth - 34}
        text={displayText}
        fontSize={11}
        fill={tokens.aiBadge.text}
        fontStyle="500"
        ellipsis
      />

      {/* Diamond connector */}
      <RegularPolygon
        x={diamondX}
        y={diamondY}
        sides={4}
        radius={connectorSize / 2}
        fill={tokens.aiBadge.bg}
        rotation={45}
      />

      {/* Connector line to target */}
      <Line
        points={[
          diamondX, diamondY + connectorSize / 2,
          targetX, targetY,
        ]}
        stroke={tokens.aiBadge.bg}
        strokeWidth={1.5}
        lineCap="round"
        dash={[3, 3]}
        opacity={0.6}
      />
    </Group>
  );
};

export default AIInsightBadge;


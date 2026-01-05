/**
 * CurvedMindMapEdge - Smooth Bezier Curve Edge with Anchor Dots
 * 
 * Features:
 * - Bezier curve connections (not straight lines)
 * - Connection anchor dots at endpoints
 * - Color based on source node state
 * - Fade-in animation
 */

import React, { useEffect, useRef, useMemo } from 'react';
import { Group, Line, Circle } from 'react-konva';
import Konva from 'konva';
import { MindmapEdge as MindmapEdgeType, MindmapNode } from '@/lib/api';
import { mindmapCardTokens as tokens } from '@/theme/theme';

interface CurvedMindMapEdgeProps {
  edge: MindmapEdgeType;
  sourceNode?: MindmapNode;
  targetNode?: MindmapNode;
  showAnchors?: boolean;
  shouldAnimate?: boolean;
}

export const CurvedMindMapEdge: React.FC<CurvedMindMapEdgeProps> = ({
  edge,
  sourceNode,
  targetNode,
  showAnchors = true,
  shouldAnimate = true,
}) => {
  const groupRef = useRef<Konva.Group>(null);

  // Fade in animation
  useEffect(() => {
    if (!groupRef.current || !shouldAnimate) return;

    groupRef.current.opacity(0);
    groupRef.current.to({
      opacity: 1,
      duration: 0.5,
    });
  }, [shouldAnimate]);

  if (!sourceNode || !targetNode) return null;

  // Get edge color based on source node state
  const getEdgeColor = () => {
    if (sourceNode.depth === 0) {
      return tokens.card.borderActive; // Root node - active blue
    }
    switch (sourceNode.status) {
      case 'generating':
        return tokens.card.borderActive;
      case 'complete':
        return tokens.card.borderDashed;
      default:
        return tokens.card.borderPending;
    }
  };

  const edgeColor = getEdgeColor();
  const isActiveEdge = sourceNode.status === 'generating' || sourceNode.depth === 0;

  // Calculate connection points
  // Source: right-center of source node
  const sourceWidth = sourceNode.width || 200;
  const sourceHeight = sourceNode.height || 80;
  const sourceX = sourceNode.x + sourceWidth;
  const sourceY = sourceNode.y + sourceHeight / 2;

  // Target: left-center of target node
  const targetHeight = targetNode.height || 80;
  const targetX = targetNode.x;
  const targetY = targetNode.y + targetHeight / 2;

  // Calculate Bezier control points for smooth S-curve
  const horizontalDistance = Math.abs(targetX - sourceX);
  const controlOffset = Math.max(horizontalDistance * 0.4, 40);

  // Create smooth Bezier curve points
  const bezierPoints = useMemo(() => {
    return [
      sourceX, sourceY,                    // Start point
      sourceX + controlOffset, sourceY,    // Control point 1
      targetX - controlOffset, targetY,    // Control point 2
      targetX, targetY,                    // End point
    ];
  }, [sourceX, sourceY, targetX, targetY, controlOffset]);

  // Determine if edge should be dashed
  const isDashed = targetNode.status !== 'complete' || sourceNode.status !== 'complete';

  return (
    <Group ref={groupRef}>
      {/* Main curve */}
      <Line
        points={bezierPoints}
        stroke={edgeColor}
        strokeWidth={2}
        bezier
        lineCap="round"
        lineJoin="round"
        dash={isDashed ? [6, 4] : undefined}
        opacity={isActiveEdge ? 1 : 0.6}
      />

      {/* Source anchor dot */}
      {showAnchors && (
        <Circle
          x={sourceX}
          y={sourceY}
          radius={4}
          fill={edgeColor}
          stroke={tokens.card.bg}
          strokeWidth={1}
        />
      )}

      {/* Target anchor dot */}
      {showAnchors && (
        <Circle
          x={targetX}
          y={targetY}
          radius={4}
          fill={edgeColor}
          stroke={tokens.card.bg}
          strokeWidth={1}
        />
      )}
    </Group>
  );
};

export default CurvedMindMapEdge;






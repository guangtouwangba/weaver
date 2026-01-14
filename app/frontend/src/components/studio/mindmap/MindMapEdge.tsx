import React, { useEffect, useRef } from 'react';
import { Line } from 'react-konva';
import Konva from 'konva';
import { MindmapEdge as MindmapEdgeType, MindmapNode } from '@/lib/api';

interface MindMapEdgeProps {
  edge: MindmapEdgeType;
  sourceNode?: MindmapNode;
  targetNode?: MindmapNode;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const MindMapEdge: React.FC<MindMapEdgeProps> = ({ edge: _edge, sourceNode, targetNode }) => {
  const lineRef = useRef<Konva.Line>(null);

  useEffect(() => {
    if (lineRef.current) {
      // Fade in animation on mount
      lineRef.current.opacity(0);
      lineRef.current.to({
        opacity: 1,
        duration: 0.5,
      });
    }
  }, []);

  if (!sourceNode || !targetNode) return null;

  // Calculate connection points
  const sourceX = sourceNode.x + (sourceNode.width || 200);
  const sourceY = sourceNode.y + (sourceNode.height || 80) / 2;
  
  const targetX = targetNode.x;
  const targetY = targetNode.y + (targetNode.height || 80) / 2;

  // Bezier curve control points
  const controlOffset = Math.abs(targetX - sourceX) * 0.5;

  return (
    <Line
      ref={lineRef}
      points={[
        sourceX, sourceY,
        sourceX + controlOffset, sourceY,
        targetX - controlOffset, targetY,
        targetX, targetY
      ]}
      stroke="#94A3B8"
      strokeWidth={2}
      tension={0.5}
      bezier
      lineCap="round"
      lineJoin="round"
    />
  );
};

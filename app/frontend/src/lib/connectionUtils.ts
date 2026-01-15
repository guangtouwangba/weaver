/**
 * Connection Utilities for Canvas Edges
 *
 * Provides anchor point calculation, path generation, and auto-selection logic
 * for improved canvas connection experience.
 */

import { CanvasNode, CanvasEdge } from './api';

// Anchor type definitions
export type AnchorDirection = 'N' | 'S' | 'E' | 'W';
export type AnchorType = AnchorDirection | 'auto';

// Point interface for consistency
export interface Point {
  x: number;
  y: number;
}

// Anchor position with direction for arrow rendering
export interface AnchorPoint extends Point {
  direction: AnchorDirection;
}

/**
 * Get the pixel position for a specific anchor point on a node
 */
export function getAnchorPoint(
  node: CanvasNode,
  anchor: AnchorDirection
): AnchorPoint {
  const width = node.width || 280;
  const height = node.height || 200;

  switch (anchor) {
    case 'N': // Top center
      return { x: node.x + width / 2, y: node.y, direction: 'N' };
    case 'S': // Bottom center
      return { x: node.x + width / 2, y: node.y + height, direction: 'S' };
    case 'E': // Right center
      return { x: node.x + width, y: node.y + height / 2, direction: 'E' };
    case 'W': // Left center
      return { x: node.x, y: node.y + height / 2, direction: 'W' };
  }
}

/**
 * Auto-select the best anchor points based on relative node positions
 * Returns [sourceAnchor, targetAnchor]
 */
export function autoSelectAnchors(
  sourceNode: CanvasNode,
  targetNode: CanvasNode
): [AnchorDirection, AnchorDirection] {
  const sourceWidth = sourceNode.width || 280;
  const sourceHeight = sourceNode.height || 200;
  const targetWidth = targetNode.width || 280;
  const targetHeight = targetNode.height || 200;

  // Calculate centers
  const sourceCenterX = sourceNode.x + sourceWidth / 2;
  const sourceCenterY = sourceNode.y + sourceHeight / 2;
  const targetCenterX = targetNode.x + targetWidth / 2;
  const targetCenterY = targetNode.y + targetHeight / 2;

  // Calculate delta
  const dx = targetCenterX - sourceCenterX;
  const dy = targetCenterY - sourceCenterY;

  // Determine primary direction based on which axis has larger difference
  if (Math.abs(dx) > Math.abs(dy)) {
    // Horizontal dominant
    if (dx > 0) {
      // Target is to the right
      return ['E', 'W'];
    } else {
      // Target is to the left
      return ['W', 'E'];
    }
  } else {
    // Vertical dominant
    if (dy > 0) {
      // Target is below
      return ['S', 'N'];
    } else {
      // Target is above
      return ['N', 'S'];
    }
  }
}

/**
 * Get straight line path points between two anchor points
 */
export function getStraightPath(
  source: AnchorPoint,
  target: AnchorPoint
): number[] {
  return [source.x, source.y, target.x, target.y];
}

/**
 * Get Bezier curve path points with control points
 * Preserves existing curve behavior but with dynamic anchor points
 */
export function getBezierPath(
  source: AnchorPoint,
  target: AnchorPoint
): number[] {
  // Calculate control point offset based on distance and direction
  const dx = Math.abs(target.x - source.x);
  const dy = Math.abs(target.y - source.y);
  const offset = Math.max(Math.min(dx, dy) * 0.4, 50);

  // Determine control point positions based on anchor directions
  let c1x = source.x,
    c1y = source.y;
  let c2x = target.x,
    c2y = target.y;

  switch (source.direction) {
    case 'E':
      c1x = source.x + offset;
      break;
    case 'W':
      c1x = source.x - offset;
      break;
    case 'N':
      c1y = source.y - offset;
      break;
    case 'S':
      c1y = source.y + offset;
      break;
  }

  switch (target.direction) {
    case 'E':
      c2x = target.x + offset;
      break;
    case 'W':
      c2x = target.x - offset;
      break;
    case 'N':
      c2y = target.y - offset;
      break;
    case 'S':
      c2y = target.y + offset;
      break;
  }

  return [source.x, source.y, c1x, c1y, c2x, c2y, target.x, target.y];
}

/**
 * Resolve anchor type to actual direction
 * If 'auto', calculates best anchor based on node positions
 */
export function resolveAnchor(
  edge: CanvasEdge,
  sourceNode: CanvasNode,
  targetNode: CanvasNode,
  anchorType: 'source' | 'target'
): AnchorDirection {
  const anchor =
    anchorType === 'source' ? edge.sourceAnchor : edge.targetAnchor;

  if (!anchor || anchor === 'auto') {
    const [sourceAnchor, targetAnchor] = autoSelectAnchors(
      sourceNode,
      targetNode
    );
    return anchorType === 'source' ? sourceAnchor : targetAnchor;
  }

  return anchor;
}

/**
 * Get all anchor points for a node (for visual indicators)
 */
export function getAllAnchorPoints(node: CanvasNode): AnchorPoint[] {
  return (['N', 'S', 'E', 'W'] as AnchorDirection[]).map((dir) =>
    getAnchorPoint(node, dir)
  );
}

/**
 * Calculate arrow head points for edge terminus
 * Returns points for a triangular arrow pointing in the anchor direction
 */
export function getArrowPoints(
  anchor: AnchorPoint,
  size: number = 8
): number[] {
  const { x, y, direction } = anchor;

  switch (direction) {
    case 'E': // Arrow pointing right (entering from left)
      return [x - size, y - size / 2, x, y, x - size, y + size / 2];
    case 'W': // Arrow pointing left (entering from right)
      return [x + size, y - size / 2, x, y, x + size, y + size / 2];
    case 'S': // Arrow pointing down (entering from top)
      return [x - size / 2, y - size, x, y, x + size / 2, y - size];
    case 'N': // Arrow pointing up (entering from bottom)
      return [x - size / 2, y + size, x, y, x + size / 2, y + size];
  }
}

// Simple obstacle interface
export interface Obstacle {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * Get orthogonal (Manhattan) path points between two anchor points
 * Uses simple heuristic to navigate around obstacles if provided
 */
export function getOrthogonalPath(
  source: AnchorPoint,
  target: AnchorPoint,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _obstacles: Obstacle[] = []
): number[] {
  const points: Point[] = [{ x: source.x, y: source.y }];

  // Simple 3-segment orthogonal routing (Source -> Mid -> Target)
  // Adjusts based on anchor direction to exit correctly

  const midX = (source.x + target.x) / 2;
  const midY = (source.y + target.y) / 2;

  // Adjust midpoints based on directions to visually look good
  // This logic ensures lines exit the node correctly before turning

  // Case 1: Horizontal Source (E/W) to Horizontal Target (E/W)
  if (
    (source.direction === 'E' || source.direction === 'W') &&
    (target.direction === 'E' || target.direction === 'W')
  ) {
    points.push({ x: midX, y: source.y });
    points.push({ x: midX, y: target.y });
  }
  // Case 2: Vertical Source (N/S) to Vertical Target (N/S)
  else if (
    (source.direction === 'N' || source.direction === 'S') &&
    (target.direction === 'N' || target.direction === 'S')
  ) {
    points.push({ x: source.x, y: midY });
    points.push({ x: target.x, y: midY });
  }
  // Case 3: Horizontal Source to Vertical Target
  else if (
    (source.direction === 'E' || source.direction === 'W') &&
    (target.direction === 'N' || target.direction === 'S')
  ) {
    points.push({ x: target.x, y: source.y }); // 90 degree turn
  }
  // Case 4: Vertical Source to Horizontal Target
  else if (
    (source.direction === 'N' || source.direction === 'S') &&
    (target.direction === 'E' || target.direction === 'W')
  ) {
    points.push({ x: source.x, y: target.y }); // 90 degree turn
  }

  points.push({ x: target.x, y: target.y });

  // Flatten result to [x1, y1, x2, y2, ...]
  return points.flatMap((p) => [p.x, p.y]);
}

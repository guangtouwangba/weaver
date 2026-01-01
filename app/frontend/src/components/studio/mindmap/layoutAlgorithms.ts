/**
 * Mind Map Layout Algorithms
 * 
 * Provides different layout strategies for organizing mindmap nodes:
 * - Radial: Nodes arranged in concentric circles around root
 * - Tree: Hierarchical top-down/left-right structure
 * - Balanced: Nodes distributed evenly on both sides of root
 */

import { MindmapNode, MindmapData } from '@/lib/api';

export type LayoutType = 'radial' | 'tree' | 'balanced';

interface LayoutOptions {
  centerX: number;
  centerY: number;
  nodeWidth?: number;
  nodeHeight?: number;
  horizontalSpacing?: number;
  verticalSpacing?: number;
  radiusStep?: number;
}

interface LayoutResult {
  nodes: MindmapNode[];
  bounds: { minX: number; minY: number; maxX: number; maxY: number };
}

/**
 * Build a tree structure from flat node list
 */
function buildTree(nodes: MindmapNode[]): Map<string, MindmapNode[]> {
  const childrenMap = new Map<string, MindmapNode[]>();

  nodes.forEach(node => {
    const parentId = node.parentId || 'root';
    if (!childrenMap.has(parentId)) {
      childrenMap.set(parentId, []);
    }
    if (node.parentId) {
      childrenMap.get(parentId)!.push(node);
    }
  });

  return childrenMap;
}

/**
 * Find the root node (depth === 0 or no parent)
 */
function findRoot(nodes: MindmapNode[]): MindmapNode | undefined {
  return nodes.find(n => n.depth === 0 || !n.parentId);
}

/**
 * Count descendants of a node
 */
function countDescendants(nodeId: string, childrenMap: Map<string, MindmapNode[]>): number {
  const children = childrenMap.get(nodeId) || [];
  let count = children.length;
  children.forEach(child => {
    count += countDescendants(child.id, childrenMap);
  });
  return count;
}

/**
 * Radial Layout
 * 
 * Arranges nodes in concentric circles around the root.
 * Children fan out in arcs based on the number of descendants.
 */
export function radialLayout(data: MindmapData, options: LayoutOptions): LayoutResult {
  const {
    centerX,
    centerY,
    nodeWidth = 200,
    nodeHeight = 80,
    radiusStep = 250,
  } = options;

  const nodes = [...data.nodes];
  const root = findRoot(nodes);
  if (!root) return { nodes, bounds: { minX: 0, minY: 0, maxX: 0, maxY: 0 } };

  const childrenMap = buildTree(nodes);
  const positioned = new Map<string, { x: number; y: number }>();

  // Position root at center
  positioned.set(root.id, { x: centerX - nodeWidth / 2, y: centerY - nodeHeight / 2 });

  // BFS to position each level
  const queue: { node: MindmapNode; startAngle: number; endAngle: number; level: number }[] = [];

  const rootChildren = childrenMap.get(root.id) || [];
  if (rootChildren.length > 0) {
    const anglePerChild = (2 * Math.PI) / rootChildren.length;
    rootChildren.forEach((child, i) => {
      queue.push({
        node: child,
        startAngle: i * anglePerChild - Math.PI / 2,
        endAngle: (i + 1) * anglePerChild - Math.PI / 2,
        level: 1,
      });
    });
  }

  while (queue.length > 0) {
    const { node, startAngle, endAngle, level } = queue.shift()!;
    const angle = (startAngle + endAngle) / 2;
    const radius = level * radiusStep;

    const x = centerX + Math.cos(angle) * radius - nodeWidth / 2;
    const y = centerY + Math.sin(angle) * radius - nodeHeight / 2;
    positioned.set(node.id, { x, y });

    const children = childrenMap.get(node.id) || [];
    if (children.length > 0) {
      const angleSpan = endAngle - startAngle;
      const anglePerChild = angleSpan / children.length;
      children.forEach((child, i) => {
        queue.push({
          node: child,
          startAngle: startAngle + i * anglePerChild,
          endAngle: startAngle + (i + 1) * anglePerChild,
          level: level + 1,
        });
      });
    }
  }

  // Apply positions to nodes
  const updatedNodes = nodes.map(n => ({
    ...n,
    x: positioned.get(n.id)?.x ?? n.x,
    y: positioned.get(n.id)?.y ?? n.y,
  }));

  // Calculate bounds
  const bounds = calculateBounds(updatedNodes, nodeWidth, nodeHeight);

  return { nodes: updatedNodes, bounds };
}

/**
 * Tree Layout
 * 
 * Arranges nodes in a hierarchical left-to-right tree structure.
 * Sibling nodes are aligned horizontally, parent-child vertically stacked.
 */
export function treeLayout(data: MindmapData, options: LayoutOptions): LayoutResult {
  const {
    centerX,
    centerY,
    nodeWidth = 200,
    nodeHeight = 80,
    horizontalSpacing = 60,
    verticalSpacing = 120,
  } = options;

  const nodes = [...data.nodes];
  const root = findRoot(nodes);
  if (!root) return { nodes, bounds: { minX: 0, minY: 0, maxX: 0, maxY: 0 } };

  const childrenMap = buildTree(nodes);
  const positioned = new Map<string, { x: number; y: number }>();

  // Calculate subtree heights for vertical positioning
  function getSubtreeHeight(nodeId: string): number {
    const children = childrenMap.get(nodeId) || [];
    if (children.length === 0) return nodeHeight;

    const childrenHeight = children.reduce(
      (sum, child) => sum + getSubtreeHeight(child.id) + verticalSpacing,
      -verticalSpacing
    );
    return Math.max(nodeHeight, childrenHeight);
  }

  // Position nodes recursively
  function positionNode(node: MindmapNode, x: number, y: number) {
    positioned.set(node.id, { x, y });

    const children = childrenMap.get(node.id) || [];
    if (children.length === 0) return;

    const childX = x + nodeWidth + horizontalSpacing;
    let currentY = y;

    // Center children around the parent's vertical center
    const totalHeight = children.reduce(
      (sum, child) => sum + getSubtreeHeight(child.id) + verticalSpacing,
      -verticalSpacing
    );
    currentY = y + nodeHeight / 2 - totalHeight / 2;

    children.forEach(child => {
      const subtreeHeight = getSubtreeHeight(child.id);
      const childY = currentY + subtreeHeight / 2 - nodeHeight / 2;
      positionNode(child, childX, childY);
      currentY += subtreeHeight + verticalSpacing;
    });
  }

  // Start positioning from root
  const rootHeight = getSubtreeHeight(root.id);
  positionNode(root, centerX - nodeWidth / 2, centerY - rootHeight / 2);

  // Apply positions
  const updatedNodes = nodes.map(n => ({
    ...n,
    x: positioned.get(n.id)?.x ?? n.x,
    y: positioned.get(n.id)?.y ?? n.y,
  }));

  const bounds = calculateBounds(updatedNodes, nodeWidth, nodeHeight);

  return { nodes: updatedNodes, bounds };
}

/**
 * Balanced Layout
 * 
 * Distributes child nodes evenly on both sides of the root.
 * Left side children go left, right side children go right.
 */
export function balancedLayout(data: MindmapData, options: LayoutOptions): LayoutResult {
  const {
    centerX,
    centerY,
    nodeWidth = 200,
    nodeHeight = 80,
    horizontalSpacing = 80,
    verticalSpacing = 40,
  } = options;

  const nodes = [...data.nodes];
  const root = findRoot(nodes);
  if (!root) return { nodes, bounds: { minX: 0, minY: 0, maxX: 0, maxY: 0 } };

  const childrenMap = buildTree(nodes);
  const positioned = new Map<string, { x: number; y: number }>();

  // Position root at center
  positioned.set(root.id, { x: centerX - nodeWidth / 2, y: centerY - nodeHeight / 2 });

  const rootChildren = childrenMap.get(root.id) || [];

  // Split children into left and right groups
  const leftChildren: MindmapNode[] = [];
  const rightChildren: MindmapNode[] = [];
  rootChildren.forEach((child, i) => {
    if (i % 2 === 0) {
      rightChildren.push(child);
    } else {
      leftChildren.push(child);
    }
  });

  // Calculate subtree size
  function getSubtreeHeight(nodeId: string): number {
    const children = childrenMap.get(nodeId) || [];
    if (children.length === 0) return nodeHeight;

    const childrenHeight = children.reduce(
      (sum, child) => sum + getSubtreeHeight(child.id) + verticalSpacing,
      -verticalSpacing
    );
    return Math.max(nodeHeight, childrenHeight);
  }

  // Position a branch (left or right)
  function positionBranch(
    children: MindmapNode[],
    direction: 'left' | 'right',
    baseX: number,
    baseY: number
  ) {
    if (children.length === 0) return;

    const totalHeight = children.reduce(
      (sum, child) => sum + getSubtreeHeight(child.id) + verticalSpacing,
      -verticalSpacing
    );

    let currentY = baseY - totalHeight / 2;
    const xOffset = direction === 'right'
      ? nodeWidth + horizontalSpacing
      : -(nodeWidth + horizontalSpacing);

    children.forEach(child => {
      const subtreeHeight = getSubtreeHeight(child.id);
      const childY = currentY + subtreeHeight / 2 - nodeHeight / 2;
      const childX = baseX + xOffset;

      positioned.set(child.id, { x: childX, y: childY });

      // Recursively position grandchildren (same direction)
      const grandchildren = childrenMap.get(child.id) || [];
      if (grandchildren.length > 0) {
        positionBranchRecursive(grandchildren, direction, childX, childY + nodeHeight / 2);
      }

      currentY += subtreeHeight + verticalSpacing;
    });
  }

  function positionBranchRecursive(
    children: MindmapNode[],
    direction: 'left' | 'right',
    parentX: number,
    parentCenterY: number
  ) {
    if (children.length === 0) return;

    const totalHeight = children.reduce(
      (sum, child) => sum + getSubtreeHeight(child.id) + verticalSpacing,
      -verticalSpacing
    );

    let currentY = parentCenterY - totalHeight / 2;
    const xOffset = direction === 'right'
      ? nodeWidth + horizontalSpacing
      : -(nodeWidth + horizontalSpacing);

    children.forEach(child => {
      const subtreeHeight = getSubtreeHeight(child.id);
      const childY = currentY + subtreeHeight / 2 - nodeHeight / 2;
      const childX = parentX + xOffset;

      positioned.set(child.id, { x: childX, y: childY });

      const grandchildren = childrenMap.get(child.id) || [];
      if (grandchildren.length > 0) {
        positionBranchRecursive(grandchildren, direction, childX, childY + nodeHeight / 2);
      }

      currentY += subtreeHeight + verticalSpacing;
    });
  }

  // Position left and right branches
  positionBranch(rightChildren, 'right', centerX - nodeWidth / 2, centerY);
  positionBranch(leftChildren, 'left', centerX - nodeWidth / 2, centerY);

  // Apply positions
  const updatedNodes = nodes.map(n => ({
    ...n,
    x: positioned.get(n.id)?.x ?? n.x,
    y: positioned.get(n.id)?.y ?? n.y,
  }));

  const bounds = calculateBounds(updatedNodes, nodeWidth, nodeHeight);

  return { nodes: updatedNodes, bounds };
}

/**
 * Calculate bounding box of all nodes
 */
function calculateBounds(
  nodes: MindmapNode[],
  defaultWidth: number,
  defaultHeight: number
): { minX: number; minY: number; maxX: number; maxY: number } {
  if (nodes.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0 };
  }

  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

  nodes.forEach(node => {
    const w = node.width || defaultWidth;
    const h = node.height || defaultHeight;
    minX = Math.min(minX, node.x);
    minY = Math.min(minY, node.y);
    maxX = Math.max(maxX, node.x + w);
    maxY = Math.max(maxY, node.y + h);
  });

  return { minX, minY, maxX, maxY };
}

/**
 * Apply a layout to mindmap data
 */
export function applyLayout(
  data: MindmapData,
  layoutType: LayoutType,
  canvasWidth: number,
  canvasHeight: number
): LayoutResult {
  const options: LayoutOptions = {
    centerX: canvasWidth / 2,
    centerY: canvasHeight / 2,
  };

  switch (layoutType) {
    case 'radial':
      return radialLayout(data, options);
    case 'tree':
      return treeLayout(data, options);
    case 'balanced':
    default:
      return balancedLayout(data, options);
  }
}

/**
 * Resolve overlaps after moving a node
 * 
 * When a node is moved, check if it overlaps with others.
 * If so, push the other nodes away to make space.
 * 
 * Strategy:
 * 1. Check intersection between sourceNode and others
 * 2. If overlap, calculate push vector (away from sourceNode center)
 * 3. Move overlapped node AND its entire subtree by that vector
 */
export function resolveOverlaps(
  nodes: MindmapNode[],
  movedNodeId: string,
  nodeWidth: number = 200,
  nodeHeight: number = 80,
  padding: number = 20
): MindmapNode[] {
  let updatedNodes = [...nodes];
  const movedNode = updatedNodes.find(n => n.id === movedNodeId);

  if (!movedNode) return nodes;

  const childrenMap = buildTree(updatedNodes);

  // Helper to get all descendants of a node to move them together
  const getSubtree = (rootId: string): string[] => {
    const subtreeIds: string[] = [rootId];
    const children = childrenMap.get(rootId) || [];
    children.forEach(child => {
      subtreeIds.push(...getSubtree(child.id));
    });
    return subtreeIds;
  };

  // Check for collisions
  // We iterate a few times to resolve cascading overlaps
  for (let iter = 0; iter < 2; iter++) {
    let hasChanges = false;

    // We only check collisions against the moved node (or nodes that were pushed)
    // But for simplicity in this MVP, we mainly check against the movedNode
    // and let the user do fine-tuning if complex chains happen.

    for (const node of updatedNodes) {
      if (node.id === movedNodeId) continue;

      // Specialized AABB collision check with padding
      const isOverlapping =
        movedNode.x < node.x + nodeWidth + padding &&
        movedNode.x + nodeWidth + padding > node.x &&
        movedNode.y < node.y + nodeHeight + padding &&
        movedNode.y + nodeHeight + padding > node.y;

      if (isOverlapping) {
        // Calculate push vector
        const dx = (node.x + nodeWidth / 2) - (movedNode.x + nodeWidth / 2);
        const dy = (node.y + nodeHeight / 2) - (movedNode.y + nodeHeight / 2);

        // Normalize
        const dist = Math.sqrt(dx * dx + dy * dy) || 1; // Avoid div by zero

        // Push direction - prioritize horizontal separation for mind maps
        const pushX = (dx / dist) * (nodeWidth + padding);
        const pushY = (dy / dist) * (nodeHeight + padding);

        // If centers are too close, force a default direction (usually down or right)
        const separationX = Math.abs(dx) < 10 ? (nodeWidth + padding) : pushX;
        const separationY = Math.abs(dy) < 10 ? (nodeHeight + padding) : pushY;

        // Apply push to the node and its subtree
        const subtreeIds = getSubtree(node.id);

        updatedNodes = updatedNodes.map(n => {
          if (subtreeIds.includes(n.id)) {
            // Determine mainly-horizontal or mainly-vertical push
            // For tree layouts, usually we want to push down or sideways
            let moveX = 0;
            let moveY = 0;

            if (Math.abs(dx) > Math.abs(dy)) {
              // Push mainly horizontally
              moveX = dx > 0 ? (nodeWidth + padding) - Math.abs(dx) : -((nodeWidth + padding) - Math.abs(dx));
              // Add a bit of extra space
              moveX *= 1.2;
            } else {
              // Push mainly vertically
              moveY = dy > 0 ? (nodeHeight + padding) - Math.abs(dy) : -((nodeHeight + padding) - Math.abs(dy));
              moveY *= 1.2;
            }

            // If centers are identical, just push down
            if (Math.abs(dx) < 1 && Math.abs(dy) < 1) {
              moveY = nodeHeight + padding;
            }

            return {
              ...n,
              x: n.x + moveX,
              y: n.y + moveY
            };
          }
          return n;
        });

        hasChanges = true;
      }
    }

    if (!hasChanges) break;
  }

  return updatedNodes;
}

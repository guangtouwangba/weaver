/**
 * Layout Algorithms Tests
 * 
 * Tests for:
 * 1. No node overlap after layout
 * 2. Balanced distribution
 * 3. Parent-child hierarchy preservation
 * 4. Performance requirements
 */

import { 
  applyLayout, 
  balancedLayout, 
  treeLayout, 
  radialLayout,
  LayoutType 
} from '../layoutAlgorithms';
import { MindmapData, MindmapNode } from '@/lib/api';

// Helper: Check if two nodes overlap
function nodesOverlap(
  node1: MindmapNode, 
  node2: MindmapNode, 
  padding: number = 0
): boolean {
  const w1 = node1.width || 200;
  const h1 = node1.height || 80;
  const w2 = node2.width || 200;
  const h2 = node2.height || 80;

  return (
    node1.x < node2.x + w2 + padding &&
    node1.x + w1 + padding > node2.x &&
    node1.y < node2.y + h2 + padding &&
    node1.y + h1 + padding > node2.y
  );
}

// Helper: Check if any nodes in the array overlap
function hasAnyOverlap(nodes: MindmapNode[], padding: number = 0): boolean {
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      if (nodesOverlap(nodes[i], nodes[j], padding)) {
        return true;
      }
    }
  }
  return false;
}

// Helper: Create a simple mindmap structure
function createSimpleMindmap(childCount: number): MindmapData {
  const rootId = 'root';
  const nodes: MindmapNode[] = [
    {
      id: rootId,
      label: 'Root',
      content: 'Root Node',
      depth: 0,
      x: 0,
      y: 0,
      width: 200,
      height: 80,
      color: 'primary',
      status: 'complete',
    },
  ];

  const edges: MindmapData['edges'] = [];

  for (let i = 0; i < childCount; i++) {
    const childId = `child-${i}`;
    nodes.push({
      id: childId,
      label: `Child ${i}`,
      content: `Child Node ${i}`,
      depth: 1,
      parentId: rootId,
      x: 0,
      y: 0,
      width: 200,
      height: 80,
      color: 'blue',
      status: 'complete',
    });
    edges.push({
      id: `edge-${rootId}-${childId}`,
      source: rootId,
      target: childId,
    });
  }

  return { nodes, edges, rootId };
}

// Helper: Create a deep tree structure
function createDeepTree(depth: number, branchFactor: number = 2): MindmapData {
  const nodes: MindmapNode[] = [];
  const edges: MindmapData['edges'] = [];
  let nodeCounter = 0;

  function addNode(parentId: string | undefined, currentDepth: number): string {
    const nodeId = `node-${nodeCounter++}`;
    nodes.push({
      id: nodeId,
      label: `Node ${nodeId}`,
      content: `Content for ${nodeId}`,
      depth: currentDepth,
      parentId,
      x: 0,
      y: 0,
      width: 200,
      height: 80,
      color: currentDepth === 0 ? 'primary' : 'blue',
      status: 'complete',
    });

    if (parentId) {
      edges.push({
        id: `edge-${parentId}-${nodeId}`,
        source: parentId,
        target: nodeId,
      });
    }

    if (currentDepth < depth) {
      for (let i = 0; i < branchFactor; i++) {
        addNode(nodeId, currentDepth + 1);
      }
    }

    return nodeId;
  }

  const rootId = addNode(undefined, 0);
  return { nodes, edges, rootId };
}

// Helper: Create mindmap from the user's example markdown structure
function createTableMarkdownMindmap(): MindmapData {
  const nodes: MindmapNode[] = [
    { id: 'root', label: 'Overview', content: 'Overview', depth: 0, x: 0, y: 0, width: 200, height: 80, color: 'primary', status: 'complete' },
    { id: 'n1', label: '从零开始', content: '从零开始', depth: 1, parentId: 'root', x: 0, y: 0, width: 200, height: 80, color: 'blue', status: 'complete' },
    { id: 'n2', label: '输出量的误区', content: '输出量的误区', depth: 1, parentId: 'root', x: 0, y: 0, width: 200, height: 80, color: 'blue', status: 'complete' },
    { id: 'n3', label: '构建你的独特信号', content: '构建你的独特信号', depth: 1, parentId: 'root', x: 0, y: 0, width: 200, height: 80, color: 'blue', status: 'complete' },
    { id: 'n4', label: '使命型 vs 话题型定位', content: '使命型 vs 话题型定位', depth: 1, parentId: 'root', x: 0, y: 0, width: 200, height: 80, color: 'blue', status: 'complete' },
    { id: 'n5', label: '核心要点', content: '核心要点', depth: 1, parentId: 'root', x: 0, y: 0, width: 200, height: 80, color: 'blue', status: 'complete' },
    // Children of 从零开始
    { id: 'n1-1', label: '收藏让你停止滑动的帖子', content: '收藏让你停止滑动的帖子', depth: 2, parentId: 'n1', x: 0, y: 0, width: 200, height: 80, color: 'green', status: 'complete' },
    { id: 'n1-2', label: '收集改变你思维的段落', content: '收集改变你思维的段落', depth: 2, parentId: 'n1', x: 0, y: 0, width: 200, height: 80, color: 'green', status: 'complete' },
    { id: 'n1-3', label: '通过接触建立品味博物馆', content: '通过接触建立品味博物馆', depth: 2, parentId: 'n1', x: 0, y: 0, width: 200, height: 80, color: 'green', status: 'complete' },
    // Children of 输出量的误区
    { id: 'n2-1', label: '发布频率 ≠ 成功', content: '发布频率 ≠ 成功', depth: 2, parentId: 'n2', x: 0, y: 0, width: 200, height: 80, color: 'green', status: 'complete' },
    { id: 'n2-2', label: '更多内容 = 更多噪音', content: '更多内容 = 更多噪音', depth: 2, parentId: 'n2', x: 0, y: 0, width: 200, height: 80, color: 'green', status: 'complete' },
    { id: 'n2-3', label: '想法质量 > 输出频率', content: '想法质量 > 输出频率', depth: 2, parentId: 'n2', x: 0, y: 0, width: 200, height: 80, color: 'green', status: 'complete' },
    // Children of 核心要点
    { id: 'n5-1', label: '发展个人视角', content: '发展个人视角，思考而非套用模板', depth: 2, parentId: 'n5', x: 0, y: 0, width: 200, height: 80, color: 'green', status: 'complete' },
    { id: 'n5-2', label: '创作你想看到的内容', content: '创作你想看到的内容', depth: 2, parentId: 'n5', x: 0, y: 0, width: 200, height: 80, color: 'green', status: 'complete' },
    { id: 'n5-3', label: '做导演而非执行者', content: '做导演而非执行者', depth: 2, parentId: 'n5', x: 0, y: 0, width: 200, height: 80, color: 'green', status: 'complete' },
  ];

  const edges = nodes
    .filter(n => n.parentId)
    .map(n => ({
      id: `edge-${n.parentId}-${n.id}`,
      source: n.parentId!,
      target: n.id,
    }));

  return { nodes, edges, rootId: 'root' };
}

describe('Layout Algorithms', () => {
  describe('No Node Overlap', () => {
    it('should not have overlapping nodes after balanced layout with simple tree', () => {
      const data = createSimpleMindmap(5);
      const result = applyLayout(data, 'balanced', 1200, 800);
      
      expect(hasAnyOverlap(result.nodes)).toBe(false);
    });

    it('should not have overlapping nodes after balanced layout with many children', () => {
      const data = createSimpleMindmap(10);
      const result = applyLayout(data, 'balanced', 1200, 800);
      
      expect(hasAnyOverlap(result.nodes)).toBe(false);
    });

    it('should not have overlapping nodes after tree layout', () => {
      const data = createDeepTree(3, 3);
      const result = applyLayout(data, 'tree', 1200, 800);
      
      expect(hasAnyOverlap(result.nodes)).toBe(false);
    });

    it('should not have overlapping nodes after radial layout', () => {
      const data = createSimpleMindmap(8);
      const result = applyLayout(data, 'radial', 1200, 800);
      
      expect(hasAnyOverlap(result.nodes)).toBe(false);
    });

    it('should not have overlapping nodes for table markdown structure', () => {
      const data = createTableMarkdownMindmap();
      const result = applyLayout(data, 'balanced', 1200, 800);
      
      expect(hasAnyOverlap(result.nodes)).toBe(false);
    });

    it('should maintain minimum spacing between nodes', () => {
      const data = createSimpleMindmap(5);
      const result = applyLayout(data, 'balanced', 1200, 800);
      
      // Check with padding (should still not overlap with 20px padding)
      expect(hasAnyOverlap(result.nodes, 20)).toBe(false);
    });
  });

  describe('Balanced Layout Distribution', () => {
    it('should distribute children evenly on left and right', () => {
      const data = createSimpleMindmap(6);
      const result = balancedLayout(data, { centerX: 600, centerY: 400 });
      
      const root = result.nodes.find(n => n.depth === 0);
      const children = result.nodes.filter(n => n.depth === 1);
      
      if (root) {
        const leftChildren = children.filter(c => c.x < root.x);
        const rightChildren = children.filter(c => c.x > root.x);
        
        // Difference should be at most 1
        expect(Math.abs(leftChildren.length - rightChildren.length)).toBeLessThanOrEqual(1);
      }
    });

    it('should handle odd number of children', () => {
      const data = createSimpleMindmap(5);
      const result = balancedLayout(data, { centerX: 600, centerY: 400 });
      
      const root = result.nodes.find(n => n.depth === 0);
      const children = result.nodes.filter(n => n.depth === 1);
      
      if (root) {
        const leftChildren = children.filter(c => c.x < root.x);
        const rightChildren = children.filter(c => c.x > root.x);
        
        // Should still be balanced (3 on one side, 2 on other)
        expect(Math.abs(leftChildren.length - rightChildren.length)).toBeLessThanOrEqual(1);
      }
    });
  });

  describe('Parent-Child Hierarchy', () => {
    it('should position children further from center than parent in balanced layout', () => {
      const data = createDeepTree(2, 3);
      const result = balancedLayout(data, { centerX: 600, centerY: 400 });
      
      const root = result.nodes.find(n => n.depth === 0);
      if (!root) return;

      const children = result.nodes.filter(n => n.parentId === root.id);
      
      children.forEach(child => {
        const rootDistFromCenter = Math.abs(root.x - 600);
        const childDistFromCenter = Math.abs(child.x - 600);
        
        // Children should be further from center
        expect(childDistFromCenter).toBeGreaterThan(rootDistFromCenter);
      });
    });

    it('should position children to the right of parent in tree layout', () => {
      const data = createDeepTree(2, 3);
      const result = treeLayout(data, { centerX: 600, centerY: 400 });
      
      result.nodes.forEach(node => {
        if (node.parentId) {
          const parent = result.nodes.find(n => n.id === node.parentId);
          if (parent) {
            // In tree layout, children should be to the right of parent
            expect(node.x).toBeGreaterThan(parent.x);
          }
        }
      });
    });
  });

  describe('Performance', () => {
    it('should complete layout for 50 nodes within reasonable time', () => {
      const data = createDeepTree(4, 3); // Creates ~40 nodes
      
      const startTime = performance.now();
      applyLayout(data, 'balanced', 1200, 800);
      const endTime = performance.now();
      
      // Should complete within 100ms
      expect(endTime - startTime).toBeLessThan(100);
    });

    it('should complete layout for 100 nodes within reasonable time', () => {
      // Create a wider tree
      const nodes: MindmapNode[] = [
        { id: 'root', label: 'Root', content: 'Root', depth: 0, x: 0, y: 0, width: 200, height: 80, color: 'primary', status: 'complete' },
      ];
      const edges: MindmapData['edges'] = [];

      // Add 99 children directly to root
      for (let i = 0; i < 99; i++) {
        const childId = `child-${i}`;
        nodes.push({
          id: childId,
          label: `Child ${i}`,
          content: `Child ${i}`,
          depth: 1,
          parentId: 'root',
          x: 0,
          y: 0,
          width: 200,
          height: 80,
          color: 'blue',
          status: 'complete',
        });
        edges.push({ id: `edge-root-${childId}`, source: 'root', target: childId });
      }

      const data: MindmapData = { nodes, edges, rootId: 'root' };
      
      const startTime = performance.now();
      applyLayout(data, 'balanced', 1200, 800);
      const endTime = performance.now();
      
      // Should complete within 100ms
      expect(endTime - startTime).toBeLessThan(100);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty mindmap', () => {
      const data: MindmapData = { nodes: [], edges: [] };
      const result = applyLayout(data, 'balanced', 1200, 800);
      
      expect(result.nodes.length).toBe(0);
    });

    it('should handle single node mindmap', () => {
      const data: MindmapData = {
        nodes: [{
          id: 'root',
          label: 'Root',
          content: 'Root',
          depth: 0,
          x: 0,
          y: 0,
          width: 200,
          height: 80,
          color: 'primary',
          status: 'complete',
        }],
        edges: [],
        rootId: 'root',
      };
      
      const result = applyLayout(data, 'balanced', 1200, 800);
      
      expect(result.nodes.length).toBe(1);
      // Root should be centered
      expect(result.nodes[0].x).toBeCloseTo(600 - 100, 0); // centerX - width/2
    });

    it('should handle nodes without root', () => {
      const data: MindmapData = {
        nodes: [
          { id: 'n1', label: 'Node 1', content: 'Node 1', depth: 1, x: 0, y: 0, width: 200, height: 80, color: 'blue', status: 'complete' },
          { id: 'n2', label: 'Node 2', content: 'Node 2', depth: 1, x: 0, y: 0, width: 200, height: 80, color: 'blue', status: 'complete' },
        ],
        edges: [],
      };
      
      // Should not throw
      expect(() => applyLayout(data, 'balanced', 1200, 800)).not.toThrow();
    });
  });

  describe('Bounds Calculation', () => {
    it('should calculate correct bounds after layout', () => {
      const data = createSimpleMindmap(5);
      const result = applyLayout(data, 'balanced', 1200, 800);
      
      // Bounds should contain all nodes
      result.nodes.forEach(node => {
        expect(node.x).toBeGreaterThanOrEqual(result.bounds.minX);
        expect(node.y).toBeGreaterThanOrEqual(result.bounds.minY);
        expect(node.x + (node.width || 200)).toBeLessThanOrEqual(result.bounds.maxX);
        expect(node.y + (node.height || 80)).toBeLessThanOrEqual(result.bounds.maxY);
      });
    });
  });
});

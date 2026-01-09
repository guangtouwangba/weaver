import { CanvasNode, CanvasEdge } from './api';

/**
 * Layout constants for Thinking Path visualization
 */
const LAYOUT_CONFIG = {
  nodeWidth: 280,
  nodeHeight: 200,
  // Horizontal spacing between columns (Q -> A -> Insights)
  columnSpacing: 100,
  // Vertical spacing between nodes in the same column
  rowSpacing: 40,
  // Starting position
  startX: 100,
  startY: 100,
  // Spacing between Q&A groups
  groupSpacing: 150,
};

/**
 * Thinking Path Layout Algorithm
 * 
 * Creates a clear left-to-right flow:
 * 
 *   Question ──> Answer ──> Insight 1
 *                      ├──> Insight 2
 *                      └──> Insight 3
 * 
 * Multiple Q&A pairs are arranged vertically:
 * 
 *   Q1 ──> A1 ──> I1, I2
 *   Q2 ──> A2 ──> I3, I4, I5
 *   Q3 ──> A3 ──> I6
 */
export function layoutThinkingPath(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  options: {
    nodeWidth?: number;
    nodeHeight?: number;
    columnSpacing?: number;
    rowSpacing?: number;
  } = {}
): CanvasNode[] {
  if (nodes.length === 0) return [];

  const config = { ...LAYOUT_CONFIG, ...options };
  const { nodeWidth, nodeHeight, columnSpacing, rowSpacing, startX, startY, groupSpacing } = config;

  // Build adjacency list (source -> targets)
  const children: Record<string, string[]> = {};
  const parents: Record<string, string[]> = {};

  nodes.forEach(n => {
    children[n.id] = [];
    parents[n.id] = [];
  });

  edges.forEach(e => {
    if (children[e.source] && parents[e.target]) {
      children[e.source].push(e.target);
      parents[e.target].push(e.source);
    }
  });

  // Categorize nodes by type
  const questions = nodes.filter(n => n.type === 'question');
  const answers = nodes.filter(n => n.type === 'answer');
  const insights = nodes.filter(n => n.type === 'insight');
  const otherNodes = nodes.filter(n => !['question', 'answer', 'insight'].includes(n.type));

  // Create a map for fast lookup
  const nodeMap: Record<string, CanvasNode> = {};
  nodes.forEach(n => { nodeMap[n.id] = { ...n }; });

  // Track current Y position for each column
  let currentY = startY;

  // Process each Q&A group
  // Find Q -> A pairs by looking at edges
  const processedQuestions = new Set<string>();
  const processedAnswers = new Set<string>();
  const processedInsights = new Set<string>();

  // Sort questions by their original Y position or ID for stability
  questions.sort((a, b) => (a.y || 0) - (b.y || 0) || a.id.localeCompare(b.id));

  questions.forEach((question, qIndex) => {
    if (processedQuestions.has(question.id)) return;
    processedQuestions.add(question.id);

    // Find the answer connected to this question
    const connectedAnswerIds = children[question.id]?.filter(id =>
      nodeMap[id]?.type === 'answer'
    ) || [];

    // Calculate the height needed for this Q&A group
    let groupHeight = nodeHeight; // At least the question height

    // Position the question
    nodeMap[question.id].x = startX;
    nodeMap[question.id].y = currentY;

    if (connectedAnswerIds.length > 0) {
      const answerId = connectedAnswerIds[0]; // Take first answer
      processedAnswers.add(answerId);

      // Find insights connected to this answer
      const connectedInsightIds = children[answerId]?.filter(id =>
        nodeMap[id]?.type === 'insight'
      ) || [];

      // Calculate insight group height
      const insightCount = connectedInsightIds.length;
      const insightsHeight = insightCount > 0
        ? insightCount * nodeHeight + (insightCount - 1) * rowSpacing
        : 0;

      // The group height is the max of question height, answer height, and insights height
      groupHeight = Math.max(nodeHeight, insightsHeight);

      // Position answer (centered vertically within the group)
      const answerY = currentY + (groupHeight - nodeHeight) / 2;
      nodeMap[answerId].x = startX + nodeWidth + columnSpacing;
      nodeMap[answerId].y = answerY;

      // Position insights (fanned out vertically, centered around the answer)
      if (insightCount > 0) {
        const insightsStartY = currentY + (groupHeight - insightsHeight) / 2;

        connectedInsightIds.forEach((insightId, iIndex) => {
          processedInsights.add(insightId);
          nodeMap[insightId].x = startX + (nodeWidth + columnSpacing) * 2;
          nodeMap[insightId].y = insightsStartY + iIndex * (nodeHeight + rowSpacing);
        });
      }
    }

    // Move to next row for the next Q&A group
    currentY += groupHeight + groupSpacing;
  });

  // Handle orphan answers (not connected to any question)
  answers.forEach(answer => {
    if (processedAnswers.has(answer.id)) return;
    processedAnswers.add(answer.id);

    // Position orphan answer
    nodeMap[answer.id].x = startX + nodeWidth + columnSpacing;
    nodeMap[answer.id].y = currentY;

    // Find and position its insights
    const connectedInsightIds = children[answer.id]?.filter(id =>
      nodeMap[id]?.type === 'insight'
    ) || [];

    const insightCount = connectedInsightIds.length;
    const insightsHeight = insightCount > 0
      ? insightCount * nodeHeight + (insightCount - 1) * rowSpacing
      : 0;

    const groupHeight = Math.max(nodeHeight, insightsHeight);
    const insightsStartY = currentY + (groupHeight - insightsHeight) / 2;

    connectedInsightIds.forEach((insightId, iIndex) => {
      processedInsights.add(insightId);
      nodeMap[insightId].x = startX + (nodeWidth + columnSpacing) * 2;
      nodeMap[insightId].y = insightsStartY + iIndex * (nodeHeight + rowSpacing);
    });

    currentY += groupHeight + groupSpacing;
  });

  // Handle orphan insights (not connected to any answer)
  let orphanInsightY = currentY;
  insights.forEach(insight => {
    if (processedInsights.has(insight.id)) return;
    processedInsights.add(insight.id);

    nodeMap[insight.id].x = startX + (nodeWidth + columnSpacing) * 2;
    nodeMap[insight.id].y = orphanInsightY;
    orphanInsightY += nodeHeight + rowSpacing;
  });

  // Handle other node types (fallback to simple stacking)
  let otherY = Math.max(currentY, orphanInsightY);
  otherNodes.forEach(node => {
    nodeMap[node.id].x = startX;
    nodeMap[node.id].y = otherY;
    otherY += nodeHeight + rowSpacing;
  });

  // Return the updated nodes
  return nodes.map(n => nodeMap[n.id]);
}

/**
 * Simple hierarchical layout (generic, for non-thinking-path use cases)
 * Arranges nodes in a Left-to-Right tree structure based on edges
 */
export function layoutHierarchical(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  options: {
    direction?: 'LR' | 'TB';
    nodeWidth?: number;
    nodeHeight?: number;
    levelSpacing?: number;
    nodeSpacing?: number;
  } = {}
): CanvasNode[] {
  if (nodes.length === 0) return [];

  const {
    direction = 'LR',
    nodeWidth = 280,
    nodeHeight = 200,
    levelSpacing = 100,
    nodeSpacing = 40,
  } = options;

  // Build graph structure
  const adj: Record<string, string[]> = {};
  const inDegree: Record<string, number> = {};

  nodes.forEach(n => {
    adj[n.id] = [];
    inDegree[n.id] = 0;
  });

  edges.forEach(e => {
    if (adj[e.source]) {
      adj[e.source].push(e.target);
      inDegree[e.target] = (inDegree[e.target] || 0) + 1;
    }
  });

  // Assign levels (BFS)
  const levels: Record<string, number> = {};
  const queue: string[] = [];

  // Find roots (nodes with 0 in-degree)
  const roots = nodes.filter(n => (inDegree[n.id] || 0) === 0);
  if (roots.length === 0 && nodes.length > 0) {
    roots.push(nodes[0]);
  }

  roots.forEach(n => {
    levels[n.id] = 0;
    queue.push(n.id);
  });

  const visited = new Set<string>(roots.map(n => n.id));

  while (queue.length > 0) {
    const u = queue.shift()!;
    const uLevel = levels[u];

    if (adj[u]) {
      adj[u].forEach(v => {
        if (!visited.has(v)) {
          visited.add(v);
          levels[v] = uLevel + 1;
          queue.push(v);
        }
      });
    }
  }

  // Handle disconnected nodes
  nodes.forEach(n => {
    if (!visited.has(n.id)) {
      levels[n.id] = 0;
    }
  });

  // Group by level
  const levelNodes: Record<number, CanvasNode[]> = {};
  let maxLevel = 0;

  nodes.forEach(n => {
    const lvl = levels[n.id] || 0;
    maxLevel = Math.max(maxLevel, lvl);
    if (!levelNodes[lvl]) levelNodes[lvl] = [];
    levelNodes[lvl].push(n);
  });

  // Assign coordinates
  const newNodes = nodes.map(n => ({ ...n }));

  for (let l = 0; l <= maxLevel; l++) {
    const nodesInLevel = levelNodes[l] || [];
    nodesInLevel.sort((a, b) => a.id.localeCompare(b.id));

    let currentOffset = 0;

    nodesInLevel.forEach(n => {
      const nodeIndex = newNodes.findIndex(node => node.id === n.id);
      if (nodeIndex === -1) return;

      if (direction === 'LR') {
        newNodes[nodeIndex].x = l * (nodeWidth + levelSpacing);
        newNodes[nodeIndex].y = currentOffset;
        currentOffset += nodeHeight + nodeSpacing;
      } else {
        newNodes[nodeIndex].x = currentOffset;
        newNodes[nodeIndex].y = l * (nodeHeight + levelSpacing);
        currentOffset += nodeWidth + nodeSpacing;
      }
    });
  }

  // Center vertically for LR layout
  if (direction === 'LR') {
    const levelHeights: Record<number, number> = {};
    for (let l = 0; l <= maxLevel; l++) {
      const count = (levelNodes[l] || []).length;
      levelHeights[l] = count * nodeHeight + (count - 1) * nodeSpacing;
    }
    const maxH = Math.max(...Object.values(levelHeights));

    newNodes.forEach(n => {
      const lvl = levels[n.id] || 0;
      const h = levelHeights[lvl];
      const shiftY = (maxH - h) / 2;
      n.y += shiftY;
    });
  }

  return newNodes;
}

/**
 * Thinking Graph Layout Constants
 */
const THINKING_GRAPH_CONFIG = {
  nodeWidth: 320,
  nodeHeight: 200,
  // Horizontal spacing between depth levels
  levelSpacing: 400,
  // Vertical spacing between siblings
  siblingSpacing: 220,
  // Starting position
  startX: 100,
  startY: 100,
  // Branch node offset
  branchOffset: 180,
};

/**
 * Thinking Graph Layout Algorithm (Dynamic Mind Map)
 * 
 * Creates a horizontal tree structure where:
 * - Root nodes start on the left
 * - Children expand to the right
 * - Siblings are stacked vertically
 * 
 * Visual representation:
 * 
 *   Root Topic A ──> Step 1 ──> Step 2
 *                           ├──> Branch: Alternative
 *                           └──> Branch: Question
 *   
 *   Root Topic B ──> Step 1 ──> Step 2 ──> Step 3
 * 
 * @param nodes - All thinking graph nodes (type: thinking_step or thinking_branch)
 * @param edges - Edges connecting the nodes
 * @param options - Layout customization options
 * @returns Nodes with updated x, y positions
 */
export function layoutThinkingGraph(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  options: {
    nodeWidth?: number;
    nodeHeight?: number;
    levelSpacing?: number;
    siblingSpacing?: number;
    startX?: number;
    startY?: number;
  } = {}
): CanvasNode[] {
  if (nodes.length === 0) return [];

  const config = { ...THINKING_GRAPH_CONFIG, ...options };
  const { nodeWidth, levelSpacing, siblingSpacing, startX, startY, branchOffset } = config;

  // Filter to thinking graph nodes only
  const thinkingNodes = nodes.filter(n =>
    n.viewType === 'thinking' &&
    (n.type === 'thinking_step' || n.type === 'thinking_branch' ||
      n.type === 'question' || n.type === 'answer' || n.type === 'insight')
  );

  if (thinkingNodes.length === 0) return nodes;

  // Build adjacency maps
  const children: Record<string, string[]> = {};
  const parent: Record<string, string> = {};

  thinkingNodes.forEach(n => {
    children[n.id] = [];
    // Also check parentStepId for direct parent reference
    if (n.parentStepId) {
      parent[n.id] = n.parentStepId;
    }
  });

  // Build from edges
  edges.forEach(e => {
    const sourceNode = thinkingNodes.find(n => n.id === e.source);
    const targetNode = thinkingNodes.find(n => n.id === e.target);

    if (sourceNode && targetNode) {
      if (!children[e.source]) children[e.source] = [];
      children[e.source].push(e.target);

      if (!parent[e.target]) {
        parent[e.target] = e.source;
      }
    }
  });

  // Find root nodes (nodes with no parent)
  const roots = thinkingNodes.filter(n => !parent[n.id]);

  // If no explicit roots, use nodes with depth === 0 or the first node
  const effectiveRoots = roots.length > 0
    ? roots
    : thinkingNodes.filter(n => n.depth === 0 || n.depth === undefined);

  if (effectiveRoots.length === 0 && thinkingNodes.length > 0) {
    effectiveRoots.push(thinkingNodes[0]);
  }

  // Sort roots by their step index or creation time
  effectiveRoots.sort((a, b) => {
    const indexA = a.thinkingStepIndex || 0;
    const indexB = b.thinkingStepIndex || 0;
    return indexA - indexB;
  });

  // Create a mutable copy for positioning
  const nodeMap: Record<string, CanvasNode> = {};
  nodes.forEach(n => { nodeMap[n.id] = { ...n }; });

  // Recursive function to calculate subtree height
  function calculateSubtreeHeight(nodeId: string): number {
    const nodeChildren = children[nodeId] || [];
    if (nodeChildren.length === 0) {
      return config.nodeHeight;
    }

    let totalHeight = 0;
    nodeChildren.forEach((childId, index) => {
      totalHeight += calculateSubtreeHeight(childId);
      if (index < nodeChildren.length - 1) {
        totalHeight += siblingSpacing - config.nodeHeight; // Gap between siblings
      }
    });

    return Math.max(totalHeight, config.nodeHeight);
  }

  // Recursive function to position a node and its children
  function positionNode(
    nodeId: string,
    x: number,
    yStart: number,
    depth: number
  ): number {
    const node = nodeMap[nodeId];
    if (!node) return yStart;

    const nodeChildren = children[nodeId] || [];

    // Calculate total height needed for children
    const subtreeHeight = calculateSubtreeHeight(nodeId);

    // Position children first to center parent
    let childY = yStart;
    const childPositions: number[] = [];

    nodeChildren.forEach((childId, index) => {
      const childNode = nodeMap[childId];
      const isBranch = childNode?.type === 'thinking_branch';

      // Branch nodes get a smaller horizontal offset
      const childX = isBranch
        ? x + nodeWidth + branchOffset
        : x + nodeWidth + levelSpacing - nodeWidth;

      childPositions.push(childY);
      childY = positionNode(childId, childX, childY, depth + 1);

      if (index < nodeChildren.length - 1) {
        childY += siblingSpacing - config.nodeHeight;
      }
    });

    // Calculate parent Y position (center among children or at yStart if no children)
    let nodeY: number;
    if (childPositions.length > 0) {
      // Center parent vertically among its children
      const firstChildY = childPositions[0];
      const lastChildY = childPositions[childPositions.length - 1];
      nodeY = (firstChildY + lastChildY) / 2;
    } else {
      nodeY = yStart;
    }

    // Update node position
    nodeMap[nodeId].x = x;
    nodeMap[nodeId].y = nodeY;
    nodeMap[nodeId].depth = depth;

    // Return the bottom of this subtree
    return Math.max(nodeY + config.nodeHeight, childY);
  }

  // Position each root tree
  let currentRootY = startY;

  effectiveRoots.forEach((root) => {
    const treeHeight = positionNode(root.id, startX, currentRootY, 0);
    currentRootY = treeHeight + siblingSpacing;
  });

  // Return all nodes with updated positions
  return nodes.map(n => nodeMap[n.id] || n);
}

/**
 * Auto-layout for a single new node in the thinking graph
 * 
 * This is used for optimistic UI when adding a new draft node.
 * It calculates the position based on the parent node without
 * reorganizing the entire graph.
 * 
 * @param parentNode - The parent node to attach to (or null for new root)
 * @param existingSiblings - Other nodes that share the same parent
 * @param options - Layout options
 * @returns The calculated position { x, y, depth }
 */
export function calculateThinkingNodePosition(
  parentNode: CanvasNode | null,
  existingSiblings: CanvasNode[],
  options: {
    levelSpacing?: number;
    siblingSpacing?: number;
    isBranch?: boolean;
  } = {}
): { x: number; y: number; depth: number } {
  const config = { ...THINKING_GRAPH_CONFIG, ...options };
  const { levelSpacing, siblingSpacing, startX, startY, branchOffset, nodeHeight } = config;

  if (!parentNode) {
    // New root node
    if (existingSiblings.length === 0) {
      return { x: startX, y: startY, depth: 0 };
    }

    // Find the bottom-most root sibling
    const maxY = Math.max(...existingSiblings.map(n => n.y + nodeHeight));
    return { x: startX, y: maxY + siblingSpacing, depth: 0 };
  }

  // Child of existing node
  const parentDepth = parentNode.depth || 0;
  const newDepth = parentDepth + 1;

  // Calculate X based on whether this is a branch
  const xOffset = options.isBranch ? branchOffset : levelSpacing;
  const newX = parentNode.x + THINKING_GRAPH_CONFIG.nodeWidth + xOffset - THINKING_GRAPH_CONFIG.nodeWidth;

  // Calculate Y based on existing siblings
  if (existingSiblings.length === 0) {
    // First child - position at parent's Y
    return { x: newX, y: parentNode.y, depth: newDepth };
  }

  // Find the bottom-most sibling
  const maxSiblingY = Math.max(...existingSiblings.map(n => n.y + nodeHeight));
  return { x: newX, y: maxSiblingY + siblingSpacing - nodeHeight, depth: newDepth };
}

// =============================================================================
// PARKING SECTION LAYOUT
// =============================================================================

/**
 * Parking Section Configuration
 * 
 * The Parking Section is a special area on the canvas where users can
 * temporarily "park" nodes for later consideration. It's placed on the
 * left side of the main canvas to keep it out of the way.
 */
export const PARKING_SECTION_CONFIG = {
  // Position (left of main canvas)
  x: -450,
  y: 100,
  // Size
  width: 350,
  minHeight: 400,
  // Internal spacing
  padding: 20,
  nodeSpacing: 30,
  // Visual
  title: '暂存区 (Parking)',
  backgroundColor: '#F9FAFB',  // Light gray
  borderColor: '#E5E7EB',      // Border gray
  headerHeight: 40,
};

/**
 * Section interface for Parking
 */
export interface ParkingSection {
  id: string;
  title: string;
  x: number;
  y: number;
  width: number;
  height: number;
  nodeIds: string[];
}

/**
 * Create or update the Parking Section
 * 
 * @param existingSection - Existing parking section (if any)
 * @param parkedNodeIds - IDs of nodes to include in parking
 * @returns Updated ParkingSection configuration
 */
export function createParkingSection(
  existingSection: ParkingSection | null,
  parkedNodeIds: string[]
): ParkingSection {
  const nodeCount = parkedNodeIds.length;
  const calculatedHeight = Math.max(
    PARKING_SECTION_CONFIG.minHeight,
    PARKING_SECTION_CONFIG.headerHeight +
    PARKING_SECTION_CONFIG.padding * 2 +
    nodeCount * (LAYOUT_CONFIG.nodeHeight + PARKING_SECTION_CONFIG.nodeSpacing)
  );

  return {
    id: existingSection?.id || `parking-section-${crypto.randomUUID()}`,
    title: PARKING_SECTION_CONFIG.title,
    x: PARKING_SECTION_CONFIG.x,
    y: PARKING_SECTION_CONFIG.y,
    width: PARKING_SECTION_CONFIG.width,
    height: calculatedHeight,
    nodeIds: parkedNodeIds,
  };
}

/**
 * Layout nodes within the Parking Section
 * 
 * Arranges parked nodes in a vertical stack within the section bounds.
 * 
 * @param nodes - Nodes to layout (only parked nodes)
 * @param section - The parking section
 * @returns Nodes with updated positions
 */
export function layoutParkingNodes(
  nodes: CanvasNode[],
  section: ParkingSection
): CanvasNode[] {
  if (nodes.length === 0) return [];

  const startX = section.x + PARKING_SECTION_CONFIG.padding;
  const startY = section.y + PARKING_SECTION_CONFIG.headerHeight + PARKING_SECTION_CONFIG.padding;

  // Scale down nodes slightly to fit parking area
  const scaledWidth = PARKING_SECTION_CONFIG.width - PARKING_SECTION_CONFIG.padding * 2;
  const scaledHeight = 120; // Smaller height for parked nodes

  return nodes.map((node, index) => ({
    ...node,
    x: startX,
    y: startY + index * (scaledHeight + PARKING_SECTION_CONFIG.nodeSpacing),
    width: scaledWidth,
    height: scaledHeight,
    // Mark as parked for styling
    isParked: true,
  }));
}

/**
 * Check if a position is within the Parking Section
 * 
 * @param x - X coordinate
 * @param y - Y coordinate
 * @param section - The parking section
 * @returns true if position is within the section
 */
export function isWithinParkingSection(
  x: number,
  y: number,
  section: ParkingSection
): boolean {
  return (
    x >= section.x &&
    x <= section.x + section.width &&
    y >= section.y &&
    y <= section.y + section.height
  );
}

/**
 * Get the position for a node being dropped into Parking Section
 * 
 * @param section - The parking section
 * @param existingParkedNodes - Nodes already in parking
 * @returns Position { x, y } for the new parked node
 */
export function getDropPositionInParking(
  section: ParkingSection,
  existingParkedNodes: CanvasNode[]
): { x: number; y: number } {
  const startX = section.x + PARKING_SECTION_CONFIG.padding;
  const startY = section.y + PARKING_SECTION_CONFIG.headerHeight + PARKING_SECTION_CONFIG.padding;
  const scaledHeight = 120;

  const y = startY + existingParkedNodes.length * (scaledHeight + PARKING_SECTION_CONFIG.nodeSpacing);  return { x: startX, y };
}

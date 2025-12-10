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



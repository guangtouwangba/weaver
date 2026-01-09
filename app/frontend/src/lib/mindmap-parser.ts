/**
 * Mindmap Markdown Parser
 *
 * Parses markdown outline format into MindmapNode and MindmapEdge structures.
 * This enables batch mindmap generation where backend returns raw markdown
 * and frontend handles parsing and rendering.
 *
 * Markdown format:
 * - # Root Title
 * - - Level 1 bullet
 *   - Level 2 bullet (2-space indent per level)
 * - Source markers: [Page X], [Page X-Y], [MM:SS], [HH:MM:SS]
 */

import { MindmapNode, MindmapEdge, MindmapData, SourceRef } from './api';

// Layout constants (should match backend)
const NODE_WIDTH = 200;
const NODE_HEIGHT = 80;

// Colors by depth level
const COLORS_BY_LEVEL = ['primary', 'blue', 'green', 'orange', 'purple', 'pink'];

function getColorForLevel(level: number): string {
  return COLORS_BY_LEVEL[level % COLORS_BY_LEVEL.length];
}

/**
 * Parse source markers from text and return clean text + source refs.
 *
 * Supports:
 * - [Page X] or [Page X-Y] for PDFs
 * - [MM:SS] or [HH:MM:SS] for videos
 * 
 * @param text - The text containing source markers
 * @param documentId - Optional document ID for source references
 * @param useTextAsQuote - If true, use the clean text as the quote for each ref
 */
function parseSourceMarkers(
  text: string,
  documentId?: string,
  useTextAsQuote: boolean = true
): { cleanText: string; sourceRefs: SourceRef[] } {
  const sourceRefs: SourceRef[] = [];

  // Pattern for page markers: [Page 15] or [Page 15-17] or [PAGE:15]
  const pagePattern = /\[(?:Page\s*|PAGE:)(\d+)(?:\s*-\s*(\d+))?\]/gi;

  // Pattern for time markers: [TIME:12:30] or [TIME:1:23:45] (also legacy [12:30])
  const timePattern = /\[(?:TIME:)?(\d{1,2}:\d{2}(?::\d{2})?)\]/g;

  // Remove markers from text first to get clean text
  let cleanText = text.replace(pagePattern, '').replace(timePattern, '').trim();

  // Quote to use for source refs (the clean text content provides context)
  const quoteText = useTextAsQuote ? cleanText : '';

  // Reset patterns for matching
  let match;
  const pagePatternForMatch = /\[(?:Page\s*|PAGE:)(\d+)(?:\s*-\s*(\d+))?\]/gi;
  while ((match = pagePatternForMatch.exec(text)) !== null) {
    const pageStart = match[1];
    const pageEnd = match[2] || pageStart;
    sourceRefs.push({
      sourceId: documentId || '',
      sourceType: 'document',
      location: pageStart === pageEnd ? `Page ${pageStart}` : `Page ${pageStart}-${pageEnd}`,
      quote: quoteText,
    });
  }

  const timePatternForMatch = /\[(?:TIME:)?(\d{1,2}:\d{2}(?::\d{2})?)\]/g;
  while ((match = timePatternForMatch.exec(text)) !== null) {
    sourceRefs.push({
      sourceId: documentId || '',
      sourceType: 'video',
      location: match[1],
      quote: quoteText,
    });
  }

  return { cleanText, sourceRefs };
}

/**
 * Generate a unique node ID.
 */
function generateNodeId(): string {
  return `node-${Math.random().toString(36).substr(2, 8)}`;
}

export interface ParseResult {
  nodes: MindmapNode[];
  edges: MindmapEdge[];
  rootId: string | null;
}

/**
 * Parse markdown outline to MindmapNode and MindmapEdge structures.
 *
 * @param markdown - Raw markdown outline
 * @param documentId - Optional document ID for source references
 * @returns ParseResult with nodes, edges, and root ID
 */
export function parseMarkdownToMindmap(
  markdown: string,
  documentId?: string
): ParseResult {
  const nodes: MindmapNode[] = [];
  const edges: MindmapEdge[] = [];
  let rootId: string | null = null;

  console.log('[MindmapParser] ========== PARSING MINDMAP MARKDOWN ==========');
  console.log('[MindmapParser] Document ID:', documentId || 'none');
  console.log('[MindmapParser] Input markdown length:', markdown?.length || 0);
  console.log('[MindmapParser] Full markdown content:');
  console.log('------- MARKDOWN START -------');
  console.log(markdown);
  console.log('------- MARKDOWN END -------');

  if (!markdown || !markdown.trim()) {
    console.log('[MindmapParser] Empty markdown, returning empty result');
    return { nodes, edges, rootId };
  }

  const lines = markdown.trim().split('\n');
  console.log('[MindmapParser] Total lines:', lines.length);

  // Stack to track parent nodes at each indent level
  // Each entry: { nodeId, indentLevel }
  const parentStack: Array<{ nodeId: string; indentLevel: number }> = [];

  // Track if we've seen the root heading yet
  let hasRoot = false;

  for (const line of lines) {
    if (!line.trim()) {
      continue;
    }

    // Check if it's a heading (# for root, ## for level 1, etc.)
    const headingMatch = line.match(/^(#+)\s*(.+)$/);
    if (headingMatch) {
      const headingLevel = headingMatch[1].length; // Number of # characters
      const label = headingMatch[2].trim();
      const { cleanText, sourceRefs } = parseSourceMarkers(label, documentId);

      const nodeId = generateNodeId();

      // First heading becomes root (depth 0), subsequent headings become children
      // Heading level: # = root (depth 0), ## = depth 1, ### = depth 2, etc.
      let depth: number;
      let parentId: string | null = null;

      if (!hasRoot) {
        // First heading is always root
        depth = 0;
        hasRoot = true;
        parentStack.length = 0;
        parentStack.push({ nodeId, indentLevel: -1 }); // Root is at indent -1
        rootId = nodeId;
      } else {
        // Subsequent headings: calculate depth based on heading level
        // ## = depth 1, ### = depth 2, etc.
        depth = headingLevel - 1;

        // Find parent: pop stack until we find a node at smaller depth
        while (parentStack.length > 0 && parentStack[parentStack.length - 1].indentLevel >= (headingLevel - 2)) {
          parentStack.pop();
        }

        parentId = parentStack.length > 0 ? parentStack[parentStack.length - 1].nodeId : rootId;
        parentStack.push({ nodeId, indentLevel: headingLevel - 2 });
      }

      const node: MindmapNode = {
        id: nodeId,
        label: cleanText.substring(0, 50), // Limit label length
        content: cleanText,
        depth,
        parentId: parentId || undefined,
        x: 0, // Frontend will apply layout
        y: 0,
        width: NODE_WIDTH,
        height: NODE_HEIGHT,
        color: depth === 0 ? 'primary' : getColorForLevel(depth),
        status: 'complete',
        sourceRefs: sourceRefs.length > 0 ? sourceRefs : undefined,
      };
      nodes.push(node);

      // Create edge to parent if not root
      if (parentId) {
        const edgeId = `edge-${parentId}-${nodeId}`;
        edges.push({
          id: edgeId,
          source: parentId,
          target: nodeId,
        });
      }

      continue;
    }

    // Check if it's a bullet point
    const bulletMatch = line.match(/^(\s*)-\s*(.+)$/);
    if (bulletMatch) {
      const indent = bulletMatch[1].length;
      const label = bulletMatch[2].trim();
      const { cleanText, sourceRefs } = parseSourceMarkers(label, documentId);

      // Calculate depth based on indent (2 spaces per level)
      const depth = Math.floor(indent / 2) + 1;

      // Find parent by popping stack until we find smaller indent
      while (parentStack.length > 0 && parentStack[parentStack.length - 1].indentLevel >= indent) {
        parentStack.pop();
      }

      const parentId = parentStack.length > 0 ? parentStack[parentStack.length - 1].nodeId : rootId;

      const nodeId = generateNodeId();
      const node: MindmapNode = {
        id: nodeId,
        label: cleanText.substring(0, 50), // Limit label length
        content: cleanText,
        depth,
        parentId: parentId || undefined,
        x: 0, // Frontend will apply layout
        y: 0,
        width: NODE_WIDTH,
        height: NODE_HEIGHT,
        color: getColorForLevel(depth),
        status: 'complete',
        sourceRefs: sourceRefs.length > 0 ? sourceRefs : undefined,
      };
      nodes.push(node);

      // Create edge
      if (parentId) {
        const edgeId = `edge-${parentId}-${nodeId}`;
        edges.push({
          id: edgeId,
          source: parentId,
          target: nodeId,
        });
      }

      // Push to stack
      parentStack.push({ nodeId, indentLevel: indent });
    }
  }

  console.log('[MindmapParser] Parsed:', nodes.length, 'nodes,', edges.length, 'edges, rootId:', rootId);
  return { nodes, edges, rootId };
}

/**
 * Convert ParseResult to MindmapData format.
 */
export function toMindmapData(result: ParseResult): MindmapData {
  return {
    nodes: result.nodes,
    edges: result.edges,
    rootId: result.rootId || undefined,
  };
}

/**
 * Parse markdown and return MindmapData directly.
 *
 * Convenience function combining parseMarkdownToMindmap and toMindmapData.
 */
export function parseMindmapFromMarkdown(
  markdown: string,
  documentId?: string
): MindmapData {
  const result = parseMarkdownToMindmap(markdown, documentId);
  return toMindmapData(result);
}

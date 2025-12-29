'use client';

import { useMemo } from 'react';
import RBush from 'rbush';

/**
 * SpatialItem represents a node's bounding box for spatial queries.
 */
export interface SpatialItem {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
    nodeId: string;
}

/**
 * CanvasNodeLike - minimal interface for nodes that can be spatially indexed.
 */
export interface CanvasNodeLike {
    id: string;
    x: number;
    y: number;
    width?: number;
    height?: number;
}

/**
 * useSpatialIndex - Returns a memoized RBush spatial index for efficient O(log N) queries.
 * 
 * @param nodes - Array of canvas nodes to index
 * @param defaultWidth - Default width for nodes without explicit width (default: 280)
 * @param defaultHeight - Default height for nodes without explicit height (default: 200)
 * @returns RBush tree for spatial queries
 * 
 * @example
 * ```tsx
 * const spatialIndex = useSpatialIndex(nodes);
 * 
 * // Query nodes in a bounding box (e.g., for box selection)
 * const selected = spatialIndex.search({
 *   minX: selectionRect.x,
 *   minY: selectionRect.y,
 *   maxX: selectionRect.x + selectionRect.width,
 *   maxY: selectionRect.y + selectionRect.height,
 * });
 * ```
 */
export function useSpatialIndex(
    nodes: CanvasNodeLike[],
    defaultWidth: number = 280,
    defaultHeight: number = 200
): RBush<SpatialItem> {
    return useMemo(() => {
        const tree = new RBush<SpatialItem>();

        if (nodes.length === 0) {
            return tree;
        }

        const items: SpatialItem[] = nodes.map(node => ({
            minX: node.x,
            minY: node.y,
            maxX: node.x + (node.width ?? defaultWidth),
            maxY: node.y + (node.height ?? defaultHeight),
            nodeId: node.id,
        }));

        // Bulk load is 2-3x faster than individual inserts
        tree.load(items);

        return tree;
    }, [nodes, defaultWidth, defaultHeight]);
}

/**
 * Helper to get node IDs from spatial query results.
 */
export function getNodeIdsFromSpatialResults(results: SpatialItem[]): Set<string> {
    return new Set(results.map(item => item.nodeId));
}

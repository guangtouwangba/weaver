'use client';

import { useMemo } from 'react';
import RBush from 'rbush';
import { SpatialItem, CanvasNodeLike, getNodeIdsFromSpatialResults } from './useSpatialIndex';

/**
 * Viewport represents the current canvas view state.
 */
export interface Viewport {
    x: number;
    y: number;
    scale: number;
}

/**
 * Dimensions represents the canvas container size in screen pixels.
 */
export interface Dimensions {
    width: number;
    height: number;
}

/**
 * useViewportCulling - Returns only nodes that are visible within the current viewport.
 * 
 * Uses spatial indexing for O(log N) query instead of O(N) filter.
 * Includes padding buffer to prevent pop-in during fast panning.
 * 
 * @param viewport - Current canvas viewport (x, y, scale)
 * @param dimensions - Canvas container dimensions in screen pixels
 * @param spatialIndex - RBush spatial index from useSpatialIndex hook
 * @param nodes - Full array of canvas nodes
 * @param padding - Extra padding in canvas coordinates (default: 200px)
 * @returns Filtered array of visible nodes
 * 
 * @example
 * ```tsx
 * const spatialIndex = useSpatialIndex(nodes);
 * const visibleNodes = useViewportCulling(viewport, dimensions, spatialIndex, nodes);
 * 
 * // Only render visible nodes
 * {visibleNodes.map(node => <CanvasNode key={node.id} {...node} />)}
 * ```
 */
export function useViewportCulling<T extends CanvasNodeLike>(
    viewport: Viewport,
    dimensions: Dimensions,
    spatialIndex: RBush<SpatialItem>,
    nodes: T[],
    padding: number = 200
): T[] {
    return useMemo(() => {
        // If no nodes or no spatial index, return empty
        if (nodes.length === 0) {
            return [];
        }

        // Compute viewport bounds in canvas coordinates
        const bounds = {
            minX: -viewport.x / viewport.scale,
            minY: -viewport.y / viewport.scale,
            maxX: (-viewport.x + dimensions.width) / viewport.scale,
            maxY: (-viewport.y + dimensions.height) / viewport.scale,
        };

        // Add padding to prevent pop-in during fast panning
        const paddedBounds = {
            minX: bounds.minX - padding,
            minY: bounds.minY - padding,
            maxX: bounds.maxX + padding,
            maxY: bounds.maxY + padding,
        };

        // Query spatial index for nodes within viewport bounds
        const visibleItems = spatialIndex.search(paddedBounds);

        // If all nodes are visible, return original array (avoid new array allocation)
        if (visibleItems.length === nodes.length) {
            return nodes;
        }

        // Build set of visible node IDs for O(1) lookup
        const visibleIds = getNodeIdsFromSpatialResults(visibleItems);

        // Filter nodes to only include visible ones
        return nodes.filter(node => visibleIds.has(node.id));
    }, [viewport.x, viewport.y, viewport.scale, dimensions.width, dimensions.height, spatialIndex, nodes, padding]);
}

/**
 * Helper to compute viewport bounds in canvas coordinates.
 * Useful for debugging or custom viewport logic.
 */
export function computeViewportBounds(
    viewport: Viewport,
    dimensions: Dimensions,
    padding: number = 0
): { minX: number; minY: number; maxX: number; maxY: number } {
    return {
        minX: -viewport.x / viewport.scale - padding,
        minY: -viewport.y / viewport.scale - padding,
        maxX: (-viewport.x + dimensions.width) / viewport.scale + padding,
        maxY: (-viewport.y + dimensions.height) / viewport.scale + padding,
    };
}

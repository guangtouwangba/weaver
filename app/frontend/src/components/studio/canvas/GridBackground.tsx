'use client';

import React, { memo } from 'react';
import { Shape, Group } from 'react-konva';

interface GridBackgroundProps {
    viewport: {
        x: number;
        y: number;
        scale: number;
    };
    dimensions: {
        width: number;
        height: number;
    };
    gridSize?: number;
    dotRadius?: number;
    dotColor?: string;
}

/**
 * GridBackground - Optimized infinite dot grid using native canvas API.
 * 
 * Uses a single Konva Shape with native canvas arc() calls instead of
 * individual Circle components. This is orders of magnitude faster
 * as it creates a single draw call vs O(N²) React elements.
 * 
 * @example
 * ```tsx
 * <GridBackground 
 *   viewport={viewport} 
 *   dimensions={dimensions} 
 * />
 * ```
 */
const GridBackground = memo(function GridBackground({
    viewport,
    dimensions,
    gridSize = 20,
    dotRadius = 1.5,
    dotColor = '#E7E5E4',
}: GridBackgroundProps) {
    return (
        <Group listening={false}>
            <Shape
                sceneFunc={(ctx) => {
                    // Calculate grid boundaries based on viewport to only draw visible dots
                    const startX = Math.floor((-viewport.x / viewport.scale) / gridSize) * gridSize;
                    const startY = Math.floor((-viewport.y / viewport.scale) / gridSize) * gridSize;
                    const endX = Math.ceil(((-viewport.x + dimensions.width) / viewport.scale) / gridSize) * gridSize;
                    const endY = Math.ceil(((-viewport.y + dimensions.height) / viewport.scale) / gridSize) * gridSize;

                    ctx.fillStyle = dotColor;

                    // Draw all dots in a single path for maximum efficiency
                    for (let x = startX; x <= endX; x += gridSize) {
                        for (let y = startY; y <= endY; y += gridSize) {
                            ctx.beginPath();
                            ctx.arc(x, y, dotRadius, 0, Math.PI * 2);
                            ctx.fill();
                        }
                    }
                }}
                listening={false}
            />
        </Group>
    );
}, (prevProps, nextProps) => {
    // Custom comparison to avoid re-renders when nothing visible has changed
    // We compare the computed grid boundaries, not just the raw viewport
    const gridSize = prevProps.gridSize || 20;

    const prevStartX = Math.floor((-prevProps.viewport.x / prevProps.viewport.scale) / gridSize) * gridSize;
    const prevStartY = Math.floor((-prevProps.viewport.y / prevProps.viewport.scale) / gridSize) * gridSize;
    const prevEndX = Math.ceil(((-prevProps.viewport.x + prevProps.dimensions.width) / prevProps.viewport.scale) / gridSize) * gridSize;
    const prevEndY = Math.ceil(((-prevProps.viewport.y + prevProps.dimensions.height) / prevProps.viewport.scale) / gridSize) * gridSize;

    const nextStartX = Math.floor((-nextProps.viewport.x / nextProps.viewport.scale) / gridSize) * gridSize;
    const nextStartY = Math.floor((-nextProps.viewport.y / nextProps.viewport.scale) / gridSize) * gridSize;
    const nextEndX = Math.ceil(((-nextProps.viewport.x + nextProps.dimensions.width) / nextProps.viewport.scale) / gridSize) * gridSize;
    const nextEndY = Math.ceil(((-nextProps.viewport.y + nextProps.dimensions.height) / nextProps.viewport.scale) / gridSize) * gridSize;

    return (
        prevStartX === nextStartX &&
        prevStartY === nextStartY &&
        prevEndX === nextEndX &&
        prevEndY === nextEndY &&
        prevProps.dotColor === nextProps.dotColor &&
        prevProps.dotRadius === nextProps.dotRadius
    );
});

export default GridBackground;

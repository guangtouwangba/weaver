'use client';

import React from 'react';
import { radii, colors } from '../tokens';

/**
 * Skeleton Component
 *
 * Loading placeholder with consistent styling.
 * Pure CSS implementation.
 */

export interface SkeletonProps extends React.HTMLAttributes<HTMLSpanElement> {
    /** Skeleton variant */
    variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
    /** Border radius for rounded variant */
    radius?: keyof typeof radii;
    width?: number | string;
    height?: number | string;
}

export const Skeleton = React.forwardRef<HTMLSpanElement, SkeletonProps>(
    function Skeleton(
        { variant = 'rounded', radius = 'md', className, style, width, height, ...props },
        ref
    ) {
        return (
            <span
                ref={ref}
                className={className}
                style={{
                    display: 'block',
                    backgroundColor: colors.neutral[200],
                    borderRadius: variant === 'circular' ? '50%' :
                                  variant === 'rounded' ? radii[radius] :
                                  variant === 'text' ? radii.sm : 0,
                    width: width,
                    height: height,
                    animation: 'skeleton-pulse 1.5s ease-in-out 0.5s infinite',
                    ...style,
                }}
                {...props}
            >
                <style dangerouslySetInnerHTML={{
                    __html: `
                        @keyframes skeleton-pulse {
                            0% { opacity: 1; }
                            50% { opacity: 0.4; }
                            100% { opacity: 1; }
                        }
                    `
                }} />
                &nbsp;
            </span>
        );
    }
);

Skeleton.displayName = 'Skeleton';

export default Skeleton;

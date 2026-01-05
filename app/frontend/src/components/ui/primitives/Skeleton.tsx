'use client';

import React from 'react';
import { Skeleton as MuiSkeleton, SkeletonProps as MuiSkeletonProps } from '@mui/material';
import { radii, colors } from '../tokens';

/**
 * Skeleton Component
 *
 * Loading placeholder with consistent styling.
 * Wraps MUI Skeleton.
 */

export interface SkeletonProps extends Omit<MuiSkeletonProps, 'variant'> {
    /** Skeleton variant */
    variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
    /** Border radius for rounded variant */
    radius?: keyof typeof radii;
}

export const Skeleton = React.forwardRef<HTMLSpanElement, SkeletonProps>(
    function Skeleton(
        { variant = 'rounded', radius = 'md', sx, ...props },
        ref
    ) {
        return (
            <MuiSkeleton
                ref={ref}
                variant={variant === 'rounded' ? 'rectangular' : variant}
                sx={{
                    bgcolor: colors.neutral[200],
                    ...(variant === 'rounded' && {
                        borderRadius: `${radii[radius]}px`,
                    }),
                    ...sx,
                }}
                {...props}
            />
        );
    }
);

Skeleton.displayName = 'Skeleton';

export default Skeleton;

'use client';

import React from 'react';
import { CircularProgress, CircularProgressProps } from '@mui/material';
import { colors } from '../tokens';

/**
 * Spinner Component
 *
 * Loading indicator with consistent styling.
 * Wraps MUI CircularProgress.
 */

export interface SpinnerProps extends Omit<CircularProgressProps, 'size' | 'color'> {
    /** Spinner size */
    size?: 'xs' | 'sm' | 'md' | 'lg' | number;
    /** Spinner color */
    color?: 'primary' | 'secondary' | 'inherit';
}

const sizeMap = {
    xs: 12,
    sm: 16,
    md: 24,
    lg: 32,
};

const colorMap = {
    primary: colors.primary[500],
    secondary: colors.neutral[500],
    inherit: 'inherit',
};

export const Spinner = React.forwardRef<HTMLSpanElement, SpinnerProps>(
    function Spinner({ size = 'md', color = 'primary', sx, ...props }, ref) {
        const sizeValue = typeof size === 'number' ? size : sizeMap[size];
        const colorValue = colorMap[color];

        return (
            <CircularProgress
                ref={ref}
                size={sizeValue}
                sx={{
                    color: colorValue,
                    ...sx,
                }}
                {...props}
            />
        );
    }
);

Spinner.displayName = 'Spinner';

export default Spinner;

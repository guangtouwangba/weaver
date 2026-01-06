'use client';

import React from 'react';
import { colors } from '../tokens';

/**
 * Spinner Component
 *
 * Loading indicator with consistent styling.
 * Pure CSS implementation.
 */

export interface SpinnerProps extends React.HTMLAttributes<HTMLSpanElement> {
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
    inherit: 'currentColor',
};

export const Spinner = React.forwardRef<HTMLSpanElement, SpinnerProps>(
    function Spinner({ size = 'md', color = 'primary', style, className, ...props }, ref) {
        const sizeValue = typeof size === 'number' ? size : sizeMap[size];
        const colorValue = colorMap[color];

        return (
            <span
                ref={ref}
                className={className}
                style={{
                    display: 'inline-block',
                    width: sizeValue,
                    height: sizeValue,
                    border: `2px solid ${colorValue === 'currentColor' ? 'currentColor' : colors.neutral[200]}`,
                    borderTopColor: colorValue === 'currentColor' ? 'transparent' : colorValue,
                    borderRadius: '50%',
                    animation: 'spin 0.75s linear infinite',
                    ...style,
                }}
                {...props}
            >
                <style dangerouslySetInnerHTML={{
                    __html: `
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                    `
                }} />
            </span>
        );
    }
);

Spinner.displayName = 'Spinner';

export default Spinner;

'use client';

import React from 'react';
import { elevation, ElevationLevel, radii, RadiusScale, spacing as spacingTokens, colors } from '../tokens';

/**
 * Surface Component
 *
 * An elevated container with consistent shadows and padding.
 * Pure CSS implementation.
 */

export interface SurfaceProps extends React.HTMLAttributes<HTMLDivElement> {
    /** Elevation level (0-6) */
    elevation?: ElevationLevel;
    /** Border radius */
    radius?: RadiusScale;
    /** Padding using spacing scale */
    padding?: keyof typeof spacingTokens | number;
    /** Whether to show border */
    bordered?: boolean;
    children?: React.ReactNode;
}

export const Surface = React.forwardRef<HTMLDivElement, SurfaceProps>(
    function Surface(
        {
            elevation: level = 1,
            radius = 'lg',
            padding,
            bordered = false,
            children,
            style,
            className,
            ...props
        },
        ref
    ) {
        const paddingValue = padding !== undefined
            ? typeof padding === 'number'
                ? spacingTokens[padding as keyof typeof spacingTokens] ?? padding
                : spacingTokens[padding as keyof typeof spacingTokens]
            : undefined;

        return (
            <div
                ref={ref}
                className={className}
                style={{
                    boxShadow: elevation[level],
                    borderRadius: `${radii[radius]}px`,
                    padding: paddingValue ? `${paddingValue}px` : undefined,
                    backgroundColor: colors.background.paper,
                    border: bordered ? `1px solid ${colors.border.default}` : undefined,
                    ...style,
                }}
                {...props}
            >
                {children}
            </div>
        );
    }
);

Surface.displayName = 'Surface';

export default Surface;

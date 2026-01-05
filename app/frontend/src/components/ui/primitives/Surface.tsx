'use client';

import React from 'react';
import { Paper, PaperProps } from '@mui/material';
import { elevation, ElevationLevel, radii, RadiusScale, spacing as spacingTokens, colors } from '../tokens';

/**
 * Surface Component
 *
 * An elevated container with consistent shadows and padding.
 * Wraps MUI Paper with design system tokens.
 */

export interface SurfaceProps extends Omit<PaperProps, 'elevation'> {
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
            sx,
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
            <Paper
                ref={ref}
                elevation={0}
                sx={{
                    boxShadow: elevation[level],
                    borderRadius: `${radii[radius]}px`,
                    padding: paddingValue ? `${paddingValue}px` : undefined,
                    bgcolor: colors.background.paper,
                    ...(bordered && {
                        border: `1px solid ${colors.border.default}`,
                    }),
                    ...sx,
                }}
                {...props}
            >
                {children}
            </Paper>
        );
    }
);

Surface.displayName = 'Surface';

export default Surface;

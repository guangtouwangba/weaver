'use client';

import React from 'react';
import { Tooltip as MuiTooltip, TooltipProps as MuiTooltipProps } from '@mui/material';
import { colors, radii, fontSize, fontWeight } from '../tokens';

/**
 * Tooltip Component
 *
 * Consistent hover hints with design system styling.
 * Wraps MUI Tooltip.
 */

export interface TooltipProps extends Omit<MuiTooltipProps, 'arrow'> {
    /** Whether to show arrow */
    arrow?: boolean;
}

export const Tooltip = React.forwardRef<HTMLDivElement, TooltipProps>(
    function Tooltip({ arrow = true, children, ...props }, ref) {
        return (
            <MuiTooltip
                ref={ref}
                arrow={arrow}
                componentsProps={{
                    tooltip: {
                        sx: {
                            bgcolor: colors.neutral[800],
                            color: colors.text.inverse,
                            fontSize: fontSize.xs,
                            fontWeight: fontWeight.medium,
                            borderRadius: `${radii.sm}px`,
                            px: 1,
                            py: 0.5,
                        },
                    },
                    arrow: {
                        sx: {
                            color: colors.neutral[800],
                        },
                    },
                }}
                {...props}
            >
                {children}
            </MuiTooltip>
        );
    }
);

Tooltip.displayName = 'Tooltip';

export default Tooltip;

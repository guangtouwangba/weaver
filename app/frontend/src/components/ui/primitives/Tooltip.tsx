'use client';

import React, { useState } from 'react';
import { colors, radii, fontSize, fontWeight } from '../tokens';

/**
 * Tooltip Component
 *
 * Consistent hover hints with design system styling.
 * Pure CSS implementation (simplified).
 */

export interface TooltipProps {
    /** Tooltip content */
    title: React.ReactNode;
    /** Whether to show arrow */
    arrow?: boolean;
    /** Position */
    placement?: 'top' | 'bottom' | 'left' | 'right';
    children: React.ReactElement;
}

export const Tooltip = React.forwardRef<HTMLDivElement, TooltipProps>(
    function Tooltip({ title, arrow = true, placement = 'bottom', children, ...props }, ref) {
        const [isVisible, setIsVisible] = useState(false);

        const positionStyles: React.CSSProperties = {
            position: 'absolute',
            zIndex: 1500,
            whiteSpace: 'nowrap',
            backgroundColor: colors.neutral[800],
            color: colors.text.inverse,
            fontSize: fontSize.xs,
            fontWeight: fontWeight.medium,
            borderRadius: radii.sm,
            padding: '4px 8px',
            pointerEvents: 'none',
            opacity: isVisible ? 1 : 0,
            transition: 'opacity 0.2s',
            ...((placement === 'top') && { bottom: '100%', left: '50%', transform: 'translateX(-50%) translateY(-8px)' }),
            ...((placement === 'bottom') && { top: '100%', left: '50%', transform: 'translateX(-50%) translateY(8px)' }),
            ...((placement === 'left') && { right: '100%', top: '50%', transform: 'translateY(-50%) translateX(-8px)' }),
            ...((placement === 'right') && { left: '100%', top: '50%', transform: 'translateY(-50%) translateX(8px)' }),
        };

        const arrowStyles: React.CSSProperties = {
            position: 'absolute',
            width: 0,
            height: 0,
            borderStyle: 'solid',
            ...((placement === 'top') && {
                bottom: -4, left: '50%', marginLeft: -4,
                borderWidth: '4px 4px 0 4px',
                borderColor: `${colors.neutral[800]} transparent transparent transparent`
            }),
            ...((placement === 'bottom') && {
                top: -4, left: '50%', marginLeft: -4,
                borderWidth: '0 4px 4px 4px',
                borderColor: `transparent transparent ${colors.neutral[800]} transparent`
            }),
            ...((placement === 'left') && {
                right: -4, top: '50%', marginTop: -4,
                borderWidth: '4px 0 4px 4px',
                borderColor: `transparent transparent transparent ${colors.neutral[800]}`
            }),
            ...((placement === 'right') && {
                left: -4, top: '50%', marginTop: -4,
                borderWidth: '4px 4px 4px 0',
                borderColor: `transparent ${colors.neutral[800]} transparent transparent`
            }),
        };

        return (
            <div
                ref={ref}
                style={{ position: 'relative', display: 'inline-flex' }}
                onMouseEnter={() => setIsVisible(true)}
                onMouseLeave={() => setIsVisible(false)}
                {...props}
            >
                {children}
                <div style={positionStyles}>
                    {title}
                    {arrow && <div style={arrowStyles} />}
                </div>
            </div>
        );
    }
);

Tooltip.displayName = 'Tooltip';

export default Tooltip;

'use client';

import React from 'react';
import { spacing as spacingTokens } from '../tokens';

/**
 * Stack Component
 *
 * A flexbox container with consistent spacing and alignment.
 * Pure CSS implementation.
 */

export interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
    /** Direction of the flex container */
    direction?: 'row' | 'column' | 'row-reverse' | 'column-reverse';
    /** Gap between children (uses spacing scale) */
    gap?: keyof typeof spacingTokens | number;
    /** Align items along the cross axis */
    align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline';
    /** Justify content along the main axis */
    justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
    /** Whether to wrap children */
    wrap?: boolean | 'wrap' | 'nowrap' | 'wrap-reverse';
    /** Whether to render as inline-flex */
    inline?: boolean;
    children?: React.ReactNode;
}

const alignMap = {
    start: 'flex-start',
    center: 'center',
    end: 'flex-end',
    stretch: 'stretch',
    baseline: 'baseline',
} as const;

const justifyMap = {
    start: 'flex-start',
    center: 'center',
    end: 'flex-end',
    between: 'space-between',
    around: 'space-around',
    evenly: 'space-evenly',
} as const;

export const Stack = React.forwardRef<HTMLDivElement, StackProps>(
    function Stack(
        {
            direction = 'column',
            gap = 0,
            align,
            justify,
            wrap = false,
            inline = false,
            children,
            style,
            className,
            ...props
        },
        ref
    ) {
        const gapValue = typeof gap === 'number'
            ? spacingTokens[gap as keyof typeof spacingTokens] ?? gap
            : spacingTokens[gap];

        const wrapValue = wrap === true ? 'wrap' : wrap === false ? 'nowrap' : wrap;

        return (
            <div
                ref={ref}
                className={className}
                style={{
                    display: inline ? 'inline-flex' : 'flex',
                    flexDirection: direction,
                    gap: `${gapValue}px`,
                    alignItems: align ? alignMap[align] : undefined,
                    justifyContent: justify ? justifyMap[justify] : undefined,
                    flexWrap: wrapValue,
                    ...style,
                }}
                {...props}
            >
                {children}
            </div>
        );
    }
);

Stack.displayName = 'Stack';

export default Stack;

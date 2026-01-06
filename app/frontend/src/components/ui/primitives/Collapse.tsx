'use client';

import React from 'react';

/**
 * Collapse Component
 *
 * Animated show/hide wrapper.
 * Pure CSS implementation using grid-template-rows trick.
 */

export interface CollapseProps extends React.HTMLAttributes<HTMLDivElement> {
    /** Whether content is visible */
    open?: boolean;
    /** Alias for open to match MUI */
    in?: boolean;
    /** Content */
    children?: React.ReactNode;
}

export const Collapse = React.forwardRef<HTMLDivElement, CollapseProps>(
    function Collapse({ open, in: inProp, children, style, className, ...props }, ref) {
        // Support both 'open' and 'in' props for flexibility
        const isOpen = open ?? inProp ?? false;

        return (
            <div
                ref={ref}
                className={className}
                style={{
                    display: 'grid',
                    gridTemplateRows: isOpen ? '1fr' : '0fr',
                    transition: 'grid-template-rows 0.3s ease-out',
                    ...style
                }}
                {...props}
            >
                <div style={{ overflow: 'hidden' }}>
                    {children}
                </div>
            </div>
        );
    }
);

Collapse.displayName = 'Collapse';

export default Collapse;

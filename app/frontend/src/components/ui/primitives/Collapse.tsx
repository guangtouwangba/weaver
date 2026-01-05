'use client';

import React from 'react';
import { Collapse as MuiCollapse, CollapseProps as MuiCollapseProps } from '@mui/material';

/**
 * Collapse Component
 *
 * Animated show/hide wrapper.
 * Wraps MUI Collapse with consistent API.
 */

export interface CollapseProps extends MuiCollapseProps {
    /** Whether content is visible */
    open?: boolean;
}

export const Collapse = React.forwardRef<HTMLDivElement, CollapseProps>(
    function Collapse({ open, in: inProp, ...props }, ref) {
        // Support both 'open' and 'in' props for flexibility
        const isOpen = open ?? inProp;

        return <MuiCollapse ref={ref} in={isOpen} {...props} />;
    }
);

Collapse.displayName = 'Collapse';

export default Collapse;

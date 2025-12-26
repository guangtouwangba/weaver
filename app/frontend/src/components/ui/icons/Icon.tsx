'use client';

import React from 'react';
import { SvgIcon } from '@mui/material';
import { IconProps, IconSize, sizeMap } from './types';

type MuiIconComponent = typeof SvgIcon;

/**
 * Creates a wrapped icon component with consistent props interface.
 * This abstraction allows easy swapping of the underlying icon library.
 */
export function createIcon(MuiIcon: MuiIconComponent, displayName: string) {
  const WrappedIcon = React.forwardRef<SVGSVGElement, IconProps>(
    function WrappedIcon(
      { size = 'md', color = 'inherit', className, style, sx, onClick, titleAccess },
      ref
    ) {
      const fontSize = typeof size === 'number' ? size : sizeMap[size as IconSize];
      
      return (
        <MuiIcon
          ref={ref}
          className={className}
          style={style}
          onClick={onClick}
          titleAccess={titleAccess}
          sx={{
            fontSize,
            color: color === 'inherit' ? 'inherit' : `${color}.main`,
            ...sx,
          }}
        />
      );
    }
  );
  
  WrappedIcon.displayName = displayName;
  return WrappedIcon;
}

/**
 * Re-export types for convenience
 */
export type { IconProps, IconSize } from './types';
export { sizeMap } from './types';


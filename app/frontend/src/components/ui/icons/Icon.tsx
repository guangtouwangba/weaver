'use client';

import React from 'react';
import { LucideIcon } from 'lucide-react';
import { IconProps, IconSize, sizeMap } from './types';
import { colors } from '../tokens';

const colorMap = {
  inherit: 'currentColor',
  primary: colors.primary[500],
  secondary: colors.neutral[500],
  error: colors.error[500],
  warning: colors.warning[500],
  info: colors.info[500],
  success: colors.success[500],
  disabled: colors.text.disabled,
  action: colors.text.secondary,
};

/**
 * Creates a wrapped icon component with consistent props interface.
 * Wraps Lucide icons with design system props.
 */
export function createIcon(Icon: LucideIcon, displayName: string) {
  const WrappedIcon = React.forwardRef<SVGSVGElement, IconProps>(
    function WrappedIcon(
      { size = 'md', color = 'inherit', className, style, onClick, titleAccess },
      ref
    ) {
      const pixelSize = typeof size === 'number' ? size : sizeMap[size as IconSize];
      const colorValue = colorMap[color as keyof typeof colorMap] || 'currentColor';

      return (
        <Icon
          ref={ref}
          size={pixelSize}
          color={colorValue}
          className={className}
          style={style}
          onClick={onClick}
          // Lucide doesn't have titleAccess, map to title for accessibility if needed
          // or aria-label if it's interactive. 
          // Best practice for SVG title is complex, but basic title works.
          {...(titleAccess ? { title: titleAccess } : {})}
        />
      );
    }
  );

  WrappedIcon.displayName = displayName;
  return WrappedIcon;
}

export * from './types';



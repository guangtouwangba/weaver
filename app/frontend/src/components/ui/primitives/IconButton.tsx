'use client';

import React from 'react';
import { IconButton as MuiIconButton, IconButtonProps as MuiIconButtonProps } from '@mui/material';
import { colors, radii } from '../tokens';

/**
 * IconButton Component
 *
 * A button containing only an icon.
 * Wraps MUI IconButton with design system tokens.
 */

export interface IconButtonProps extends Omit<MuiIconButtonProps, 'size' | 'color'> {
    /** Icon element */
    icon?: React.ReactNode;
    /** Button size */
    size?: 'xs' | 'sm' | 'md' | 'lg';
    /** Button variant */
    variant?: 'default' | 'ghost' | 'outline';
    /** Active state */
    active?: boolean;
    children?: React.ReactNode;
}

const sizeStyles = {
    xs: { size: 24, iconSize: 14 },
    sm: { size: 32, iconSize: 16 },
    md: { size: 40, iconSize: 20 },
    lg: { size: 48, iconSize: 24 },
};

const getVariantStyles = (variant: IconButtonProps['variant'], active?: boolean) => {
    const activeStyle = active ? { bgcolor: colors.primary[50], color: colors.primary[600] } : {};

    switch (variant) {
        case 'ghost':
            return {
                bgcolor: 'transparent',
                color: colors.text.secondary,
                '&:hover': {
                    bgcolor: colors.neutral[100],
                    color: colors.text.primary,
                },
                ...activeStyle,
            };
        case 'outline':
            return {
                bgcolor: 'transparent',
                color: colors.text.secondary,
                border: `1px solid ${colors.border.default}`,
                '&:hover': {
                    bgcolor: colors.neutral[50],
                    borderColor: colors.border.strong,
                },
                ...activeStyle,
            };
        default:
            return {
                bgcolor: colors.neutral[100],
                color: colors.text.secondary,
                '&:hover': {
                    bgcolor: colors.neutral[200],
                    color: colors.text.primary,
                },
                ...activeStyle,
            };
    }
};

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
    function IconButton(
        {
            icon,
            size = 'md',
            variant = 'ghost',
            active = false,
            children,
            sx,
            ...props
        },
        ref
    ) {
        const sizeStyle = sizeStyles[size];
        const variantStyle = getVariantStyles(variant, active);

        return (
            <MuiIconButton
                ref={ref}
                sx={{
                    width: sizeStyle.size,
                    height: sizeStyle.size,
                    borderRadius: `${radii.md}px`,
                    transition: 'all 0.15s ease',
                    '& > svg': {
                        fontSize: sizeStyle.iconSize,
                    },
                    ...variantStyle,
                    '&:focus-visible': {
                        outline: `2px solid ${colors.primary[500]}`,
                        outlineOffset: 2,
                    },
                    ...sx,
                }}
                {...props}
            >
                {icon || children}
            </MuiIconButton>
        );
    }
);

IconButton.displayName = 'IconButton';

export default IconButton;

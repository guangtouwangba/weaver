'use client';

import React from 'react';
import { Button as MuiButton, ButtonProps as MuiButtonProps, CircularProgress } from '@mui/material';
import { colors, radii, fontWeight } from '../tokens';

/**
 * Button Component
 *
 * Styled button with design system variants.
 * Wraps MUI Button with consistent API.
 */

export interface ButtonProps extends Omit<MuiButtonProps, 'variant' | 'color'> {
    /** Button variant */
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
    /** Button size */
    size?: 'sm' | 'md' | 'lg';
    /** Whether the button is in loading state */
    loading?: boolean;
    /** Icon to display before text */
    icon?: React.ReactNode;
    /** Icon to display after text */
    iconRight?: React.ReactNode;
    children?: React.ReactNode;
}

const sizeStyles = {
    sm: {
        height: 32,
        px: 2,
        fontSize: 13,
    },
    md: {
        height: 40,
        px: 3,
        fontSize: 14,
    },
    lg: {
        height: 48,
        px: 4,
        fontSize: 16,
    },
};

const getVariantStyles = (variant: ButtonProps['variant']) => {
    switch (variant) {
        case 'primary':
            return {
                bgcolor: colors.primary[500],
                color: '#FFFFFF',
                '&:hover': {
                    bgcolor: colors.primary[600],
                },
                '&:active': {
                    bgcolor: colors.primary[700],
                },
                '&:disabled': {
                    bgcolor: colors.neutral[200],
                    color: colors.neutral[400],
                },
            };
        case 'secondary':
            return {
                bgcolor: colors.neutral[100],
                color: colors.text.primary,
                '&:hover': {
                    bgcolor: colors.neutral[200],
                },
                '&:active': {
                    bgcolor: colors.neutral[300],
                },
                '&:disabled': {
                    bgcolor: colors.neutral[100],
                    color: colors.neutral[400],
                },
            };
        case 'ghost':
            return {
                bgcolor: 'transparent',
                color: colors.text.primary,
                '&:hover': {
                    bgcolor: colors.neutral[100],
                },
                '&:active': {
                    bgcolor: colors.neutral[200],
                },
                '&:disabled': {
                    color: colors.neutral[400],
                },
            };
        case 'danger':
            return {
                bgcolor: colors.error[500],
                color: '#FFFFFF',
                '&:hover': {
                    bgcolor: colors.error[600],
                },
                '&:active': {
                    bgcolor: colors.error[700],
                },
                '&:disabled': {
                    bgcolor: colors.neutral[200],
                    color: colors.neutral[400],
                },
            };
        case 'outline':
            return {
                bgcolor: 'transparent',
                color: colors.text.primary,
                border: `1px solid ${colors.border.default}`,
                '&:hover': {
                    bgcolor: colors.neutral[50],
                    borderColor: colors.border.strong,
                },
                '&:active': {
                    bgcolor: colors.neutral[100],
                },
                '&:disabled': {
                    borderColor: colors.neutral[200],
                    color: colors.neutral[400],
                },
            };
        default:
            return {};
    }
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    function Button(
        {
            variant = 'primary',
            size = 'md',
            loading = false,
            icon,
            iconRight,
            disabled,
            children,
            sx,
            ...props
        },
        ref
    ) {
        const sizeStyle = sizeStyles[size];
        const variantStyle = getVariantStyles(variant);

        return (
            <MuiButton
                ref={ref}
                disabled={disabled || loading}
                sx={{
                    minHeight: sizeStyle.height,
                    px: sizeStyle.px,
                    fontSize: sizeStyle.fontSize,
                    fontWeight: fontWeight.medium,
                    borderRadius: `${radii.md}px`,
                    textTransform: 'none',
                    boxShadow: 'none',
                    transition: 'all 0.15s ease',
                    ...variantStyle,
                    '&:focus-visible': {
                        outline: `2px solid ${colors.primary[500]}`,
                        outlineOffset: 2,
                    },
                    ...sx,
                }}
                {...props}
            >
                {loading ? (
                    <CircularProgress size={16} color="inherit" sx={{ mr: children ? 1 : 0 }} />
                ) : icon ? (
                    <span style={{ marginRight: children ? 8 : 0, display: 'flex' }}>{icon}</span>
                ) : null}
                {children}
                {iconRight && !loading && (
                    <span style={{ marginLeft: 8, display: 'flex' }}>{iconRight}</span>
                )}
            </MuiButton>
        );
    }
);

Button.displayName = 'Button';

export default Button;

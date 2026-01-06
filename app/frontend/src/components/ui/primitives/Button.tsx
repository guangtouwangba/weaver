'use client';

import React from 'react';
import { colors, radii, fontWeight } from '../tokens';
import { Spinner } from './Spinner';

/**
 * Button Component
 *
 * Styled button with design system variants.
 * Pure CSS implementation.
 */

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
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
    /** Start icon alias (for compatibility) */
    startIcon?: React.ReactNode;
    /** End icon alias (for compatibility) */
    endIcon?: React.ReactNode;
    children?: React.ReactNode;
    /** Optional href for anchor tag behavior */
    href?: string;
    target?: string;
    rel?: string;
}

const sizeStyles = {
    sm: {
        height: 32,
        px: 12,
        fontSize: 13,
    },
    md: {
        height: 40,
        px: 16,
        fontSize: 14,
    },
    lg: {
        height: 48,
        px: 24,
        fontSize: 16,
    },
};

const getVariantStyles = (variant: ButtonProps['variant'], disabled?: boolean) => {
    if (disabled) {
        return {
            backgroundColor: colors.neutral[200],
            color: colors.neutral[400],
            border: 'none',
            cursor: 'not-allowed',
        };
    }

    switch (variant) {
        case 'primary':
            return {
                backgroundColor: colors.primary[500],
                color: '#FFFFFF',
                border: 'none',
            };
        case 'secondary':
            return {
                backgroundColor: colors.neutral[100],
                color: colors.text.primary,
                border: 'none',
            };
        case 'ghost':
            return {
                backgroundColor: 'transparent',
                color: colors.text.primary,
                border: 'none',
            };
        case 'danger':
            return {
                backgroundColor: colors.error[500],
                color: '#FFFFFF',
                border: 'none',
            };
        case 'outline':
            return {
                backgroundColor: 'transparent',
                color: colors.text.primary,
                border: `1px solid ${colors.border.default}`,
            };
        default:
            return {
                backgroundColor: colors.primary[500],
                color: '#FFFFFF',
                border: 'none',
            };
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
            startIcon,
            endIcon,
            children,
            className,
            style,
            disabled,
            href,
            onClick,
            ...props
        },
        ref
    ) {
        const sizeStyle = sizeStyles[size];
        const [isHovered, setIsHovered] = React.useState(false);
        const [isActive, setIsActive] = React.useState(false);
        const [isFocused, setIsFocused] = React.useState(false);

        const isDisabled = disabled || loading;
        const variantStyles = getVariantStyles(variant, isDisabled);

        const hoverStyles = !isDisabled && isHovered ? (
            variant === 'primary' ? { backgroundColor: colors.primary[600] } :
            variant === 'secondary' ? { backgroundColor: colors.neutral[200] } :
            variant === 'ghost' ? { backgroundColor: colors.neutral[100] } :
            variant === 'danger' ? { backgroundColor: colors.error[600] } :
            variant === 'outline' ? { backgroundColor: colors.neutral[50], borderColor: colors.border.strong } :
            {}
        ) : {};

        const activeStyles = !isDisabled && isActive ? (
            variant === 'primary' ? { backgroundColor: colors.primary[700] } :
            variant === 'secondary' ? { backgroundColor: colors.neutral[300] } :
            variant === 'ghost' ? { backgroundColor: colors.neutral[200] } :
            variant === 'danger' ? { backgroundColor: colors.error[700] } :
            variant === 'outline' ? { backgroundColor: colors.neutral[100] } :
            {}
        ) : {};

        const buttonStyles: React.CSSProperties = {
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: sizeStyle.height,
            paddingLeft: sizeStyle.px,
            paddingRight: sizeStyle.px,
            fontSize: sizeStyle.fontSize,
            fontWeight: fontWeight.medium,
            borderRadius: radii.md,
            transition: 'all 0.15s ease',
            cursor: isDisabled ? 'not-allowed' : 'pointer',
            gap: 8,
            textDecoration: 'none',
            outline: isFocused ? `2px solid ${colors.primary[500]}` : 'none',
            boxSizing: 'border-box',
            ...variantStyles,
            ...hoverStyles,
            ...activeStyles,
            ...style,
        };

        const leftIcon = loading ? <Spinner size="sm" color="inherit" /> : (icon || startIcon);
        const rightIcon = iconRight || endIcon;

        // If href is provided, render as anchor
        if (href) {
            return (
                <a
                    href={href}
                    style={buttonStyles}
                    onMouseEnter={() => setIsHovered(true)}
                    onMouseLeave={() => setIsHovered(false)}
                    onMouseDown={() => setIsActive(true)}
                    onMouseUp={() => setIsActive(false)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    onClick={onClick as any}
                    {...(props as any)}
                >
                    {leftIcon}
                    {children}
                    {rightIcon}
                </a>
            );
        }

        return (
            <button
                ref={ref}
                disabled={isDisabled}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                onMouseDown={() => setIsActive(true)}
                onMouseUp={() => setIsActive(false)}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                onClick={onClick}
                style={buttonStyles}
                {...props}
            >
                {leftIcon}
                {children}
                {rightIcon}
            </button>
        );
    }
);

Button.displayName = 'Button';

export default Button;

'use client';

import React from 'react';
import { colors, radii } from '../tokens';

/**
 * IconButton Component
 *
 * A button containing only an icon.
 * Pure CSS implementation.
 */

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
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

const getVariantStyles = (variant: IconButtonProps['variant'], active?: boolean, disabled?: boolean) => {
    if (disabled) {
        return {
            backgroundColor: 'transparent',
            color: colors.text.disabled,
            border: variant === 'outline' ? `1px solid ${colors.border.default}` : 'none',
            cursor: 'not-allowed',
        };
    }

    const activeStyle = active ? { backgroundColor: colors.primary[50], color: colors.primary[600] } : {};

    switch (variant) {
        case 'ghost':
            return {
                backgroundColor: 'transparent',
                color: colors.text.secondary,
                border: 'none',
                ...activeStyle,
            };
        case 'outline':
            return {
                backgroundColor: 'transparent',
                color: colors.text.secondary,
                border: `1px solid ${colors.border.default}`,
                ...activeStyle,
            };
        default:
            return {
                backgroundColor: colors.neutral[100],
                color: colors.text.secondary,
                border: 'none',
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
            className,
            style,
            disabled,
            ...props
        },
        ref
    ) {
        const sizeStyle = sizeStyles[size];
        const [isHovered, setIsHovered] = React.useState(false);
        const [isFocused, setIsFocused] = React.useState(false);

        const variantStyles = getVariantStyles(variant, active, disabled);

        const hoverStyles = !disabled && isHovered ? (
            variant === 'ghost' ? {
                backgroundColor: colors.neutral[100],
                color: colors.text.primary,
            } : variant === 'outline' ? {
                backgroundColor: colors.neutral[50],
                borderColor: colors.border.strong,
            } : {
                backgroundColor: colors.neutral[200],
                color: colors.text.primary,
            }
        ) : {};

        // If custom style includes 'background' (shorthand), remove backgroundColor to avoid conflict
        const hasBackgroundShorthand = style && 'background' in style;
        const finalVariantStyles = hasBackgroundShorthand
            ? { ...variantStyles, backgroundColor: undefined }
            : variantStyles;
        const finalHoverStyles = hasBackgroundShorthand
            ? { ...hoverStyles, backgroundColor: undefined }
            : hoverStyles;

        return (
            <button
                ref={ref}
                className={className}
                disabled={disabled}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: sizeStyle.size,
                    height: sizeStyle.size,
                    borderRadius: radii.md,
                    transition: 'all 0.15s ease',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    fontSize: sizeStyle.iconSize,
                    outline: isFocused ? `2px solid ${colors.primary[500]}` : 'none',
                    padding: 0,
                    ...finalVariantStyles,
                    ...finalHoverStyles,
                    ...style,
                }}
                {...props}
            >
                {/* Clone the icon to apply size if needed, or just render it */}
                {React.Children.map(icon || children, child => {
                    if (React.isValidElement(child)) {
                        const props = child.props as { size?: number | string };
                        return React.cloneElement(child, {
                            size: props.size || sizeStyle.iconSize,
                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        } as any);
                    }
                    return child;
                })}
            </button>
        );
    }
);

IconButton.displayName = 'IconButton';

export default IconButton;

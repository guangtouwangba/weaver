'use client';

import React from 'react';
import { colors, radii, fontSize, fontWeight } from '../tokens';

/**
 * Chip Component
 *
 * A compact element for displaying labels, tags, or selections.
 * Pure CSS implementation without MUI dependency.
 */

export interface ChipProps {
    /** Text content of the chip */
    label: string;
    /** Visual style variant */
    variant?: 'filled' | 'outlined' | 'soft';
    /** Color scheme */
    color?: 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info';
    /** Size of the chip */
    size?: 'sm' | 'md' | 'lg';
    /** Optional icon at the start */
    icon?: React.ReactNode;
    /** Callback when delete button is clicked (shows delete button when provided) */
    onDelete?: () => void;
    /** Callback when chip is clicked */
    onClick?: () => void;
    /** Whether the chip is disabled */
    disabled?: boolean;
    /** Additional CSS class */
    className?: string;
    /** Additional inline styles */
    style?: React.CSSProperties;
}

const sizeStyles = {
    sm: {
        height: 20,
        fontSize: fontSize.xs,
        paddingX: 8,
        iconSize: 12,
    },
    md: {
        height: 24,
        fontSize: fontSize.xs,
        paddingX: 10,
        iconSize: 14,
    },
    lg: {
        height: 32,
        fontSize: fontSize.sm,
        paddingX: 12,
        iconSize: 16,
    },
};

const colorPalettes = {
    default: {
        filled: { bg: colors.neutral[200], text: colors.neutral[800], border: 'transparent' },
        outlined: { bg: 'transparent', text: colors.neutral[700], border: colors.neutral[300] },
        soft: { bg: colors.neutral[100], text: colors.neutral[700], border: 'transparent' },
    },
    primary: {
        filled: { bg: colors.primary[500], text: '#fff', border: 'transparent' },
        outlined: { bg: 'transparent', text: colors.primary[600], border: colors.primary[300] },
        soft: { bg: colors.primary[50], text: colors.primary[700], border: 'transparent' },
    },
    success: {
        filled: { bg: colors.success[500], text: '#fff', border: 'transparent' },
        outlined: { bg: 'transparent', text: colors.success[600], border: colors.success[300] },
        soft: { bg: colors.success[50], text: colors.success[700], border: 'transparent' },
    },
    warning: {
        filled: { bg: colors.warning[500], text: '#fff', border: 'transparent' },
        outlined: { bg: 'transparent', text: colors.warning[600], border: colors.warning[300] },
        soft: { bg: colors.warning[50], text: colors.warning[700], border: 'transparent' },
    },
    error: {
        filled: { bg: colors.error[500], text: '#fff', border: 'transparent' },
        outlined: { bg: 'transparent', text: colors.error[600], border: colors.error[300] },
        soft: { bg: colors.error[50], text: colors.error[700], border: 'transparent' },
    },
    info: {
        filled: { bg: colors.primary[400], text: '#fff', border: 'transparent' },
        outlined: { bg: 'transparent', text: colors.primary[500], border: colors.primary[200] },
        soft: { bg: colors.primary[50], text: colors.primary[600], border: 'transparent' },
    },
};

export const Chip = React.forwardRef<HTMLDivElement, ChipProps>(
    function Chip(
        {
            label,
            variant = 'filled',
            color = 'default',
            size = 'md',
            icon,
            onDelete,
            onClick,
            disabled = false,
            className,
            style,
        },
        ref
    ) {
        const sizeStyle = sizeStyles[size];
        const colorStyle = colorPalettes[color][variant];

        const handleClick = (e: React.MouseEvent) => {
            if (disabled) return;
            onClick?.(e as any);
        };

        const handleDelete = (e: React.MouseEvent) => {
            e.stopPropagation();
            if (disabled) return;
            onDelete?.();
        };

        return (
            <div
                ref={ref}
                className={className}
                onClick={onClick ? handleClick : undefined}
                style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'flex-start', // Changed from center to prevent overflow overlap
                    gap: 4,
                    height: sizeStyle.height,
                    paddingLeft: sizeStyle.paddingX,
                    paddingRight: onDelete ? sizeStyle.paddingX - 4 : sizeStyle.paddingX,
                    borderRadius: radii.full,
                    fontSize: sizeStyle.fontSize,
                    fontWeight: fontWeight.medium,
                    fontFamily: 'inherit',
                    backgroundColor: colorStyle.bg,
                    color: colorStyle.text,
                    border: `1px solid ${colorStyle.border}`,
                    cursor: onClick && !disabled ? 'pointer' : 'default',
                    opacity: disabled ? 0.5 : 1,
                    transition: 'all 0.15s ease',
                    userSelect: 'none',
                    whiteSpace: 'nowrap',
                    maxWidth: '100%', // Ensure chip doesn't exceed parent
                    ...style,
                }}
            >
                {icon && (
                    <span
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            marginLeft: -2,
                            flexShrink: 0, // Prevent icon from shrinking
                        }}
                    >
                        {icon}
                    </span>
                )}
                <span style={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    minWidth: 0, // Allow flex child to shrink below content size
                }}>
                    {label}
                </span>
                {onDelete && (
                    <button
                        type="button"
                        onClick={handleDelete}
                        disabled={disabled}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: sizeStyle.iconSize + 4,
                            height: sizeStyle.iconSize + 4,
                            marginLeft: 2,
                            marginRight: -4,
                            padding: 0,
                            border: 'none',
                            borderRadius: '50%',
                            backgroundColor: 'transparent',
                            color: 'inherit',
                            cursor: disabled ? 'default' : 'pointer',
                            opacity: 0.7,
                            transition: 'opacity 0.15s, background-color 0.15s',
                            flexShrink: 0, // Prevent delete button from shrinking
                        }}
                        onMouseEnter={(e) => {
                            if (!disabled) {
                                e.currentTarget.style.opacity = '1';
                                e.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.1)';
                            }
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.opacity = '0.7';
                            e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                    >
                        <svg
                            width={sizeStyle.iconSize}
                            height={sizeStyle.iconSize}
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <line x1="18" y1="6" x2="6" y2="18" />
                            <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                    </button>
                )}
            </div>
        );
    }
);

Chip.displayName = 'Chip';

export default Chip;

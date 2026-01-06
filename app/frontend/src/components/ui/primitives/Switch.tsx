'use client';

import React from 'react';
import { colors, radii } from '../tokens';

/**
 * Switch Component
 *
 * A toggle switch for binary states.
 * Pure CSS implementation without MUI dependency.
 */

export interface SwitchProps {
    /** Whether the switch is checked */
    checked?: boolean;
    /** Callback when the switch state changes */
    onChange?: (checked: boolean) => void;
    /** Whether the switch is disabled */
    disabled?: boolean;
    /** Name attribute */
    name?: string;
    /** Optional label */
    label?: string;
    /** Color scheme */
    color?: 'primary' | 'success' | 'warning' | 'error';
    /** Size of the switch */
    size?: 'sm' | 'md' | 'lg';
    /** Additional CSS class */
    className?: string;
    /** Additional inline styles */
    style?: React.CSSProperties;
}

const sizeConfig = {
    sm: { width: 28, height: 16, thumb: 12, translate: 12 },
    md: { width: 36, height: 20, thumb: 16, translate: 16 },
    lg: { width: 44, height: 24, thumb: 20, translate: 20 },
};

const colorMap = {
    primary: colors.primary[500],
    success: colors.success[500],
    warning: colors.warning[500],
    error: colors.error[500],
};

export const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
    function Switch(
        {
            checked = false,
            onChange,
            disabled = false,
            name,
            label,
            color = 'primary',
            size = 'md',
            className,
            style,
        },
        ref
    ) {
        const config = sizeConfig[size];
        const activeColor = colorMap[color];

        const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
            if (!disabled) {
                onChange?.(e.target.checked);
            }
        };

        return (
            <label
                className={className}
                style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    opacity: disabled ? 0.5 : 1,
                    ...style,
                }}
            >
                <div
                    style={{
                        position: 'relative',
                        width: config.width,
                        height: config.height,
                        borderRadius: radii.full,
                        backgroundColor: checked ? activeColor : colors.neutral[300],
                        transition: 'background-color 0.2s',
                    }}
                >
                    <input
                        ref={ref}
                        type="checkbox"
                        checked={checked}
                        onChange={handleChange}
                        disabled={disabled}
                        name={name}
                        style={{
                            position: 'absolute',
                            width: '100%',
                            height: '100%',
                            opacity: 0,
                            margin: 0,
                            cursor: disabled ? 'not-allowed' : 'pointer',
                            zIndex: 1,
                        }}
                    />
                    <div
                        style={{
                            position: 'absolute',
                            top: 2,
                            left: 2,
                            width: config.thumb,
                            height: config.thumb,
                            borderRadius: '50%',
                            backgroundColor: '#fff',
                            boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                            transition: 'transform 0.2s',
                            transform: checked ? `translateX(${config.translate}px)` : 'translateX(0)',
                        }}
                    />
                </div>
                {label && (
                    <span style={{ fontSize: 14, color: colors.text.primary }}>
                        {label}
                    </span>
                )}
            </label>
        );
    }
);

Switch.displayName = 'Switch';

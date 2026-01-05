'use client';

import React from 'react';
import { colors, radii } from '../tokens';

/**
 * Checkbox Component
 *
 * A checkbox for binary selection.
 * Pure CSS implementation without MUI dependency.
 */

export interface CheckboxProps {
    /** Whether the checkbox is checked */
    checked?: boolean;
    /** Callback when the checkbox state changes */
    onChange?: (checked: boolean) => void;
    /** Whether the checkbox is disabled */
    disabled?: boolean;
    /** Name attribute for forms */
    name?: string;
    /** Optional label text */
    label?: string;
    /** Whether to show indeterminate state */
    indeterminate?: boolean;
    /** Color scheme */
    color?: 'primary' | 'error';
    /** Size of the checkbox */
    size?: 'sm' | 'md' | 'lg';
    /** Additional CSS class */
    className?: string;
    /** Additional inline styles */
    style?: React.CSSProperties;
}

const sizeConfig = {
    sm: { box: 14, icon: 10, fontSize: 12, radius: 3 },
    md: { box: 18, icon: 12, fontSize: 14, radius: 4 },
    lg: { box: 22, icon: 14, fontSize: 16, radius: 5 },
};

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
    function Checkbox(
        {
            checked = false,
            onChange,
            disabled = false,
            name,
            label,
            indeterminate = false,
            color = 'primary',
            size = 'md',
            className,
            style,
        },
        ref
    ) {
        const config = sizeConfig[size];
        const activeColor = color === 'error' ? colors.error[500] : colors.primary[500];
        const isActive = checked || indeterminate;

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
                <span
                    style={{
                        position: 'relative',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: config.box,
                        height: config.box,
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
                        }}
                    />
                    <span
                        style={{
                            width: config.box,
                            height: config.box,
                            borderRadius: config.radius,
                            border: `2px solid ${isActive ? activeColor : colors.neutral[400]}`,
                            backgroundColor: isActive ? activeColor : 'transparent',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            transition: 'all 0.15s ease',
                        }}
                    >
                        {checked && !indeterminate && (
                            <svg
                                width={config.icon}
                                height={config.icon}
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="white"
                                strokeWidth="3"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            >
                                <polyline points="20 6 9 17 4 12" />
                            </svg>
                        )}
                        {indeterminate && (
                            <svg
                                width={config.icon}
                                height={config.icon}
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="white"
                                strokeWidth="3"
                                strokeLinecap="round"
                            >
                                <line x1="5" y1="12" x2="19" y2="12" />
                            </svg>
                        )}
                    </span>
                </span>
                {label && (
                    <span
                        style={{
                            fontSize: config.fontSize,
                            color: disabled ? colors.text.disabled : colors.text.primary,
                        }}
                    >
                        {label}
                    </span>
                )}
            </label>
        );
    }
);

Checkbox.displayName = 'Checkbox';

export default Checkbox;

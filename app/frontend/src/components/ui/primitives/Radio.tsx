'use client';

import React from 'react';
import { colors } from '../tokens';

/**
 * Radio Component
 *
 * A radio button for single selection from a group.
 * Pure CSS implementation without MUI dependency.
 */

export interface RadioProps {
    /** Whether the radio is checked */
    checked?: boolean;
    /** Callback when the radio state changes */
    onChange?: (checked: boolean) => void;
    /** Whether the radio is disabled */
    disabled?: boolean;
    /** Name attribute for form grouping */
    name?: string;
    /** Value for the radio */
    value?: string;
    /** Optional label text */
    label?: string;
    /** Color scheme */
    color?: 'primary' | 'error';
    /** Size of the radio */
    size?: 'sm' | 'md' | 'lg';
    /** Additional CSS class */
    className?: string;
    /** Additional inline styles */
    style?: React.CSSProperties;
}

const sizeConfig = {
    sm: { outer: 16, inner: 8, fontSize: 12 },
    md: { outer: 20, inner: 10, fontSize: 14 },
    lg: { outer: 24, inner: 12, fontSize: 16 },
};

export const Radio = React.forwardRef<HTMLInputElement, RadioProps>(
    function Radio(
        {
            checked = false,
            onChange,
            disabled = false,
            name,
            value,
            label,
            color = 'primary',
            size = 'md',
            className,
            style,
        },
        ref
    ) {
        const config = sizeConfig[size];
        const activeColor = color === 'error' ? colors.error[500] : colors.primary[500];

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
                        width: config.outer,
                        height: config.outer,
                    }}
                >
                    <input
                        ref={ref}
                        type="radio"
                        checked={checked}
                        onChange={handleChange}
                        disabled={disabled}
                        name={name}
                        value={value}
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
                            width: config.outer,
                            height: config.outer,
                            borderRadius: '50%',
                            border: `2px solid ${checked ? activeColor : colors.neutral[400]}`,
                            backgroundColor: 'transparent',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            transition: 'all 0.15s ease',
                        }}
                    >
                        {checked && (
                            <span
                                style={{
                                    width: config.inner,
                                    height: config.inner,
                                    borderRadius: '50%',
                                    backgroundColor: activeColor,
                                    transition: 'transform 0.15s ease',
                                }}
                            />
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

Radio.displayName = 'Radio';

export default Radio;

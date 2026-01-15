'use client';

import React, { useState, useId } from 'react';
import { colors, radii, fontSize, fontWeight, fontFamily } from '../tokens';

/**
 * TextField Component
 *
 * A versatile text input field with label and helper text support.
 * Pure CSS implementation without MUI dependency.
 */

export interface TextFieldProps {
    /** Label text above the input */
    label?: string;
    /** Placeholder text */
    placeholder?: string;
    /** Current value */
    value?: string;
    /** Default value for uncontrolled mode */
    defaultValue?: string;
    /** Change handler */
    onChange?: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    /** Blur handler */
    onBlur?: (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    /** Focus handler */
    onFocus?: (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    /** Key down handler */
    onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    /** Whether the field has an error */
    error?: boolean;
    /** Helper text below the input */
    helperText?: string;
    /** Whether to render as textarea */
    multiline?: boolean;
    /** Number of rows for multiline */
    rows?: number;
    /** Minimum rows for multiline */
    minRows?: number;
    /** Maximum rows for multiline */
    maxRows?: number;
    /** Whether the field is disabled */
    disabled?: boolean;
    /** Whether the field is read-only */
    readOnly?: boolean;
    /** Whether to take full width */
    fullWidth?: boolean;
    /** Element to render at the start of the input */
    startAdornment?: React.ReactNode;
    /** Element to render at the end of the input */
    endAdornment?: React.ReactNode;
    /** Size variant */
    size?: 'sm' | 'md' | 'lg';
    /** Input type */
    type?: 'text' | 'password' | 'email' | 'number' | 'search' | 'tel' | 'url';
    /** Name attribute */
    name?: string;
    /** Autofocus */
    autoFocus?: boolean;
    /** Autocomplete attribute */
    autoComplete?: string;
    /** Required field */
    required?: boolean;
    /** Additional CSS class */
    className?: string;
    /** Additional inline styles for wrapper */
    style?: React.CSSProperties;
    /** Additional inline styles for input */
    inputStyle?: React.CSSProperties;
}

const sizeConfig = {
    sm: { height: 32, padding: '6px 10px', fontSize: fontSize.sm, labelSize: fontSize.xs },
    md: { height: 40, padding: '8px 12px', fontSize: fontSize.base, labelSize: fontSize.sm },
    lg: { height: 48, padding: '12px 16px', fontSize: fontSize.lg, labelSize: fontSize.base },
};

export const TextField = React.forwardRef<HTMLInputElement | HTMLTextAreaElement, TextFieldProps>(
    function TextField(
        {
            label,
            placeholder,
            value,
            defaultValue,
            onChange,
            onBlur,
            onFocus,
            onKeyDown,
            error = false,
            helperText,
            multiline = false,
            rows = 4,
            minRows,
            maxRows,
            disabled = false,
            readOnly = false,
            fullWidth = false,
            startAdornment,
            endAdornment,
            size = 'md',
            type = 'text',
            name,
            autoFocus,
            autoComplete,
            required,
            className,
            style,
            inputStyle,
        },
        ref
    ) {
        const [isFocused, setIsFocused] = useState(false);
        const id = useId();
        const config = sizeConfig[size];

        const borderColor = error
            ? colors.error[500]
            : isFocused
                ? colors.primary[500]
                : colors.border.default;

        const handleFocus = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
            setIsFocused(true);
            onFocus?.(e);
        };

        const handleBlur = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
            setIsFocused(false);
            onBlur?.(e);
        };

        const inputProps = {
            id,
            name,
            value,
            defaultValue,
            placeholder,
            disabled,
            readOnly,
            autoFocus,
            autoComplete,
            required,
            onChange,
            onBlur: handleBlur,
            onFocus: handleFocus,
            onKeyDown,
            style: {
                flex: 1,
                width: '100%',
                border: 'none',
                outline: 'none',
                backgroundColor: 'transparent',
                fontSize: config.fontSize,
                fontFamily: fontFamily.sans,
                color: disabled ? colors.text.disabled : colors.text.primary,
                '::placeholder': { color: colors.text.muted },
                ...inputStyle,
            } as React.CSSProperties,
        };

        return (
            <div
                className={className}
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                    width: fullWidth ? '100%' : 'auto',
                    ...style,
                }}
            >
                {label && (
                    <label
                        htmlFor={id}
                        style={{
                            fontSize: config.labelSize,
                            fontWeight: fontWeight.medium,
                            color: error ? colors.error[600] : colors.text.primary,
                        }}
                    >
                        {label}
                        {required && (
                            <span style={{ color: colors.error[500], marginLeft: 2 }}>*</span>
                        )}
                    </label>
                )}
                <div
                    style={{
                        display: 'flex',
                        alignItems: multiline ? 'flex-start' : 'center',
                        gap: 8,
                        minHeight: multiline ? undefined : config.height,
                        padding: config.padding,
                        backgroundColor: disabled ? colors.neutral[100] : colors.background.paper,
                        border: `1px solid ${borderColor}`,
                        borderRadius: radii.md,
                        transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
                        boxShadow: isFocused && !error ? `0 0 0 3px ${colors.primary[100]}` : undefined,
                    }}
                >
                    {startAdornment && (
                        <span style={{ display: 'flex', color: colors.text.secondary }}>
                            {startAdornment}
                        </span>
                    )}
                    {multiline ? (
                        <textarea
                            ref={ref as React.Ref<HTMLTextAreaElement>}
                            rows={rows}
                            {...inputProps}
                            style={{
                                ...inputProps.style,
                                resize: 'vertical',
                                minHeight: minRows ? minRows * 24 : undefined,
                                maxHeight: maxRows ? maxRows * 24 : undefined,
                            }}
                        />
                    ) : (
                        <input
                            ref={ref as React.Ref<HTMLInputElement>}
                            type={type}
                            {...inputProps}
                        />
                    )}
                    {endAdornment && (
                        <span style={{ display: 'flex', color: colors.text.secondary }}>
                            {endAdornment}
                        </span>
                    )}
                </div>
                {helperText && (
                    <span
                        style={{
                            fontSize: fontSize.xs,
                            color: error ? colors.error[500] : colors.text.secondary,
                        }}
                    >
                        {helperText}
                    </span>
                )}
            </div>
        );
    }
);

TextField.displayName = 'TextField';

export default TextField;

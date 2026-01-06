'use client';

import React from 'react';
import { TextField, TextFieldProps } from './TextField';

/**
 * Input Component
 *
 * Compatibility wrapper around TextField.
 * Replaces MUI TextField wrapper.
 */

export interface InputProps extends Omit<TextFieldProps, 'variant' | 'startAdornment' | 'endAdornment'> {
    /** Icon or element to display at start */
    startIcon?: React.ReactNode;
    /** Icon or element to display at end */
    endIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement | HTMLTextAreaElement, InputProps>(
    function Input(
        {
            startIcon,
            endIcon,
            ...props
        },
        ref
    ) {
        return (
            <TextField
                ref={ref}
                startAdornment={startIcon}
                endAdornment={endIcon}
                {...props}
            />
        );
    }
);

Input.displayName = 'Input';

export default Input;

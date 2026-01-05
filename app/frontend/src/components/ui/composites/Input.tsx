'use client';

import React from 'react';
import {
    TextField as MuiTextField,
    TextFieldProps as MuiTextFieldProps,
    InputAdornment,
} from '@mui/material';
import { colors, radii, fontSize, fontWeight } from '../tokens';

/**
 * Input Component
 *
 * Text input with consistent styling.
 * Wraps MUI TextField with design system tokens.
 */

export interface InputProps extends Omit<MuiTextFieldProps, 'variant' | 'size'> {
    /** Input size */
    size?: 'sm' | 'md' | 'lg';
    /** Icon or element to display at start */
    startIcon?: React.ReactNode;
    /** Icon or element to display at end */
    endIcon?: React.ReactNode;
}

const sizeStyles = {
    sm: {
        height: 32,
        fontSize: fontSize.sm,
        px: 2,
    },
    md: {
        height: 40,
        fontSize: fontSize.base,
        px: 2.5,
    },
    lg: {
        height: 48,
        fontSize: fontSize.base,
        px: 3,
    },
};

export const Input = React.forwardRef<HTMLDivElement, InputProps>(
    function Input(
        {
            size = 'md',
            startIcon,
            endIcon,
            sx,
            ...props
        },
        ref
    ) {
        const sizeStyle = sizeStyles[size];

        return (
            <MuiTextField
                ref={ref}
                variant="outlined"
                fullWidth
                InputProps={{
                    startAdornment: startIcon ? (
                        <InputAdornment position="start" sx={{ color: colors.text.muted }}>
                            {startIcon}
                        </InputAdornment>
                    ) : undefined,
                    endAdornment: endIcon ? (
                        <InputAdornment position="end" sx={{ color: colors.text.muted }}>
                            {endIcon}
                        </InputAdornment>
                    ) : undefined,
                }}
                sx={{
                    '& .MuiOutlinedInput-root': {
                        height: sizeStyle.height,
                        fontSize: sizeStyle.fontSize,
                        borderRadius: `${radii.md}px`,
                        backgroundColor: colors.background.paper,
                        '& fieldset': {
                            borderColor: colors.border.default,
                        },
                        '&:hover fieldset': {
                            borderColor: colors.border.strong,
                        },
                        '&.Mui-focused fieldset': {
                            borderColor: colors.primary[500],
                            borderWidth: 2,
                        },
                        '& input': {
                            px: sizeStyle.px,
                        },
                    },
                    '& .MuiInputLabel-root': {
                        fontSize: fontSize.sm,
                        fontWeight: fontWeight.medium,
                        color: colors.text.secondary,
                        '&.Mui-focused': {
                            color: colors.primary[600],
                        },
                    },
                    ...sx,
                }}
                {...props}
            />
        );
    }
);

Input.displayName = 'Input';

export default Input;

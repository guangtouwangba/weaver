'use client';

import React from 'react';
import { Typography, TypographyProps } from '@mui/material';
import { textVariants, TextVariant, colors } from '../tokens';

/**
 * Text Component
 *
 * Semantic text with consistent typography and colors.
 * Wraps MUI Typography with design system tokens.
 */

export interface TextProps extends Omit<TypographyProps, 'variant' | 'color'> {
    /** Typography variant */
    variant?: TextVariant;
    /** Text color using semantic names */
    color?: 'primary' | 'secondary' | 'muted' | 'disabled' | 'inverse' | 'error' | 'success' | 'warning' | 'inherit';
    /** Whether to truncate with ellipsis */
    truncate?: boolean;
    /** Max number of lines before truncating */
    lineClamp?: number;
    children?: React.ReactNode;
}

const colorMap: Record<NonNullable<TextProps['color']>, string> = {
    primary: colors.text.primary,
    secondary: colors.text.secondary,
    muted: colors.text.muted,
    disabled: colors.text.disabled,
    inverse: colors.text.inverse,
    error: colors.error[500],
    success: colors.success[500],
    warning: colors.warning[500],
    inherit: 'inherit',
};

const variantToComponent: Record<TextVariant, 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'p' | 'span'> = {
    h1: 'h1',
    h2: 'h2',
    h3: 'h3',
    h4: 'h4',
    h5: 'h5',
    h6: 'h6',
    body: 'p',
    bodySmall: 'p',
    caption: 'span',
    label: 'span',
    overline: 'span',
    code: 'code',
};

export const Text = React.forwardRef<HTMLElement, TextProps>(
    function Text(
        {
            variant = 'body',
            color = 'primary',
            truncate = false,
            lineClamp,
            children,
            sx,
            ...props
        },
        ref
    ) {
        const variantStyle = textVariants[variant];
        const colorValue = colorMap[color];

        return (
            <Typography
                ref={ref}
                component={variantToComponent[variant]}
                sx={{
                    fontFamily: variantStyle.fontFamily,
                    fontSize: variantStyle.fontSize,
                    fontWeight: variantStyle.fontWeight,
                    lineHeight: variantStyle.lineHeight,
                    letterSpacing: 'letterSpacing' in variantStyle ? variantStyle.letterSpacing : undefined,
                    textTransform: 'textTransform' in variantStyle ? variantStyle.textTransform : undefined,
                    color: colorValue,
                    ...(truncate && {
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                    }),
                    ...(lineClamp && {
                        display: '-webkit-box',
                        WebkitLineClamp: lineClamp,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                    }),
                    ...sx,
                }}
                {...props}
            >
                {children}
            </Typography>
        );
    }
);

Text.displayName = 'Text';

export default Text;

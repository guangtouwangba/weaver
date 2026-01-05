'use client';

/**
 * Design System Typography Tokens
 *
 * Font families, sizes, weights, and line heights.
 */

export const fontFamily = {
    sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    mono: '"SF Mono", "Roboto Mono", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
} as const;

export const fontSize = {
    xs: 12,
    sm: 14,
    base: 16,
    lg: 18,
    xl: 20,
    '2xl': 24,
    '3xl': 30,
    '4xl': 36,
    '5xl': 48,
} as const;

export const fontWeight = {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
} as const;

export const lineHeight = {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
} as const;

export const letterSpacing = {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0em',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
} as const;

// Semantic typography variants (composites)
export const textVariants = {
    h1: {
        fontSize: fontSize['4xl'],
        fontWeight: fontWeight.bold,
        lineHeight: lineHeight.tight,
        fontFamily: fontFamily.sans,
    },
    h2: {
        fontSize: fontSize['3xl'],
        fontWeight: fontWeight.bold,
        lineHeight: lineHeight.tight,
        fontFamily: fontFamily.sans,
    },
    h3: {
        fontSize: fontSize['2xl'],
        fontWeight: fontWeight.semibold,
        lineHeight: lineHeight.snug,
        fontFamily: fontFamily.sans,
    },
    h4: {
        fontSize: fontSize.xl,
        fontWeight: fontWeight.semibold,
        lineHeight: lineHeight.snug,
        fontFamily: fontFamily.sans,
    },
    h5: {
        fontSize: fontSize.lg,
        fontWeight: fontWeight.semibold,
        lineHeight: lineHeight.normal,
        fontFamily: fontFamily.sans,
    },
    h6: {
        fontSize: fontSize.base,
        fontWeight: fontWeight.semibold,
        lineHeight: lineHeight.normal,
        fontFamily: fontFamily.sans,
    },
    body: {
        fontSize: fontSize.base,
        fontWeight: fontWeight.normal,
        lineHeight: lineHeight.normal,
        fontFamily: fontFamily.sans,
    },
    bodySmall: {
        fontSize: fontSize.sm,
        fontWeight: fontWeight.normal,
        lineHeight: lineHeight.normal,
        fontFamily: fontFamily.sans,
    },
    caption: {
        fontSize: fontSize.xs,
        fontWeight: fontWeight.normal,
        lineHeight: lineHeight.normal,
        fontFamily: fontFamily.sans,
    },
    label: {
        fontSize: fontSize.sm,
        fontWeight: fontWeight.medium,
        lineHeight: lineHeight.tight,
        fontFamily: fontFamily.sans,
    },
    overline: {
        fontSize: fontSize.xs,
        fontWeight: fontWeight.semibold,
        lineHeight: lineHeight.normal,
        letterSpacing: letterSpacing.wider,
        textTransform: 'uppercase' as const,
        fontFamily: fontFamily.sans,
    },
    code: {
        fontSize: fontSize.sm,
        fontWeight: fontWeight.normal,
        lineHeight: lineHeight.normal,
        fontFamily: fontFamily.mono,
    },
} as const;

// Type exports
export type FontSize = keyof typeof fontSize;
export type FontWeight = keyof typeof fontWeight;
export type TextVariant = keyof typeof textVariants;

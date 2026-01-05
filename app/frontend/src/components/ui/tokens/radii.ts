'use client';

/**
 * Design System Radius Tokens
 *
 * Border radius scale for consistent rounded corners.
 */

export const radii = {
    none: 0,
    xs: 2,
    sm: 4,
    md: 6,
    lg: 8,
    xl: 12,
    '2xl': 16,
    '3xl': 24,
    full: 9999,
} as const;

// Semantic aliases
export const radiusAliases = {
    button: radii.md,
    input: radii.md,
    card: radii.lg,
    modal: radii.xl,
    chip: radii.full,
    avatar: radii.full,
} as const;

// Type exports
export type RadiusScale = keyof typeof radii;
export type RadiusAlias = keyof typeof radiusAliases;

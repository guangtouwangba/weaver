'use client';

/**
 * Design System Shadow Tokens
 *
 * Elevation levels for surfaces and overlays.
 */

export const shadows = {
    none: 'none',
    xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)',
} as const;

// Semantic elevation levels (maps to MUI elevation)
export const elevation = {
    0: shadows.none,
    1: shadows.xs,
    2: shadows.sm,
    3: shadows.md,
    4: shadows.lg,
    5: shadows.xl,
    6: shadows['2xl'],
} as const;

// Type exports
export type ShadowLevel = keyof typeof shadows;
export type ElevationLevel = keyof typeof elevation;

'use client';

/**
 * Design System Spacing Tokens
 *
 * Consistent spacing scale based on 4px grid.
 * Use these values for margins, paddings, and gaps.
 */

export const spacing = {
    0: 0,
    0.5: 2,
    1: 4,
    1.5: 6,
    2: 8,
    2.5: 10,
    3: 12,
    4: 16,
    5: 20,
    6: 24,
    7: 28,
    8: 32,
    9: 36,
    10: 40,
    11: 44,
    12: 48,
    14: 56,
    16: 64,
    20: 80,
    24: 96,
    28: 112,
    32: 128,
    36: 144,
    40: 160,
    44: 176,
    48: 192,
} as const;

// Semantic spacing aliases
export const spacingAliases = {
    xs: spacing[1],   // 4px
    sm: spacing[2],   // 8px
    md: spacing[4],   // 16px
    lg: spacing[6],   // 24px
    xl: spacing[8],   // 32px
    '2xl': spacing[12], // 48px
    '3xl': spacing[16], // 64px
} as const;

// Type exports
export type SpacingScale = keyof typeof spacing;
export type SpacingAlias = keyof typeof spacingAliases;

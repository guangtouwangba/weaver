'use client';

/**
 * Design System Color Tokens
 *
 * Semantic color palette for the application.
 * These tokens provide a consistent color language across all components.
 */

export const colors = {
    // Primary brand color (Teal - warm, approachable)
    // Primary brand color (Sage Green - matte, natural, less fatigue)
    primary: {
        50: '#F5F9F6',  // very light sage/mint
        100: '#E6F4EA',
        200: '#CEE9D5',
        300: '#A6D6B4',
        400: '#75BA8C',
        500: '#388E3C', // User requested "Forest/Olive" lean
        600: '#2E7D32',
        700: '#1B5E20',
        800: '#144616', // darker forest
        900: '#0C2B0E',
        950: '#051406',
    },


    // Neutral / Gray scale (Warm Stone palette)
    // Yellow/brown undertones for paper-like reading experience
    neutral: {
        50: '#FAFAF9',
        100: '#F5F5F4',
        200: '#E7E5E4',
        300: '#D6D3D1',
        400: '#A8A29E',
        500: '#78716C',
        600: '#57534E',
        700: '#44403C',
        800: '#292524',
        900: '#1C1917',
        950: '#0C0A09',
    },

    // Success / Green
    success: {
        50: '#ECFDF5',
        100: '#D1FAE5',
        200: '#A7F3D0',
        300: '#6EE7B7',
        400: '#34D399',
        500: '#10B981',
        600: '#059669',
        700: '#047857',
        800: '#065F46',
        900: '#064E3B',
    },

    // Warning / Amber
    warning: {
        50: '#FFFBEB',
        100: '#FEF3C7',
        200: '#FDE68A',
        300: '#FCD34D',
        400: '#FBBF24',
        500: '#F59E0B',
        600: '#D97706',
        700: '#B45309',
        800: '#92400E',
        900: '#78350F',
    },

    // Error / Red
    error: {
        50: '#FEF2F2',
        100: '#FEE2E2',
        200: '#FECACA',
        300: '#FCA5A5',
        400: '#F87171',
        500: '#EF4444',
        600: '#DC2626',
        700: '#B91C1C',
        800: '#991B1B',
        900: '#7F1D1D',
    },

    // Info / Blue
    info: {
        50: '#EFF6FF',
        100: '#DBEAFE',
        200: '#BFDBFE',
        300: '#93C5FD',
        400: '#60A5FA',
        500: '#3B82F6',
        600: '#2563EB',
        700: '#1D4ED8',
        800: '#1E40AF',
        900: '#1E3A8A',
    },

    // Background colors (warm tones)
    background: {
        default: '#FAFAF9', // gray.50 - warm canvas
        paper: '#FAFAF9',
        subtle: '#F5F5F4', // gray.100
        muted: '#E7E5E4', // gray.200
    },

    // Text colors (warm tones, reduced contrast)
    text: {
        primary: '#292524', // gray.800 - brownish-gray
        secondary: '#78716C', // gray.500
        muted: '#A8A29E', // gray.400
        disabled: '#D6D3D1', // gray.300
        inverse: '#FAFAF9', // gray.50
    },

    // Border colors (warm tones)
    border: {
        default: '#E7E5E4', // gray.200
        muted: '#F5F5F4', // gray.100
        strong: '#D6D3D1', // gray.300
    },
} as const;

// Type exports for type-safe usage
export type ColorScale = typeof colors.primary;
export type SemanticColors = typeof colors;

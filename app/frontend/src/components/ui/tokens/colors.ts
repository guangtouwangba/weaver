'use client';

/**
 * Design System Color Tokens
 *
 * Semantic color palette for the application.
 * Theme: Violet + Cool Gray - Modern, clean, creative
 */

export const colors = {
    // Primary brand color (Violet - creative, intelligent)
    primary: {
        50: '#F5F3FF',   // very light violet
        100: '#EDE9FE',  // tag backgrounds
        200: '#DDD6FE',  // disabled states
        300: '#C4B5FD',  // focus rings
        400: '#A78BFA',  // secondary actions
        500: '#7C3AED',  // main brand color
        600: '#6D28D9',  // hover states
        700: '#5B21B6',  // active states, dark text
        800: '#4C1D95',  // headers on light bg
        900: '#3B0764',  // darkest
        950: '#2E1065',
    },

    // Neutral / Gray scale (Cool Gray palette)
    // Clean, crisp, modern feel
    neutral: {
        50: '#F9FAFB',   // page background
        100: '#F3F4F6',  // card backgrounds, panels
        200: '#E5E7EB',  // borders, dividers
        300: '#D1D5DB',  // disabled borders
        400: '#9CA3AF',  // placeholder text
        500: '#6B7280',  // secondary text
        600: '#4B5563',  // labels
        700: '#374151',  // subheadings
        800: '#1F2937',  // primary text
        900: '#111827',  // headlines
        950: '#030712',
    },

    // Accent color (Rose/Coral - for likes, hearts, notifications)
    accent: {
        50: '#FFF1F2',
        100: '#FFE4E6',
        200: '#FECDD3',
        300: '#FDA4AF',
        400: '#FB7185',
        500: '#F43F5E',  // hearts, likes
        600: '#E11D48',
        700: '#BE123C',
        800: '#9F1239',
        900: '#881337',
        950: '#4C0519',
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

    // Background colors (cool, clean)
    background: {
        default: '#FFFFFF',  // pure white
        paper: '#FFFFFF',
        subtle: '#F9FAFB',   // neutral.50
        muted: '#F3F4F6',    // neutral.100
    },

    // Text colors (cool gray, clean contrast)
    text: {
        primary: '#1F2937',   // neutral.800
        secondary: '#6B7280', // neutral.500
        muted: '#9CA3AF',     // neutral.400
        disabled: '#D1D5DB',  // neutral.300
        inverse: '#FFFFFF',
    },

    // Border colors (cool gray)
    border: {
        default: '#E5E7EB',  // neutral.200
        muted: '#F3F4F6',    // neutral.100
        strong: '#D1D5DB',   // neutral.300
    },

    // Selection state (distinctive dashed purple)
    selection: {
        border: '#7C3AED',       // primary.500
        borderStyle: 'dashed',
        background: '#F5F3FF',   // primary.50
        focusRing: '#C4B5FD',    // primary.300
    },

    // Tab states
    tab: {
        active: '#7C3AED',       // primary.500 (violet)
        inactive: '#6B7280',     // neutral.500
        hover: '#A78BFA',        // primary.400
        activeBackground: '#F5F3FF', // primary.50
    },
} as const;

// Type exports for type-safe usage
export type ColorScale = typeof colors.primary;
export type SemanticColors = typeof colors;

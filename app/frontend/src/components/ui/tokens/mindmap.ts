/**
 * Mindmap Card Design Tokens
 *
 * Violet theme with cool gray neutrals.
 * Uses dashed purple borders for selection - distinctive visual signature.
 */

export const mindmapCardTokens = {
    // Card backgrounds
    card: {
        bg: '#FFFFFF',
        bgRoot: '#F9FAFB',       // neutral.50
        borderActive: '#7C3AED', // primary.500 (violet)
        borderDashed: '#7C3AED', // primary.500 (violet) - for selection
        borderPending: '#D1D5DB', // neutral.300
        shadow: '0 4px 12px rgba(0,0,0,0.08)',
        shadowHover: '0 6px 16px rgba(0,0,0,0.12)',
        cornerRadius: 12,
    },
    // Status colors
    status: {
        success: '#10B981',      // success.500
        successBg: '#D1FAE5',    // success.100
        processing: '#7C3AED',   // primary.500 (violet)
        processingBg: '#EDE9FE', // primary.100
        pending: '#9CA3AF',      // neutral.400
        pendingBg: '#F3F4F6',    // neutral.100
        error: '#EF4444',        // error.500
        errorBg: '#FEE2E2',      // error.100
    },
    // Text colors
    text: {
        title: '#1F2937',        // neutral.800
        content: '#6B7280',      // neutral.500
        muted: '#9CA3AF',        // neutral.400
        onDark: '#FFFFFF',
    },
    // Tags/Chips (violet theme)
    tags: {
        bg: '#EDE9FE',           // primary.100
        text: '#5B21B6',         // primary.700
        border: '#DDD6FE',       // primary.200
    },
    // AI Insight Badge
    aiBadge: {
        bg: '#7C3AED',           // primary.500
        text: '#FFFFFF',
        accent: '#FBBF24',       // warning.400
    },
    // Root node specific (violet glow)
    root: {
        glowColor: '#7C3AED',    // primary.500
        glowOpacity: 0.3,
        iconColor: '#7C3AED',    // primary.500
    },
    // Selection state (distinctive dashed border)
    selection: {
        border: '2px dashed #7C3AED',
        background: '#F5F3FF',   // primary.50
        focusRing: '0 0 0 3px rgba(124, 58, 237, 0.3)',
    },
    // Animation timing
    animation: {
        pulse: 1.5,   // seconds
        skeleton: 1.2, // seconds
        dots: 0.6,    // seconds per dot
    },
};

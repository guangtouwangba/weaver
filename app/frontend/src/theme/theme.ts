'use client';

/**
 * Chakra UI Theme Configuration
 *
 * Cool Gray + Violet palette for a modern, clean experience.
 * Inspired by contemporary productivity tools - creative, intelligent, approachable.
 *
 * Key decisions:
 * - Cool Gray palette for clean, crisp UI
 * - Violet brand color for creativity and intelligence
 * - Pure white background for clarity
 * - Dashed purple selection for distinctive visual signature
 */

import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

const config: ThemeConfig = {
    initialColorMode: 'light',
    useSystemColorMode: false, // Dark mode deferred to future iteration
};

const theme = extendTheme({
    config,
    colors: {
        // Override default gray with Cool Gray palette
        gray: {
            50: '#F9FAFB',  // Page background
            100: '#F3F4F6', // Card backgrounds, panels
            200: '#E5E7EB', // Borders, dividers
            300: '#D1D5DB', // Disabled borders
            400: '#9CA3AF', // Placeholder text
            500: '#6B7280', // Secondary text
            600: '#4B5563', // Labels
            700: '#374151', // Subheadings
            800: '#1F2937', // Primary text
            900: '#111827', // Headlines
        },
        // Brand color: Violet for actions and selections
        brand: {
            50: '#F5F3FF',  // Selection backgrounds
            100: '#EDE9FE', // Tag backgrounds
            200: '#DDD6FE', // Disabled states
            300: '#C4B5FD', // Focus rings
            400: '#A78BFA', // Secondary actions, hover
            500: '#7C3AED', // Primary buttons, main brand
            600: '#6D28D9', // Hover state
            700: '#5B21B6', // Active state
            800: '#4C1D95', // Headers on light
            900: '#3B0764', // Darkest
        },
        // Accent color for likes, hearts, notifications
        accent: {
            50: '#FFF1F2',
            100: '#FFE4E6',
            200: '#FECDD3',
            300: '#FDA4AF',
            400: '#FB7185',
            500: '#F43F5E', // Hearts, likes
            600: '#E11D48',
            700: '#BE123C',
            800: '#9F1239',
            900: '#881337',
        },
    },
    styles: {
        global: {
            body: {
                bg: 'white',
                color: 'gray.800',
            },
        },
    },
    components: {
        // Default button to use brand color scheme
        Button: {
            defaultProps: {
                colorScheme: 'brand',
            },
        },
        // Tab styling
        Tabs: {
            variants: {
                line: {
                    tab: {
                        color: 'gray.500',
                        _selected: {
                            color: 'brand.500',
                            borderColor: 'brand.500',
                        },
                        _hover: {
                            color: 'brand.400',
                        },
                    },
                },
            },
        },
    },
    // Focus ring uses brand color for accessibility
    shadows: {
        outline: '0 0 0 3px rgba(124, 58, 237, 0.4)', // brand.500 at 40% opacity
    },
});

export default theme;

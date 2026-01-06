'use client';

/**
 * Chakra UI Theme Configuration
 *
 * Warm Gray (Stone) palette for a paper-like reading experience.
 * Inspired by Notion, Miro, Substack - human, approachable, easy on the eyes.
 *
 * Key decisions:
 * - Replaced Chakra's default blue-gray with Stone palette (yellow/brown undertones)
 * - Teal brand color for actions and selections
 * - Reduced contrast (gray.800 instead of pure black) for reduced eye strain
 */

import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

const config: ThemeConfig = {
    initialColorMode: 'light',
    useSystemColorMode: false, // Dark mode deferred to future iteration
};

const theme = extendTheme({
    config,
    colors: {
        // Override default gray with warm Stone palette
        gray: {
            50: '#FAFAF9', // Canvas background - subtle warm white
            100: '#F5F5F4', // Sidebar, panels
            200: '#E7E5E4', // Borders, dividers
            300: '#D6D3D1',
            400: '#A8A29E',
            500: '#78716C', // Secondary text, placeholders
            600: '#57534E',
            700: '#44403C',
            800: '#292524', // Primary text - brownish-gray, not black
            900: '#1C1917',
        },
        // Brand color: Teal for actions and selections
        brand: {
            50: '#F0FDFA',
            100: '#CCFBF1',
            200: '#99F6E4',
            300: '#5EEAD4',
            400: '#2DD4BF', // Selection highlight
            500: '#0D9488', // Primary buttons
            600: '#0F766E', // Hover state
            700: '#115E59',
            800: '#134E4A',
            900: '#042F2E',
        },
    },
    styles: {
        global: {
            body: {
                bg: 'gray.50',
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
    },
    // Focus ring uses brand color for accessibility
    shadows: {
        outline: '0 0 0 3px rgba(13, 148, 136, 0.4)', // brand.500 at 40% opacity
    },
});

export default theme;

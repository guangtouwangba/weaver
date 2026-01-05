'use client';

/**
 * Design System Tokens - Barrel Export
 *
 * Central export point for all design tokens.
 * Import from '@/components/ui/tokens' for consistent styling.
 */

// Color tokens
export { colors } from './colors';
export type { ColorScale, SemanticColors } from './colors';

// Spacing tokens
export { spacing, spacingAliases } from './spacing';
export type { SpacingScale, SpacingAlias } from './spacing';

// Typography tokens
export {
    fontFamily,
    fontSize,
    fontWeight,
    lineHeight,
    letterSpacing,
    textVariants,
} from './typography';
export type { FontSize, FontWeight, TextVariant } from './typography';

// Shadow tokens
export { shadows, elevation } from './shadows';
export type { ShadowLevel, ElevationLevel } from './shadows';

// Radius tokens
export { radii, radiusAliases } from './radii';
export type { RadiusScale, RadiusAlias } from './radii';

/**
 * Design System Tokens
 * Based on design/design-system.json
 * 
 * These tokens provide a 1:1 mapping of the design system to TypeScript constants
 * for use throughout the application.
 */

// Color Tokens
export const colors = {
  surface: {
    page: '#F5F6F9',
    card: '#FFFFFF',
    subtle: '#F9FAFB',
  },
  text: {
    primary: '#111827',
    secondary: '#4B5563',
    muted: '#9CA3AF',
    onAccent: '#FFFFFF',
    onWarning: '#1F2933',
    onPositive: '#064E3B',
  },
  border: {
    subtle: '#E5E7EB',
    strong: '#D1D5DB',
    focus: '#2563EB',
  },
  primary: {
    strong: '#3B82F6',
    soft: '#E0ECFF',
    hover: '#2563EB',
    pressed: '#1D4ED8',
  },
  secondary: {
    indigo: '#6366F1',
    purple: '#8B5CF6',
    pink: '#EC4899',
  },
  emerald: {
    strong: '#10B981',
    soft: '#D1FAE5',
  },
  orange: {
    strong: '#F97316',
    soft: '#FFEDD5',
  },
  yellow: {
    strong: '#FACC15',
    soft: '#FEF9C3',
  },
  red: {
    strong: '#F97373',
    soft: '#FEE2E2',
  },
  status: {
    info: '#3B82F6',
    success: '#10B981',
    warning: '#FBBF24',
    error: '#F97373',
    neutral: '#6B7280',
  },
};

// Spacing Tokens (in px)
export const spacing = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 40,
};

// Corner Radius Tokens (in px)
export const radius = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  pill: 999,
};

// Shadow Tokens
export const shadows = {
  none: 'none',
  soft: '0 4px 16px 0 rgba(15, 23, 42, 0.08)',
  medium: '0 8px 24px 0 rgba(15, 23, 42, 0.12)',
};

// Typography Tokens
export const typography = {
  fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", Inter, sans-serif',
  displayLg: {
    size: 32,
    lineHeight: 1.25,
    weight: 600,
  },
  displayMd: {
    size: 24,
    lineHeight: 1.3,
    weight: 600,
  },
  title: {
    size: 20,
    lineHeight: 1.3,
    weight: 600,
  },
  subtitle: {
    size: 16,
    lineHeight: 1.4,
    weight: 500,
  },
  body: {
    size: 14,
    lineHeight: 1.5,
    weight: 400,
  },
  bodyBold: {
    size: 14,
    lineHeight: 1.5,
    weight: 600,
  },
  caption: {
    size: 12,
    lineHeight: 1.5,
    weight: 400,
  },
  label: {
    size: 11,
    lineHeight: 1.4,
    weight: 600,
  },
};

// Motion Tokens
export const motion = {
  timing: {
    fast: 120,
    normal: 180,
    slow: 240,
  },
  easing: {
    standard: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
    emphasized: 'cubic-bezier(0.2, 1, 0.2, 1)',
  },
};

// Component-specific constants
export const components = {
  button: {
    primary: {
      height: 40,
      paddingHorizontal: 20,
    },
    secondary: {
      height: 36,
      paddingHorizontal: 18,
    },
    ghost: {
      height: 32,
      paddingHorizontal: 16,
    },
    tiny: {
      height: 24,
      paddingHorizontal: 12,
    },
  },
  chip: {
    height: 24,
    paddingHorizontal: 10,
    gap: 8,
  },
  card: {
    padding: 20,
  },
  listItem: {
    height: 56,
    paddingHorizontal: 16,
    gap: 12,
  },
  input: {
    height: 40,
    paddingHorizontal: 12,
  },
};

// Status chip variants
export const chipVariants = {
  pending: {
    background: colors.yellow.soft,
    color: colors.text.onWarning,
  },
  confirmed: {
    background: colors.emerald.soft,
    color: colors.emerald.strong,
  },
  alert: {
    background: colors.red.soft,
    color: colors.red.strong,
  },
  active: {
    background: colors.primary.soft,
    color: colors.primary.strong,
  },
  closed: {
    background: colors.surface.subtle,
    color: colors.text.muted,
  },
  info: {
    background: colors.primary.soft,
    color: colors.primary.strong,
  },
  success: {
    background: colors.emerald.soft,
    color: colors.emerald.strong,
  },
  warning: {
    background: colors.orange.soft,
    color: colors.text.onWarning,
  },
  error: {
    background: colors.red.soft,
    color: colors.text.onWarning,
  },
};


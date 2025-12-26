'use client';

import { createTheme } from '@mui/material/styles';

// ============================================================================
// MindMap Card Theme Tokens
// ============================================================================
export const mindmapCardTokens = {
  // Card backgrounds
  card: {
    bg: '#FFFFFF',
    bgRoot: '#F8FAFC',
    borderActive: '#4F46E5',
    borderDashed: '#94A3B8',
    borderPending: '#D1D5DB',
    shadow: '0 4px 12px rgba(0,0,0,0.08)',
    shadowHover: '0 6px 16px rgba(0,0,0,0.12)',
    cornerRadius: 12,
  },
  // Status colors
  status: {
    success: '#22C55E',
    successBg: '#DCFCE7',
    processing: '#3B82F6',
    processingBg: '#DBEAFE',
    pending: '#9CA3AF',
    pendingBg: '#F3F4F6',
    error: '#EF4444',
    errorBg: '#FEE2E2',
  },
  // Text colors
  text: {
    title: '#1F2937',
    content: '#6B7280',
    muted: '#9CA3AF',
    onDark: '#FFFFFF',
  },
  // Tags/Chips
  tags: {
    bg: '#EFF6FF',
    text: '#1E40AF',
    border: '#BFDBFE',
  },
  // AI Insight Badge
  aiBadge: {
    bg: '#1F2937',
    text: '#FFFFFF',
    accent: '#FBBF24',
  },
  // Root node specific
  root: {
    glowColor: '#4F46E5',
    glowOpacity: 0.3,
    iconColor: '#4F46E5',
  },
  // Animation timing
  animation: {
    pulse: 1.5, // seconds
    skeleton: 1.2, // seconds
    dots: 0.6, // seconds per dot
  },
};

const theme = createTheme({
  typography: {
    fontFamily: '"Inter", "San Francisco", "Segoe UI", "Helvetica Neue", "Lucida Grande", sans-serif',
  },
  palette: {
    mode: 'light',
    primary: {
      main: '#171717', // Dark gray/black for primary actions
    },
    background: {
      default: '#ffffff', // White to allow global dot pattern to show clearly
      paper: '#FFFFFF',   // White for cards and canvas
    },
    text: {
      primary: '#171717',
      secondary: '#6B7280', // Tailwind gray-500
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none', // No uppercase buttons
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none', // Disable elevation overlays in dark mode if we switch
        },
        rounded: {
          borderRadius: 12,
        },
      },
    },
  },
});

export default theme;

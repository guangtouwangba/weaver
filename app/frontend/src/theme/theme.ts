'use client';

import { createTheme } from '@mui/material/styles';

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
      default: '#F9FAFB', // Very light gray (Tailwind gray-50) for the app shell
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

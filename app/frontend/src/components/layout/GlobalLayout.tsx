'use client';

import React from 'react';
import { Box } from '@mui/material';
import GlobalSidebar from './GlobalSidebar';

const SIDEBAR_WIDTH = 72;

export default function GlobalLayout({ children }: { children: React.ReactNode }) {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <GlobalSidebar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          ml: `${SIDEBAR_WIDTH}px`, // Reserve space for fixed sidebar
          minHeight: '100vh',
          backgroundColor: 'background.paper', // Default to paper (white) for content areas
        }}
      >
        {children}
      </Box>
    </Box>
  );
}


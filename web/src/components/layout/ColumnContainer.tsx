'use client';

import React from 'react';
import { Box } from '@mui/material';

interface ColumnContainerProps {
  children: React.ReactNode;
  flex?: number;
  width?: number | string;
  borderLeft?: boolean;
  borderRight?: boolean;
}

export default function ColumnContainer({ 
  children, 
  flex, 
  width,
  borderLeft = false,
  borderRight = false
}: ColumnContainerProps) {
  return (
    <Box sx={{ 
      flex: flex, 
      width: width,
      flexShrink: width ? 0 : 1,
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      borderLeft: borderLeft ? '1px solid' : 'none',
      borderRight: borderRight ? '1px solid' : 'none',
      borderColor: 'divider',
      overflow: 'hidden',
      bgcolor: 'background.paper'
    }}>
      {children}
    </Box>
  );
}


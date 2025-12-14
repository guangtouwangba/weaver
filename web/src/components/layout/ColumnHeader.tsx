'use client';

import React from 'react';
import { Box, Typography } from '@mui/material';

interface ColumnHeaderProps {
  title: string;
  icon?: React.ElementType;
  action?: React.ReactNode;
}

export default function ColumnHeader({ title, icon: Icon, action }: ColumnHeaderProps) {
  return (
    <Box sx={{ 
      height: 48, 
      borderBottom: '1px solid', 
      borderColor: 'divider', 
      display: 'flex', 
      alignItems: 'center', 
      px: 2,
      gap: 1,
      bgcolor: 'background.default'
    }}>
      {Icon && <Icon size={18} className="text-gray-500" />}
      <Typography variant="subtitle2" fontWeight="600" sx={{ flexGrow: 1 }}>
        {title}
      </Typography>
      {action}
    </Box>
  );
}


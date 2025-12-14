'use client';

import React from 'react';
import { LucideProps } from 'lucide-react';
import { Box } from '@mui/material';

interface IconWrapperProps extends LucideProps {
  icon: React.ElementType;
}

export default function IconWrapper({ icon: Icon, ...props }: IconWrapperProps) {
  return (
    <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center' }}>
      <Icon {...props} />
    </Box>
  );
}


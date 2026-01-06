'use client';

import React from 'react';
import { colors } from '@/components/ui/tokens';

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
    <div style={{
      flex: flex,
      width: width,
      flexShrink: width ? 0 : 1,
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      borderLeft: borderLeft ? `1px solid ${colors.border.default}` : 'none',
      borderRight: borderRight ? `1px solid ${colors.border.default}` : 'none',
      overflow: 'hidden',
      backgroundColor: colors.background.paper
    }}>
      {children}
    </div>
  );
}

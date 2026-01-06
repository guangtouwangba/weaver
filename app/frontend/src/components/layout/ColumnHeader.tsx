'use client';

import React from 'react';
import { Text } from '@/components/ui/primitives';
import { colors } from '@/components/ui/tokens';

interface ColumnHeaderProps {
  title: string;
  icon?: React.ElementType;
  action?: React.ReactNode;
}

export default function ColumnHeader({ title, icon: Icon, action }: ColumnHeaderProps) {
  return (
    <div style={{
      height: 48,
      borderBottom: `1px solid ${colors.border.default}`,
      display: 'flex',
      alignItems: 'center',
      paddingLeft: 16,
      paddingRight: 16,
      gap: 8,
      backgroundColor: colors.background.default
    }}>
      {Icon && <Icon size={18} className="text-gray-500" />}
      <div style={{ flexGrow: 1 }}>
        <Text variant="bodySmall" style={{ fontWeight: 600 }}>
          {title}
        </Text>
      </div>
      {action}
    </div>
  );
}

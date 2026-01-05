'use client';

import { ReactNode } from 'react';
import { Surface, Stack, Text } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';

interface TemplateCardProps {
  title: string;
  description: string;
  icon: ReactNode;
  color?: string;
  onClick: () => void;
}

export default function TemplateCard({ title, description, icon, color, onClick }: TemplateCardProps) {
  return (
    <Surface
      elevation={0}
      radius="lg"
      bordered
      onClick={onClick}
      sx={{
        p: 3,
        height: '100%',
        cursor: 'pointer',
        transition: 'all 0.2s',
        display: 'flex',
        flexDirection: 'column',
        '&:hover': {
          borderColor: colors.primary[500],
          transform: 'translateY(-2px)',
          boxShadow: shadows.md,
        },
      }}
    >
      <Stack direction="column" gap={2}>
        <div style={{ color: color || colors.primary[500] }}>
          {icon}
        </div>
        <Text variant="h6" color="primary">
          {title}
        </Text>
        <Text variant="bodySmall" color="secondary">
          {description}
        </Text>
      </Stack>
    </Surface>
  );
}

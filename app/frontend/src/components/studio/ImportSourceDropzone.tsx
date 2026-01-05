'use client';

import React from 'react';
import { Stack, Text } from '@/components/ui';
import { colors, radii } from '@/components/ui/tokens';
import { AddIcon } from '@/components/ui/icons';

interface ImportSourceDropzoneProps {
  onClick: () => void;
  onDragEnter: (e: React.DragEvent) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  isDragging?: boolean;
}

export default function ImportSourceDropzone({
  onClick,
  onDragEnter,
  onDragOver,
  onDragLeave,
  onDrop,
  isDragging = false,
}: ImportSourceDropzoneProps) {
  return (
    <Stack
      direction="column"
      align="center"
      justify="center"
      gap={1}
      onClick={onClick}
      onDragEnter={onDragEnter}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      sx={{
        border: '2px dashed',
        borderColor: isDragging ? colors.primary[500] : colors.border.default,
        borderRadius: `${radii.lg}px`,
        p: 3,
        cursor: 'pointer',
        bgcolor: isDragging ? colors.primary[50] : 'transparent',
        transition: 'all 0.2s ease-in-out',
        minHeight: 120,
        '&:hover': {
          borderColor: colors.primary[500],
          bgcolor: colors.primary[50],
        }
      }}
    >
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: '50%',
          backgroundColor: colors.primary[50],
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: colors.primary[500],
          border: `1px solid ${colors.primary[100]}`,
        }}
      >
        <AddIcon size="lg" />
      </div>
      <Text
        variant="bodySmall"
        sx={{
          color: colors.neutral[600],
          fontWeight: 600,
        }}
      >
        Import Source
      </Text>
    </Stack>
  );
}

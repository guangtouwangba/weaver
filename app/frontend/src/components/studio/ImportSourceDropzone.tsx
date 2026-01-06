'use client';

import React, { useState } from 'react';
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
  const [isHovered, setIsHovered] = useState(false);

  const isActive = isDragging || isHovered;

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
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        border: '2px dashed',
        borderColor: isActive ? colors.primary[500] : colors.border.default, // Gray default
        borderRadius: radii.lg,
        padding: 24,
        cursor: 'pointer',
        backgroundColor: isActive ? colors.primary[50] : colors.neutral[50], // Gray-50 default, Sage-50 on active/hover
        transition: 'all 0.2s ease-in-out',
        minHeight: 120,
      }}
    >
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: '50%',
          backgroundColor: isActive ? colors.primary[50] : colors.neutral[100], // Gray-100 default
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: isActive ? colors.primary[500] : colors.neutral[400], // Gray-400 default
          border: '1px solid', // Border style
          borderColor: isActive ? colors.primary[100] : 'transparent', // No border by default (or subtle)
        }}
      >
        <AddIcon size="lg" />
      </div>
      <Text
        variant="bodySmall"
        style={{
          color: colors.neutral[600],
          fontWeight: 600,
        }}
      >
        Import Source
      </Text>
    </Stack>
  );
}

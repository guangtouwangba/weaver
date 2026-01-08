'use client';

import { Project } from '@/lib/api';
import { Surface, Stack, Text, IconButton } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import { MoreVertIcon, DescriptionIcon, HistoryIcon } from '@/components/ui/icons';
import Link from 'next/link';
import { useState } from 'react';

// Simple hash for consistent colors (same as ProjectCard)
const getProjectColor = (name: string) => {
  const palettes = [
    { bg: '#FEE2E2', color: '#B91C1C' }, // Red
    { bg: '#FFEDD5', color: '#C2410C' }, // Orange
    { bg: '#FEF3C7', color: '#B45309' }, // Amber
    { bg: '#ECFCCB', color: '#4D7C0F' }, // Lime
    { bg: '#D1FAE5', color: '#047857' }, // Emerald
    { bg: '#EDE9FE', color: '#6D28D9' }, // Violet
    { bg: '#E0F2FE', color: '#0369A1' }, // Sky
    { bg: '#E0E7FF', color: '#4338CA' }, // Indigo
    { bg: '#FAE8FF', color: '#A21CAF' }, // Fuchsia
    { bg: '#FFE4E6', color: '#BE123C' }, // Rose
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return palettes[Math.abs(hash) % palettes.length];
};

interface ProjectListItemProps {
  project: Project;
  onOpenMenu: (event: React.MouseEvent<HTMLElement>, project: Project) => void;
}

export default function ProjectListItem({ project, onOpenMenu }: ProjectListItemProps) {
  const [isHovered, setIsHovered] = useState(false);

  // Calculate relative time
  const getRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    return date.toLocaleDateString();
  };

  const palette = getProjectColor(project.name);

  return (
    <Link href={`/studio/${project.id}`} style={{ textDecoration: 'none' }}>
      <Surface
        elevation={0}
        radius="md"
        bordered
        style={{
          padding: '16px 20px',
          position: 'relative',
          transition: 'all 0.18s ease',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          borderColor: isHovered ? colors.primary[500] : colors.neutral[200],
          backgroundColor: '#fff',
          boxShadow: isHovered 
            ? '0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04)' 
            : '0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)',
          transform: isHovered ? 'translateY(-2px)' : 'translateY(0)',
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Colored Project Icon */}
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: radii.sm,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: palette.bg,
            color: palette.color,
            fontSize: '1rem',
            fontWeight: 600,
            flexShrink: 0,
          }}
        >
          {project.name.charAt(0).toUpperCase()}
        </div>

        {/* Project Name */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <Text variant="body" weight="600" truncate style={{ color: '#111827', fontWeight: 600 }}>
            {project.name}
          </Text>
          {project.description && (
            <Text
              variant="caption"
              color="secondary"
              truncate
              style={{ marginTop: 2 }}
            >
              {project.description}
            </Text>
          )}
        </div>

        {/* Document count placeholder */}
        <Stack direction="row" align="center" gap={4} style={{ color: '#9CA3AF', minWidth: 80 }}>
          <DescriptionIcon size={14} />
          <Text variant="caption" color="secondary">
            {project.document_count || 0} docs
          </Text>
        </Stack>

        {/* Last modified */}
        <Stack direction="row" align="center" gap={4} style={{ color: '#9CA3AF', minWidth: 100 }}>
          <HistoryIcon size={14} />
          <Text variant="caption" color="secondary">
            {getRelativeTime(project.updated_at)}
          </Text>
        </Stack>

        {/* Menu button */}
        <IconButton
          size="sm"
          variant="ghost"
          onClick={(e: React.MouseEvent<HTMLElement>) => {
            e.preventDefault();
            onOpenMenu(e, project);
          }}
          style={{
            opacity: isHovered ? 1 : 0.4,
            transition: 'opacity 0.15s ease',
          }}
        >
          <MoreVertIcon size={16} />
        </IconButton>
      </Surface>
    </Link>
  );
}

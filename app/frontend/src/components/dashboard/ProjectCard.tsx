'use client';

import { Project } from '@/lib/api';
import { Surface, Stack, Text, IconButton } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import { MoreVertIcon } from '@/components/ui/icons';
import Link from 'next/link';
import { useState } from 'react';

// Simple hash for consistent colors
const getProjectColor = (name: string) => {
  // Pastel palette (Plan A: Random soft backgrounds)
  const palettes = [
    { bg: '#FEE2E2', color: '#B91C1C' }, // Red
    { bg: '#FFEDD5', color: '#C2410C' }, // Orange
    { bg: '#FEF3C7', color: '#B45309' }, // Amber
    { bg: '#ECFCCB', color: '#4D7C0F' }, // Lime
    { bg: '#D1FAE5', color: '#047857' }, // Emerald
    { bg: '#CCFBF1', color: '#0F766E' }, // Teal
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

interface ProjectCardProps {
  project: Project;
  onOpenMenu: (event: React.MouseEvent<HTMLElement>, project: Project) => void;
}

export default function ProjectCard({ project, onOpenMenu }: ProjectCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  // Calculate relative time (e.g., "Edited 2h ago")
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

  return (
    <Link href={`/studio/${project.id}`} style={{ textDecoration: 'none' }}>
      <Surface
        elevation={0}
        radius="lg"
        bordered
        style={{
          padding: 24,
          height: '100%',
          position: 'relative',
          transition: 'all 0.2s',
          display: 'flex',
          flexDirection: 'column',
          borderColor: isHovered ? colors.primary[500] : undefined,
          transform: isHovered ? 'translateY(-2px)' : undefined,
          boxShadow: isHovered ? shadows.md : undefined,
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <Stack direction="row" align="center" style={{ marginBottom: 16 }}>
          {/* Colored Project Icon */}
          {(() => {
            const palette = getProjectColor(project.name);
            return (
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: radii.md,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: palette.bg,
                  color: palette.color,
                  fontSize: '1.25rem',
                  fontWeight: 600,
                  marginRight: 16,
                }}
              >
                {project.name.charAt(0).toUpperCase()}
              </div>
            );
          })()}
          <div style={{ minWidth: 0, flex: 1 }}>
            <Text variant="h6" truncate>
              {project.name}
            </Text>
          </div>
        </Stack>

        {project.description && (
          <Text
            variant="bodySmall"
            color="secondary"
            style={{
              marginBottom: 16,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {project.description}
          </Text>
        )}

        <Stack direction="row" justify="end" align="center" style={{ marginTop: 'auto' }}>
          <Text variant="caption" color="secondary">
            Edited {getRelativeTime(project.updated_at)}
          </Text>
        </Stack>

        <IconButton
          size="sm"
          variant="ghost"
          onClick={(e: React.MouseEvent<HTMLElement>) => {
            e.preventDefault(); // Prevent navigation
            onOpenMenu(e, project);
          }}
          style={{
            position: 'absolute',
            top: 12,
            right: 12,
            opacity: isHovered ? 1 : 0.6,
          }}
        >
          <MoreVertIcon size={16} />
        </IconButton>
      </Surface>
    </Link>
  );
}

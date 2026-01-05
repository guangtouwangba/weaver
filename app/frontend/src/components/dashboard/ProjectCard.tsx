'use client';

import { Project } from '@/lib/api';
import { Surface, Stack, Text, IconButton } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import { MoreVertIcon } from '@/components/ui/icons';
import Link from 'next/link';

// Simple hash for consistent colors
const getProjectColor = (name: string) => {
  const projectColors = [
    '#4f46e5', // Indigo
    '#059669', // Emerald
    '#d97706', // Amber
    '#dc2626', // Red
    '#7c3aed', // Violet
    '#2563eb', // Blue
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return projectColors[Math.abs(hash) % projectColors.length];
};

interface ProjectCardProps {
  project: Project;
  onOpenMenu: (event: React.MouseEvent<HTMLElement>, project: Project) => void;
}

export default function ProjectCard({ project, onOpenMenu }: ProjectCardProps) {
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
        sx={{
          p: 3,
          height: '100%',
          position: 'relative',
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
        <Stack direction="row" align="center" sx={{ mb: 2 }}>
          {/* Colored Project Icon */}
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: radii.md,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: getProjectColor(project.name),
              color: 'white',
              fontSize: '1.25rem',
              fontWeight: 600,
              marginRight: 16,
            }}
          >
            {project.name.charAt(0).toUpperCase()}
          </div>
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
            sx={{
              mb: 2,
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

        <Stack direction="row" justify="end" align="center" sx={{ mt: 'auto' }}>
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
          sx={{
            position: 'absolute',
            top: 12,
            right: 12,
            opacity: 0.6,
            '&:hover': { opacity: 1 }
          }}
        >
          <MoreVertIcon size="sm" />
        </IconButton>
      </Surface>
    </Link>
  );
}

import { Project } from '@/lib/api';
import { Paper, Typography, Box, IconButton } from '@mui/material';
import { MoreVertIcon } from '@/components/ui/icons';
import Link from 'next/link';

// Simple hash for consistent colors
const getProjectColor = (name: string) => {
  const colors = [
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
  return colors[Math.abs(hash) % colors.length];
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
      <Paper
        elevation={0}
        sx={{
          p: 3,
          height: '100%',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 3,
          position: 'relative',
          transition: 'all 0.2s',
          backgroundColor: 'white',
          display: 'flex',
          flexDirection: 'column',
          '&:hover': {
            borderColor: 'primary.main',
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 16px rgba(0,0,0,0.05)',
          },
        }}
      >
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
          {/* Colored Project Icon */}
          <Box sx={{
            width: 48,
            height: 48,
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: getProjectColor(project.name),
            color: 'white',
            fontSize: '1.25rem',
            fontWeight: 600,
            mr: 2
          }}>
            {project.name.charAt(0).toUpperCase()}
          </Box>
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography variant="h6" fontWeight="600" color="text.primary" noWrap>
              {project.name}
            </Typography>
          </Box>
        </Box>

        {project.description && (
          <Typography variant="body2" color="text.secondary" sx={{
            mb: 2,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            color: '#4b5563' // Darker gray for better contrast
          }}>
            {project.description}
          </Typography>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', mt: 'auto' }}>
          <Typography variant="caption" sx={{ color: '#6b7280' }}>
            Edited {getRelativeTime(project.updated_at)}
          </Typography>
        </Box>

        <IconButton
          size="small"
          onClick={(e) => {
            e.preventDefault(); // Prevent navigation
            onOpenMenu(e, project);
          }}
          sx={{
            position: 'absolute',
            top: 12,
            right: 12,
            color: 'text.secondary',
            opacity: 0.6,
            '&:hover': { opacity: 1, bgcolor: 'action.hover' }
          }}
        >
          <MoreVertIcon size="sm" />
        </IconButton>
      </Paper>
    </Link>
  );
}


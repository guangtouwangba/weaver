import { Project } from '@/lib/api';
import { Paper, Typography, Box, IconButton, Avatar, AvatarGroup } from '@mui/material';
import { MoreVertIcon } from '@/components/ui/icons';
import Link from 'next/link';

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
          '&:hover': {
            borderColor: 'primary.main',
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 16px rgba(0,0,0,0.05)',
          },
        }}
      >
        <Box sx={{ 
          height: 100, 
          bgcolor: 'grey.50', 
          borderRadius: 2, 
          mb: 2, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          overflow: 'hidden'
        }}>
           {/* Placeholder for project preview/thumbnail */}
           <Box sx={{ width: 48, height: 48, bgcolor: 'primary.main', opacity: 0.05, borderRadius: 1 }} />
        </Box>

        <Typography variant="h6" fontWeight="600" color="text.primary" gutterBottom noWrap>
          {project.name}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ 
          mb: 2, 
          height: 40, 
          overflow: 'hidden', 
          textOverflow: 'ellipsis', 
          display: '-webkit-box', 
          WebkitLineClamp: 2, 
          WebkitBoxOrient: 'vertical' 
        }}>
          {project.description || 'No description'}
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 'auto' }}>
           <AvatarGroup max={3} sx={{ '& .MuiAvatar-root': { width: 24, height: 24, fontSize: 12 } }}>
              <Avatar sx={{ bgcolor: 'primary.light' }}>AL</Avatar>
           </AvatarGroup>
           
           <Typography variant="caption" color="text.secondary">
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


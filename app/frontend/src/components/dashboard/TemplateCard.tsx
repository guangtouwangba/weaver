import { ReactNode } from 'react';
import { Paper, Typography, Box } from '@mui/material';

interface TemplateCardProps {
  title: string;
  description: string;
  icon: ReactNode;
  color?: string;
  onClick: () => void;
}

export default function TemplateCard({ title, description, icon, color = 'primary.main', onClick }: TemplateCardProps) {
  return (
    <Paper
      elevation={0}
      onClick={onClick}
      sx={{
        p: 3,
        height: '100%',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 3,
        cursor: 'pointer',
        transition: 'all 0.2s',
        display: 'flex',
        flexDirection: 'column',
        '&:hover': {
          borderColor: 'primary.main',
          transform: 'translateY(-2px)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        },
      }}
    >
      <Box sx={{ color: color, mb: 2 }}>
        {icon}
      </Box>
      <Typography variant="subtitle1" fontWeight="600" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {description}
      </Typography>
    </Paper>
  );
}


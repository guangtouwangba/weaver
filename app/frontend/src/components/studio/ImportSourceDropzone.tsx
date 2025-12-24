import React from 'react';
import { Box, Typography } from '@mui/material';
import { Plus } from 'lucide-react';

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
    <Box
      onClick={onClick}
      onDragEnter={onDragEnter}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      sx={{
        border: '2px dashed',
        borderColor: isDragging ? '#6366F1' : '#E5E7EB', // Indigo-500 : Gray-200
        borderRadius: 3, // Slightly more rounded (12px)
        p: 3,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 1.5,
        cursor: 'pointer',
        bgcolor: isDragging ? '#EEF2FF' : 'transparent', // Indigo-50 : Transparent
        transition: 'all 0.2s ease-in-out',
        minHeight: 120, // Match the height in the description/screenshot
        '&:hover': {
          borderColor: '#6366F1', // Indigo-500
          bgcolor: '#EEF2FF', // Indigo-50
        }
      }}
    >
      <Box
        sx={{
          width: 48,
          height: 48,
          borderRadius: '50%',
          bgcolor: '#EEF2FF', // Indigo-50
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#6366F1', // Indigo-500
          border: '1px solid',
          borderColor: '#E0E7FF', // Indigo-100
        }}
      >
        <Plus size={24} strokeWidth={2.5} />
      </Box>
      <Typography 
        variant="body2" 
        sx={{ 
          color: '#4B5563', // Gray-600
          fontWeight: 600,
          fontSize: '0.9rem'
        }}
      >
        Import Source
      </Typography>
    </Box>
  );
}


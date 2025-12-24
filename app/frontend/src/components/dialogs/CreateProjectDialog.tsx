'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Button, 
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Typography,
  Box,
  IconButton,
  InputAdornment
} from "@mui/material";
import { X, Tag, ArrowRight } from "lucide-react";
import { projectsApi } from "@/lib/api";

interface CreateProjectDialogProps {
  open: boolean;
  onClose: () => void;
  onProjectCreated?: (project: any) => void;
}

export default function CreateProjectDialog({ open, onClose, onProjectCreated }: CreateProjectDialogProps) {
  const router = useRouter();
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [newProjectTags, setNewProjectTags] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    
    try {
      setCreating(true);
      setError(null);
      const project = await projectsApi.create(newProjectName, newProjectDescription || undefined);
      
      if (onProjectCreated) {
        onProjectCreated(project);
      } else {
        router.push(`/studio/${project.id}`);
      }
      
      handleClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  const handleClose = () => {
    setNewProjectName('');
    setNewProjectDescription('');
    setNewProjectTags('');
    setError(null);
    onClose();
  };

  // Custom input style for a cleaner look
  const inputSx = {
    '& .MuiOutlinedInput-root': {
      borderRadius: 1.5, // Less rounded to match screenshot (looks like ~6-8px)
      bgcolor: 'background.paper',
      fontSize: '0.9rem',
      '& fieldset': {
        borderColor: '#E5E7EB',
      },
      '&:hover fieldset': {
        borderColor: '#D1D5DB',
      },
      '&.Mui-focused fieldset': {
        borderColor: '#6366f1', // Indigo focus
        borderWidth: 1,
      },
    },
    '& .MuiInputLabel-root': {
      color: '#374151', // Gray-700
      fontWeight: 600,
      fontSize: '0.9rem',
      marginBottom: '6px', // Spacing between label and input
      position: 'static', // Static position for label above input
      transform: 'none',
      '&.Mui-focused': {
        color: '#374151',
      }
    },
    // Hide default legend since we are using static label
    '& legend': { display: 'none' },
  };

  return (
    <Dialog 
      open={open} 
      onClose={() => !creating && handleClose()}
      maxWidth={false}
      PaperProps={{
        sx: {
          borderRadius: 3,
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          width: 'calc(100% - 32px)',
          maxWidth: 520,
          m: 2,
          p: 0,
          overflow: 'hidden'
        }
      }}
    >
      {/* Header */}
      <Box sx={{ px: 3, py: 2.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h6" fontWeight="700" sx={{ lineHeight: 1.2 }}>
          Create New Project
        </Typography>
        <IconButton 
          onClick={handleClose} 
          disabled={creating}
          size="small" 
          sx={{ color: 'text.secondary' }}
        >
          <X size={20} />
        </IconButton>
      </Box>
      
      <DialogContent sx={{ px: 3, py: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Typography component="label" sx={{ display: 'block', mb: 1, fontWeight: 600, fontSize: '0.9rem', color: '#374151' }}>
            Project Name
          </Typography>
          <TextField
            autoFocus
            fullWidth
            placeholder="Enter project name"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            disabled={creating}
            error={!!error}
            helperText={error}
            sx={inputSx}
            size="medium"
            hiddenLabel
          />
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography component="label" sx={{ display: 'block', mb: 1, fontWeight: 600, fontSize: '0.9rem', color: '#374151' }}>
            Description <Typography component="span" variant="caption" color="text.secondary" sx={{ fontWeight: 400 }}>(Optional)</Typography>
          </Typography>
          <TextField
            fullWidth
            placeholder="Briefly describe the goals and scope of this research..."
            multiline
            rows={4}
            value={newProjectDescription}
            onChange={(e) => setNewProjectDescription(e.target.value)}
            disabled={creating}
            sx={inputSx}
            hiddenLabel
          />
        </Box>

        <Box sx={{ mb: 1 }}>
          <Typography component="label" sx={{ display: 'block', mb: 1, fontWeight: 600, fontSize: '0.9rem', color: '#374151' }}>
            Tags
          </Typography>
          <TextField
            fullWidth
            placeholder="Add tags to organize (e.g., Marketing, Q1)"
            value={newProjectTags}
            onChange={(e) => setNewProjectTags(e.target.value)}
            disabled={creating}
            sx={inputSx}
            hiddenLabel
            InputProps={{
              startAdornment: (
                <InputAdornment position="start" sx={{ color: 'text.secondary', ml: 0.5 }}>
                  <Tag size={16} />
                </InputAdornment>
              ),
            }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            Separate tags with commas
          </Typography>
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ px: 3, py: 2.5, borderTop: '1px solid', borderColor: 'divider' }}>
        <Button 
          onClick={handleClose} 
          disabled={creating}
          sx={{ 
            color: 'text.secondary', 
            textTransform: 'none',
            fontWeight: 500,
            mr: 'auto' // Push to left
          }}
        >
          Cancel
        </Button>
        <Button 
          onClick={handleCreateProject} 
          variant="contained"
          disabled={!newProjectName.trim() || creating}
          endIcon={!creating && <ArrowRight size={16} />}
          sx={{ 
            textTransform: 'none',
            borderRadius: 2,
            px: 3,
            py: 1,
            fontWeight: 600,
            bgcolor: '#4f46e5', // Indigo-600
            '&:hover': {
              bgcolor: '#4338ca',
            }
          }}
        >
          {creating ? <CircularProgress size={20} color="inherit" /> : 'Next'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

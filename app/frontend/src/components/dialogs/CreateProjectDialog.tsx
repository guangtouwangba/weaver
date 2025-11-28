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
} from "@mui/material";
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
    setError(null);
    onClose();
  };

  // Custom input style for a cleaner look
  const inputSx = {
    '& .MuiOutlinedInput-root': {
      borderRadius: 2.5,
      bgcolor: '#F9FAFB',
      fontSize: '0.9rem',
      '& fieldset': {
        borderColor: '#E5E7EB',
      },
      '&:hover fieldset': {
        borderColor: '#D1D5DB',
      },
      '&.Mui-focused fieldset': {
        borderColor: 'primary.main',
        borderWidth: 1,
      },
    },
    '& .MuiInputLabel-root': {
      color: '#6B7280',
      fontWeight: 500,
      fontSize: '0.85rem',
    },
  };

  return (
    <Dialog 
      open={open} 
      onClose={() => !creating && handleClose()}
      maxWidth={false}
      sx={{
        '& .MuiDialog-container': {
          alignItems: 'center',
        }
      }}
      PaperProps={{
        sx: {
          borderRadius: 4,
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          width: 'calc(100% - 64px)',
          maxWidth: 480,
          m: 0,
        }
      }}
    >
      <DialogTitle sx={{ pb: 1, pt: 2.5, px: 3, fontSize: '1rem', fontWeight: 600 }}>
        Create New Project
      </DialogTitle>
      
      <DialogContent sx={{ px: 3, pb: 2, pt: '8px !important' }}>
        <TextField
          autoFocus
          margin="none"
          label="Project Name"
          placeholder="e.g., Quantum Computing Research"
          fullWidth
          value={newProjectName}
          onChange={(e) => setNewProjectName(e.target.value)}
          disabled={creating}
          error={!!error}
          helperText={error}
          sx={{ mb: 2.5, ...inputSx }}
          InputLabelProps={{ shrink: true }} 
          size="small"
        />
        <TextField
          margin="none"
          label="Description"
          placeholder="What is this project about?"
          fullWidth
          multiline
          rows={3}
          value={newProjectDescription}
          onChange={(e) => setNewProjectDescription(e.target.value)}
          disabled={creating}
          sx={inputSx}
          InputLabelProps={{ shrink: true }}
          size="small"
        />
      </DialogContent>
      
      <DialogActions sx={{ px: 3, pb: 2.5, pt: 1 }}>
        <Button 
          onClick={handleClose} 
          disabled={creating}
          size="small"
          sx={{ 
            color: 'text.secondary', 
            textTransform: 'none',
            borderRadius: 2,
            px: 2,
            mr: 1
          }}
        >
          Cancel
        </Button>
        <Button 
          onClick={handleCreateProject} 
          variant="contained"
          disabled={!newProjectName.trim() || creating}
          size="small"
          sx={{ 
            textTransform: 'none',
            borderRadius: 2,
            boxShadow: 'none',
            px: 3,
            py: 0.8,
            bgcolor: '#171717',
            '&:hover': {
              bgcolor: '#000',
              boxShadow: 'none'
            }
          }}
        >
          {creating ? <CircularProgress size={16} color="inherit" /> : 'Create Project'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Button,
  Dialog,
  DialogContent,
  DialogActions,
  TextField,
  InputAdornment
} from "@mui/material";
import { Stack, Text, IconButton, Spinner } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import { CloseIcon, TagIcon, ArrowForwardIcon } from '@/components/ui/icons';
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
      borderRadius: radii.md,
      bgcolor: colors.background.paper,
      fontSize: '0.9rem',
      '& fieldset': {
        borderColor: colors.border.default,
      },
      '&:hover fieldset': {
        borderColor: colors.neutral[400],
      },
      '&.Mui-focused fieldset': {
        borderColor: colors.primary[500],
        borderWidth: 1,
      },
    },
    '& .MuiInputLabel-root': {
      color: colors.text.primary,
      fontWeight: 600,
      fontSize: '0.9rem',
      marginBottom: '6px',
      position: 'static',
      transform: 'none',
      '&.Mui-focused': {
        color: colors.text.primary,
      }
    },
    '& legend': { display: 'none' },
  };

  return (
    <Dialog
      open={open}
      onClose={() => !creating && handleClose()}
      maxWidth={false}
      PaperProps={{
        sx: {
          borderRadius: radii.lg,
          boxShadow: shadows.xl,
          width: 'calc(100% - 32px)',
          maxWidth: 520,
          m: 2,
          p: 0,
          overflow: 'hidden'
        }
      }}
    >
      {/* Header */}
      <Stack
        direction="row"
        align="center"
        justify="between"
        sx={{
          px: 3,
          py: 2.5,
          borderBottom: `1px solid ${colors.border.default}`
        }}
      >
        <Text variant="h6">Create New Project</Text>
        <IconButton
          onClick={handleClose}
          disabled={creating}
          size="sm"
          variant="ghost"
        >
          <CloseIcon size="md" />
        </IconButton>
      </Stack>

      <DialogContent sx={{ px: 3, py: 3 }}>
        <div style={{ marginBottom: 24 }}>
          <Text variant="label" sx={{ display: 'block', mb: 1, color: colors.text.primary }}>
            Project Name
          </Text>
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
        </div>

        <div style={{ marginBottom: 24 }}>
          <Stack direction="row" gap={1} sx={{ mb: 1 }}>
            <Text variant="label" sx={{ color: colors.text.primary }}>
              Description
            </Text>
            <Text variant="caption" color="secondary">(Optional)</Text>
          </Stack>
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
        </div>

        <div style={{ marginBottom: 8 }}>
          <Text variant="label" sx={{ display: 'block', mb: 1, color: colors.text.primary }}>
            Tags
          </Text>
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
                <InputAdornment position="start" sx={{ color: colors.text.secondary, ml: 0.5 }}>
                  <TagIcon size="sm" />
                </InputAdornment>
              ),
            }}
          />
          <Text variant="caption" color="secondary" sx={{ mt: 0.5, display: 'block' }}>
            Separate tags with commas
          </Text>
        </div>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2.5, borderTop: `1px solid ${colors.border.default}` }}>
        <Button
          onClick={handleClose}
          disabled={creating}
          sx={{
            color: colors.text.secondary,
            textTransform: 'none',
            fontWeight: 500,
            mr: 'auto'
          }}
        >
          Cancel
        </Button>
        <Button
          onClick={handleCreateProject}
          variant="contained"
          disabled={!newProjectName.trim() || creating}
          endIcon={!creating && <ArrowForwardIcon size="sm" />}
          sx={{
            textTransform: 'none',
            borderRadius: radii.md,
            px: 3,
            py: 1,
            fontWeight: 600,
            bgcolor: colors.primary[600],
            '&:hover': {
              bgcolor: colors.primary[700],
            }
          }}
        >
          {creating ? <Spinner size="xs" color="inherit" /> : 'Next'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Stack, Text, IconButton, Spinner, Button, Dialog, TextField } from '@/components/ui';
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

  return (
    <Dialog
      open={open}
      onClose={() => !creating && handleClose()}
      title="Create New Project"
      showCloseButton
      size="md"
      actions={
        <Stack direction="row" justify="end" gap={2} sx={{ width: '100%' }}>
          <Button
            variant="ghost"
            onClick={handleClose}
            disabled={creating}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleCreateProject}
            disabled={creating || !newProjectName.trim()}
          >
            {creating ? (
              <>
                <Spinner size="sm" sx={{ mr: 2, color: 'currentcolor' }} />
                Creating...
              </>
            ) : (
              <>
                Create Project
                <ArrowForwardIcon size="sm" style={{ marginLeft: 8 }} />
              </>
            )}
          </Button>
        </Stack>
      }
    >
      <Stack gap={3}>
        <TextField
          label="Project Name"
          autoFocus
          fullWidth
          placeholder="Enter project name"
          value={newProjectName}
          onChange={(e) => setNewProjectName(e.target.value)}
          disabled={creating}
          error={!!error}
          helperText={error || undefined}
        />

        <TextField
          label="Description"
          fullWidth
          placeholder="Briefly describe the goals and scope of this research..."
          multiline
          rows={4}
          value={newProjectDescription}
          onChange={(e) => setNewProjectDescription(e.target.value)}
          disabled={creating}
          helperText="(Optional)"
        />

        <TextField
          label="Tags"
          fullWidth
          placeholder="Add tags to organize (e.g., Marketing, Q1)"
          value={newProjectTags}
          onChange={(e) => setNewProjectTags(e.target.value)}
          disabled={creating}
          startAdornment={<TagIcon size="sm" style={{ color: colors.text.secondary }} />}
          helperText="Separate tags with commas"
        />
      </Stack>
    </Dialog>
  );
}

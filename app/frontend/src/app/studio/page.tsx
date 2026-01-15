'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import GlobalLayout from '@/components/layout/GlobalLayout';
import { Stack, Text, Button, Spinner, Surface } from '@/components/ui/primitives';
import { colors } from '@/components/ui/tokens';
import { TextField } from '@/components/ui/composites';
import { FolderOpenIcon, AddIcon, DashboardIcon, ArrowForwardIcon } from '@/components/ui/icons';
import { projectsApi, Project } from '@/lib/api';


export default function StudioIndexPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Create project form state
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        // Check if there's a last accessed project in localStorage
        const lastProjectId = localStorage.getItem('lastProjectId');
        if (lastProjectId) {
          // Optimistic redirect
          router.replace(`/studio/${lastProjectId}`);
          return;
        }

        // Otherwise, load projects and show selection
        const response = await projectsApi.list();
        setProjects(response.items);

        // If there's exactly one project, auto-open it
        if (response.items.length === 1) {
          router.replace(`/studio/${response.items[0].id}`);
          return;
        }

        setLoading(false);
      } catch (err) {
        console.error('Failed to load projects:', err);
        setError('Failed to load projects');
        setLoading(false);
      }
    };

    loadProjects();
  }, [router]);

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;

    try {
      setCreating(true);
      setCreateError(null);
      const project = await projectsApi.create(newProjectName, newProjectDescription || undefined);
      router.push(`/studio/${project.id}`);
    } catch (err: any) { // eslint-disable-line @typescript-eslint/no-explicit-any
      setCreateError(err.message || 'Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  const handleCloseDialog = () => {
    if (creating) return;
    setNewProjectName('');
    setNewProjectDescription('');
    setCreateError(null);
    setCreateDialogOpen(false);
  };

  if (loading) {
    return (
      <GlobalLayout>
        <Stack
          align="center"
          justify="center"
          sx={{
            height: '100vh',
            gap: 2,
            bgcolor: '#FAFAF9'
          }}
        >
          <Spinner size={32} color="secondary" />
          <Text variant="bodySmall" color="secondary">Loading workspace...</Text>
        </Stack>
      </GlobalLayout>
    );
  }

  if (error) {
    return (
      <GlobalLayout>
        <Stack
          align="center"
          justify="center"
          sx={{
            height: '100vh',
            gap: 2,
            bgcolor: '#FAFAFA'
          }}
        >
          <Text color="error">{error}</Text>
          <Button variant="primary" onClick={() => router.push('/dashboard')}>
            Go to Dashboard
          </Button>
        </Stack>
      </GlobalLayout>
    );
  }

  // No projects or multiple projects - show selection
  return (
    <GlobalLayout>
      <Stack
        align="center"
        justify="center"
        sx={{
          minHeight: '100vh',
          p: 4,
          bgcolor: '#F5F5F4'
        }}
      >
        <Surface
          elevation={0}
          sx={{
            p: 0,
            maxWidth: 480,
            width: '100%',
            borderRadius: 4,
            overflow: 'hidden',
            border: '1px solid',
            borderColor: 'divider',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
          }}
        >
          {/* Header */}
          <Stack sx={{ p: 4, textAlign: 'center', bgcolor: 'white' }}>
            <Stack
              align="center"
              justify="center"
              sx={{
                width: 56,
                height: 56,
                bgcolor: '#F0FDFA',
                color: 'primary.main',
                mx: 'auto',
                mb: 2,
                borderRadius: '50%'
              }}
            >
              <DashboardIcon size={28} />
            </Stack>
            <Text variant="h5" fontWeight="700" gutterBottom color="primary">
              Welcome to Studio
            </Text>
            <Text variant="bodySmall" color="secondary">
              {projects.length > 0
                ? "Select a project to continue your research"
                : "Your intelligent research workspace awaits"
              }
            </Text>
          </Stack>

          <Stack sx={{ borderBottom: 1, borderColor: 'divider' }} />

          {/* Content */}
          <Stack sx={{ p: 2, bgcolor: '#FAFAF9', minHeight: 200, justifyContent: projects.length > 0 ? 'flex-start' : 'center' }}>

            {projects.length > 0 ? (
              <Stack gap={1}>
                <Text variant="caption" fontWeight="600" color="secondary" sx={{ px: 2, mb: 1, display: 'block' }}>
                  RECENT PROJECTS
                </Text>
                {projects.map((project) => (
                  <Button
                    key={project.id}
                    variant="ghost"
                    fullWidth
                    onClick={() => {
                      localStorage.setItem('lastProjectId', project.id);
                      router.push(`/studio/${project.id}`);
                    }}
                    sx={{
                      justifyContent: 'space-between',
                      textTransform: 'none',
                      py: 1.5,
                      px: 2,
                      bgcolor: 'white',
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 2,
                      color: 'text.primary',
                      '&:hover': {
                        bgcolor: 'white',
                        borderColor: 'primary.main',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                      }
                    }}
                  >
                    <Stack direction="row" align="center" gap={1.5}>
                      <FolderOpenIcon size={18} color="primary" />
                      <Text variant="bodySmall" fontWeight="500">{project.name}</Text>
                    </Stack>
                    <ArrowForwardIcon size={16} style={{ color: colors.neutral[400] }} />
                  </Button>
                ))}
              </Stack>
            ) : (
              <Stack sx={{ textAlign: 'center', py: 4 }}>
                <Text variant="bodySmall" color="secondary" sx={{ mb: 3, maxWidth: 280, mx: 'auto' }}>
                  Create a project to start weaving documents into actionable insights.
                </Text>
              </Stack>
            )}
          </Stack>

          <Stack sx={{ borderBottom: 1, borderColor: 'divider' }} />

          {/* Footer */}
          <Stack sx={{ p: 2, bgcolor: 'white' }}>
            <Button
              variant="primary"
              fullWidth
              size="lg"
              icon={<AddIcon size="md" />}
              onClick={() => setCreateDialogOpen(true)}
              sx={{
                textTransform: 'none',
                borderRadius: 2,
                boxShadow: 'none',
                py: 1.5,
                bgcolor: '#292524',
                '&:hover': {
                  bgcolor: '#1C1917',
                  boxShadow: 'none'
                }
              }}
            >
              Create New Project
            </Button>
          </Stack>
        </Surface>

        {/* Inline Modal */}
        {createDialogOpen && (
          <Stack
            align="center"
            justify="center"
            sx={{
              position: 'fixed',
              top: 0,
              right: 0,
              bottom: 0,
              left: 72,  // Same as sidebar width to align with content area
              bgcolor: 'rgba(0, 0, 0, 0.5)',
              zIndex: 1300,
              p: 4,
            }}
            onClick={handleCloseDialog}
          >
            <Surface
              elevation={0}
              onClick={(e) => e.stopPropagation()}
              sx={{
                maxWidth: 480,
                width: '100%',
                borderRadius: 4,
                overflow: 'hidden',
                border: '1px solid',
                borderColor: 'divider',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                bgcolor: 'white',
              }}
            >
              {/* Dialog Title */}
              <Stack sx={{ px: 3, pt: 2.5, pb: 1 }}>
                <Text variant="h6" fontWeight="600">
                  Create New Project
                </Text>
              </Stack>

              {/* Dialog Content */}
              <Stack sx={{ px: 3, pb: 2 }}>
                <TextField
                  autoFocus
                  label="Project Name"
                  placeholder="e.g., Quantum Computing Research"
                  fullWidth
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  disabled={creating}
                  error={!!createError}
                  helperText={createError || undefined}
                  style={{ marginBottom: 20 }}
                  size="sm"
                />
                <TextField
                  label="Description"
                  placeholder="What is this project about?"
                  fullWidth
                  multiline
                  rows={3}
                  value={newProjectDescription}
                  onChange={(e) => setNewProjectDescription(e.target.value)}
                  disabled={creating}
                  size="sm"
                />
              </Stack>

              {/* Dialog Actions */}
              <Stack direction="row" sx={{ px: 3, pb: 2.5, pt: 1, justifyContent: 'flex-end', gap: 1 }}>
                <Button
                  onClick={handleCloseDialog}
                  disabled={creating}
                  size="sm"
                  variant="ghost"
                  sx={{
                    color: 'text.secondary',
                    textTransform: 'none',
                    borderRadius: 2,
                    px: 2,
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateProject}
                  variant="primary"
                  disabled={!newProjectName.trim() || creating}
                  size="sm"
                  sx={{
                    textTransform: 'none',
                    borderRadius: 2,
                    boxShadow: 'none',
                    px: 3,
                    py: 0.8,
                    bgcolor: '#292524',
                    '&:hover': {
                      bgcolor: '#1C1917',
                      boxShadow: 'none',
                    },
                  }}
                >
                  {creating ? <Spinner size={16} color="inherit" /> : 'Create Project'}
                </Button>
              </Stack>
            </Surface>
          </Stack>
        )}
      </Stack>
    </GlobalLayout>
  );
}

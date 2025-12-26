'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import GlobalLayout from '@/components/layout/GlobalLayout';
import { Box, Typography, Button, CircularProgress, Paper, Avatar, Divider, TextField } from '@mui/material';
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
    } catch (err: any) {
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

  if (loading) {
    return (
      <GlobalLayout>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100vh',
          flexDirection: 'column',
          gap: 2,
          bgcolor: '#FAFAFA'
        }}>
          <CircularProgress size={32} sx={{ color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">Loading workspace...</Typography>
        </Box>
      </GlobalLayout>
    );
  }

  if (error) {
    return (
      <GlobalLayout>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100vh',
          flexDirection: 'column',
          gap: 2,
          bgcolor: '#FAFAFA'
        }}>
          <Typography color="error">{error}</Typography>
          <Button variant="contained" onClick={() => router.push('/dashboard')}>
            Go to Dashboard
          </Button>
        </Box>
      </GlobalLayout>
    );
  }

  // No projects or multiple projects - show selection
  return (
    <GlobalLayout>
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        minHeight: '100vh',
        p: 4,
        bgcolor: '#F3F4F6'
      }}>
        <Paper 
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
          <Box sx={{ p: 4, textAlign: 'center', bgcolor: 'white' }}>
            <Avatar sx={{ width: 56, height: 56, bgcolor: '#EFF6FF', color: 'primary.main', mx: 'auto', mb: 2 }}>
              <DashboardIcon size={28} />
            </Avatar>
            <Typography variant="h5" fontWeight="700" gutterBottom color="text.primary">
              Welcome to Studio
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {projects.length > 0 
                ? "Select a project to continue your research"
                : "Your intelligent research workspace awaits"
              }
            </Typography>
          </Box>

          <Divider />

          {/* Content */}
          <Box sx={{ p: 2, bgcolor: '#FAFAFA', minHeight: 200, display: 'flex', flexDirection: 'column', justifyContent: projects.length > 0 ? 'flex-start' : 'center' }}>
            
            {projects.length > 0 ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Typography variant="caption" fontWeight="600" color="text.secondary" sx={{ px: 2, mb: 1, display: 'block' }}>
                  RECENT PROJECTS
                </Typography>
                {projects.map((project) => (
                  <Button
                    key={project.id}
                    variant="text"
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
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <FolderOpenIcon size={18} sx={{ color: 'primary.main' }} />
                      <Typography variant="body2" fontWeight="500">{project.name}</Typography>
                    </Box>
                    <ArrowForwardIcon size={16} sx={{ color: 'grey.400' }} />
                  </Button>
                ))}
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 280, mx: 'auto' }}>
                  Create a project to start weaving documents into actionable insights.
                </Typography>
              </Box>
            )}
          </Box>

          <Divider />

          {/* Footer */}
          <Box sx={{ p: 2, bgcolor: 'white' }}>
            <Button
              variant="contained"
              fullWidth
              size="large"
              startIcon={<AddIcon size="md" />}
              onClick={() => setCreateDialogOpen(true)}
              sx={{ 
                textTransform: 'none', 
                borderRadius: 2,
                boxShadow: 'none',
                py: 1.5,
                bgcolor: '#171717',
                '&:hover': {
                  bgcolor: '#000',
                  boxShadow: 'none'
                }
              }}
            >
              Create New Project
            </Button>
          </Box>
        </Paper>

        {/* Inline Modal - uses same layout as background card for perfect alignment */}
        {createDialogOpen && (
          <Box
            sx={{
              position: 'fixed',
              top: 0,
              right: 0,
              bottom: 0,
              left: 72,  // Same as sidebar width to align with content area
              bgcolor: 'rgba(0, 0, 0, 0.5)',
              zIndex: 1300,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 4,  // Same padding as the container
            }}
            onClick={handleCloseDialog}
          >
            <Paper
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
              <Box sx={{ px: 3, pt: 2.5, pb: 1 }}>
                <Typography variant="subtitle1" fontWeight="600">
                  Create New Project
                </Typography>
              </Box>
              
              {/* Dialog Content */}
              <Box sx={{ px: 3, pb: 2 }}>
                <TextField
                  autoFocus
                  margin="none"
                  label="Project Name"
                  placeholder="e.g., Quantum Computing Research"
                  fullWidth
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  disabled={creating}
                  error={!!createError}
                  helperText={createError}
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
              </Box>
              
              {/* Dialog Actions */}
              <Box sx={{ px: 3, pb: 2.5, pt: 1, display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                <Button
                  onClick={handleCloseDialog}
                  disabled={creating}
                  size="small"
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
                      boxShadow: 'none',
                    },
                  }}
                >
                  {creating ? <CircularProgress size={16} color="inherit" /> : 'Create Project'}
                </Button>
              </Box>
            </Paper>
          </Box>
        )}
      </Box>
    </GlobalLayout>
  );
}

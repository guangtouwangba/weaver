'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import GlobalLayout from '@/components/layout/GlobalLayout';
import { Box, Typography, Button, CircularProgress, Paper } from '@mui/material';
import { FolderOpen, Plus } from 'lucide-react';
import { projectsApi, Project } from '@/lib/api';

export default function StudioIndexPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        // Check if there's a last accessed project in localStorage
        const lastProjectId = localStorage.getItem('lastProjectId');
        if (lastProjectId) {
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

  if (loading) {
    return (
      <GlobalLayout>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100vh',
          flexDirection: 'column',
          gap: 2
        }}>
          <CircularProgress />
          <Typography color="text.secondary">Loading workspace...</Typography>
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
          gap: 2
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
        height: '100vh',
        p: 4
      }}>
        <Paper sx={{ p: 4, maxWidth: 500, width: '100%', textAlign: 'center' }}>
          <FolderOpen size={48} className="text-blue-500 mx-auto mb-4" />
          <Typography variant="h5" fontWeight="bold" gutterBottom>
            Select a Project
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            Choose a project to open in Studio, or create a new one.
          </Typography>

          {projects.length > 0 ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
              {projects.map((project) => (
                <Button
                  key={project.id}
                  variant="outlined"
                  fullWidth
                  onClick={() => {
                    localStorage.setItem('lastProjectId', project.id);
                    router.push(`/studio/${project.id}`);
                  }}
                  sx={{ 
                    justifyContent: 'flex-start', 
                    textTransform: 'none',
                    py: 1.5
                  }}
                >
                  <FolderOpen size={16} className="mr-2" />
                  {project.name}
                </Button>
              ))}
            </Box>
          ) : (
            <Typography color="text.secondary" sx={{ mb: 3 }}>
              No projects yet. Create your first project to get started.
            </Typography>
          )}

          <Button
            variant="contained"
            startIcon={<Plus size={16} />}
            onClick={() => router.push('/dashboard')}
            sx={{ textTransform: 'none' }}
          >
            Create New Project
          </Button>
        </Paper>
      </Box>
    </GlobalLayout>
  );
}

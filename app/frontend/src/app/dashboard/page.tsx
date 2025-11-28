'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import GlobalLayout from "@/components/layout/GlobalLayout";
import { 
  Box, 
  Typography, 
  Button, 
  Card,
  CardContent,
  CardActions,
  IconButton,
  CircularProgress,
  Alert
} from "@mui/material";
import { Plus, Trash2, FolderOpen } from "lucide-react";
import { projectsApi, Project } from "@/lib/api";
import CreateProjectDialog from '@/components/dialogs/CreateProjectDialog';

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await projectsApi.list();
      setProjects(response.items);
    } catch (err: any) {
      setError(err.message || 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = async (projectId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this project?')) return;
    
    try {
      await projectsApi.delete(projectId);
      setProjects(projects.filter(p => p.id !== projectId));
    } catch (err: any) {
      setError(err.message || 'Failed to delete project');
    }
  };

  const handleOpenProject = (projectId: string) => {
    router.push(`/studio/${projectId}`);
  };

  const handleProjectCreated = (project: Project) => {
    setProjects([...projects, project]);
    // Option: navigate to studio directly, or just update list
    // router.push(`/studio/${project.id}`); 
    // For dashboard, maybe just update list is better, but user expects to work on it
    router.push(`/studio/${project.id}`);
  };

  return (
    <GlobalLayout>
      <Box sx={{ p: 4, maxWidth: 1200, mx: 'auto' }}>
        {/* Header */}
        <Box sx={{ mb: 6 }}>
          <Typography variant="h4" fontWeight="600" gutterBottom>
            Projects
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your research projects and knowledge bases
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Create Project Zone */}
        <Box 
          sx={{ 
            border: '2px dashed', 
            borderColor: 'divider', 
            borderRadius: 4, 
            p: 6, 
            textAlign: 'center',
            mb: 6,
            bgcolor: 'background.default'
          }}
        >
          <FolderOpen size={48} className="mx-auto mb-4 text-gray-400" />
          <Typography variant="h6" gutterBottom>
            Create New Knowledge Project
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Start a new research project to organize your documents and insights
          </Typography>
          <Button 
            variant="contained" 
            startIcon={<Plus />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Project
          </Button>
        </Box>

        {/* Projects List */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" fontWeight="600">
            Your Projects ({projects.length})
          </Typography>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : projects.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="body1" color="text.secondary">
              No projects yet. Create your first project to get started!
            </Typography>
          </Box>
        ) : (
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 3 }}>
            {projects.map((project) => (
              <Card 
                key={project.id}
                sx={{ 
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': { 
                    boxShadow: 4,
                    borderColor: 'primary.main'
                  }
                }}
                onClick={() => handleOpenProject(project.id)}
              >
                <CardContent>
                  <Typography variant="h6" fontWeight="600" gutterBottom>
                    {project.name}
                  </Typography>
                  {project.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {project.description}
                    </Typography>
                  )}
                  <Typography variant="caption" color="text.disabled">
                    Updated {new Date(project.updated_at).toLocaleDateString()}
                  </Typography>
                </CardContent>
                <CardActions sx={{ justifyContent: 'flex-end', px: 2, pb: 2 }}>
                  <IconButton 
                    size="small" 
                    onClick={(e) => handleDeleteProject(project.id, e)}
                    sx={{ color: 'error.main' }}
                  >
                    <Trash2 size={16} />
                  </IconButton>
                </CardActions>
              </Card>
            ))}
          </Box>
        )}

        <CreateProjectDialog 
          open={createDialogOpen} 
          onClose={() => setCreateDialogOpen(false)}
          onProjectCreated={handleProjectCreated}
        />
      </Box>
    </GlobalLayout>
  );
}

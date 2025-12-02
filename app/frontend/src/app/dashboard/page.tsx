'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import GlobalLayout from "@/components/layout/GlobalLayout";
import { 
  Box, 
  Typography, 
  Button, 
  Paper,
  IconButton,
  CircularProgress,
  Alert,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar
} from "@mui/material";
import { Plus, Trash2, FolderOpen, MoreVertical, Pencil } from "lucide-react";
import { projectsApi, Project } from "@/lib/api";
import CreateProjectDialog from '@/components/dialogs/CreateProjectDialog';

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Menu state
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [menuProject, setMenuProject] = useState<Project | null>(null);

  // Delete dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Snackbar state
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  const menuOpen = Boolean(menuAnchorEl);

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

  const handleOpenProject = (projectId: string) => {
    router.push(`/studio/${projectId}`);
  };

  const handleProjectCreated = (project: Project) => {
    setProjects((prev) => [...prev, project]);
    router.push(`/studio/${project.id}`);
  };

  const handleOpenMenu = (event: React.MouseEvent<HTMLElement>, project: Project) => {
    event.stopPropagation();
    setMenuAnchorEl(event.currentTarget);
    setMenuProject(project);
  };

  const handleCloseMenu = () => {
    setMenuAnchorEl(null);
    setMenuProject(null);
  };

  const handleOpenDeleteDialog = () => {
    if (!menuProject) return;
    setProjectToDelete(menuProject);
    setDeleteDialogOpen(true);
    handleCloseMenu();
  };

  const handleCloseDeleteDialog = () => {
    if (deleting) return;
    setDeleteDialogOpen(false);
    setProjectToDelete(null);
  };

  const handleConfirmDelete = async () => {
    if (!projectToDelete) return;
    setDeleting(true);
    try {
      await projectsApi.delete(projectToDelete.id);
      setProjects((prev) => prev.filter((p) => p.id !== projectToDelete.id));
      setSnackbarMessage(`Project "${projectToDelete.name}" deleted`);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
      setDeleteDialogOpen(false);
      setProjectToDelete(null);
    } catch (err: any) {
      setSnackbarMessage(err.message || 'Failed to delete project');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setDeleting(false);
    }
  };

  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  return (
    <GlobalLayout>
      <Box sx={{ p: 4, maxWidth: 1200, mx: 'auto' }}>
        {/* Header */}
        <Box sx={{ mb: 6, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" fontWeight="600" gutterBottom>
              Projects
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Manage your research projects and knowledge bases
            </Typography>
          </Box>
          <Button 
            variant="contained" 
            startIcon={<Plus />}
            onClick={() => setCreateDialogOpen(true)}
            sx={{ textTransform: 'none', borderRadius: 2 }}
          >
            New Project
          </Button>
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
            sx={{ textTransform: 'none', borderRadius: 2 }}
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
              <Paper 
                key={project.id}
                elevation={0}
                sx={{ 
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 3,
                  overflow: 'hidden',
                  transition: 'all 0.2s',
                  cursor: 'pointer',
                  '&:hover': { 
                    transform: 'translateY(-4px)',
                    boxShadow: '0 12px 24px rgba(0,0,0,0.05)',
                    borderColor: 'primary.main'
                  }
                }}
                onClick={() => handleOpenProject(project.id)}
              >
                {/* Content Area */}
                <Box sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography 
                      variant="h6" 
                      fontWeight="bold" 
                      color="text.primary" 
                      sx={{ lineHeight: 1.3, flex: 1, pr: 1 }}
                    >
                      {project.name}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={(e) => handleOpenMenu(e, project)}
                      sx={{ 
                        mt: -0.5, 
                        mr: -1,
                        color: 'text.secondary',
                        '&:hover': { 
                          color: 'text.primary',
                          bgcolor: 'action.hover'
                        }
                      }}
                    >
                      <MoreVertical size={16} />
                    </IconButton>
                  </Box>
                  
                  {project.description && (
                    <Typography 
                      variant="body2" 
                      color="text.secondary" 
                      sx={{ 
                        mb: 3,
                        height: 40,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                      }}
                    >
                      {project.description}
                    </Typography>
                  )}

                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="caption" color="text.secondary">
                      Updated {new Date(project.updated_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            ))}
          </Box>
        )}

        <CreateProjectDialog 
          open={createDialogOpen} 
          onClose={() => setCreateDialogOpen(false)}
          onProjectCreated={handleProjectCreated}
        />

        {/* Card menu */}
        <Menu
          anchorEl={menuAnchorEl}
          open={menuOpen}
          onClose={handleCloseMenu}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        >
          <MenuItem disabled sx={{ color: 'text.disabled' }}>
            <ListItemIcon sx={{ color: 'inherit', minWidth: 32 }}>
              <Pencil size={16} />
            </ListItemIcon>
            <ListItemText primary="Edit" />
          </MenuItem>
          <MenuItem
            onClick={handleOpenDeleteDialog}
            sx={{ color: 'error.main' }}
          >
            <ListItemIcon sx={{ color: 'inherit', minWidth: 32 }}>
              <Trash2 size={16} />
            </ListItemIcon>
            <ListItemText primary="Delete" />
          </MenuItem>
        </Menu>

        {/* Delete confirmation dialog */}
        <Dialog
          open={deleteDialogOpen}
          onClose={handleCloseDeleteDialog}
          maxWidth="xs"
          fullWidth
        >
          <DialogTitle>Delete Project</DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="text.secondary">
              Are you sure you want to delete "
              <strong>{projectToDelete?.name}</strong>
              "? This action cannot be undone.
            </Typography>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2.5 }}>
            <Button
              onClick={handleCloseDeleteDialog}
              disabled={deleting}
              sx={{ textTransform: 'none', color: 'text.secondary' }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleConfirmDelete}
              disabled={deleting}
              color="error"
              variant="contained"
              sx={{ textTransform: 'none' }}
            >
              {deleting && <CircularProgress size={16} sx={{ mr: 1 }} />}
              Delete
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar for delete feedback */}
        <Snackbar
          open={snackbarOpen}
          autoHideDuration={4000}
          onClose={handleSnackbarClose}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert
            onClose={handleSnackbarClose}
            severity={snackbarSeverity}
            sx={{ width: '100%' }}
          >
            {snackbarMessage}
          </Alert>
        </Snackbar>
      </Box>
    </GlobalLayout>
  );
}

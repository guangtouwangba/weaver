'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import GlobalLayout from "@/components/layout/GlobalLayout";
import { 
  Box, 
  Typography, 
  Button, 
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
  Snackbar,
  Stack
} from "@mui/material";
import { 
  DeleteIcon, 
  EditIcon, 
  GridViewIcon, 
  ViewListIcon,
  AddIcon,
  UploadFileIcon,
} from '@/components/ui/icons';
import { projectsApi, Project } from "@/lib/api";
import CreateProjectDialog from '@/components/dialogs/CreateProjectDialog';
import ProjectCard from '@/components/dashboard/ProjectCard';

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  
  // Tab state (visual only for now)
  const [activeTab, setActiveTab] = useState('Recent Projects');

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
      // Sort by updated_at desc
      const sortedProjects = response.items.sort((a, b) => 
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      );
      setProjects(sortedProjects);
    } catch (err: any) {
      setError(err.message || 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleProjectCreated = (project: Project) => {
    // Add new project to top
    setProjects((prev) => [project, ...prev]);
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


  // Derived state
  const recentProjects = projects.slice(0, 4);

  return (
    <GlobalLayout>
      <Box sx={{ p: 4, maxWidth: 1200, mx: 'auto' }}>
        
        {/* Header Section */}
        <Box sx={{ mb: 6, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" fontWeight="bold" gutterBottom>
              Welcome back, Alex 👋
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Pick up where you left off or start a new analysis.
            </Typography>
          </Box>
          <Stack direction="row" spacing={2}>
             <Button 
              variant="outlined" 
              startIcon={<UploadFileIcon size="md" />}
              sx={{ textTransform: 'none', borderRadius: 2, bgcolor: 'background.paper', borderColor: 'divider', color: 'text.primary' }}
            >
              Import
            </Button>
            <Button 
              variant="contained" 
              startIcon={<AddIcon size="md" />}
              onClick={() => setCreateDialogOpen(true)}
              sx={{ textTransform: 'none', borderRadius: 2, bgcolor: '#4f46e5', '&:hover': { bgcolor: '#4338ca' } }}
            >
              Create New Project
            </Button>
          </Stack>
        </Box>


        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Recent Projects Section */}
            <Box sx={{ mb: 6 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="h6" fontWeight="bold" sx={{ lineHeight: 1 }}>
                      Recent Projects
                    </Typography>
                    <Box sx={{ width: '1px', height: 20, bgcolor: 'divider', mx: 1 }} />
                    <Stack direction="row" spacing={0.5}>
                      {['All Projects', 'Starred', 'Shared with me'].map((tab) => {
                        const isSelected = activeTab === tab || (activeTab === 'Recent Projects' && tab === 'All Projects');
                        return (
                          <Box 
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            sx={{ 
                              px: 2,
                              py: 0.5,
                              borderRadius: 2,
                              cursor: 'pointer',
                              bgcolor: isSelected ? '#eff6ff' : 'transparent',
                              color: isSelected ? '#4f46e5' : 'text.secondary',
                              fontWeight: isSelected ? 600 : 500,
                              transition: 'all 0.2s',
                              fontSize: '0.95rem',
                              '&:hover': { 
                                bgcolor: isSelected ? '#eff6ff' : 'rgba(0,0,0,0.04)',
                                color: isSelected ? '#4f46e5' : 'text.primary'
                              }
                            }}
                          >
                            {tab}
                          </Box>
                        );
                      })}
                    </Stack>
                  </Box>
                  
                  <Stack direction="row" spacing={2} alignItems="center" sx={{ color: 'text.secondary' }}>
                    <GridViewIcon size="md" sx={{ cursor: 'pointer' }} />
                    <ViewListIcon size="md" sx={{ cursor: 'pointer' }} />
                    <Typography variant="body2" sx={{ cursor: 'pointer', fontWeight: 500 }}>Last Modified</Typography>
                  </Stack>
              </Box>
              
              {projects.length > 0 ? (
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 3 }}>
                  {(activeTab === 'Recent Projects' ? recentProjects : projects).map((project) => (
                    <ProjectCard 
                      key={project.id} 
                      project={project} 
                      onOpenMenu={handleOpenMenu}
                    />
                  ))}
                </Box>
              ) : (
                <Box sx={{ py: 8, textAlign: 'center', bgcolor: 'background.paper', borderRadius: 3, border: '1px dashed', borderColor: 'divider' }}>
                   <Typography color="text.secondary">No projects yet. Create one to get started.</Typography>
                </Box>
              )}
            </Box>

          </>
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
              <EditIcon size="sm" />
            </ListItemIcon>
            <ListItemText primary="Edit" />
          </MenuItem>
          <MenuItem
            onClick={handleOpenDeleteDialog}
            sx={{ color: 'error.main' }}
          >
            <ListItemIcon sx={{ color: 'inherit', minWidth: 32 }}>
              <DeleteIcon size="sm" />
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

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import GlobalLayout from "@/components/layout/GlobalLayout";
import {
  Text,
  Button,
  Surface,
  Spinner,
  Stack,
  Dialog,
  Menu,
  MenuItem
} from "@/components/ui";
import {
  DeleteIcon,
  EditIcon,
  GridViewIcon,
  ViewListIcon,
  AddIcon,
  UploadFileIcon,
  CloseIcon,
  CheckIcon,
  ExpandMoreIcon,
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
  const [activeTab, setActiveTab] = useState('All Projects');

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
      <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>

        {/* Header Section */}
        <div style={{ marginBottom: 48, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div>
            <Text variant="h4" style={{ fontWeight: 'bold', marginBottom: 8 }}>
              Projects
            </Text>
            <Text variant="body" style={{ color: '#6B7280' }}>
              Pick up where you left off or start a new analysis.
            </Text>
          </div>
          <Stack direction="row" gap={16}>
            {/* Import Button */}
            <Button
              variant="outline"
              onClick={() => { }} // Placeholder
              style={{ backgroundColor: '#fff' }}
            >
              <UploadFileIcon size={20} style={{ marginRight: 8 }} />
              Import
            </Button>
            <Button
              variant="primary"
              onClick={() => setCreateDialogOpen(true)}
            >
              <AddIcon size={20} style={{ marginRight: 8 }} />
              Create New Project
            </Button>
          </Stack>
        </div>


        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 64 }}>
            <Spinner size="lg" />
          </div>
        ) : (
          <>
            {/* Filters & Content Section */}
            <div style={{ marginBottom: 48 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <Stack direction="row" gap={4}>
                    {['Recent', 'All Projects', 'Starred'].map((tab) => {
                      const isSelected = activeTab === tab;
                      return (
                        <div
                          key={tab}
                          onClick={() => setActiveTab(tab)}
                          style={{
                            padding: '8px 16px',
                            cursor: 'pointer',
                            backgroundColor: 'transparent',
                            borderBottom: isSelected ? '2px solid #0D9488' : '2px solid transparent', // Teal-600 to match text
                            color: isSelected ? '#0D9488' : '#6B7280', // Teal-600
                            fontWeight: isSelected ? 600 : 500,
                            transition: 'all 0.2s',
                            fontSize: '0.95rem',
                            marginBottom: '-2px',
                          }}
                          onMouseEnter={(e) => { if (!isSelected) { e.currentTarget.style.color = '#111827'; } }}
                          onMouseLeave={(e) => { if (!isSelected) { e.currentTarget.style.color = '#6B7280'; } }}
                        >
                          {tab}
                        </div>
                      );
                    })}
                  </Stack>
                </div>

                <Stack direction="row" gap={16} align="center" style={{ color: '#6B7280' }}>
                  <div style={{ cursor: 'pointer' }}><GridViewIcon size={20} /></div>
                  <div style={{ cursor: 'pointer' }}><ViewListIcon size={20} /></div>
                  <Text variant="bodySmall" style={{ cursor: 'pointer', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 4 }}>
                    Last Modified
                    <ExpandMoreIcon size={16} />
                  </Text>
                </Stack>
              </div>

              {(() => {
                const filteredProjects = projects.filter(p => {
                  if (activeTab === 'Recent') {
                    const sevenDaysAgo = new Date();
                    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
                    return new Date(p.updated_at) > sevenDaysAgo;
                  }
                  if (activeTab === 'Starred') {
                    return false;
                  }
                  return true;
                });

                if (projects.length === 0) {
                  return (
                    <div style={{ padding: 64, textAlign: 'center', backgroundColor: '#fff', borderRadius: 12, border: '1px dashed #E7E5E4' }}>
                      <Text style={{ color: '#6B7280' }}>No projects yet. Create one to get started.</Text>
                    </div>
                  );
                }

                if (filteredProjects.length === 0) {
                  return (
                    <div style={{ padding: 64, textAlign: 'center', backgroundColor: '#fff', borderRadius: 12, border: '1px dashed #E7E5E4' }}>
                      <Text style={{ color: '#6B7280' }}>
                        {activeTab === 'Recent' ? 'No projects modified in the last 7 days.' : 'No projects found.'}
                      </Text>
                    </div>
                  );
                }

                return (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 24 }}>
                    {filteredProjects.map((project) => (
                      <ProjectCard
                        key={project.id}
                        project={project}
                        onOpenMenu={handleOpenMenu}
                      />
                    ))}
                  </div>
                );
              })()}
            </div>

          </>
        )}

        <CreateProjectDialog
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          onProjectCreated={handleProjectCreated}
        />

        {/* Card menu */}
        {/* Card menu */}
        <Menu
          open={menuOpen}
          onClose={handleCloseMenu}
          anchorPosition={menuAnchorEl ? { top: menuAnchorEl.getBoundingClientRect().bottom + window.scrollY, left: menuAnchorEl.getBoundingClientRect().right - 160 + window.scrollX } : undefined}
          anchorReference="anchorPosition"
        >
          <MenuItem disabled style={{ color: '#9CA3AF' }}>
            <div style={{ color: 'inherit', minWidth: 32, display: 'flex' }}>
              <EditIcon size={16} />
            </div>
            <Text>Edit</Text>
          </MenuItem>
          <MenuItem
            onClick={handleOpenDeleteDialog}
            style={{ color: '#EF4444' }}
          >
            <div style={{ color: 'inherit', minWidth: 32, display: 'flex' }}>
              <DeleteIcon size={16} />
            </div>
            <Text>Delete</Text>
          </MenuItem>
        </Menu>

        {/* Delete confirmation dialog */}
        <Dialog
          open={deleteDialogOpen}
          onClose={handleCloseDeleteDialog}
          title="Delete Project"
          size="sm"
          actions={
            <>
              <Button
                variant="ghost"
                onClick={handleCloseDeleteDialog}
                disabled={deleting}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={handleConfirmDelete}
                loading={deleting}
              >
                Delete
              </Button>
            </>
          }
        >
          <div style={{ padding: 24 }}>
            <Text variant="body" style={{ color: '#6B7280' }}>
              Are you sure you want to delete "
              <strong>{projectToDelete?.name}</strong>
              "? This action cannot be undone.
            </Text>
          </div>
        </Dialog>

        {/* Snackbar replacement (Toast) */}
        {snackbarOpen && (
          <div style={{
            position: 'fixed',
            bottom: 24,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 2000,
            minWidth: 300
          }}>
            <Surface
              elevation={3}
              radius="lg"
              style={{
                padding: '12px 16px',
                backgroundColor: snackbarSeverity === 'success' ? '#10B981' : '#EF4444',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
              }}
            >
              <Text variant="bodySmall" style={{ color: 'white', fontWeight: 500 }}>
                {snackbarMessage}
              </Text>
              <div onClick={handleSnackbarClose} style={{ cursor: 'pointer', marginLeft: 16, display: 'flex', alignItems: 'center' }}>
                <CloseIcon size={16} style={{ color: 'white' }} />
              </div>
            </Surface>
          </div>
        )}

      </div>
    </GlobalLayout>
  );
}

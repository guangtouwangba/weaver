'use client';

import { useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Button,
  Avatar,
  Tooltip
} from "@mui/material";
import {
  ShareIcon,
  SearchIcon,
  ChevronLeftIcon,
  ExpandMoreIcon
} from '@/components/ui/icons';
import NotificationsMui from '@mui/icons-material/Notifications';
import GlobalLayout from "@/components/layout/GlobalLayout";
import { useStudio, StudioProvider } from "@/contexts/StudioContext";
import ResourceSidebar from "@/components/studio/ResourceSidebar";
import KonvaCanvas from "@/components/studio/KonvaCanvas";
import CanvasControls from "@/components/studio/CanvasControls";
import ImportSourceDialog from "@/components/dialogs/ImportSourceDialog";
import { documentsApi } from "@/lib/api";

export default function StudioPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  // Show loading or error state if projectId is not available
  if (!projectId) {
    return (
      <GlobalLayout>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
          <Typography>Loading project...</Typography>
        </Box>
      </GlobalLayout>
    );
  }

  return (
    <StudioProvider projectId={projectId}>
      <StudioPageContent />
    </StudioProvider>
  );
}

function StudioPageContent() {
  const {
    project,
    messages,
    canvasNodes,
    setCanvasNodes,
    canvasEdges,
    setCanvasEdges,
    canvasViewport,
    setCanvasViewport,
    projectId,
    documents,
    setDocuments,
    addNodeToCanvas
  } = useStudio();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [interactionMode, setInteractionMode] = useState<'select' | 'pan'>('select');
  const [selectedNodeIds, setSelectedNodeIds] = useState<Set<string>>(new Set());

  // Import Dialog State
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);

  // Placeholder handlers for canvas controls
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.1, 2));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.1, 0.1));
  const handleFitView = () => setZoom(1);

  // Delete handler for selected nodes
  const handleDelete = () => {
    if (selectedNodeIds.size === 0) return;
    setCanvasNodes(canvasNodes.filter(node => !selectedNodeIds.has(node.id)));
    setSelectedNodeIds(new Set());
  };

  // Handle File Upload from Dialog
  const handleFileSelect = async (file: File) => {
    try {
      const newDoc = await documentsApi.upload(projectId, file);
      setDocuments([newDoc, ...documents]);
    } catch (error) {
      console.error('Upload failed:', error);
      // You might want to show a toast/notification here
    }
  };

  // Handle URL Import from Dialog
  const handleUrlImport = async (url: string) => {
    // Placeholder for URL import logic
    console.log('Importing URL:', url);
  };

  return (
    <GlobalLayout>
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>

        {/* Left: Resource Sidebar */}
        <ResourceSidebar
          width={300}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Main: Canvas Workspace */}
        <Box sx={{ flexGrow: 1, position: 'relative', display: 'flex', flexDirection: 'column', bgcolor: '#F9FAFB' }}>

          {/* Minimalist Header */}
          <Paper
            elevation={0}
            sx={{
              height: 56,
              px: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid',
              borderColor: 'divider',
              borderRadius: 0,
              zIndex: 10
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Tooltip title="Back to Dashboard">
                <IconButton size="small" href="/dashboard">
                  <ChevronLeftIcon size="md" />
                </IconButton>
              </Tooltip>
              {project && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Typography variant="subtitle2" fontWeight="600">
                    {project.name}
                  </Typography>
                  <ExpandMoreIcon size="sm" sx={{ color: 'grey.400' }} />
                </Box>
              )}
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <IconButton size="small">
                <SearchIcon size={18} />
              </IconButton>
              <IconButton size="small">
                <NotificationsMui sx={{ fontSize: 18 }} />
              </IconButton>
              <Button
                variant="outlined"
                size="small"
                startIcon={<ShareIcon size="sm" />}
                sx={{ textTransform: 'none', borderRadius: 2 }}
              >
                Share
              </Button>
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main', fontSize: 14 }}>AL</Avatar>
            </Box>
          </Paper>

          {/* Whiteboard Area */}
          <Box sx={{ flexGrow: 1, position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <KonvaCanvas
              nodes={canvasNodes}
              edges={canvasEdges}
              viewport={canvasViewport}
              onNodesChange={setCanvasNodes}
              onEdgesChange={setCanvasEdges}
              onViewportChange={setCanvasViewport}
              onNodeAdd={addNodeToCanvas}
              onOpenImport={() => setIsImportDialogOpen(true)}
              toolMode={interactionMode === 'pan' ? 'hand' : 'select'}
              onToolChange={(tool) => setInteractionMode(tool === 'hand' ? 'pan' : 'select')}
            />


            {/* Canvas Controls (Bottom Right) */}
            <CanvasControls
              zoom={zoom}
              onZoomIn={handleZoomIn}
              onZoomOut={handleZoomOut}
              onFitView={handleFitView}
              interactionMode={interactionMode}
              onModeChange={setInteractionMode}
              onDelete={handleDelete}
              hasSelection={selectedNodeIds.size > 0}
            />
          </Box>
        </Box>
      </Box>

      {/* Import Dialog */}
      <ImportSourceDialog
        open={isImportDialogOpen}
        onClose={() => setIsImportDialogOpen(false)}
        onFileSelect={handleFileSelect}
        onUrlImport={handleUrlImport}
      />
    </GlobalLayout>
  );
}

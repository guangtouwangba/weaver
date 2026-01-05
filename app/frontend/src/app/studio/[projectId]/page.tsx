'use client';

import { useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import {
  Box,
  Typography,
} from "@mui/material";
import GlobalLayout from "@/components/layout/GlobalLayout";
import { useStudio, StudioProvider } from "@/contexts/StudioContext";
import ResourceSidebar from "@/components/studio/ResourceSidebar";
import AssistantPanel from "@/components/studio/AssistantPanel";
import KonvaCanvas from "@/components/studio/KonvaCanvas";
import CanvasControls from "@/components/studio/CanvasControls";
import ImportSourceDialog from "@/components/dialogs/ImportSourceDialog";
import PDFPreviewModal from "@/components/pdf/PDFPreviewModal";
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
    canvasNodes,
    setCanvasNodes,
    canvasEdges,
    setCanvasEdges,
    canvasViewport,
    setCanvasViewport,
    projectId,
    projectTitle,
    documents,
    setDocuments,
    addNodeToCanvas,
    openDocumentPreview,
    navigateToSource,
  } = useStudio();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
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

          {/* Whiteboard Area */}

          {/* Whiteboard Area */}
          <Box sx={{ flexGrow: 1, position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <KonvaCanvas
              nodes={canvasNodes}
              edges={canvasEdges}
              viewport={canvasViewport}
              onNodesChange={setCanvasNodes}
              onEdgesChange={setCanvasEdges}
              onViewportChange={setCanvasViewport}
              onNodeAdd={(node) => addNodeToCanvas(node as any)}
              onOpenImport={() => setIsImportDialogOpen(true)}
              toolMode={interactionMode === 'pan' ? 'hand' : 'select'}
              onToolChange={(tool) => setInteractionMode(tool === 'hand' ? 'pan' : 'select')}
              onOpenSource={(id, page) => {
                if (page) navigateToSource(id, page);
                openDocumentPreview(id);
              }}
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

            {/* Right: Assistant Panel (Overlay) */}
            <AssistantPanel
              visible={isChatOpen}
              width={400}
              onToggle={() => setIsChatOpen(!isChatOpen)}
            />
          </Box>
        </Box>
      </Box >

      {/* Import Dialog */}
      < ImportSourceDialog
        open={isImportDialogOpen}
        onClose={() => setIsImportDialogOpen(false)
        }
        onFileSelect={handleFileSelect}
        onUrlImport={handleUrlImport}
      />

      <PDFPreviewModal />
    </GlobalLayout >
  );
}

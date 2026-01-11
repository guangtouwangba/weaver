'use client';

import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "next/navigation";
import {
  Text,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { AnonymousLimitPrompt } from "@/components/AnonymousLimitPrompt";
import GlobalLayout from "@/components/layout/GlobalLayout";
import { useStudio, StudioProvider } from "@/contexts/StudioContext";
import { useNotification } from "@/contexts/NotificationContext";
import ResourceSidebar from "@/components/studio/ResourceSidebar";
import AssistantPanel from "@/components/studio/AssistantPanel";
import KonvaCanvas from "@/components/studio/KonvaCanvas";
import CanvasControls from "@/components/studio/CanvasControls";
import ImportSourceDialog from "@/components/dialogs/ImportSourceDialog";
import PDFPreviewModal from "@/components/pdf/PDFPreviewModal";
import { documentsApi, canvasApi, urlApi } from "@/lib/api";
import { detectPlatform, type Platform } from '@/lib/platform-icons';

export default function StudioPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  // Show loading or error state if projectId is not available
  if (!projectId) {
    return (
      <GlobalLayout>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
          <Text>Loading project...</Text>
        </div>
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
    viewStates,
    projectId,
    projectTitle,
    documents,
    setDocuments,
    addUrlContent,
    addNodeToCanvas,
    openDocumentPreview,
    navigateToSource,
  } = useStudio();
  const toast = useNotification();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [interactionMode, setInteractionMode] = useState<'select' | 'pan' | 'connect' | 'logic_connect' | 'magic'>('select');
  const [selectedNodeIds, setSelectedNodeIds] = useState<Set<string>>(new Set());

  // Import Dialog State
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);

  // Auto-save canvas changes (debounced)
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (canvasNodes.length > 0 || canvasEdges.length > 0) {
        canvasApi.save(projectId, {
          nodes: canvasNodes,
          edges: canvasEdges,
          sections: [],
          viewport: canvasViewport,
          viewStates: viewStates,
        }).then(() => {
          console.log('[Canvas] Auto-saved successfully');
        }).catch(err => console.error('[Canvas] Auto-save failed:', err));
      }
    }, 2000); // Debounce 2 seconds
    return () => clearTimeout(timeout);
  }, [canvasNodes, canvasEdges, canvasViewport, viewStates, projectId]);

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

  const { isAnonymous } = useAuth();
  const [limitPromptOpen, setLimitPromptOpen] = useState(false);

  // Handle File Upload from Dialog
  const handleFileSelect = async (file: File) => {
    if (isAnonymous && documents.length >= 2) {
      setIsImportDialogOpen(false);
      setLimitPromptOpen(true);
      return;
    }

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
    if (isAnonymous && documents.length >= 2) {
      setIsImportDialogOpen(false);
      setLimitPromptOpen(true);
      return;
    }

    const toastId = toast.loading("Extracting content...", "Please wait while we process the URL");
    try {
      console.log('Importing URL:', url);
      // Start extraction
      const pendingContent = await urlApi.extract(url);
      console.log('URL extraction started:', pendingContent.id);

      // Poll for completion
      const completedContent = await urlApi.waitForCompletion(pendingContent.id, {
        maxAttempts: 120,
        intervalMs: 1000,
      });
      console.log('URL extraction completed:', completedContent);

      // Add to documents list (urlContents in StudioContext)
      addUrlContent(completedContent);

      toast.updateNotification(toastId, {
        type: 'success',
        title: 'Import Successful',
        message: `Successfully imported "${completedContent.title || 'URL content'}"`,
      });
    } catch (error) {
      console.error('URL extraction failed:', error);
      toast.updateNotification(toastId, {
        type: 'error',
        title: 'Import Failed',
        message: error instanceof Error ? error.message : 'Failed to extract content from URL',
      });
    }
  };

  return (
    <GlobalLayout>
      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>

        {/* Left: Resource Sidebar */}
        <ResourceSidebar
          width={300}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Main: Canvas Workspace */}
        <div style={{ flexGrow: 1, position: 'relative', display: 'flex', flexDirection: 'column', backgroundColor: '#F9FAFB' }}>

          {/* Whiteboard Area */}
          <div style={{ flexGrow: 1, position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <KonvaCanvas
              nodes={canvasNodes}
              edges={canvasEdges}
              viewport={canvasViewport}
              onNodesChange={setCanvasNodes}
              onEdgesChange={setCanvasEdges}
              onViewportChange={setCanvasViewport}
              onNodeAdd={(node) => addNodeToCanvas(node as any)}
              onOpenImport={() => setIsImportDialogOpen(true)}
              toolMode={interactionMode === 'pan' ? 'hand' : interactionMode}
              onToolChange={(tool) => {
                if (tool === 'hand') setInteractionMode('pan');
                else setInteractionMode(tool as 'select' | 'connect' | 'logic_connect');
              }}
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
          </div>
        </div>
      </div>

      {/* Import Dialog */}
      <ImportSourceDialog
        open={isImportDialogOpen}
        onClose={() => setIsImportDialogOpen(false)}
        onFileSelect={handleFileSelect}
        onUrlImport={handleUrlImport}
      />

      <AnonymousLimitPrompt
        isOpen={limitPromptOpen}
        onClose={() => setLimitPromptOpen(false)}
        limitType="files"
      />

      <PDFPreviewModal />
    </GlobalLayout>
  );
}

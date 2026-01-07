'use client';

import { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { Surface, Text, IconButton, Button, Tooltip, Collapse, Chip, Progress, Modal, Stack } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import {
  DescriptionIcon,
  FullscreenIcon,
  FullscreenExitIcon,
  FolderOpenIcon,
  ExpandMoreIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  MenuOpenIcon,
  GridViewIcon,
  ViewListIcon,
  CloudUploadIcon,
  CheckIcon,
  ErrorIcon,
  DeleteIcon,
  AccountTreeIcon,
  ShareIcon,
  LinkIcon,
  GlobeIcon,
} from '@/components/ui/icons';
import { useStudio } from '@/contexts/StudioContext';
import { documentsApi, ProjectDocument, urlApi, UrlContent } from '@/lib/api';
import { PlatformIcon, detectPlatform, type Platform } from '@/lib/platform-icons';
import { useDocumentWebSocket } from '@/hooks/useDocumentWebSocket';
import ImportSourceDialog from '@/components/dialogs/ImportSourceDialog';
import ImportSourceDropzone from '@/components/studio/ImportSourceDropzone';

// Dynamically import PDFViewer with SSR disabled to avoid "document is not defined" error
// from pdfjs-dist/web/pdf_viewer which accesses document at module evaluation time
const PDFViewer = dynamic(
  () => import('@/components/pdf/PDFViewer').then(mod => mod.PDFViewer),
  { ssr: false }
);

// Import createDragHandler separately since it doesn't access document at module level
import { createDragHandler } from '@/components/pdf/DragHandler';

interface SourcePanelProps {
  visible: boolean;
  width: number;
  onToggle: () => void;
}

// Upload state type
type UploadState = 'idle' | 'uploading' | 'processing' | 'success' | 'error';

// URL extraction state
interface PendingUrlExtraction {
  id: string;
  url: string;
  platform: Platform;
  status: 'extracting' | 'completed' | 'failed';
  title?: string;
  thumbnailUrl?: string;
  errorMessage?: string;
  content?: UrlContent;
}

export default function SourcePanel({ visible, width, onToggle }: SourcePanelProps) {
  const { projectId, documents, setDocuments, activeDocumentId, setActiveDocumentId, sourceNavigation } = useStudio();
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('grid');
  const [isReaderExpanded, setIsReaderExpanded] = useState(false);
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [filesExpanded, setFilesExpanded] = useState(true);

  // Upload state
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadFileName, setUploadFileName] = useState<string | null>(null);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Delete state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [docToDelete, setDocToDelete] = useState<ProjectDocument | null>(null);
  const [deleting, setDeleting] = useState(false);

  // URL extraction state
  const [pendingUrlExtractions, setPendingUrlExtractions] = useState<PendingUrlExtraction[]>([]);

  // Vertical Resize State
  const [splitRatio, setSplitRatio] = useState(0.4);
  const [isVerticalDragging, setIsVerticalDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const activeDocument = documents.find(d => d.id === activeDocumentId);

  useEffect(() => {
    if (activeDocumentId) {
      setFileUrl(documentsApi.getFileUrl(activeDocumentId));
      setPageNumber(1);
    } else {
      setFileUrl(null);
    }
  }, [activeDocumentId]);

  // Handle source navigation (jump to page when source is clicked)
  useEffect(() => {
    if (sourceNavigation && sourceNavigation.documentId === activeDocumentId) {
      setPageNumber(sourceNavigation.pageNumber);
    }
  }, [sourceNavigation, activeDocumentId]);

  // WebSocket for real-time document status updates (replaces polling)
  useDocumentWebSocket({
    projectId,
    enabled: documents.some(d =>
      d.status === 'pending' ||
      d.status === 'processing' ||
      d.graph_status === 'pending' ||
      d.graph_status === 'processing'
    ),
    onDocumentStatusChange: (event) => {
      console.log('[SourcePanel] Document status update:', event);
      setDocuments(prev => prev.map(doc =>
        doc.id === event.document_id
          ? {
            ...doc,
            status: event.status,
            summary: event.summary ?? doc.summary,
            page_count: event.page_count ?? doc.page_count,
            graph_status: event.graph_status ?? doc.graph_status,
          }
          : doc
      ));
    },
  });

  // Handle Drag Start for PDF Text Selection
  useEffect(() => {
    const handleDragStart = (e: DragEvent) => {
      const selection = window.getSelection();
      // Only inject metadata if there is a selection and an active document
      if (selection && selection.toString() && activeDocument) {
        // Check if the selection is inside the PDF viewer to avoid interfering with other drags
        const isInsidePdf = (e.target as HTMLElement)?.closest('.pdf-viewer-container');
        if (!isInsidePdf) return;

        // Use custom drag handler for preview and data
        const handler = createDragHandler(activeDocument.id, activeDocument.filename);

        // We need to cast e to any or compatible type because DragHandler expects React.DragEvent
        // but the API it uses (dataTransfer) is the same.
        handler.handleDragStart(e as unknown as React.DragEvent, {
          text: selection.toString(),
          pageNumber: pageNumber
        });
      }
    };

    document.addEventListener('dragstart', handleDragStart);
    return () => document.removeEventListener('dragstart', handleDragStart);
  }, [activeDocument, pageNumber]);

  // Vertical Resize Logic
  const handleVerticalMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsVerticalDragging(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isVerticalDragging && containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const ratio = (e.clientY - rect.top) / rect.height;
        setSplitRatio(Math.min(Math.max(ratio, 0.2), 0.8));
      }
    };
    const handleMouseUp = () => setIsVerticalDragging(false);

    if (isVerticalDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    }
  }, [isVerticalDragging]);

  const onDocumentLoadSuccess = (numPages: number) => {
    setNumPages(numPages);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;

    const file = e.target.files[0];
    await handleFileUpload(file);

    // Reset file input
    e.target.value = '';
  };

  const handleFileUpload = async (file: File) => {
    setUploadFileName(file.name);
    setUploadState('uploading');
    setUploadProgress(0);
    setUploadError(null);

    try {
      // Try presigned URL upload first (Supabase Storage)
      const newDoc = await documentsApi.uploadWithPresignedUrl(
        projectId,
        file,
        (progress) => {
          setUploadProgress(progress);
          // When upload is complete, switch to processing state
          if (progress === 100) {
            setUploadState('processing');
          }
        }
      );

      setUploadState('success');
      setDocuments([...documents, newDoc]);

      // Reset after a short delay
      setTimeout(() => {
        setUploadState('idle');
        setUploadProgress(0);
        setUploadFileName(null);
      }, 2000);

    } catch (presignError: any) {
      console.warn("Presigned URL upload failed, falling back to direct upload:", presignError.message);

      // Fallback to direct upload if presigned URL is not available
      try {
        setUploadState('uploading');
        setUploadProgress(50); // Indeterminate progress for fallback

        const newDoc = await documentsApi.upload(projectId, file);

        setUploadState('success');
        setDocuments([...documents, newDoc]);

        setTimeout(() => {
          setUploadState('idle');
          setUploadProgress(0);
          setUploadFileName(null);
        }, 2000);

      } catch (fallbackError: any) {
        console.error("Upload failed:", fallbackError);
        setUploadState('error');
        setUploadError(fallbackError.message || 'Upload failed');

        setTimeout(() => {
          setUploadState('idle');
          setUploadError(null);
          setUploadFileName(null);
        }, 5000);
      }
    }
  };

  const handleUrlImport = async (url: string) => {
    const platform = detectPlatform(url);
    const extractionId = `url-${Date.now()}`;

    // Add pending extraction to list immediately
    const pendingExtraction: PendingUrlExtraction = {
      id: extractionId,
      url,
      platform,
      status: 'extracting',
    };
    setPendingUrlExtractions(prev => [pendingExtraction, ...prev]);

    try {
      // Start extraction - returns immediately with pending status
      const pendingContent = await urlApi.extract(url);

      // Poll for completion in background
      const completedContent = await urlApi.waitForCompletion(pendingContent.id, {
        maxAttempts: 120,
        intervalMs: 1000,
        onStatusChange: (status) => {
          // Update title/thumbnail as they become available
          if (status.title || status.thumbnail_url) {
            setPendingUrlExtractions(prev =>
              prev.map(p =>
                p.id === extractionId
                  ? { ...p, title: status.title || p.title, thumbnailUrl: status.thumbnail_url || p.thumbnailUrl }
                  : p
              )
            );
          }
        },
      });

      // Update to completed
      setPendingUrlExtractions(prev =>
        prev.map(p =>
          p.id === extractionId
            ? {
                ...p,
                status: 'completed',
                title: completedContent.title || undefined,
                thumbnailUrl: completedContent.thumbnail_url || undefined,
                content: completedContent,
              }
            : p
        )
      );
    } catch (error) {
      console.error('URL extraction failed:', error);
      // Update to failed
      setPendingUrlExtractions(prev =>
        prev.map(p =>
          p.id === extractionId
            ? {
                ...p,
                status: 'failed',
                errorMessage: error instanceof Error ? error.message : 'Failed to extract URL',
              }
            : p
        )
      );
    }
  };

  const handleRemoveUrlExtraction = (id: string) => {
    setPendingUrlExtractions(prev => prev.filter(p => p.id !== id));
  };

  // PDF Pagination
  const goToPrevPage = () => {
    setPageNumber(prev => Math.max(prev - 1, 1));
  };

  const goToNextPage = () => {
    setPageNumber(prev => Math.min(prev + 1, numPages));
  };

  // Delete handlers
  const handleDeleteClick = (doc: ProjectDocument) => {
    setDocToDelete(doc);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!docToDelete) return;

    setDeleting(true);
    try {
      await documentsApi.delete(docToDelete.id);

      // Remove from local state
      setDocuments(documents.filter(d => d.id !== docToDelete.id));

      // Clear active document if it was deleted
      if (activeDocumentId === docToDelete.id) {
        setActiveDocumentId(null);
      }

      setDeleteDialogOpen(false);
      setDocToDelete(null);
    } catch (error) {
      console.error("Failed to delete document:", error);
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setDocToDelete(null);
  };

  // Format date for display
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Recently';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Get status display info
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'pending':
        return { label: 'Queued', color: '#F59E0B', bgcolor: '#FEF3C7' };
      case 'processing':
        return { label: 'Processing', color: '#3B82F6', bgcolor: '#DBEAFE' };
      case 'ready':
        return { label: 'Ready', color: '#10B981', bgcolor: '#D1FAE5' };
      case 'error':
        return { label: 'Error', color: '#EF4444', bgcolor: '#FEE2E2' };
      default:
        return { label: status, color: '#6B7280', bgcolor: '#F3F4F6' };
    }
  };

  // Render file card based on view mode
  const renderFileCard = (doc: ProjectDocument) => {
    const isActive = activeDocumentId === doc.id;
    const isProcessing = doc.status === 'pending' || doc.status === 'processing';
    const isGraphProcessing = doc.graph_status === 'pending' || doc.graph_status === 'processing';
    const isGraphReady = doc.graph_status === 'ready';
    const statusInfo = getStatusInfo(doc.status);

    if (viewMode === 'list') {
      return (
        <div
          key={doc.id}
          onClick={() => !isProcessing && setActiveDocumentId(doc.id)}
          style={{
            display: 'flex',
            gap: 12,
            padding: 12,
            marginBottom: 8,
            borderRadius: 8,
            backgroundColor: isActive ? '#EFF6FF' : 'transparent',
            border: '1px solid',
            borderColor: isActive ? '#BFDBFE' : 'transparent',
            cursor: isProcessing ? 'default' : 'pointer',
            transition: 'all 0.2s',
            position: 'relative',
            opacity: isProcessing ? 0.7 : 1,
          }}
        >
          <DescriptionIcon size={16} style={{ color: isActive ? colors.primary[500] : colors.neutral[400], marginTop: 4 }} />
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Text variant="bodySmall" weight={isActive ? "500" : "400"} color={isActive ? "primary" : "default"} sx={{ flex: 1 }} className="truncate">
                {doc.filename}
              </Text>
              {doc.status !== 'ready' && (
                <Chip
                  label={statusInfo.label}
                  size="sm"
                  style={{
                    height: 18,
                    fontSize: '0.65rem',
                    backgroundColor: statusInfo.bgcolor,
                    color: statusInfo.color,
                    fontWeight: 500,
                  }}
                />
              )}

              {/* Graph Status Icon */}
              {isGraphProcessing && (
                <Tooltip title="Building knowledge graph...">
                  <AccountTreeIcon size={14} style={{ color: colors.primary[500], animation: 'spin 3s linear infinite' }} />
                </Tooltip>
              )}
              {isGraphReady && isActive && (
                <Tooltip title="Graph ready">
                  <ShareIcon size={14} style={{ color: colors.success[500] }} />
                </Tooltip>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Text variant="caption" color="secondary">{formatDate(doc.created_at)}</Text>
              {doc.page_count && doc.page_count > 0 && (
                <>
                  <Text variant="caption" color="disabled">•</Text>
                  <Text variant="caption" color="secondary">{doc.page_count}p</Text>
                </>
              )}
            </div>
            {isProcessing && (
              <Progress
                value={undefined}
                variant="linear"
                style={{
                  marginTop: 4,
                  height: 2,
                  borderRadius: 4,
                  backgroundColor: colors.neutral[200],
                  color: statusInfo.color
                }}
              />
            )}
          </div>
          <Tooltip title="Delete">
            <IconButton
              className="delete-btn"
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteClick(doc);
              }}
              style={{
                opacity: 0,
                transition: 'opacity 0.2s',
                color: colors.text.secondary,
              }}
            >
              <DeleteIcon size={14} />
            </IconButton>
          </Tooltip>
        </div>
      );
    }

    // Grid Mode
    return (
      <div key={doc.id} style={{ position: 'relative' }} onClick={() => !isProcessing && setActiveDocumentId(doc.id)}>
        <Surface
          elevation={0}
          style={{
            padding: 0,
            overflow: 'hidden',
            borderRadius: 8,
            border: isActive ? '2px solid' : '1px solid',
            borderColor: isActive ? colors.primary[500] : colors.border.default,
            cursor: isProcessing ? 'default' : 'pointer',
            transition: 'all 0.2s',
            opacity: isProcessing ? 0.7 : 1,
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          {/* Thumbnail Area */}
          <div style={{
            height: 80,
            backgroundColor: '#F3F4F6',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            borderBottom: '1px solid',
            borderColor: colors.border.default
          }}>
            {/* PDF Thumbnail Placeholder */}
            <div style={{
              width: 40,
              height: 56,
              backgroundColor: 'white',
              boxShadow: shadows.sm,
              display: 'flex',
              flexDirection: 'column',
              padding: 4,
              gap: 4,
              borderRadius: 2
            }}>
              <div style={{ width: '80%', height: 3, backgroundColor: '#E5E7EB', borderRadius: 1 }} />
              <div style={{ width: '100%', height: 2, backgroundColor: '#F3F4F6' }} />
              <div style={{ width: '100%', height: 2, backgroundColor: '#F3F4F6' }} />
              <div style={{ width: '60%', height: 2, backgroundColor: '#F3F4F6' }} />
            </div>

            {/* Status Badge for Grid View */}
            {doc.status !== 'ready' && (
              <Chip
                label={statusInfo.label}
                size="sm"
                style={{
                  position: 'absolute',
                  top: 4,
                  left: 4,
                  height: 18,
                  fontSize: '0.6rem',
                  backgroundColor: statusInfo.bgcolor,
                  color: statusInfo.color,
                  fontWeight: 500,
                }}
              />
            )}

            {/* Graph Status Icon for Grid View */}
            {isGraphProcessing && (
              <Tooltip title="Building knowledge graph...">
                <div style={{
                  position: 'absolute',
                  top: 4,
                  left: doc.status !== 'ready' ? 'auto' : 4,
                  right: doc.status !== 'ready' ? 32 : 'auto', // Avoid delete button overlap
                  backgroundColor: 'rgba(255,255,255,0.8)',
                  borderRadius: '50%',
                  padding: 4,
                  display: 'flex',
                  boxShadow: shadows.sm
                }}>
                  <AccountTreeIcon size={12} style={{ color: colors.primary[500], animation: 'spin 3s linear infinite' }} />
                </div>
              </Tooltip>
            )}

            {/* Delete Button */}
            <IconButton
              className="delete-btn-grid"
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteClick(doc);
              }}
              style={{
                position: 'absolute',
                top: 4,
                right: 4,
                opacity: 0,
                transition: 'opacity 0.2s',
                backgroundColor: 'white',
                boxShadow: shadows.sm,
                width: 24,
                height: 24,
              }}
            >
              <DeleteIcon size={12} />
            </IconButton>

            {/* Processing indicator for grid view */}
            {isProcessing && (
              <Progress
                value={undefined}
                variant="linear"
                style={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  height: 3,
                  backgroundColor: colors.neutral[200],
                  color: statusInfo.color
                }}
              />
            )}

            {/* Active Indicator */}
            {isActive && (
              <div style={{
                position: 'absolute',
                top: 8,
                right: 8,
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: colors.primary[500],
                border: '2px solid white'
              }} />
            )}
          </div>

          {/* File Info */}
          <div style={{ padding: 12 }}>
            <Text
              variant="caption"
              weight="600"
              style={{ display: 'block', lineHeight: 1.2, marginBottom: 4 }}
              className="truncate"
              title={doc.filename}
            >
              {doc.filename}
            </Text>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <DescriptionIcon size={12} style={{ color: colors.neutral[400] }} />
              <Text variant="caption" color="secondary" style={{ fontSize: 10 }}>
                {formatDate(doc.created_at)}
              </Text>
              {doc.page_count && doc.page_count > 0 && (
                <Chip
                  label={`${doc.page_count}p`}
                  size="sm"
                  style={{ height: 16, fontSize: 9, backgroundColor: '#F3F4F6' }}
                />
              )}
            </div>
          </div>
        </Surface>
      </div>
    );
  };

  if (!visible) {
    return (
      <div style={{ width: 48, height: '100vh', borderRight: '1px solid', borderColor: colors.border.default, display: 'flex', flexDirection: 'column', alignItems: 'center', backgroundColor: colors.background.paper }}>
        <div style={{ height: 48, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid', borderColor: colors.border.default, flexShrink: 0 }}>
          <Tooltip content="Expand (⌘\)" placement="right">
            <IconButton onClick={onToggle} size="sm"><MenuOpenIcon size={18} /></IconButton>
          </Tooltip>
        </div>
        <div style={{ paddingTop: 8, paddingBottom: 8 }}>
          <Tooltip content="Documents" placement="right">
            <div style={{ padding: 8, borderRadius: 8, backgroundColor: '#EFF6FF', cursor: 'pointer' }} onClick={onToggle}>
              <FolderOpenIcon size={16} style={{ color: colors.primary[500] }} />
            </div>
          </Tooltip>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} style={{ width, height: '100vh', flexShrink: 1, minWidth: 280, display: 'flex', flexDirection: 'column', borderRight: '1px solid', borderColor: colors.border.default, overflow: 'hidden', backgroundColor: colors.background.paper }}>
      {/* Browser Header */}
      <div style={{ height: isReaderExpanded ? 0 : (activeDocument ? `${splitRatio * 100}%` : '100%'), display: 'flex', flexDirection: 'column', overflow: 'hidden', transition: isVerticalDragging ? 'none' : 'all 0.3s ease' }}>
        <div style={{ padding: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <FolderOpenIcon size={16} style={{ color: colors.primary[500] }} />
            <Text variant="body" weight="bold">Documents</Text>
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <div style={{ backgroundColor: '#F3F4F6', borderRadius: 4, padding: 2, display: 'flex' }}>
              <IconButton size="sm" onClick={() => setViewMode('list')} style={{ padding: 4, backgroundColor: viewMode === 'list' ? '#fff' : 'transparent', borderRadius: 4 }}><ViewListIcon size={12} /></IconButton>
              <IconButton size="sm" onClick={() => setViewMode('grid')} style={{ padding: 4, backgroundColor: viewMode === 'grid' ? '#fff' : 'transparent', borderRadius: 4 }}><GridViewIcon size={12} /></IconButton>
            </div>
            <Tooltip title="Collapse (⌘\)"><IconButton size="sm" onClick={onToggle}><MenuOpenIcon size={14} /></IconButton></Tooltip>
          </div>
        </div>

        <div style={{ paddingLeft: 16, paddingRight: 16, marginBottom: 16 }}>
          {/* Import Source Area */}
          <ImportSourceDropzone
            onClick={() => setImportDialogOpen(true)}
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            isDragging={isDragging}
          />
        </div>

        <div style={{ flexGrow: 1, overflowY: 'auto', paddingLeft: 16, paddingRight: 16, paddingBottom: 16 }}>
          {/* Collapsible FILES Section */}
          <div
            onClick={() => setFilesExpanded(!filesExpanded)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 8,
              color: colors.text.secondary,
              cursor: 'pointer',
              userSelect: 'none',
            }}
          >
            <ExpandMoreIcon
              size={12}
              style={{
                transform: filesExpanded ? 'rotate(0deg)' : 'rotate(-90deg)',
                transition: 'transform 0.2s ease'
              }}
            />
            <Text variant="caption" weight="bold">RECENT UPLOADS</Text>
          </div>

          <Collapse open={filesExpanded}>
            <div style={{
              display: viewMode === 'grid' ? 'grid' : 'block',
              gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
              gap: 12
            }}>
              {/* Uploading Card */}
              {(uploadState === 'uploading' || uploadState === 'processing') && (
                viewMode === 'list' ? (
                  <div style={{
                    display: 'flex',
                    gap: 12,
                    padding: 12,
                    marginBottom: 8,
                    borderRadius: 8,
                    backgroundColor: '#F9FAFB',
                    border: '1px solid',
                    borderColor: colors.border.default,
                    alignItems: 'center'
                  }}>
                    <div style={{
                      width: 32,
                      height: 32,
                      backgroundColor: colors.neutral[100],
                      borderRadius: 4,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      {uploadState === 'processing' ? (
                        <AccountTreeIcon size={16} style={{ color: colors.primary[500], animation: 'spin 3s linear infinite' }} />
                      ) : (
                        <CloudUploadIcon size={16} style={{ color: colors.primary[500] }} />
                      )}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <Text variant="bodySmall" className="truncate" weight="500">
                          {uploadFileName || 'Uploading...'}
                        </Text>
                        <Text variant="caption" color="secondary">
                          {uploadState === 'uploading' ? `${Math.round(uploadProgress)}%` : 'Processing...'}
                        </Text>
                      </div>
                      <Progress
                        value={uploadState === 'processing' ? undefined : uploadProgress}
                        variant="linear"
                        style={{
                          height: 4,
                          borderRadius: 4,
                          backgroundColor: colors.neutral[200],
                          color: colors.primary[500]
                        }}
                      />
                    </div>
                  </div>
                ) : (
                  // Grid version
                  <Surface
                    elevation={0}
                    style={{
                      padding: 0,
                      overflow: 'hidden',
                      borderRadius: 8,
                      border: '1px solid',
                      borderColor: colors.primary[500],
                      opacity: 0.8,
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                  >
                    <div style={{
                      height: 80,
                      backgroundColor: '#F3F4F6',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      position: 'relative'
                    }}>
                      <CloudUploadIcon size={24} style={{ color: colors.primary[500] }} />
                      <Progress
                        value={uploadState === 'processing' ? undefined : uploadProgress}
                        variant="linear"
                        style={{
                          position: 'absolute',
                          bottom: 0,
                          left: 0,
                          right: 0,
                          height: 3
                        }}
                      />
                    </div>
                    <div style={{ padding: 12 }}>
                      <Text variant="caption" weight="600" className="truncate" style={{ display: 'block' }}>
                        {uploadFileName}
                      </Text>
                      <Text variant="caption" color="secondary">
                        {uploadState === 'uploading' ? 'Uploading...' : 'Processing...'}
                      </Text>
                    </div>
                  </Surface>
                )
              )}

              {/* URL Extraction Cards */}
              {pendingUrlExtractions.map((extraction) => (
                viewMode === 'list' ? (
                  <div
                    key={extraction.id}
                    style={{
                      display: 'flex',
                      gap: 12,
                      padding: 12,
                      marginBottom: 8,
                      borderRadius: 8,
                      backgroundColor: extraction.status === 'failed' ? '#FEF2F2' : '#F9FAFB',
                      border: '1px solid',
                      borderColor: extraction.status === 'failed' 
                        ? '#FECACA' 
                        : extraction.status === 'completed' 
                        ? colors.success[200] 
                        : colors.border.default,
                      alignItems: 'center',
                    }}
                  >
                    <div
                      style={{
                        width: 32,
                        height: 32,
                        backgroundColor: extraction.status === 'failed' 
                          ? '#FEE2E2' 
                          : extraction.status === 'completed'
                          ? colors.success[50]
                          : colors.neutral[100],
                        borderRadius: 4,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {extraction.status === 'extracting' ? (
                        <LinkIcon size={16} style={{ color: colors.primary[500], animation: 'pulse 1.5s ease-in-out infinite' }} />
                      ) : extraction.status === 'failed' ? (
                        <ErrorIcon size={16} style={{ color: '#EF4444' }} />
                      ) : (
                        <PlatformIcon platform={extraction.platform} size={16} />
                      )}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <Text variant="bodySmall" className="truncate" weight="500">
                        {extraction.title || extraction.url.slice(0, 40) + '...'}
                      </Text>
                      <Text variant="caption" color="secondary">
                        {extraction.status === 'extracting' 
                          ? 'Extracting content...' 
                          : extraction.status === 'failed'
                          ? extraction.errorMessage || 'Failed to extract'
                          : extraction.platform.charAt(0).toUpperCase() + extraction.platform.slice(1)}
                      </Text>
                    </div>
                    {extraction.status !== 'extracting' && (
                      <IconButton
                        size="sm"
                        onClick={() => handleRemoveUrlExtraction(extraction.id)}
                        style={{ opacity: 0.6 }}
                      >
                        <DeleteIcon size={14} />
                      </IconButton>
                    )}
                  </div>
                ) : (
                  // Grid version
                  <Surface
                    key={extraction.id}
                    elevation={0}
                    style={{
                      padding: 0,
                      overflow: 'hidden',
                      borderRadius: 8,
                      border: '1px solid',
                      borderColor: extraction.status === 'failed'
                        ? '#FECACA'
                        : extraction.status === 'completed'
                        ? colors.success[200]
                        : colors.primary[300],
                      opacity: extraction.status === 'extracting' ? 0.8 : 1,
                      cursor: extraction.status === 'completed' ? 'pointer' : 'default',
                    }}
                  >
                    {/* Thumbnail area */}
                    <div
                      style={{
                        width: '100%',
                        height: 80,
                        backgroundColor: extraction.status === 'failed' 
                          ? '#FEE2E2' 
                          : colors.neutral[100],
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        backgroundImage: extraction.thumbnailUrl ? `url(${extraction.thumbnailUrl})` : undefined,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                      }}
                    >
                      {!extraction.thumbnailUrl && (
                        extraction.status === 'extracting' ? (
                          <LinkIcon size={24} style={{ color: colors.primary[500], animation: 'pulse 1.5s ease-in-out infinite' }} />
                        ) : extraction.status === 'failed' ? (
                          <ErrorIcon size={24} style={{ color: '#EF4444' }} />
                        ) : (
                          <PlatformIcon platform={extraction.platform} size={24} />
                        )
                      )}
                    </div>
                    {/* Info area */}
                    <div style={{ padding: 8 }}>
                      <Text variant="caption" className="truncate" style={{ display: 'block', marginBottom: 2 }}>
                        {extraction.title || extraction.url.slice(0, 30) + '...'}
                      </Text>
                      <Text variant="caption" color="secondary">
                        {extraction.status === 'extracting' 
                          ? 'Extracting...' 
                          : extraction.status === 'failed'
                          ? 'Failed'
                          : extraction.platform}
                      </Text>
                    </div>
                  </Surface>
                )
              ))}

              {documents.map(renderFileCard)}
            </div>
          </Collapse>
        </div>
      </div>

      {/* PDF Viewer */}
      {activeDocument && fileUrl && (
        <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderTop: '1px solid', borderColor: colors.border.default }}>
          <div
            onMouseDown={handleVerticalMouseDown}
            style={{
              height: 44,
              display: 'flex',
              alignItems: 'center',
              paddingLeft: 16,
              paddingRight: 16,
              justifyContent: 'space-between',
              backgroundColor: colors.background.default,
              cursor: 'row-resize',
              borderBottom: '1px solid',
              borderColor: colors.border.default
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Chip
                label="PDF"
                size="sm"
                style={{
                  height: 20,
                  fontSize: 10,
                  fontWeight: 'bold',
                  backgroundColor: '#FEE2E2',
                  color: '#DC2626'
                }}
              />
              <Text variant="bodySmall" className="truncate" style={{ maxWidth: 150 }}>{activeDocument.filename}</Text>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              {/* Pagination Controls */}
              <IconButton
                size="sm"
                onClick={goToPrevPage}
                disabled={pageNumber <= 1}
                style={{ padding: 4 }}
              >
                <ChevronLeftIcon size={16} />
              </IconButton>
              <Text variant="caption" style={{ minWidth: 60, textAlign: 'center' }}>
                {pageNumber} / {numPages}
              </Text>
              <IconButton
                size="sm"
                onClick={goToNextPage}
                disabled={pageNumber >= numPages}
                style={{ padding: 4 }}
              >
                <ChevronRightIcon size={16} />
              </IconButton>

              <IconButton size="sm" onClick={() => setIsReaderExpanded(!isReaderExpanded)} style={{ marginLeft: 8 }}>
                {isReaderExpanded ? <FullscreenExitIcon size={14} /> : <FullscreenIcon size={14} />}
              </IconButton>
            </div>
          </div>

          <div style={{ flexGrow: 1, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <PDFViewer
              documentId={activeDocument.id}
              fileUrl={fileUrl}
              pageNumber={pageNumber}
              onPageChange={setPageNumber}
              onDocumentLoad={onDocumentLoadSuccess}
              highlightText={sourceNavigation?.searchText}
            />
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <Modal
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        size="sm"
      >
        <Modal.Header>
          <Text variant="h6">Delete Document</Text>
        </Modal.Header>
        <Modal.Content>
          <Text variant="body">
            Are you sure you want to delete <strong>{docToDelete?.filename}</strong>?
            This will also remove all associated text chunks and embeddings. This action cannot be undone.
          </Text>
        </Modal.Content>
        <Modal.Footer>
          <Button
            variant="ghost"
            onClick={handleDeleteCancel}
            disabled={deleting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="danger"
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Import Source Dialog */}
      <ImportSourceDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        onFileSelect={handleFileUpload}
        onUrlImport={handleUrlImport}
        acceptedFileTypes={['.pdf', '.docx', '.csv', '.jpg', '.jpeg']}
        maxFileSize={25}
      />
    </div>
  );
}

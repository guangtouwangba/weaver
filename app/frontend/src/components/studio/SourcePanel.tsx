'use client';

import { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  IconButton, 
  Button,
  Tooltip,
  Collapse,
  Chip,
  LinearProgress,
  Alert,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from "@mui/material";
import { 
  FileText, 
  Maximize2, 
  Minimize2, 
  FolderOpen,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
  LayoutGrid,
  List as ListIcon,
  Upload,
  CloudUpload,
  CheckCircle,
  AlertCircle,
  Trash2,
  MoreVertical,
  Network,
  Share2,
} from "lucide-react";
import { useStudio } from '@/contexts/StudioContext';
import { documentsApi, ProjectDocument } from '@/lib/api';

// PDF Viewer
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface SourcePanelProps {
  visible: boolean;
  width: number;
  onToggle: () => void;
}

// Upload state type
type UploadState = 'idle' | 'uploading' | 'processing' | 'success' | 'error';

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
  
  // Delete state
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [menuDocId, setMenuDocId] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [docToDelete, setDocToDelete] = useState<ProjectDocument | null>(null);
  const [deleting, setDeleting] = useState(false);
  
  // Vertical Resize State
  const [splitRatio, setSplitRatio] = useState(0.4);
  const [isVerticalDragging, setIsVerticalDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const pageRef = useRef<HTMLDivElement>(null);

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

  // Highlight text in PDF when searchText is provided
  useEffect(() => {
    if (!sourceNavigation?.searchText || !pageRef.current || pageNumber !== sourceNavigation.pageNumber) return;
    
    // Wait for PDF text layer to render
    const highlightText = () => {
      const textLayer = pageRef.current?.querySelector('.react-pdf__Page__textContent');
      if (!textLayer) {
        // Retry after a short delay if text layer not ready
        setTimeout(highlightText, 100);
        return;
      }

      // Remove previous highlights
      const previousHighlights = textLayer.querySelectorAll('span[data-highlighted="true"]');
      previousHighlights.forEach(el => {
        el.removeAttribute('data-highlighted');
        el.style.backgroundColor = '';
        el.style.borderRadius = '';
        el.style.padding = '';
      });

      // Extract search text (remove quotes, ellipsis, etc.)
      let searchText = sourceNavigation.searchText || '';
      searchText = searchText.replace(/^["'"]+|["'"]+$/g, '').replace(/\.\.\./g, '').trim();
      if (!searchText || searchText.length < 3) return;

      // Get all text spans and build full text
      const textSpans = Array.from(textLayer.querySelectorAll('span'));
      const fullText = textSpans.map(span => span.textContent || '').join('');
      const searchLower = searchText.toLowerCase();
      const fullTextLower = fullText.toLowerCase();
      
      // Find position of search text in full text
      const searchIndex = fullTextLower.indexOf(searchLower);
      if (searchIndex === -1) {
        // Try to find partial match (first 20 chars)
        const partialSearch = searchText.substring(0, 20).toLowerCase();
        const partialIndex = fullTextLower.indexOf(partialSearch);
        if (partialIndex === -1) return;
        
        // Highlight spans around partial match
        let charCount = 0;
        textSpans.forEach(span => {
          const spanText = span.textContent || '';
          const spanStart = charCount;
          const spanEnd = charCount + spanText.length;
          
          if (spanStart <= partialIndex + partialSearch.length && spanEnd >= partialIndex) {
            span.setAttribute('data-highlighted', 'true');
            span.style.backgroundColor = '#FFEB3B';
            span.style.borderRadius = '2px';
            span.style.padding = '1px 2px';
          }
          
          charCount = spanEnd;
        });
      } else {
        // Highlight spans containing the search text
        let charCount = 0;
        textSpans.forEach(span => {
          const spanText = span.textContent || '';
          const spanStart = charCount;
          const spanEnd = charCount + spanText.length;
          
          if (spanStart <= searchIndex + searchText.length && spanEnd >= searchIndex) {
            span.setAttribute('data-highlighted', 'true');
            span.style.backgroundColor = '#FFEB3B';
            span.style.borderRadius = '2px';
            span.style.padding = '1px 2px';
          }
          
          charCount = spanEnd;
        });
      }

      // Scroll to first highlight if found
      const firstHighlight = textLayer.querySelector('span[data-highlighted="true"]');
      if (firstHighlight) {
        setTimeout(() => {
          firstHighlight.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
        }, 100);
      }
    };

    // Delay to ensure PDF is rendered
    const timeoutId = setTimeout(highlightText, 500);
    return () => clearTimeout(timeoutId);
  }, [sourceNavigation, pageNumber, activeDocumentId]);

  // Poll for document status updates (for pending/processing documents)
  useEffect(() => {
    const pendingDocs = documents.filter(d => 
      d.status === 'pending' || 
      d.status === 'processing' || 
      (d.graph_status === 'pending' || d.graph_status === 'processing')
    );
    
    if (pendingDocs.length === 0) return;
    
    const pollInterval = setInterval(async () => {
      try {
        // Refresh document list to get updated statuses
        const response = await documentsApi.list(projectId);
        const updatedDocs = response.items;
        
        // Check if any status changed
        const hasChanges = updatedDocs.some(updatedDoc => {
          const existingDoc = documents.find(d => d.id === updatedDoc.id);
          if (!existingDoc) return true;
          return existingDoc.status !== updatedDoc.status || existingDoc.graph_status !== updatedDoc.graph_status;
        });
        
        if (hasChanges) {
          setDocuments(updatedDocs);
        }
      } catch (error) {
        console.error('Failed to poll document status:', error);
      }
    }, 3000); // Poll every 3 seconds
    
    return () => clearInterval(pollInterval);
  }, [documents, projectId, setDocuments]);

  // Handle Drag Start for PDF Text Selection
  useEffect(() => {
    const handleDragStart = (e: DragEvent) => {
      const selection = window.getSelection();
      // Only inject metadata if there is a selection and an active document
      if (selection && selection.toString() && activeDocument) {
        const metadata = {
            sourceId: activeDocument.id,
            sourceType: 'pdf',
            sourceTitle: activeDocument.filename,
            pageNumber: pageNumber,
            content: selection.toString()
        };
        e.dataTransfer?.setData('application/json', JSON.stringify(metadata));
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

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    
    const file = e.target.files[0];
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
    
    // Reset file input
    e.target.value = '';
  };

  // PDF Pagination
  const goToPrevPage = () => {
    setPageNumber(prev => Math.max(prev - 1, 1));
  };

  const goToNextPage = () => {
    setPageNumber(prev => Math.min(prev + 1, numPages));
  };

  // Menu handlers
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, docId: string) => {
    event.stopPropagation();
    setMenuAnchorEl(event.currentTarget);
    setMenuDocId(docId);
  };

  const handleMenuClose = () => {
    setMenuAnchorEl(null);
    setMenuDocId(null);
  };

  // Delete handlers
  const handleDeleteClick = (doc: ProjectDocument) => {
    setDocToDelete(doc);
    setDeleteDialogOpen(true);
    handleMenuClose();
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
        <Box 
          key={doc.id} 
          onClick={() => !isProcessing && setActiveDocumentId(doc.id)}
          sx={{ 
            display: 'flex', 
            gap: 1.5, 
            p: 1.5, 
            mb: 1, 
            borderRadius: 2, 
            bgcolor: isActive ? '#EFF6FF' : 'transparent', 
            border: '1px solid', 
            borderColor: isActive ? '#BFDBFE' : 'transparent',
            '&:hover': { bgcolor: isActive ? '#EFF6FF' : 'action.hover', '& .delete-btn': { opacity: 1 } }, 
            cursor: isProcessing ? 'default' : 'pointer', 
            transition: 'all 0.2s',
            position: 'relative',
            opacity: isProcessing ? 0.7 : 1,
          }}
        >
          <FileText size={16} className={isActive ? "text-blue-600 mt-0.5" : "text-gray-400 mt-0.5"} />
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" fontWeight={isActive ? "500" : "400"} color={isActive ? "primary.main" : "text.primary"} noWrap sx={{ flex: 1 }}>
                {doc.filename}
              </Typography>
              {doc.status !== 'ready' && (
                <Chip 
                  label={statusInfo.label} 
                  size="small" 
                  sx={{ 
                    height: 18, 
                    fontSize: '0.65rem',
                    bgcolor: statusInfo.bgcolor,
                    color: statusInfo.color,
                    fontWeight: 500,
                  }} 
                />
              )}
              
              {/* Graph Status Icon */}
              {isGraphProcessing && (
                <Tooltip title="Building knowledge graph...">
                  <Network size={14} className="text-blue-500 animate-spin-slow" style={{ animation: 'spin 3s linear infinite' }} />
                </Tooltip>
              )}
              {isGraphReady && isActive && (
                <Tooltip title="Graph ready">
                  <Share2 size={14} className="text-green-500" />
                </Tooltip>
              )}
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" color="text.secondary">{formatDate(doc.created_at)}</Typography>
              {doc.page_count && doc.page_count > 0 && (
                <>
                  <Typography variant="caption" color="text.disabled">•</Typography>
                  <Typography variant="caption" color="text.secondary">{doc.page_count}p</Typography>
                </>
              )}
            </Box>
            {isProcessing && (
              <LinearProgress 
                sx={{ 
                  mt: 0.5, 
                  height: 2, 
                  borderRadius: 1,
                  bgcolor: 'grey.200',
                  '& .MuiLinearProgress-bar': { bgcolor: statusInfo.color }
                }} 
              />
            )}
          </Box>
          <Tooltip title="Delete">
            <IconButton
              className="delete-btn"
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteClick(doc);
              }}
              sx={{ 
                opacity: 0, 
                transition: 'opacity 0.2s',
                color: 'text.secondary',
                '&:hover': { color: 'error.main', bgcolor: 'error.50' }
              }}
            >
              <Trash2 size={14} />
            </IconButton>
          </Tooltip>
        </Box>
      );
    }

    // Grid Mode
    return (
      <Box key={doc.id} sx={{ position: 'relative' }} onClick={() => !isProcessing && setActiveDocumentId(doc.id)}>
        <Paper
          elevation={0}
          sx={{ 
            p: 0, 
            overflow: 'hidden', 
            borderRadius: 2, 
            border: isActive ? '2px solid' : '1px solid', 
            borderColor: isActive ? 'primary.main' : 'divider',
            cursor: isProcessing ? 'default' : 'pointer', 
            transition: 'all 0.2s', 
            opacity: isProcessing ? 0.7 : 1,
            '&:hover': { 
              borderColor: isActive ? 'primary.main' : 'grey.400', 
              transform: isProcessing ? 'none' : 'translateY(-2px)',
              '& .delete-btn-grid': { opacity: 1 }
            }, 
            display: 'flex', 
            flexDirection: 'column'
          }}
        >
          {/* Thumbnail Area */}
          <Box sx={{ 
            height: 80, 
            bgcolor: '#F3F4F6', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            position: 'relative', 
            borderBottom: '1px solid', 
            borderColor: 'divider' 
          }}>
            {/* PDF Thumbnail Placeholder */}
            <Box sx={{ 
              width: 40, 
              height: 56, 
              bgcolor: 'white', 
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)', 
              display: 'flex', 
              flexDirection: 'column', 
              p: 0.5, 
              gap: 0.5,
              borderRadius: 0.5
            }}>
              <Box sx={{ width: '80%', height: 3, bgcolor: '#E5E7EB', borderRadius: 1 }} />
              <Box sx={{ width: '100%', height: 2, bgcolor: '#F3F4F6' }} />
              <Box sx={{ width: '100%', height: 2, bgcolor: '#F3F4F6' }} />
              <Box sx={{ width: '60%', height: 2, bgcolor: '#F3F4F6' }} />
            </Box>
            
            {/* Status Badge for Grid View */}
            {doc.status !== 'ready' && (
              <Chip 
                label={statusInfo.label} 
                size="small" 
                sx={{ 
                  position: 'absolute',
                  top: 4,
                  left: 4,
                  height: 18, 
                  fontSize: '0.6rem',
                  bgcolor: statusInfo.bgcolor,
                  color: statusInfo.color,
                  fontWeight: 500,
                }} 
              />
            )}
            
            {/* Graph Status Icon for Grid View */}
            {isGraphProcessing && (
              <Tooltip title="Building knowledge graph...">
                <Box sx={{ 
                  position: 'absolute', 
                  top: 4, 
                  left: doc.status !== 'ready' ? 'auto' : 4, 
                  right: doc.status !== 'ready' ? 32 : 'auto', // Avoid delete button overlap
                  bgcolor: 'rgba(255,255,255,0.8)', 
                  borderRadius: '50%', 
                  p: 0.5,
                  display: 'flex',
                  boxShadow: 1
                }}>
                  <Network size={12} className="text-blue-500" style={{ animation: 'spin 3s linear infinite' }} />
                </Box>
              </Tooltip>
            )}
            
            {/* Delete Button */}
            <IconButton
              className="delete-btn-grid"
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteClick(doc);
              }}
              sx={{ 
                position: 'absolute',
                top: 4,
                right: 4,
                opacity: 0, 
                transition: 'opacity 0.2s',
                bgcolor: 'white',
                boxShadow: 1,
                width: 24,
                height: 24,
                '&:hover': { bgcolor: 'error.50', color: 'error.main' }
              }}
            >
              <Trash2 size={12} />
            </IconButton>
            
            {/* Processing indicator for grid view */}
            {isProcessing && (
              <LinearProgress 
                sx={{ 
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  height: 3,
                  bgcolor: 'grey.200',
                  '& .MuiLinearProgress-bar': { bgcolor: statusInfo.color }
                }} 
              />
            )}
            
            {/* Active Indicator */}
            {isActive && (
              <Box sx={{ 
                position: 'absolute', 
                top: 8, 
                right: 8, 
                width: 8, 
                height: 8, 
                borderRadius: '50%', 
                bgcolor: 'primary.main', 
                border: '2px solid white' 
              }} />
            )}
          </Box>
          
          {/* File Info */}
          <Box sx={{ p: 1.5 }}>
            <Typography 
              variant="caption" 
              fontWeight="600" 
              sx={{ display: 'block', lineHeight: 1.2, mb: 0.5 }} 
              noWrap 
              title={doc.filename}
            >
              {doc.filename}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FileText size={12} className="text-gray-400" />
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>
                {formatDate(doc.created_at)}
              </Typography>
              {doc.page_count && doc.page_count > 0 && (
                <Chip 
                  label={`${doc.page_count}p`} 
                  size="small" 
                  sx={{ height: 16, fontSize: 9, bgcolor: '#F3F4F6' }} 
                />
              )}
            </Box>
          </Box>
        </Paper>
      </Box>
    );
  };

  if (!visible) {
    return (
      <Box sx={{ width: 48, height: '100vh', borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', alignItems: 'center', bgcolor: 'background.paper' }}>
        <Box sx={{ height: 48, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid', borderColor: 'divider', flexShrink: 0 }}>
          <Tooltip title="Expand (⌘\)" placement="right">
            <IconButton onClick={onToggle} size="small"><PanelLeftOpen size={18} /></IconButton>
          </Tooltip>
        </Box>
        <Box sx={{ py: 2 }}>
          <Tooltip title="Documents" placement="right">
            <Box sx={{ p: 1, borderRadius: 1, bgcolor: '#EFF6FF', cursor: 'pointer' }} onClick={onToggle}>
              <FolderOpen size={16} className="text-blue-600" />
            </Box>
          </Tooltip>
        </Box>
      </Box>
    );
  }

  return (
    <Box ref={containerRef} sx={{ width, height: '100vh', flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid', borderColor: 'divider', overflow: 'hidden', bgcolor: 'background.paper' }}>
      {/* Browser Header */}
      <Box sx={{ height: isReaderExpanded ? 0 : (activeDocument ? `${splitRatio * 100}%` : '100%'), display: 'flex', flexDirection: 'column', overflow: 'hidden', transition: isVerticalDragging ? 'none' : 'all 0.3s ease' }}>
        <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FolderOpen size={16} className="text-blue-600" />
            <Typography variant="subtitle2" fontWeight="bold">Documents</Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Box sx={{ bgcolor: '#F3F4F6', borderRadius: 1, p: 0.25, display: 'flex' }}>
              <IconButton size="small" onClick={() => setViewMode('list')} sx={{ p: 0.5, bgcolor: viewMode === 'list' ? '#fff' : 'transparent', borderRadius: 0.5 }}><ListIcon size={12} /></IconButton>
              <IconButton size="small" onClick={() => setViewMode('grid')} sx={{ p: 0.5, bgcolor: viewMode === 'grid' ? '#fff' : 'transparent', borderRadius: 0.5 }}><LayoutGrid size={12} /></IconButton>
            </Box>
            <Tooltip title="Collapse (⌘\)"><IconButton size="small" onClick={onToggle}><PanelLeftClose size={14} /></IconButton></Tooltip>
          </Box>
        </Box>
        
        <Box sx={{ px: 2, mb: 2 }}>
          {/* Upload Button / Progress */}
          {uploadState === 'idle' ? (
            <Button 
              component="label" 
              fullWidth 
              variant="contained" 
              size="small" 
              startIcon={<CloudUpload size={14} />} 
              sx={{ 
                bgcolor: '#171717', 
                textTransform: 'none', 
                borderRadius: 1.5, 
                '&:hover': { bgcolor: '#000' } 
              }}
            >
              Upload PDF
              <input type="file" hidden accept=".pdf" onChange={handleUpload} />
            </Button>
          ) : (
            <Paper 
              elevation={0} 
              sx={{ 
                p: 1.5, 
                borderRadius: 1.5, 
                border: '1px solid', 
                borderColor: uploadState === 'error' ? 'error.main' : uploadState === 'success' ? 'success.main' : 'divider',
                bgcolor: uploadState === 'error' ? 'error.50' : uploadState === 'success' ? 'success.50' : 'background.default'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: uploadState === 'uploading' || uploadState === 'processing' ? 1 : 0 }}>
                {uploadState === 'uploading' && <CloudUpload size={14} className="text-blue-500" />}
                {uploadState === 'processing' && <CloudUpload size={14} className="text-orange-500 animate-pulse" />}
                {uploadState === 'success' && <CheckCircle size={14} className="text-green-600" />}
                {uploadState === 'error' && <AlertCircle size={14} className="text-red-600" />}
                
                <Typography variant="caption" fontWeight="500" noWrap sx={{ flex: 1 }}>
                  {uploadState === 'uploading' && `Uploading ${uploadFileName}...`}
                  {uploadState === 'processing' && 'Processing document...'}
                  {uploadState === 'success' && 'Upload complete!'}
                  {uploadState === 'error' && (uploadError || 'Upload failed')}
                </Typography>
                
                {(uploadState === 'uploading' || uploadState === 'processing') && (
                  <Typography variant="caption" color="text.secondary">
                    {uploadState === 'uploading' ? `${uploadProgress}%` : ''}
                  </Typography>
                )}
              </Box>
              
              {(uploadState === 'uploading' || uploadState === 'processing') && (
                <LinearProgress 
                  variant={uploadState === 'processing' ? 'indeterminate' : 'determinate'}
                  value={uploadProgress}
                  sx={{ 
                    height: 4, 
                    borderRadius: 2,
                    bgcolor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: uploadState === 'processing' ? 'warning.main' : 'primary.main'
                    }
                  }}
                />
              )}
            </Paper>
          )}
        </Box>

        <Box sx={{ flexGrow: 1, overflowY: 'auto', px: 2, pb: 2 }}>
          {/* Collapsible FILES Section */}
          <Box 
            onClick={() => setFilesExpanded(!filesExpanded)}
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 1, 
              mb: 1, 
              color: 'text.secondary',
              cursor: 'pointer',
              userSelect: 'none',
              '&:hover': { color: 'text.primary' }
            }}
          >
            <ChevronDown 
              size={12} 
              style={{ 
                transform: filesExpanded ? 'rotate(0deg)' : 'rotate(-90deg)',
                transition: 'transform 0.2s ease'
              }} 
            />
            <Typography variant="caption" fontWeight="bold">FILES ({documents.length})</Typography>
          </Box>
          
          <Collapse in={filesExpanded}>
            <Box sx={{ 
              display: viewMode === 'grid' ? 'grid' : 'block', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', 
              gap: 1.5 
            }}>
              {documents.map(renderFileCard)}
            </Box>
          </Collapse>
        </Box>
      </Box>

      {/* PDF Viewer */}
      {activeDocument && fileUrl && (
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderTop: '1px solid', borderColor: 'divider' }}>
          <Box 
            onMouseDown={handleVerticalMouseDown}
            sx={{ 
              height: 44, 
              display: 'flex', 
              alignItems: 'center', 
              px: 2, 
              justifyContent: 'space-between', 
              bgcolor: 'background.default',
              cursor: 'row-resize',
              borderBottom: '1px solid', borderColor: 'divider'
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip 
                label="PDF" 
                size="small" 
                sx={{ 
                  height: 20, 
                  fontSize: 10, 
                  fontWeight: 'bold',
                  bgcolor: '#FEE2E2', 
                  color: '#DC2626' 
                }} 
              />
              <Typography variant="subtitle2" noWrap sx={{ maxWidth: 150 }}>{activeDocument.filename}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {/* Pagination Controls */}
              <IconButton 
                size="small" 
                onClick={goToPrevPage} 
                disabled={pageNumber <= 1}
                sx={{ p: 0.5 }}
              >
                <ChevronLeft size={16} />
              </IconButton>
              <Typography variant="caption" sx={{ minWidth: 60, textAlign: 'center' }}>
                {pageNumber} / {numPages}
              </Typography>
              <IconButton 
                size="small" 
                onClick={goToNextPage} 
                disabled={pageNumber >= numPages}
                sx={{ p: 0.5 }}
              >
                <ChevronRight size={16} />
              </IconButton>
              
              <IconButton size="small" onClick={() => setIsReaderExpanded(!isReaderExpanded)} sx={{ ml: 1 }}>
                {isReaderExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
              </IconButton>
            </Box>
          </Box>
          
          <Box 
            ref={pageRef}
            sx={{ flexGrow: 1, overflow: 'auto', bgcolor: '#f5f5f5', display: 'flex', justifyContent: 'center', p: 2 }}
          >
            <Document
              file={fileUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              loading={<Typography variant="body2" sx={{ mt: 4 }}>Loading PDF...</Typography>}
              error={<Typography variant="body2" color="error" sx={{ mt: 4 }}>Failed to load PDF</Typography>}
            >
              <Page 
                pageNumber={pageNumber} 
                renderTextLayer={true}
                renderAnnotationLayer={true}
                width={width - 40}
              />
            </Document>
          </Box>
        </Box>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle sx={{ pb: 1 }}>
          Delete Document
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete <strong>{docToDelete?.filename}</strong>? 
            This will also remove all associated text chunks and embeddings. This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button 
            onClick={handleDeleteCancel} 
            disabled={deleting}
            sx={{ textTransform: 'none' }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error" 
            variant="contained"
            disabled={deleting}
            sx={{ textTransform: 'none' }}
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

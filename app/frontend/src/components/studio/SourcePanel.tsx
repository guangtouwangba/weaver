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

export default function SourcePanel({ visible, width, onToggle }: SourcePanelProps) {
  const { projectId, documents, setDocuments, activeDocumentId, setActiveDocumentId } = useStudio();
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('grid');
  const [isReaderExpanded, setIsReaderExpanded] = useState(false);
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [filesExpanded, setFilesExpanded] = useState(true);
  
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
    if (e.target.files && e.target.files[0]) {
      try {
        const newDoc = await documentsApi.upload(projectId, e.target.files[0]);
        setDocuments([...documents, newDoc]);
      } catch (error) {
        console.error("Upload failed:", error);
      }
    }
  };

  // PDF Pagination
  const goToPrevPage = () => {
    setPageNumber(prev => Math.max(prev - 1, 1));
  };

  const goToNextPage = () => {
    setPageNumber(prev => Math.min(prev + 1, numPages));
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

  // Render file card based on view mode
  const renderFileCard = (doc: ProjectDocument) => {
    const isActive = activeDocumentId === doc.id;
    
    if (viewMode === 'list') {
      return (
        <Box 
          key={doc.id} 
          onClick={() => setActiveDocumentId(doc.id)}
          sx={{ 
            display: 'flex', 
            gap: 1.5, 
            p: 1.5, 
            mb: 1, 
            borderRadius: 2, 
            bgcolor: isActive ? '#EFF6FF' : 'transparent', 
            border: '1px solid', 
            borderColor: isActive ? '#BFDBFE' : 'transparent',
            '&:hover': { bgcolor: isActive ? '#EFF6FF' : 'action.hover' }, 
            cursor: 'pointer', 
            transition: 'all 0.2s'
          }}
        >
          <FileText size={16} className={isActive ? "text-blue-600 mt-0.5" : "text-gray-400 mt-0.5"} />
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography variant="body2" fontWeight={isActive ? "500" : "400"} color={isActive ? "primary.main" : "text.primary"} noWrap>
              {doc.filename}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" color="text.secondary">{formatDate(doc.created_at)}</Typography>
              {doc.page_count && doc.page_count > 0 && (
                <>
                  <Typography variant="caption" color="text.disabled">•</Typography>
                  <Typography variant="caption" color="text.secondary">{doc.page_count}p</Typography>
                </>
              )}
            </Box>
          </Box>
        </Box>
      );
    }

    // Grid Mode
    return (
      <Box key={doc.id} sx={{ position: 'relative' }} onClick={() => setActiveDocumentId(doc.id)}>
        <Paper
          elevation={0}
          sx={{ 
            p: 0, 
            overflow: 'hidden', 
            borderRadius: 2, 
            border: isActive ? '2px solid' : '1px solid', 
            borderColor: isActive ? 'primary.main' : 'divider',
            cursor: 'pointer', 
            transition: 'all 0.2s', 
            '&:hover': { borderColor: isActive ? 'primary.main' : 'grey.400', transform: 'translateY(-2px)' }, 
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
      <Box sx={{ width: 48, borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', alignItems: 'center', bgcolor: 'background.paper' }}>
        <Box sx={{ height: 48, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid', borderColor: 'divider' }}>
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
    <Box ref={containerRef} sx={{ width, flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid', borderColor: 'divider', overflow: 'hidden', bgcolor: 'background.paper' }}>
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
          <Button component="label" fullWidth variant="contained" size="small" startIcon={<Upload size={14} />} sx={{ bgcolor: '#171717', textTransform: 'none', borderRadius: 1.5, '&:hover': { bgcolor: '#000' } }}>
            Upload PDF
            <input type="file" hidden accept=".pdf" onChange={handleUpload} />
          </Button>
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
          
          <Box sx={{ flexGrow: 1, overflow: 'auto', bgcolor: '#f5f5f5', display: 'flex', justifyContent: 'center', p: 2 }}>
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
                onLoadSuccess={() => console.log('Page loaded')}
              />
            </Document>
          </Box>
        </Box>
      )}
    </Box>
  );
}

'use client';

import React, { useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Paper,
  LinearProgress,
  Collapse,
  CircularProgress,
  Skeleton,
  Tooltip
} from '@mui/material';
import {
  DescriptionIcon,
  ExpandMoreIcon,
  DeleteIcon,
  CloudUploadIcon,
  UploadFileIcon,
  MenuOpenIcon
} from '@/components/ui/icons';
import { useStudio } from '@/contexts/StudioContext';
import { documentsApi, ProjectDocument } from '@/lib/api';
import { useDocumentWebSocket } from '@/hooks/useDocumentWebSocket';
import ImportSourceDialog from '@/components/dialogs/ImportSourceDialog';
import ImportSourceDropzone from '@/components/studio/ImportSourceDropzone';
import DocumentPreviewCard from '@/components/studio/DocumentPreviewCard';

interface ResourceSidebarProps {
  width?: number;
  collapsed?: boolean;
  onToggle?: () => void;
}

// Helper function to format file size
const formatFileSize = (bytes: number | undefined): string => {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Custom PDF Icon Component
const CustomPdfIcon = ({ size = 24 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" fill="#EF4444" />
    <path d="M14 2V8H20" fill="#B91C1C" fillOpacity="0.5" />
    <text x="50%" y="15" fontFamily="sans-serif" fontSize="6" fill="white" fontWeight="bold" textAnchor="middle">PDF</text>
  </svg>
);

// Helper function to get icon props based on file extension
const getFileIconProps = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'pdf':
      return { icon: <CustomPdfIcon size={24} />, bg: '#FEF2F2' }; // Red-50
    case 'doc':
    case 'docx':
      return { icon: <DescriptionIcon size="lg" sx={{ color: '#3B82F6' }} />, bg: '#EFF6FF' }; // Blue-500, Blue-50
    case 'csv':
    case 'xlsx':
    case 'xls':
      return { icon: <DescriptionIcon size="lg" sx={{ color: '#10B981' }} />, bg: '#ECFDF5' }; // Emerald-500, Emerald-50
    default:
      return { icon: <DescriptionIcon size="lg" sx={{ color: '#6B7280' }} />, bg: '#F3F4F6' }; // Gray-500, Gray-100
  }
};

// Reusable Skeleton Component
const SkeletonBar = ({ width, height = 16, sx = {} }: { width: string | number, height?: number, sx?: any }) => (
  <Box
    sx={{
      width,
      height,
      bgcolor: 'rgba(0,0,0,0.06)',
      borderRadius: 1,
      animation: 'pulse 1.5s ease-in-out infinite',
      '@keyframes pulse': {
        '0%': { opacity: 0.6 },
        '50%': { opacity: 1 },
        '100%': { opacity: 0.6 }
      },
      ...sx
    }}
  />
);

export default function ResourceSidebar({ width = 300, collapsed = false, onToggle }: ResourceSidebarProps) {
  const { projectId, documents, setDocuments, activeDocumentId, setActiveDocumentId, openDocumentPreview } = useStudio();

  // Subscribe to document status updates
  useDocumentWebSocket(projectId, documents, setDocuments);

  // UI State
  const [filesExpanded, setFilesExpanded] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadFileName, setUploadFileName] = useState<string | null>(null);
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());

  // Drag handlers
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

  const handleFileUpload = async (file: File) => {
    if (!projectId) return;

    setIsUploading(true);
    setUploadFileName(file.name);
    setUploadProgress(0);

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => Math.min(prev + 10, 90));
    }, 200);

    try {
      const newDoc = await documentsApi.upload(projectId, file);
      setDocuments([newDoc, ...documents]);
      setUploadProgress(100);

      setTimeout(() => {
        setIsUploading(false);
        setUploadFileName(null);
        setUploadProgress(0);
      }, 500);
    } catch (error) {
      console.error('Upload failed:', error);
      setIsUploading(false);
      setUploadFileName(null);
      setUploadProgress(0);
    } finally {
      clearInterval(progressInterval);
    }
  };

  const handleDeleteDocument = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!projectId) return;

    setDeletingIds(prev => new Set(prev).add(docId));

    try {
      await documentsApi.delete(docId);
      setDocuments(documents.filter(d => d.id !== docId));
      if (activeDocumentId === docId) {
        setActiveDocumentId(null);
      }
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setDeletingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(docId);
        return newSet;
      });
    }
  };

  if (collapsed) {
    return (
      <Box
        sx={{
          width: 48,
          height: '100%',
          flexShrink: 0,
          borderRight: '1px solid',
          borderColor: 'divider',
          bgcolor: 'background.paper',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          py: 2
        }}
      >
        <Tooltip title="Expand Sidebar" placement="right">
          <IconButton onClick={onToggle} size="small">
            <MenuOpenIcon size={18} style={{ transform: 'rotate(180deg)' }} />
          </IconButton>
        </Tooltip>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        width,
        minWidth: width,
        flexShrink: 0,
        height: '100%',
        borderRight: '1px solid',
        borderColor: 'divider',
        bgcolor: 'background.paper',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h6" fontWeight="bold">Resources</Typography>
        <Tooltip title="Collapse Sidebar" placement="left">
          <IconButton onClick={onToggle} size="small">
            <MenuOpenIcon size={18} />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Content */}
      <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
        {/* Import Source Area */}
        <Box sx={{ mb: 3 }}>
          <ImportSourceDropzone
            onClick={() => setImportDialogOpen(true)}
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            isDragging={isDragging}
          />
        </Box>

        {/* File List */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, cursor: 'pointer' }} onClick={() => setFilesExpanded(!filesExpanded)}>
          <ExpandMoreIcon size="sm" style={{ transform: filesExpanded ? 'rotate(0deg)' : 'rotate(-90deg)', transition: 'transform 0.2s' }} />
          <Typography variant="subtitle2" color="text.secondary" sx={{ ml: 1 }}>RECENT UPLOADS</Typography>
        </Box>

        <Collapse in={filesExpanded}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {/* Uploading Card */}
            {isUploading && (
              <Box
                sx={{
                  p: 2,
                  borderRadius: 3,
                  border: '1px solid',
                  borderColor: '#E5E7EB', // Gray-200
                  bgcolor: '#F9FAFB', // Gray-50
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                }}
              >
                <Box sx={{
                  width: 48,
                  height: 48,
                  borderRadius: 2,
                  bgcolor: '#E5E7EB', // Gray-200
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  <UploadFileIcon size="lg" sx={{ color: '#6B7280' }} /> {/* Gray-500 */}
                </Box>

                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <SkeletonBar width="80%" height={20} sx={{ mb: 1, bgcolor: 'rgba(0, 0, 0, 0.08)' }} />
                  <SkeletonBar width="50%" height={16} sx={{ bgcolor: 'rgba(0, 0, 0, 0.04)' }} />
                </Box>

                <CircularProgress
                  size={20}
                  thickness={5}
                  sx={{
                    color: '#6366F1', // Indigo-500
                    '& .MuiCircularProgress-circle': { strokeLinecap: 'round' }
                  }}
                />
              </Box>
            )}

            {/* Document Cards */}
            {documents.map(doc => (
              <DocumentPreviewCard
                key={doc.id}
                document={doc}
                isActive={activeDocumentId === doc.id}
                isDeleting={deletingIds.has(doc.id)}
                onSelect={() => {
                  setActiveDocumentId(doc.id);
                  if (doc.filename.toLowerCase().endsWith('.pdf')) {
                    openDocumentPreview(doc.id);
                  }
                }}
                onDelete={(e) => handleDeleteDocument(doc.id, e)}
              />
            ))}

            {documents.length === 0 && !isUploading && (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                No documents yet. Import one to get started.
              </Typography>
            )}
          </Box>
        </Collapse>
      </Box>

      {/* Import Dialog */}
      <ImportSourceDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        onFileSelect={handleFileUpload}
      />
    </Box>
  );
}


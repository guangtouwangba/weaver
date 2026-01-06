'use client';

import React, { useState } from 'react';
import { Collapse } from '@/components/ui/primitives';
import { Stack, Text, IconButton, Tooltip, Spinner } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
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
      return { icon: <DescriptionIcon size="lg" style={{ color: '#3B82F6' }} />, bg: '#EFF6FF' }; // Blue-500, Blue-50
    case 'csv':
    case 'xlsx':
    case 'xls':
      return { icon: <DescriptionIcon size="lg" style={{ color: '#10B981' }} />, bg: '#ECFDF5' }; // Emerald-500, Emerald-50
    default:
      return { icon: <DescriptionIcon size="lg" style={{ color: '#6B7280' }} />, bg: '#F3F4F6' }; // Gray-500, Gray-100
  }
};

// Reusable Skeleton Component
const SkeletonBar = ({ width, height = 16, style = {} }: { width: string | number, height?: number, style?: React.CSSProperties }) => (
  <div
    style={{
      width: typeof width === 'number' ? `${width}px` : width,
      height,
      backgroundColor: 'rgba(0,0,0,0.06)',
      borderRadius: radii.sm,
      animation: 'pulse 1.5s ease-in-out infinite',
      ...style
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
      <Stack
        direction="column"
        align="center"
        style={{
          width: 48,
          height: '100%',
          flexShrink: 0,
          borderRight: `1px solid ${colors.border.default}`,
          backgroundColor: colors.background.paper,
          paddingTop: 16,
          paddingBottom: 16,
        }}
      >
        <Tooltip title="Expand Sidebar" placement="right">
          <IconButton size="sm" onClick={onToggle}>
            <MenuOpenIcon size={18} style={{ transform: 'rotate(180deg)' }} />
          </IconButton>
        </Tooltip>
      </Stack>
    );
  }

  return (
    <Stack
      direction="column"
      style={{
        width,
        minWidth: width,
        flexShrink: 0,
        height: '100%',
        borderRight: `1px solid ${colors.border.default}`,
        backgroundColor: colors.background.paper,
      }}
    >
      {/* Header */}
      <Stack
        direction="row"
        align="center"
        justify="between"
        style={{
          padding: 16,
          borderBottom: `1px solid ${colors.border.default}`,
        }}
      >
        <Text variant="h6">Resources</Text>
        <Tooltip title="Collapse Sidebar" placement="left">
          <IconButton size="sm" onClick={onToggle}>
            <MenuOpenIcon size={18} />
          </IconButton>
        </Tooltip>
      </Stack>

      {/* Content */}
      <div style={{ flexGrow: 1, overflowY: 'auto', padding: 16 }}>
        {/* Import Source Area */}
        <div style={{ marginBottom: 24 }}>
          <ImportSourceDropzone
            onClick={() => setImportDialogOpen(true)}
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            isDragging={isDragging}
          />
        </div>

        {/* File List */}
        <Stack
          direction="row"
          align="center"
          style={{ marginBottom: 16, cursor: 'pointer' }}
          onClick={() => setFilesExpanded(!filesExpanded)}
        >
          <ExpandMoreIcon size="sm" style={{ transform: filesExpanded ? 'rotate(0deg)' : 'rotate(-90deg)', transition: 'transform 0.2s' }} />
          <Text variant="overline" color="secondary" style={{ marginLeft: 8 }}>RECENT UPLOADS</Text>
        </Stack>

        <Collapse in={filesExpanded}>
          <Stack direction="column" gap={1}>
            {/* Uploading Card */}
            {isUploading && (
              <Stack
                direction="row"
                align="center"
                gap={2}
                style={{
                  padding: 16,
                  borderRadius: `${radii.lg}px`,
                  border: `1px solid ${colors.neutral[200]}`,
                  backgroundColor: colors.neutral[50],
                }}
              >
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: radii.md,
                    backgroundColor: colors.neutral[200],
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <UploadFileIcon size="lg" style={{ color: colors.neutral[500] }} />
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <SkeletonBar width="80%" height={20} style={{ marginBottom: 8, backgroundColor: 'rgba(0, 0, 0, 0.08)' }} />
                  <SkeletonBar width="50%" height={16} style={{ backgroundColor: 'rgba(0, 0, 0, 0.04)' }} />
                </div>

                <Spinner size="sm" style={{ color: colors.primary[500] }} />
              </Stack>
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
              <Text variant="bodySmall" color="secondary" style={{ textAlign: 'center', padding: '16px 0' }}>
                No documents yet. Import one to get started.
              </Text>
            )}
          </Stack>
        </Collapse>
      </div>

      {/* Import Dialog */}
      <ImportSourceDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        onFileSelect={handleFileUpload}
      />

      <style>{`
        @keyframes pulse {
          0% { opacity: 0.6; }
          50% { opacity: 1; }
          100% { opacity: 0.6; }
        }
      `}</style>
    </Stack>
  );
}

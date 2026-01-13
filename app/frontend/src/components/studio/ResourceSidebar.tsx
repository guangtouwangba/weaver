'use client';

import React, { useState } from 'react';
import { Collapse } from '@/components/ui/primitives';
import { Stack, Text, IconButton, Tooltip, Spinner, ConfirmDialog } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import {
  DescriptionIcon,
  ExpandMoreIcon,
  DeleteIcon,
  CloudUploadIcon,
  UploadFileIcon,
  MenuOpenIcon,
  CloseIcon,
  ErrorIcon,
} from '@/components/ui/icons';
import { useStudio } from '@/contexts/StudioContext';
import { documentsApi, ProjectDocument, urlApi, UrlContent } from '@/lib/api';
import { PlatformIcon, detectPlatform, type Platform } from '@/lib/platform-icons';
import { useDocumentWebSocket } from '@/hooks/useDocumentWebSocket';
import ImportSourceDialog from '@/components/dialogs/ImportSourceDialog';
import ImportSourceDropzone from '@/components/studio/ImportSourceDropzone';
import DocumentPreviewCard from '@/components/studio/DocumentPreviewCard';
// YouTubePlayerModal is now global in StudioPage
import WebPageReaderModal from '@/components/studio/WebPageReaderModal';

interface ResourceSidebarProps {
  width?: number;
  collapsed?: boolean;
  onToggle?: () => void;
}

// Type for pending URL extraction
interface PendingUrlExtraction {
  id: string;
  url: string;
  platform: Platform;
  status: 'extracting' | 'completed' | 'failed';
  title?: string;
  thumbnailUrl?: string;
  errorMessage?: string;
  content?: UrlContent;
  metadata?: {
    videoId?: string;
    duration?: number;
    channelName?: string;
    channelAvatar?: string;
    viewCount?: string;
    publishedAt?: string;
  };
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
  const {
    projectId,
    documents,
    setDocuments,
    activeDocumentId,
    setActiveDocumentId,
    openDocumentPreview,
    urlContents,
    addUrlContent,
    removeUrlContent,
    deleteDocument,
    playVideo, // <--- Add this
  } = useStudio();

  // Subscribe to document status updates
  useDocumentWebSocket({
    projectId,
    onDocumentStatusChange: (event) => {
      // Logic for updating document status if needed
    }
  });

  // UI State
  const [filesExpanded, setFilesExpanded] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadFileName, setUploadFileName] = useState<string | null>(null);
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());

  // Delete confirmation state
  const [confirmDeleteDoc, setConfirmDeleteDoc] = useState<string | null>(null);
  const [confirmDeleteUrl, setConfirmDeleteUrl] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // URL extraction state
  const [pendingUrlExtractions, setPendingUrlExtractions] = useState<PendingUrlExtraction[]>([]);

  // Removed local youtubeModal state

  // Web Page Reader Modal state
  const [webPageReader, setWebPageReader] = useState<{
    open: boolean;
    title: string;
    content: string;
    sourceUrl?: string;
  } | null>(null);

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

  const handleDeleteDocument = async (docId: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setIsDeleting(true);
    setDeletingIds(prev => new Set(prev).add(docId));

    try {
      await deleteDocument(docId);
      setConfirmDeleteDoc(null);
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setIsDeleting(false);
      setDeletingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(docId);
        return newSet;
      });
    }
  };

  // Handle URL import
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
      // Pass projectId to persist the URL content with this project
      const pendingContent = await urlApi.extract(url, { projectId });

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

      // Add to persistent URL contents in context (so it survives page refresh)
      addUrlContent(completedContent);

      // Remove from pending extractions (now it's in urlContents)
      setPendingUrlExtractions(prev => prev.filter(p => p.id !== extractionId));
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

  // Remove URL extraction from list (pending or persisted)
  const handleRemoveUrlExtraction = async (id: string, isPersisted: boolean = false) => {
    if (isPersisted) {
      setIsDeleting(true);
      try {
        await removeUrlContent(id);
        setConfirmDeleteUrl(null);
      } catch (error) {
        console.error('Failed to delete URL content:', error);
      } finally {
        setIsDeleting(false);
      }
    } else {
      setPendingUrlExtractions(prev => prev.filter(p => p.id !== id));
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

            {/* URL Extraction Cards */}
            {pendingUrlExtractions.map((extraction) => (
              <Stack
                key={extraction.id}
                direction="row"
                align="center"
                gap={2}
                draggable={extraction.status === 'completed'}
                onDragStart={(e: React.DragEvent) => {
                  if (extraction.status !== 'completed') return;
                  const dragData = {
                    type: 'url',
                    id: extraction.id,
                    platform: extraction.platform,
                    contentType: extraction.platform === 'youtube' || extraction.platform === 'bilibili' || extraction.platform === 'douyin' ? 'video' : 'article',
                    title: extraction.title,
                    url: extraction.url,
                    content: extraction.content?.content,
                    status: extraction.status,
                    thumbnailUrl: extraction.thumbnailUrl,
                    metadata: extraction.metadata,
                    videoId: extraction.metadata?.videoId,
                    duration: extraction.metadata?.duration,
                    channelName: extraction.metadata?.channelName,
                    viewCount: extraction.metadata?.viewCount,
                    publishedAt: extraction.metadata?.publishedAt,
                  };
                  e.dataTransfer.setData('application/json', JSON.stringify(dragData));
                  e.dataTransfer.effectAllowed = 'copy';
                }}
                onClick={() => {
                  // Open YouTube player modal for completed YouTube extractions
                  if (extraction.status === 'completed' && extraction.platform === 'youtube' && extraction.metadata?.videoId) {
                    playVideo(extraction.metadata.videoId, {
                      title: extraction.title || 'YouTube Video',
                      channelName: extraction.metadata.channelName,
                      viewCount: extraction.metadata.viewCount,
                      publishedAt: extraction.metadata.publishedAt,
                      sourceUrl: extraction.url,
                    });
                  } else if (extraction.status === 'completed' && extraction.platform === 'web' && extraction.content) {
                    // For web pages, open the reader modal preview
                    setWebPageReader({
                      open: true,
                      title: extraction.title || 'Web Page',
                      content: extraction.content?.content || '',
                      sourceUrl: extraction.url,
                    });
                  }
                }}
                style={{
                  padding: 16,
                  borderRadius: `${radii.lg}px`,
                  border: `1px solid ${extraction.status === 'failed' ? colors.error[200] : colors.neutral[200]}`,
                  backgroundColor: extraction.status === 'failed' ? colors.error[50] : colors.neutral[50],
                  cursor: extraction.status === 'completed' ? (extraction.platform === 'youtube' ? 'pointer' : 'grab') : 'default',
                }}
              >
                {/* Platform Icon */}
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: radii.md,
                    backgroundColor: extraction.thumbnailUrl ? 'transparent' : colors.neutral[200],
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    overflow: 'hidden',
                  }}
                >
                  {extraction.thumbnailUrl ? (
                    <img
                      src={extraction.thumbnailUrl}
                      alt={extraction.title || 'Thumbnail'}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <PlatformIcon platform={extraction.platform} size={24} />
                  )}
                </div>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  {extraction.status === 'extracting' ? (
                    <>
                      <SkeletonBar width="80%" height={20} style={{ marginBottom: 8, backgroundColor: 'rgba(0, 0, 0, 0.08)' }} />
                      <SkeletonBar width="50%" height={16} style={{ backgroundColor: 'rgba(0, 0, 0, 0.04)' }} />
                    </>
                  ) : extraction.status === 'failed' ? (
                    <>
                      <Text variant="bodySmall" style={{ fontWeight: 500, color: colors.error[700] }}>
                        Failed to extract
                      </Text>
                      <Text variant="caption" color="secondary" style={{ display: 'block', marginTop: 4 }}>
                        {extraction.errorMessage || 'Unknown error'}
                      </Text>
                    </>
                  ) : (
                    <>
                      <Text variant="bodySmall" style={{ fontWeight: 500 }}>
                        {extraction.title || extraction.url}
                      </Text>
                      <Text variant="caption" color="secondary" style={{ display: 'block', marginTop: 4 }}>
                        {extraction.platform.charAt(0).toUpperCase() + extraction.platform.slice(1)}
                      </Text>
                    </>
                  )}
                </div>

                {/* Status/Action */}
                {extraction.status === 'extracting' ? (
                  <Spinner size="sm" style={{ color: colors.primary[500] }} />
                ) : extraction.status === 'failed' ? (
                  <IconButton size="sm" onClick={() => handleRemoveUrlExtraction(extraction.id)}>
                    <CloseIcon size={16} />
                  </IconButton>
                ) : null}
              </Stack>
            ))}

            {/* Persisted URL Content Cards (loaded from backend) */}
            {urlContents.map((urlContent) => {
              const platform = urlContent.platform as Platform;
              const metadata = urlContent.meta_data as {
                video_id?: string;
                duration?: number;
                channel_name?: string;
                view_count?: string;
                published_at?: string;
              } | undefined;

              return (
                <Stack
                  key={urlContent.id}
                  direction="row"
                  align="center"
                  gap={2}
                  draggable
                  onDragStart={(e: React.DragEvent) => {
                    const dragData = {
                      type: 'url',
                      id: urlContent.id,
                      platform: urlContent.platform,
                      contentType: urlContent.content_type,
                      title: urlContent.title,
                      url: urlContent.url,
                      content: urlContent.content,
                      status: urlContent.status,
                      thumbnailUrl: urlContent.thumbnail_url,
                      metadata: {
                        videoId: metadata?.video_id,
                        duration: metadata?.duration,
                        channelName: metadata?.channel_name,
                        viewCount: metadata?.view_count,
                        publishedAt: metadata?.published_at,
                      },
                      videoId: metadata?.video_id,
                      duration: metadata?.duration,
                      channelName: metadata?.channel_name,
                      viewCount: metadata?.view_count,
                      publishedAt: metadata?.published_at,
                    };
                    e.dataTransfer.setData('application/json', JSON.stringify(dragData));
                    e.dataTransfer.effectAllowed = 'copy';
                  }}
                  onClick={() => {
                    // Open YouTube player modal for YouTube content
                    if (platform === 'youtube' && metadata?.video_id) {
                      playVideo(metadata.video_id, {
                        title: urlContent.title || 'YouTube Video',
                        channelName: metadata.channel_name,
                        viewCount: metadata.view_count,
                        publishedAt: metadata.published_at,
                        sourceUrl: urlContent.url,
                      });
                    } else if (platform === 'web') {
                      // Open Web Reader modal for web content
                      setWebPageReader({
                        open: true,
                        title: urlContent.title || 'Web Page',
                        content: urlContent.content || '',
                        sourceUrl: urlContent.url,
                      });
                    }
                  }}
                  style={{
                    padding: 16,
                    borderRadius: `${radii.lg}px`,
                    border: `1px solid ${colors.neutral[200]}`,
                    backgroundColor: colors.neutral[50],
                    cursor: platform === 'youtube' ? 'pointer' : 'grab',
                    position: 'relative',
                  }}
                >
                  {/* Platform Icon / Thumbnail */}
                  <div
                    style={{
                      width: 48,
                      height: 48,
                      borderRadius: radii.md,
                      backgroundColor: urlContent.thumbnail_url ? 'transparent' : colors.neutral[200],
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      overflow: 'hidden',
                    }}
                  >
                    {urlContent.thumbnail_url ? (
                      <img
                        src={urlContent.thumbnail_url}
                        alt={urlContent.title || 'Thumbnail'}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <PlatformIcon platform={platform} size={24} />
                    )}
                  </div>

                  {/* Content */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <Text variant="bodySmall" style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {urlContent.title || urlContent.url}
                    </Text>
                    <Text variant="caption" color="secondary" style={{ display: 'block', marginTop: 4 }}>
                      {urlContent.platform.charAt(0).toUpperCase() + urlContent.platform.slice(1)}
                    </Text>
                  </div>

                  {/* Delete Button */}
                  <IconButton
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setConfirmDeleteUrl(urlContent.id);
                    }}
                    style={{ opacity: 0.6 }}
                  >
                    <DeleteIcon size={16} />
                  </IconButton>
                </Stack>
              );
            })}

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
                onDelete={(e) => {
                  e.stopPropagation();
                  setConfirmDeleteDoc(doc.id);
                }}
              />
            ))}

            {documents.length === 0 && urlContents.length === 0 && pendingUrlExtractions.length === 0 && !isUploading && (
              <Text variant="bodySmall" color="secondary" style={{ textAlign: 'center', padding: '16px 0' }}>
                No documents yet. Import one to get started.
              </Text>
            )}
          </Stack>
        </Collapse>
      </div>

      <ImportSourceDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        onFileSelect={handleFileUpload}
        onUrlImport={handleUrlImport}
      />

      {/* YouTube Player Modal - Now Global */}

      {/* Web Page Reader Modal */}
      {webPageReader && (
        <WebPageReaderModal
          open={webPageReader.open}
          onClose={() => setWebPageReader(null)}
          title={webPageReader.title}
          content={webPageReader.content}
          sourceUrl={webPageReader.sourceUrl}
          domain={webPageReader.sourceUrl ? new URL(webPageReader.sourceUrl).hostname : undefined}
        />
      )}

      {/* Confirm Delete Document Dialog */}
      <ConfirmDialog
        open={confirmDeleteDoc !== null}
        onClose={() => setConfirmDeleteDoc(null)}
        onConfirm={() => { if (confirmDeleteDoc) handleDeleteDocument(confirmDeleteDoc); }}
        title="Delete Document"
        message={`Are you sure you want to delete "${documents.find(d => d.id === confirmDeleteDoc)?.filename}"? This action cannot be undone.`}
        confirmLabel="Delete"
        isDanger={true}
        loading={isDeleting}
      />

      {/* Confirm Delete URL Dialog */}
      <ConfirmDialog
        open={confirmDeleteUrl !== null}
        onClose={() => setConfirmDeleteUrl(null)}
        onConfirm={() => { if (confirmDeleteUrl) handleRemoveUrlExtraction(confirmDeleteUrl, true); }}
        title="Remove Link"
        message={`Are you sure you want to remove "${urlContents.find(u => u.id === confirmDeleteUrl)?.title || 'this link'}"? This action cannot be undone.`}
        confirmLabel="Remove"
        isDanger={true}
        loading={isDeleting}
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

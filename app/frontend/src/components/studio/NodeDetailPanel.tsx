'use client';

/**
 * Node Detail Panel
 * A slide-over panel to view and manage node details on the canvas.
 * Follows the "Canvas is Workbench, Panel is Context" principle.
 */

import { useState } from 'react';
import { Chip, Divider, TextField, Button as MuiButton } from '@mui/material';
import { Surface, Stack, Text, IconButton, Button } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import {
  CloseIcon,
  EditIcon,
  DeleteIcon,
  DescriptionIcon,
  HelpOutlineIcon,
  CheckIcon,
  LinkIcon,
  OpenInNewIcon,
  ChatBubbleOutlineIcon,
  LightbulbIcon,
  MenuBookIcon,
  PublicIcon,
} from '@/components/ui/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CanvasNode, SourceRef } from '@/lib/api';

interface NodeDetailPanelProps {
  node: CanvasNode | null;
  onClose: () => void;
  onDelete?: (nodeId: string) => void;
  onEdit?: (nodeId: string, updates: Partial<CanvasNode>) => void;
  onOpenSourceRef?: (ref: SourceRef) => void;  // Unified source navigation
  onOpenSource?: (sourceId: string, pageNumber?: number) => void;  // Legacy: PDF-specific
}

// Get icon and color based on node type
const getNodeTypeInfo = (node: CanvasNode) => {
  const typeMap: Record<string, { icon: React.ReactNode; label: string; color: string; bgColor: string }> = {
    // Source Node Types
    source_pdf: {
      icon: <MenuBookIcon size={20} />,
      label: 'PDF Document',
      color: '#DC2626',
      bgColor: '#FEF2F2',
    },
    source_markdown: {
      icon: <DescriptionIcon size={20} />,
      label: 'Markdown',
      color: '#2563EB',
      bgColor: '#EFF6FF',
    },
    source_web: {
      icon: <PublicIcon size={20} />,
      label: 'Web Page',
      color: '#059669',
      bgColor: '#ECFDF5',
    },
    source_text: {
      icon: <DescriptionIcon size={20} />,
      label: 'Text File',
      color: '#6B7280',
      bgColor: '#F9FAFB',
    },
    // Thinking Path Node Types
    question: {
      icon: <HelpOutlineIcon size={20} />,
      label: 'Question',
      color: '#3B82F6',
      bgColor: '#EFF6FF',
    },
    answer: {
      icon: <ChatBubbleOutlineIcon size={20} />,
      label: 'Answer',
      color: '#10B981',
      bgColor: '#F0FDF4',
    },
    insight: {
      icon: <LightbulbIcon size={20} />,
      label: 'Insight',
      color: '#F59E0B',
      bgColor: '#FFFBEB',
    },
    conclusion: {
      icon: <CheckIcon size={20} />,
      label: 'Conclusion',
      color: '#8B5CF6',
      bgColor: '#F5F3FF',
    },
    // Default
    card: {
      icon: <DescriptionIcon size={20} />,
      label: 'Note',
      color: '#6B7280',
      bgColor: '#F9FAFB',
    },
    knowledge: {
      icon: <DescriptionIcon size={20} />,
      label: 'Knowledge',
      color: '#6B7280',
      bgColor: '#F9FAFB',
    },
  };

  // Handle source nodes with specific file types
  if (node.subType === 'source' && node.fileMetadata?.fileType) {
    const sourceKey = `source_${node.fileMetadata.fileType}`;
    if (typeMap[sourceKey]) {
      return typeMap[sourceKey];
    }
  }

  return typeMap[node.type] || typeMap.card;
};

export default function NodeDetailPanel({
  node,
  onClose,
  onDelete,
  onEdit,
  onOpenSourceRef,
  onOpenSource,
}: NodeDetailPanelProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');

  if (!node) return null;

  const typeInfo = getNodeTypeInfo(node);
  const isSourceNode = node.subType === 'source';
  const hasSourceRef = !isSourceNode && (node.sourceRef || node.sourceId);

  const handleStartEdit = () => {
    setEditTitle(node.title);
    setEditContent(node.content);
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    if (onEdit) {
      onEdit(node.id, {
        title: editTitle,
        content: editContent,
      });
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditTitle('');
    setEditContent('');
  };

  const handleDelete = () => {
    if (onDelete) {
      onDelete(node.id);
      onClose();
    }
  };

  const handleOpenSource = () => {
    // Prefer sourceRef if available, otherwise fall back to legacy sourceId/sourcePage
    if (node.sourceRef && onOpenSourceRef) {
      onOpenSourceRef(node.sourceRef);
    } else if (node.sourceId) {
      // Construct PDF SourceRef from legacy fields
      if (onOpenSourceRef) {
        onOpenSourceRef({ type: 'pdf', documentId: node.sourceId, page: node.sourcePage || 1 });
      } else if (onOpenSource) {
        onOpenSource(node.sourceId, node.sourcePage);
      }
    }
  };

  return (
    <Stack
      direction="column"
      sx={{
        position: 'absolute',
        right: 0,
        top: 0,
        bottom: 0,
        width: 400,
        bgcolor: colors.background.paper,
        borderLeft: `1px solid ${colors.border.default}`,
        zIndex: 1200,
        boxShadow: shadows.xl,
        animation: 'slideInRight 0.2s ease-out',
        '@keyframes slideInRight': {
          from: {
            transform: 'translateX(100%)',
            opacity: 0,
          },
          to: {
            transform: 'translateX(0)',
            opacity: 1,
          },
        },
      }}
    >
      {/* Header */}
      <Stack
        direction="row"
        align="start"
        gap={2}
        sx={{
          p: 2,
          borderBottom: `1px solid ${colors.border.default}`,
          bgcolor: typeInfo.bgColor,
        }}
      >
        <div
          style={{
            marginTop: 4,
            color: typeInfo.color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {typeInfo.icon}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <Text
            variant="overline"
            sx={{
              color: typeInfo.color,
              fontWeight: 'bold',
              letterSpacing: '0.5px',
            }}
          >
            {typeInfo.label}
          </Text>
          {isEditing ? (
            <TextField
              fullWidth
              size="small"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              sx={{ mt: 0.5 }}
              autoFocus
            />
          ) : (
            <Text
              variant="h6"
              sx={{
                lineHeight: 1.3,
                mt: 0.5,
                wordBreak: 'break-word',
              }}
            >
              {node.title}
            </Text>
          )}
        </div>
        <IconButton size="sm" variant="ghost" onClick={onClose} sx={{ flexShrink: 0 }}>
          <CloseIcon size={18} />
        </IconButton>
      </Stack>

      {/* Content (Scrollable) */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
        {isEditing ? (
          <TextField
            fullWidth
            multiline
            minRows={8}
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            placeholder="Enter content..."
            sx={{
              '& .MuiInputBase-root': {
                fontSize: '0.95rem',
                lineHeight: 1.7,
              },
            }}
          />
        ) : (
          <div
            style={{}}
            className="markdown-content"
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {node.content || '*No content*'}
            </ReactMarkdown>
          </div>
        )}

        {/* Tags */}
        {node.tags && node.tags.length > 0 && (
          <div style={{ marginTop: 24 }}>
            <Text
              variant="caption"
              color="secondary"
              sx={{ fontWeight: 600, mb: 1, display: 'block' }}
            >
              Tags
            </Text>
            <Stack direction="row" gap={0} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
              {node.tags.map((tag) => (
                <Chip
                  key={tag}
                  label={tag}
                  size="small"
                  sx={{
                    height: 24,
                    fontSize: '0.75rem',
                    bgcolor: colors.neutral[100],
                  }}
                />
              ))}
            </Stack>
          </div>
        )}

        {/* Metadata */}
        {(node.createdAt || node.viewType || isSourceNode) && (
          <div style={{ marginTop: 24 }}>
            <Text
              variant="caption"
              color="secondary"
              sx={{ fontWeight: 600, mb: 1, display: 'block' }}
            >
              Properties
            </Text>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 8,
                fontSize: '0.8rem',
              }}
            >
              {node.viewType && (
                <>
                  <Text variant="caption" color="secondary">
                    View:
                  </Text>
                  <Text variant="caption">
                    {node.viewType === 'thinking' ? 'Thinking Path' : 'Free Canvas'}
                  </Text>
                </>
              )}
              {isSourceNode && node.fileMetadata?.pageCount && (
                <>
                  <Text variant="caption" color="secondary">
                    Pages:
                  </Text>
                  <Text variant="caption">
                    {node.fileMetadata.pageCount}
                  </Text>
                </>
              )}
              {node.createdAt && (
                <>
                  <Text variant="caption" color="secondary">
                    Created:
                  </Text>
                  <Text variant="caption">
                    {new Date(node.createdAt).toLocaleDateString()}
                  </Text>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div
        style={{
          padding: 16,
          backgroundColor: colors.neutral[50],
          borderTop: `1px solid ${colors.border.default}`,
        }}
      >
        {/* Source Reference */}
        {hasSourceRef && (
          <MuiButton
            startIcon={<OpenInNewIcon size={14} />}
            fullWidth
            onClick={handleOpenSource}
            sx={{
              mb: 2,
              justifyContent: 'flex-start',
              textTransform: 'none',
              bgcolor: 'white',
              border: `1px solid ${colors.border.default}`,
              color: colors.text.primary,
              '&:hover': {
                bgcolor: colors.neutral[50],
                borderColor: colors.primary[500],
              },
            }}
          >
            View Source {node.sourcePage ? `(Page ${node.sourcePage})` : ''}
          </MuiButton>
        )}

        {/* Source Node: Open Document */}
        {isSourceNode && node.sourceId && (
          <MuiButton
            startIcon={<OpenInNewIcon size={14} />}
            fullWidth
            onClick={handleOpenSource}
            sx={{
              mb: 2,
              justifyContent: 'flex-start',
              textTransform: 'none',
              bgcolor: 'white',
              border: `1px solid ${colors.border.default}`,
              color: colors.text.primary,
              '&:hover': {
                bgcolor: colors.neutral[50],
                borderColor: colors.primary[500],
              },
            }}
          >
            Open Document
          </MuiButton>
        )}

        {/* Linked Messages */}
        {node.messageIds && node.messageIds.length > 0 && (
          <div
            style={{
              marginBottom: 16,
              padding: 12,
              backgroundColor: 'white',
              border: `1px solid ${colors.border.default}`,
              borderRadius: radii.sm,
            }}
          >
            <Stack direction="row" align="center" gap={1} sx={{ mb: 0.5 }}>
              <LinkIcon size={12} />
              <Text variant="caption" sx={{ fontWeight: 600 }}>
                Linked to {node.messageIds.length} chat message(s)
              </Text>
            </Stack>
          </div>
        )}

        {/* Action Buttons */}
        <Divider sx={{ my: 1.5 }} />
        <Stack direction="row" gap={1} justify="end">
          {isEditing ? (
            <>
              <MuiButton size="small" onClick={handleCancelEdit}>
                Cancel
              </MuiButton>
              <MuiButton
                size="small"
                variant="contained"
                onClick={handleSaveEdit}
                startIcon={<CheckIcon size={14} />}
              >
                Save
              </MuiButton>
            </>
          ) : (
            <>
              <MuiButton
                size="small"
                startIcon={<EditIcon size={14} />}
                onClick={handleStartEdit}
              >
                Edit
              </MuiButton>
              <MuiButton
                size="small"
                color="error"
                startIcon={<DeleteIcon size={14} />}
                onClick={handleDelete}
              >
                Delete
              </MuiButton>
            </>
          )}
        </Stack>
      </div>

      <style>{`
        .markdown-content p { margin-bottom: 12px; line-height: 1.7; }
        .markdown-content ul, .markdown-content ol { padding-left: 16px; margin-bottom: 12px; }
        .markdown-content li { margin-bottom: 4px; }
        .markdown-content code {
          background-color: ${colors.neutral[100]};
          padding: 2px 4px;
          border-radius: 4px;
          font-size: 0.85em;
        }
        .markdown-content pre {
          background-color: ${colors.neutral[100]};
          padding: 12px;
          border-radius: 8px;
          overflow: auto;
          font-size: 0.85em;
        }
        .markdown-content blockquote {
          border-left: 3px solid ${colors.neutral[300]};
          padding-left: 16px;
          padding-top: 4px;
          padding-bottom: 4px;
          margin: 8px 0;
          color: ${colors.text.secondary};
          font-style: italic;
        }
      `}</style>
    </Stack>
  );
}

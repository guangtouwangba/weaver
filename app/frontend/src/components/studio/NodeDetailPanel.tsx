'use client';

/**
 * Node Detail Panel
 * A slide-over panel to view and manage node details on the canvas.
 * Follows the "Canvas is Workbench, Panel is Context" principle.
 */

import { useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Chip,
  Button,
  Divider,
  TextField,
  Stack,
} from '@mui/material';
import {
  CloseIcon,
  EditIcon,
  DeleteIcon,
  DescriptionIcon,
  HelpOutlineIcon,
  CheckIcon,
  LinkIcon,
} from '@/components/ui/icons';
import OpenInNewMui from '@mui/icons-material/OpenInNew';
import ChatBubbleOutlineMui from '@mui/icons-material/ChatBubbleOutline';
import TipsAndUpdatesMui from '@mui/icons-material/TipsAndUpdates';
import MenuBookMui from '@mui/icons-material/MenuBook';
import PublicMui from '@mui/icons-material/Public';
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
      icon: <MenuBookMui sx={{ fontSize: 20 }} />,
      label: 'PDF Document',
      color: '#DC2626',
      bgColor: '#FEF2F2',
    },
    source_markdown: {
      icon: <DescriptionMui sx={{ fontSize: 20 }} />,
      label: 'Markdown',
      color: '#2563EB',
      bgColor: '#EFF6FF',
    },
    source_web: {
      icon: <LanguageMui sx={{ fontSize: 20 }} />,
      label: 'Web Page',
      color: '#059669',
      bgColor: '#ECFDF5',
    },
    source_text: {
      icon: <DescriptionMui sx={{ fontSize: 20 }} />,
      label: 'Text File',
      color: '#6B7280',
      bgColor: '#F9FAFB',
    },
    // Thinking Path Node Types
    question: {
      icon: <HelpMui sx={{ fontSize: 20 }} />,
      label: 'Question',
      color: '#3B82F6',
      bgColor: '#EFF6FF',
    },
    answer: {
      icon: <CommentMui sx={{ fontSize: 20 }} />,
      label: 'Answer',
      color: '#10B981',
      bgColor: '#F0FDF4',
    },
    insight: {
      icon: <LightbulbMui sx={{ fontSize: 20 }} />,
      label: 'Insight',
      color: '#F59E0B',
      bgColor: '#FFFBEB',
    },
    conclusion: {
      icon: <CheckMui sx={{ fontSize: 20 }} />,
      label: 'Conclusion',
      color: '#8B5CF6',
      bgColor: '#F5F3FF',
    },
    // Default
    card: {
      icon: <DescriptionMui sx={{ fontSize: 20 }} />,
      label: 'Note',
      color: '#6B7280',
      bgColor: '#F9FAFB',
    },
    knowledge: {
      icon: <DescriptionMui sx={{ fontSize: 20 }} />,
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
    <Box
      sx={{
        position: 'absolute',
        right: 0,
        top: 0,
        bottom: 0,
        width: 400,
        bgcolor: 'background.paper',
        borderLeft: '1px solid',
        borderColor: 'divider',
        zIndex: 1200,
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-4px 0 24px rgba(0,0,0,0.08)',
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
      <Box
        sx={{
          p: 2,
          borderBottom: '1px solid',
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'flex-start',
          gap: 2,
          bgcolor: typeInfo.bgColor,
        }}
      >
        <Box
          sx={{
            mt: 0.5,
            color: typeInfo.color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {typeInfo.icon}
        </Box>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography
            variant="caption"
            sx={{
              textTransform: 'uppercase',
              fontWeight: 'bold',
              color: typeInfo.color,
              letterSpacing: '0.5px',
            }}
          >
            {typeInfo.label}
          </Typography>
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
            <Typography
              variant="h6"
              sx={{
                lineHeight: 1.3,
                mt: 0.5,
                fontWeight: 600,
                wordBreak: 'break-word',
              }}
            >
              {node.title}
            </Typography>
          )}
        </Box>
        <IconButton onClick={onClose} size="small" sx={{ flexShrink: 0 }}>
          <CloseIcon size={18} />
        </IconButton>
      </Box>

      {/* Content (Scrollable) */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
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
          <Box
            sx={{
              '& p': { mb: 1.5, lineHeight: 1.7 },
              '& ul, & ol': { pl: 2, mb: 1.5 },
              '& li': { mb: 0.5 },
              '& code': {
                bgcolor: 'grey.100',
                px: 0.5,
                py: 0.25,
                borderRadius: 0.5,
                fontSize: '0.85em',
              },
              '& pre': {
                bgcolor: 'grey.100',
                p: 1.5,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.85em',
              },
              '& blockquote': {
                borderLeft: '3px solid',
                borderColor: 'grey.300',
                pl: 2,
                py: 0.5,
                my: 1,
                color: 'text.secondary',
                fontStyle: 'italic',
              },
            }}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {node.content || '*No content*'}
            </ReactMarkdown>
          </Box>
        )}

        {/* Tags */}
        {node.tags && node.tags.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, mb: 1, display: 'block' }}
            >
              Tags
            </Typography>
            <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
              {node.tags.map((tag) => (
                <Chip
                  key={tag}
                  label={tag}
                  size="small"
                  sx={{
                    height: 24,
                    fontSize: '0.75rem',
                    bgcolor: 'grey.100',
                  }}
                />
              ))}
            </Stack>
          </Box>
        )}

        {/* Metadata */}
        {(node.createdAt || node.viewType || isSourceNode) && (
          <Box sx={{ mt: 3 }}>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, mb: 1, display: 'block' }}
            >
              Properties
            </Typography>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 1,
                fontSize: '0.8rem',
              }}
            >
              {node.viewType && (
                <>
                  <Typography variant="caption" color="text.secondary">
                    View:
                  </Typography>
                  <Typography variant="caption">
                    {node.viewType === 'thinking' ? 'Thinking Path' : 'Free Canvas'}
                  </Typography>
                </>
              )}
              {isSourceNode && node.fileMetadata?.pageCount && (
                <>
                  <Typography variant="caption" color="text.secondary">
                    Pages:
                  </Typography>
                  <Typography variant="caption">
                    {node.fileMetadata.pageCount}
                  </Typography>
                </>
              )}
              {node.createdAt && (
                <>
                  <Typography variant="caption" color="text.secondary">
                    Created:
                  </Typography>
                  <Typography variant="caption">
                    {new Date(node.createdAt).toLocaleDateString()}
                  </Typography>
                </>
              )}
            </Box>
          </Box>
        )}
      </Box>

      {/* Footer */}
      <Box
        sx={{
          p: 2,
          bgcolor: 'grey.50',
          borderTop: '1px solid',
          borderColor: 'divider',
        }}
      >
        {/* Source Reference */}
        {hasSourceRef && (
          <Button
            startIcon={<OpenInNewIcon size={14} />}
            fullWidth
            onClick={handleOpenSource}
            sx={{
              mb: 2,
              justifyContent: 'flex-start',
              textTransform: 'none',
              bgcolor: 'white',
              border: '1px solid',
              borderColor: 'divider',
              color: 'text.primary',
              '&:hover': {
                bgcolor: 'grey.50',
                borderColor: 'primary.main',
              },
            }}
          >
            View Source {node.sourcePage ? `(Page ${node.sourcePage})` : ''}
          </Button>
        )}

        {/* Source Node: Open Document */}
        {isSourceNode && node.sourceId && (
          <Button
            startIcon={<OpenInNewIcon size={14} />}
            fullWidth
            onClick={handleOpenSource}
            sx={{
              mb: 2,
              justifyContent: 'flex-start',
              textTransform: 'none',
              bgcolor: 'white',
              border: '1px solid',
              borderColor: 'divider',
              color: 'text.primary',
              '&:hover': {
                bgcolor: 'grey.50',
                borderColor: 'primary.main',
              },
            }}
          >
            Open Document
          </Button>
        )}

        {/* Linked Messages */}
        {node.messageIds && node.messageIds.length > 0 && (
          <Box
            sx={{
              mb: 2,
              p: 1.5,
              bgcolor: 'white',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <LinkIcon size={12} />
              <Typography variant="caption" fontWeight={600}>
                Linked to {node.messageIds.length} chat message(s)
              </Typography>
            </Box>
          </Box>
        )}

        {/* Action Buttons */}
        <Divider sx={{ my: 1.5 }} />
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
          {isEditing ? (
            <>
              <Button size="small" onClick={handleCancelEdit}>
                Cancel
              </Button>
              <Button
                size="small"
                variant="contained"
                onClick={handleSaveEdit}
                startIcon={<Check size={14} />}
              >
                Save
              </Button>
            </>
          ) : (
            <>
              <Button
                size="small"
                startIcon={<EditIcon size={14} />}
                onClick={handleStartEdit}
              >
                Edit
              </Button>
              <Button
                size="small"
                color="error"
                startIcon={<DeleteIcon size={14} />}
                onClick={handleDelete}
              >
                Delete
              </Button>
            </>
          )}
        </Box>
      </Box>
    </Box>
  );
}

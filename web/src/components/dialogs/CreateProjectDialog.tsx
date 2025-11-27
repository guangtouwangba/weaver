'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Fade,
  Slide,
  IconButton,
  Chip,
  InputAdornment,
  Grid,
  Paper,
} from '@mui/material';
import { 
  X, Upload, FileText, Sparkles, FolderPlus, CheckCircle2, 
  Link as LinkIcon, Image as ImageIcon, File, Trash2, Plus,
  Loader2
} from 'lucide-react';
import { useRouter } from 'next/navigation';

interface CreateProjectDialogProps {
  open: boolean;
  onClose: () => void;
}

// AI Processing Steps
const PROCESSING_STEPS = [
  "Analyzing uploaded documents...",
  "Extracting key concepts...",
  "Generating vector embeddings...",
  "Weaving knowledge graph...",
  "Finalizing project..."
];

interface FileItem {
  file: File;
  preview?: string;
  type: 'file' | 'url';
  url?: string;
}

export default function CreateProjectDialog({ open, onClose }: CreateProjectDialogProps) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [projectName, setProjectName] = useState('');
  const [description, setDescription] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [items, setItems] = useState<FileItem[]>([]);
  const [dragCounter, setDragCounter] = useState(0);

  // Generate preview for files
  const generatePreview = useCallback((file: File): Promise<string | undefined> => {
    return new Promise((resolve) => {
      if (file.type === 'application/pdf') {
        // For PDF, we'll create a simple preview placeholder
        // In production, you'd use a PDF library to extract first page
        const reader = new FileReader();
        reader.onload = () => {
          // Create a canvas representation
          resolve(undefined); // Return undefined for now, we'll show icon instead
        };
        reader.readAsDataURL(file);
      } else {
        resolve(undefined);
      }
    });
  }, []);

  const handleClose = useCallback(() => {
    if (!isLoading && !isProcessing) {
      setProjectName('');
      setDescription('');
      setUrlInput('');
      setError(null);
      setItems([]);
      setDragCounter(0);
      setProcessingStep(0);
      setIsProcessing(false);
      onClose();
    }
  }, [isLoading, isProcessing, onClose]);

  // Effect for processing steps animation
  useEffect(() => {
    if (isProcessing) {
      const interval = setInterval(() => {
        setProcessingStep(prev => {
          if (prev < PROCESSING_STEPS.length - 1) {
            return prev + 1;
          }
          return prev;
        });
      }, 800); // Change step every 800ms

      return () => clearInterval(interval);
    }
  }, [isProcessing]);

  const handleCreate = useCallback(async () => {
    if (!projectName.trim()) {
      setError('Project name is required');
      return;
    }

    setIsLoading(true);
    setIsProcessing(true);
    setError(null);

    try {
      // Simulate quick API call for creation
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Generate a mock project ID
      const mockProjectId = `project-${Date.now()}`;
      
      // Mark as initializing in localStorage to trigger animation in Studio
      if (typeof window !== 'undefined') {
        localStorage.setItem(`project_initializing_${mockProjectId}`, 'true');
      }
      
      // Navigate to studio with the new project
      router.push(`/studio?projectId=${mockProjectId}`);
      
      // Close dialog after navigation starts
      // setTimeout(handleClose, 100);
    } catch (err: any) {
      setError(err.message || 'Failed to create project');
      setIsLoading(false);
      setIsProcessing(false);
    } 
  }, [projectName, description, router, handleClose]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.types.includes('Files')) {
      setIsDragging(true);
    }
  }, []);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter(prev => prev + 1);
    if (e.dataTransfer.types.includes('Files')) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter(prev => {
      const newCount = prev - 1;
      if (newCount === 0) {
        setIsDragging(false);
      }
      return newCount;
    });
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    setDragCounter(0);

    const files = Array.from(e.dataTransfer.files);
    const validFiles = files.filter(
      file => file.type === 'application/pdf' || 
              file.type.startsWith('text/') ||
              file.name.endsWith('.pdf') ||
              file.name.endsWith('.txt') ||
              file.name.endsWith('.md')
    );

    if (validFiles.length > 0) {
      const newItems: FileItem[] = validFiles.map(file => ({
        file,
        type: 'file' as const,
      }));
      setItems(prev => [...prev, ...newItems]);
      setError(null);
    } else if (files.length > 0) {
      setError('Please upload PDF, text, or markdown files only');
    }
  }, []);

  const handleRemoveItem = useCallback((index: number) => {
    setItems(prev => prev.filter((_, i) => i !== index));
  }, []);

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter(
      file => file.type === 'application/pdf' || 
              file.type.startsWith('text/') ||
              file.name.endsWith('.pdf') ||
              file.name.endsWith('.txt') ||
              file.name.endsWith('.md')
    );
    if (validFiles.length > 0) {
      const newItems: FileItem[] = validFiles.map(file => ({
        file,
        type: 'file' as const,
      }));
      setItems(prev => [...prev, ...newItems]);
      setError(null);
    } else if (files.length > 0) {
      setError('Please upload PDF, text, or markdown files only');
    }
    // Reset input so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const handleDropZoneClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const normalizeUrl = useCallback((url: string): string | null => {
    let normalized = url.trim();
    
    // Remove leading/trailing whitespace
    normalized = normalized.replace(/^\s+|\s+$/g, '');
    
    // If no protocol, try to add https://
    if (!/^https?:\/\//i.test(normalized)) {
      // Check if it looks like a domain (contains at least one dot and valid characters)
      if (/^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}/.test(normalized)) {
        normalized = `https://${normalized}`;
      } else {
        return null;
      }
    }
    
    // Validate the URL
    try {
      const urlObj = new URL(normalized);
      // Ensure it has a valid protocol
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        return null;
      }
      return normalized;
    } catch {
      return null;
    }
  }, []);

  const handleAddUrl = useCallback(() => {
    if (!urlInput.trim()) return;
    
    const normalizedUrl = normalizeUrl(urlInput);
    if (normalizedUrl) {
      setItems(prev => [...prev, { type: 'url' as const, url: normalizedUrl }]);
      setUrlInput('');
      setError(null);
    } else {
      setError('Please enter a valid URL (e.g., example.com or https://example.com)');
    }
  }, [urlInput, normalizeUrl]);

  const handleUrlKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddUrl();
    }
  }, [handleAddUrl]);

  // Keyboard shortcuts
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) {
        handleClose();
      } else if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && !isLoading && projectName.trim()) {
        e.preventDefault();
        handleCreate();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, isLoading, projectName, handleClose, handleCreate]);

  // Reset drag counter when dialog closes
  useEffect(() => {
    if (!open) {
      setDragCounter(0);
      setIsDragging(false);
    }
  }, [open]);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatUrlDisplay = (url: string): string => {
    try {
      const urlObj = new URL(url);
      // Return domain + path (truncated if too long)
      const domain = urlObj.hostname;
      const path = urlObj.pathname + urlObj.search;
      
      // If total length is reasonable, show domain + path
      const full = domain + path;
      if (full.length <= 40) {
        return full;
      }
      
      // Otherwise, show domain + truncated path
      if (path.length > 20) {
        return `${domain}${path.substring(0, 17)}...`;
      }
      return full;
    } catch {
      // Fallback: truncate the original URL
      return url.length > 40 ? `${url.substring(0, 37)}...` : url;
    }
  };

  const getUrlDomain = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname.replace(/^www\./, ''); // Remove www. prefix
    } catch {
      return url;
    }
  };

  const getFileIcon = (item: FileItem) => {
    if (item.type === 'url') {
      return <LinkIcon size={20} />;
    }
    const file = item.file;
    if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
      return <FileText size={20} />;
    }
    return <File size={20} />;
  };

  const getFileColor = (item: FileItem) => {
    if (item.type === 'url') {
      return '#3B82F6'; // Blue for links
    }
    const file = item.file;
    if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
      return '#EF4444'; // Red for PDF
    }
    return '#6B7280'; // Gray for text files
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      TransitionComponent={Fade}
      TransitionProps={{ timeout: 200 }}
      PaperProps={{
        sx: {
          borderRadius: 4,
          boxShadow: '0 24px 48px rgba(0,0,0,0.12), 0 8px 16px rgba(0,0,0,0.08)',
          overflow: 'hidden',
          border: '1px solid',
          borderColor: 'divider',
          maxHeight: '90vh',
        },
      }}
      slotProps={{
        backdrop: {
          sx: {
            backgroundColor: 'rgba(0, 0, 0, 0.4)',
            backdropFilter: 'blur(4px)',
          },
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 2.5,
          pt: 3,
          px: 3,
          borderBottom: isProcessing ? 'none' : '1px solid',
          borderColor: 'divider',
          background: isProcessing ? 'transparent' : 'linear-gradient(135deg, rgba(23,23,23,0.02) 0%, rgba(23,23,23,0.01) 100%)',
        }}
      >
        {!isProcessing && (
          <>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: 2,
                  bgcolor: 'primary.main',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                }}
              >
                <FolderPlus size={20} />
              </Box>
              <Typography variant="h6" fontWeight="600">
                Create New Project
              </Typography>
            </Box>
            <IconButton
              onClick={handleClose}
              disabled={isLoading}
              size="small"
              sx={{
                color: 'text.secondary',
                '&:hover': { 
                  bgcolor: 'action.hover',
                  color: 'text.primary',
                },
                transition: 'all 0.2s',
              }}
            >
              <X size={18} />
            </IconButton>
          </>
        )}
      </DialogTitle>

      <DialogContent sx={{ pt: 3, px: 3, pb: 2 }}>
          <>
            {error && (
              <Slide direction="down" in={!!error} timeout={200}>
                <Alert 
                  severity="error" 
                  sx={{ mb: 3, borderRadius: 2 }} 
                  onClose={() => setError(null)}
                >
                  {error}
                </Alert>
              </Slide>
            )}

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {/* Project Name */}
              <Box sx={{ mt: 1 }}>
                <TextField
                  label="Project Name"
                  value={projectName}
                  onChange={(e) => {
                    setProjectName(e.target.value);
                    setError(null);
                  }}
                  placeholder="e.g., Research_v1 (NLP)"
                  required
                  fullWidth
                  disabled={isLoading}
                  autoFocus
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                      transition: 'all 0.2s',
                      '&:hover': {
                        '& .MuiOutlinedInput-notchedOutline': {
                          borderColor: 'primary.main',
                        },
                      },
                      '&.Mui-focused': {
                        '& .MuiOutlinedInput-notchedOutline': {
                          borderWidth: 2,
                        },
                      },
                    },
                  }}
                />
              </Box>

              {/* Description */}
              <Box>
                <TextField
                  label="Description (Optional)"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Brief description of your project"
                  multiline
                  rows={3}
                  fullWidth
                  disabled={isLoading}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                      transition: 'all 0.2s',
                      '&:hover': {
                        '& .MuiOutlinedInput-notchedOutline': {
                          borderColor: 'primary.main',
                        },
                      },
                      '&.Mui-focused': {
                        '& .MuiOutlinedInput-notchedOutline': {
                          borderWidth: 2,
                        },
                      },
                    },
                  }}
                />
              </Box>

              {/* URL Input */}
              <Box>
                <TextField
                  label="Add URL (Optional)"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  onKeyPress={handleUrlKeyPress}
                  placeholder="Paste a link to add it to your project"
                  fullWidth
                  disabled={isLoading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LinkIcon size={18} color="#6B7280" />
                      </InputAdornment>
                    ),
                    endAdornment: urlInput.trim() && (
                      <InputAdornment position="end">
                        <IconButton
                          size="small"
                          onClick={handleAddUrl}
                          disabled={isLoading}
                          sx={{
                            color: 'primary.main',
                            '&:hover': { bgcolor: 'primary.50' },
                          }}
                        >
                          <Plus size={16} />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                      transition: 'all 0.2s',
                      '&:hover': {
                        '& .MuiOutlinedInput-notchedOutline': {
                          borderColor: 'primary.main',
                        },
                      },
                      '&.Mui-focused': {
                        '& .MuiOutlinedInput-notchedOutline': {
                          borderWidth: 2,
                        },
                      },
                    },
                  }}
                />
              </Box>

              {/* Drag & Drop Zone */}
              <Box>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.txt,.md"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                <Box
                  onDragOver={handleDragOver}
                  onDragEnter={handleDragEnter}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={handleDropZoneClick}
                  sx={{
                    border: '2px dashed',
                    borderColor: isDragging ? 'primary.main' : 'divider',
                    borderRadius: 3,
                    p: 5,
                    textAlign: 'center',
                    bgcolor: isDragging 
                      ? 'rgba(23, 23, 23, 0.04)' 
                      : 'background.default',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    cursor: 'pointer',
                    position: 'relative',
                    overflow: 'hidden',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: '-100%',
                      width: '100%',
                      height: '100%',
                      background: 'linear-gradient(90deg, transparent, rgba(23,23,23,0.05), transparent)',
                      transition: 'left 0.5s',
                    },
                    '&:hover': {
                      borderColor: 'primary.main',
                      bgcolor: 'rgba(23, 23, 23, 0.02)',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                      '&::before': {
                        left: '100%',
                      },
                    },
                    ...(isDragging && {
                      transform: 'scale(1.02)',
                      boxShadow: '0 8px 24px rgba(23,23,23,0.12)',
                    }),
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 2,
                      position: 'relative',
                      zIndex: 1,
                    }}
                  >
                    <Box
                      sx={{
                        width: 64,
                        height: 64,
                        borderRadius: '50%',
                        bgcolor: isDragging ? 'primary.main' : 'action.hover',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'all 0.3s',
                        transform: isDragging ? 'scale(1.1) rotate(5deg)' : 'scale(1)',
                      }}
                    >
                      <Upload
                        size={28}
                        style={{
                          color: isDragging ? 'white' : '#6B7280',
                          transition: 'color 0.3s',
                        }}
                      />
                    </Box>
                    <Box>
                      <Typography 
                        variant="body1" 
                        fontWeight="500"
                        color={isDragging ? 'primary.main' : 'text.primary'}
                        gutterBottom
                      >
                        {isDragging ? 'Drop files here' : 'Drag files here to upload'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        or click to browse • Supports multiple files
                      </Typography>
                    </Box>
                    <Chip
                      label="PDF, TXT, MD files"
                      size="small"
                      sx={{
                        bgcolor: 'background.paper',
                        border: '1px solid',
                        borderColor: 'divider',
                        fontSize: '0.75rem',
                      }}
                    />
                  </Box>
                </Box>
              </Box>

              {/* Items Grid (Files & URLs) */}
              {items.length > 0 && (
                <Fade in={items.length > 0} timeout={300}>
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Typography variant="caption" fontWeight="600" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <FileText size={14} />
                        {items.length} {items.length === 1 ? 'item' : 'items'} added
                      </Typography>
                      <Chip
                        label="Ready"
                        size="small"
                        icon={<CheckCircle2 size={12} />}
                        sx={{
                          bgcolor: 'success.50',
                          color: 'success.main',
                          fontSize: '0.7rem',
                          height: 20,
                        }}
                      />
                    </Box>
                    <Grid container spacing={2}>
                      {items.map((item, index) => (
                        <Grid item xs={6} sm={4} key={index}>
                          <Paper
                            elevation={0}
                            sx={{
                              p: 2,
                              borderRadius: 2.5,
                              border: '1px solid',
                              borderColor: 'divider',
                              bgcolor: 'background.paper',
                              position: 'relative',
                              transition: 'all 0.2s',
                              '&:hover': {
                                borderColor: 'primary.main',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                                transform: 'translateY(-2px)',
                                '& .remove-btn': {
                                  opacity: 1,
                                },
                              },
                            }}
                          >
                            {/* Preview Area */}
                            <Box
                              sx={{
                                width: '100%',
                                height: 120,
                                borderRadius: 1.5,
                                bgcolor: 'action.hover',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                mb: 1.5,
                                position: 'relative',
                                overflow: 'hidden',
                              }}
                            >
                              {item.type === 'url' ? (
                                <Box
                                  sx={{
                                    width: 48,
                                    height: 48,
                                    borderRadius: 1.5,
                                    bgcolor: getFileColor(item),
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'white',
                                  }}
                                >
                                  {getFileIcon(item)}
                                </Box>
                              ) : (
                                <Box
                                  sx={{
                                    width: 48,
                                    height: 48,
                                    borderRadius: 1.5,
                                    bgcolor: getFileColor(item),
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'white',
                                  }}
                                >
                                  {getFileIcon(item)}
                                </Box>
                              )}
                            </Box>

                            {/* File Info */}
                            <Box sx={{ minHeight: 40 }}>
                              {item.type === 'url' ? (
                                <>
                                  <Typography
                                    variant="body2"
                                    fontWeight="600"
                                    sx={{
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      whiteSpace: 'nowrap',
                                      mb: 0.5,
                                    }}
                                    title={item.url}
                                  >
                                    {getUrlDomain(item.url)}
                                  </Typography>
                                  <Typography
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      whiteSpace: 'nowrap',
                                      display: 'block',
                                    }}
                                    title={item.url}
                                  >
                                    {formatUrlDisplay(item.url)}
                                  </Typography>
                                </>
                              ) : (
                                <>
                                  <Typography
                                    variant="body2"
                                    fontWeight="500"
                                    sx={{
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      display: '-webkit-box',
                                      WebkitLineClamp: 2,
                                      WebkitBoxOrient: 'vertical',
                                      mb: 0.5,
                                    }}
                                  >
                                    {item.file.name}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {formatFileSize(item.file.size)}
                                  </Typography>
                                </>
                              )}
                            </Box>

                            {/* Remove Button */}
                            <IconButton
                              className="remove-btn"
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRemoveItem(index);
                              }}
                              disabled={isLoading}
                              sx={{
                                position: 'absolute',
                                top: 8,
                                right: 8,
                                bgcolor: 'background.paper',
                                color: 'error.main',
                                opacity: 0,
                                transition: 'opacity 0.2s',
                                '&:hover': {
                                  bgcolor: 'error.50',
                                },
                                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                              }}
                            >
                              <Trash2 size={14} />
                            </IconButton>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                </Fade>
              )}
            </Box>
          </>
      </DialogContent>

      {!isProcessing && (
        <DialogActions
          sx={{
            px: 3,
            py: 2.5,
            borderTop: '1px solid',
            borderColor: 'divider',
            gap: 1.5,
            bgcolor: 'background.default',
          }}
        >
          <Button
            onClick={handleClose}
            disabled={isLoading}
            sx={{
              textTransform: 'none',
              color: 'text.secondary',
              px: 2.5,
              '&:hover': {
                bgcolor: 'action.hover',
              },
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            disabled={isLoading || !projectName.trim()}
            variant="contained"
            startIcon={isLoading ? undefined : <Sparkles size={16} />}
            sx={{
              textTransform: 'none',
              bgcolor: 'primary.main',
              px: 3,
              py: 1,
              borderRadius: 2,
              fontWeight: 500,
              boxShadow: '0 2px 8px rgba(23,23,23,0.2)',
              '&:hover': {
                bgcolor: 'primary.dark',
                boxShadow: '0 4px 12px rgba(23,23,23,0.3)',
                transform: 'translateY(-1px)',
              },
              '&:disabled': {
                bgcolor: 'action.disabledBackground',
                color: 'action.disabled',
              },
              transition: 'all 0.2s',
            }}
          >
            {isLoading ? (
              <>
                <CircularProgress size={16} sx={{ mr: 1 }} />
                Creating...
              </>
            ) : (
              'Create Project'
            )}
          </Button>
        </DialogActions>
      )}
    </Dialog>
  );
}

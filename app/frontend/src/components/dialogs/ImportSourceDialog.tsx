'use client';

import { useState, useRef, DragEvent } from 'react';
import {
  Dialog,
  DialogContent,
  Box,
  Typography,
  Button,
  TextField,
  IconButton,
  InputAdornment,
} from '@mui/material';
import { X, CloudUpload, FolderOpen, Link as LinkIcon } from 'lucide-react';

interface ImportSourceDialogProps {
  open: boolean;
  onClose: () => void;
  onFileSelect: (file: File) => void;
  onUrlImport?: (url: string) => void;
  acceptedFileTypes?: string[];
  maxFileSize?: number; // in MB
}

export default function ImportSourceDialog({
  open,
  onClose,
  onFileSelect,
  onUrlImport,
  acceptedFileTypes = ['.pdf', '.docx', '.csv', '.jpg', '.jpeg'],
  maxFileSize = 25,
}: ImportSourceDialogProps) {
  const [url, setUrl] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    // Validate file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!acceptedFileTypes.includes(fileExtension)) {
      alert(`File type not supported. Accepted types: ${acceptedFileTypes.join(', ')}`);
      return;
    }

    // Validate file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxFileSize) {
      alert(`File size exceeds ${maxFileSize}MB limit.`);
      return;
    }

    onFileSelect(file);
    onClose();
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleUrlImport = () => {
    if (url.trim() && onUrlImport) {
      onUrlImport(url.trim());
      setUrl('');
      onClose();
    }
  };

  const handleClose = () => {
    setUrl('');
    setIsDragging(false);
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        },
      }}
    >
      {/* Header */}
      <Box sx={{ px: 3, py: 2.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box>
          <Typography variant="h6" fontWeight="700" sx={{ lineHeight: 1.2, mb: 0.5 }}>
            Import Source
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Add documents, data, or links to your whiteboard.
          </Typography>
        </Box>
        <IconButton onClick={handleClose} size="small" sx={{ color: 'text.secondary' }}>
          <X size={20} />
        </IconButton>
      </Box>

      <DialogContent sx={{ px: 3, py: 3 }}>
        {/* File Upload Section */}
        <Box
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          sx={{
            border: '2px dashed',
            borderColor: isDragging ? '#4f46e5' : '#E5E7EB',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            bgcolor: isDragging ? '#eff6ff' : 'transparent',
            transition: 'all 0.2s',
            mb: 4,
            cursor: 'pointer',
            '&:hover': {
              borderColor: '#4f46e5',
              bgcolor: '#f9fafb',
            },
          }}
          onClick={handleBrowseClick}
        >
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                bgcolor: '#4f46e5',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 1,
              }}
            >
              <CloudUpload size={32} color="white" />
            </Box>
            <Box>
              <Typography variant="body1" sx={{ mb: 0.5 }}>
                <Typography
                  component="span"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleBrowseClick();
                  }}
                  sx={{
                    color: '#4f46e5',
                    cursor: 'pointer',
                    fontWeight: 500,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  Click to upload
                </Typography>
                {' or drag and drop'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {acceptedFileTypes.map((ext) => ext.toUpperCase().replace('.', '')).join(', ')} (max {maxFileSize}MB)
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<FolderOpen size={16} />}
              onClick={(e) => {
                e.stopPropagation();
                handleBrowseClick();
              }}
              sx={{
                textTransform: 'none',
                borderRadius: 2,
                borderColor: '#E5E7EB',
                color: 'text.primary',
                bgcolor: 'white',
                '&:hover': {
                  borderColor: '#D1D5DB',
                  bgcolor: '#F9FAFB',
                },
              }}
            >
              Browse Files
            </Button>
          </Box>
          <input
            ref={fileInputRef}
            type="file"
            hidden
            accept={acceptedFileTypes.join(',')}
            onChange={handleFileInputChange}
          />
        </Box>

        {/* Import from URL Section */}
        <Box>
          <Typography
            variant="overline"
            sx={{
              fontSize: '0.7rem',
              fontWeight: 700,
              letterSpacing: '0.1em',
              color: 'text.secondary',
              mb: 2,
              display: 'block',
            }}
          >
            IMPORT FROM URL
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              placeholder="Paste a link to a webpage, article, or image..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleUrlImport();
                }
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LinkIcon size={18} color="#9CA3AF" />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  bgcolor: 'background.paper',
                  '& fieldset': {
                    borderColor: '#E5E7EB',
                  },
                  '&:hover fieldset': {
                    borderColor: '#D1D5DB',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#4f46e5',
                  },
                },
              }}
            />
            <Button
              variant="contained"
              onClick={handleUrlImport}
              disabled={!url.trim()}
              sx={{
                textTransform: 'none',
                borderRadius: 2,
                px: 3,
                bgcolor: '#6B7280',
                '&:hover': {
                  bgcolor: '#4B5563',
                },
                '&:disabled': {
                  bgcolor: '#E5E7EB',
                  color: '#9CA3AF',
                },
              }}
            >
              Import
            </Button>
          </Box>
        </Box>
      </DialogContent>

      {/* Footer */}
      <Box sx={{ px: 3, py: 2.5, display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid', borderColor: 'divider' }}>
        <Button
          onClick={handleClose}
          sx={{
            textTransform: 'none',
            color: 'text.secondary',
            fontWeight: 500,
          }}
        >
          Cancel
        </Button>
      </Box>
    </Dialog>
  );
}


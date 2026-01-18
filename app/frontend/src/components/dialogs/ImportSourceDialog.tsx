'use client';

import { useState, useRef, DragEvent } from 'react';
import { Modal, Button } from '@/components/ui/primitives';
import { TextField } from '@/components/ui/composites';
import {
  CloudUploadIcon,
  FolderOpenIcon,
  LinkIcon,
} from '@/components/ui/icons';
import { colors } from '@/components/ui/tokens';

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
  acceptedFileTypes = ['.pdf', '.docx', '.csv', '.jpg', '.jpeg', '.txt'],
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
      alert(
        `File type not supported. Accepted types: ${acceptedFileTypes.join(', ')}`
      );
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
    const trimmedUrl = url.trim();
    if (!trimmedUrl) return;

    // Call the URL import callback (SourcePanel handles extraction)
    if (onUrlImport) {
      onUrlImport(trimmedUrl);
    }

    setUrl('');
    onClose();
  };

  const handleClose = () => {
    setUrl('');
    setIsDragging(false);
    onClose();
  };

  return (
    <Modal open={open} onClose={handleClose} size="md">
      <Modal.Header>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span
            style={{
              fontSize: 18,
              fontWeight: 600,
              lineHeight: 1.2,
              marginBottom: 4,
            }}
          >
            Import Source
          </span>
          <span style={{ fontSize: 12, color: colors.text.secondary }}>
            Add documents, data, or links to your whiteboard.
          </span>
        </div>
      </Modal.Header>

      <Modal.Content>
        {/* File Upload Section */}
        <div
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            border: '2px dashed',
            borderColor: isDragging
              ? colors.primary[500]
              : colors.border.default,
            borderRadius: 8,
            padding: 32,
            textAlign: 'center',
            backgroundColor: isDragging ? colors.primary[50] : 'transparent',
            transition: 'all 0.2s',
            marginBottom: 32,
            cursor: 'pointer',
          }}
          onClick={handleBrowseClick}
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                backgroundColor: colors.primary[50], // Soft background
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 8,
                color: colors.primary[600], // Colored icon
              }}
            >
              <CloudUploadIcon size={32} style={{ color: 'currentColor' }} />
            </div>
            <div>
              <div style={{ marginBottom: 4 }}>
                <span
                  onClick={(e) => {
                    e.stopPropagation();
                    handleBrowseClick();
                  }}
                  style={{
                    color: colors.primary[600],
                    cursor: 'pointer',
                    fontWeight: 600,
                  }}
                >
                  Click to upload
                </span>
                <span> or drag and drop</span>
              </div>
              <div style={{ fontSize: 12, color: colors.text.secondary }}>
                {acceptedFileTypes
                  .map((ext) => ext.toUpperCase().replace('.', ''))
                  .join(', ')}{' '}
                (max {maxFileSize}MB)
              </div>
            </div>
            <Button
              variant="outline"
              icon={<FolderOpenIcon size="sm" />}
              onClick={(e) => {
                e.stopPropagation();
                handleBrowseClick();
              }}
            >
              Browse Files
            </Button>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            hidden
            accept={acceptedFileTypes.join(',')}
            onChange={handleFileInputChange}
          />
        </div>

        {/* Import from URL Section */}
        <div>
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              letterSpacing: '0.1em',
              color: colors.text.secondary,
              marginBottom: 16,
              display: 'block',
              textTransform: 'uppercase',
            }}
          >
            IMPORT FROM URL
          </span>
          <div style={{ display: 'flex', gap: 8 }}>
            <TextField
              fullWidth
              placeholder="Paste a link to a webpage, YouTube video, or article..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleUrlImport();
                }
              }}
              startAdornment={<LinkIcon size={18} color="secondary" />}
            />
            <Button
              variant="primary"
              onClick={handleUrlImport}
              disabled={!url.trim()}
            >
              Import
            </Button>
          </div>
        </div>
      </Modal.Content>

      <Modal.Footer>
        <Button variant="ghost" onClick={handleClose}>
          Cancel
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

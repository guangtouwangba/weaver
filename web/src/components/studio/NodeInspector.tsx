'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, TextField, IconButton, Drawer, Select, MenuItem, Switch, FormControlLabel, Chip } from '@mui/material';
import { X, Sparkles, GripVertical } from 'lucide-react';

interface CanvasNode {
  id: string;
  title: string;
  content?: string;
  color?: string;
  tags?: string[];
  [key: string]: any;
}

interface NodeInspectorProps {
  node: CanvasNode | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (nodeId: string, updates: Partial<CanvasNode>) => void;
}

const MIN_WIDTH = 280;
const MAX_WIDTH = 800;
const DEFAULT_WIDTH = 420;

export function NodeInspector({ node, isOpen, onClose, onUpdate }: NodeInspectorProps) {
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [isResizing, setIsResizing] = useState(false);
  const startXRef = useRef(0);
  const startWidthRef = useRef(DEFAULT_WIDTH);

  // Load saved width from localStorage
  useEffect(() => {
    const savedWidth = localStorage.getItem('inspectorWidth');
    if (savedWidth) {
      const parsedWidth = parseInt(savedWidth, 10);
      if (parsedWidth >= MIN_WIDTH && parsedWidth <= MAX_WIDTH) {
        setWidth(parsedWidth);
      }
    }
  }, []);

  // Save width to localStorage
  useEffect(() => {
    localStorage.setItem('inspectorWidth', width.toString());
  }, [width]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    startXRef.current = e.clientX;
    startWidthRef.current = width;
  };

  useEffect(() => {
    if (!isResizing) {
      document.body.classList.remove('inspector-resizing');
      return;
    }

    document.body.classList.add('inspector-resizing');

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = startXRef.current - e.clientX;
      const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidthRef.current + deltaX));
      setWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.body.classList.remove('inspector-resizing');
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.classList.remove('inspector-resizing');
    };
  }, [isResizing]);

  if (!node) return null;

  const handleUpdate = (field: string, value: any) => {
    onUpdate(node.id, { [field]: value });
  };

  return (
    <Drawer
      anchor="right"
      open={isOpen}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: width,
          bgcolor: 'white',
          boxShadow: '-4px 0 20px rgba(0,0,0,0.15)',
          transition: isResizing ? 'none' : 'width 0.2s ease',
        }
      }}
    >
      {/* Resize Handle */}
      <Box
        onMouseDown={handleMouseDown}
        sx={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: 8,
          cursor: 'ew-resize',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'background-color 0.2s',
          '&:hover': {
            bgcolor: 'rgba(59, 130, 246, 0.1)',
          },
          ...(isResizing && {
            bgcolor: 'rgba(59, 130, 246, 0.2)',
          }),
        }}
      >
        <GripVertical 
          size={16} 
          style={{ 
            color: '#94A3B8',
            opacity: isResizing ? 1 : 0.4,
            transition: 'opacity 0.2s',
          }} 
        />
      </Box>

      {/* Header */}
      <Box sx={{ 
        p: 2.5, 
        borderBottom: '1px solid', 
        borderColor: 'divider',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        bgcolor: '#FAFAFA'
      }}>
        <Typography variant="h6" fontWeight="600" sx={{ fontSize: 18 }}>
          Node Settings
        </Typography>
        <IconButton onClick={onClose} size="small" sx={{ '&:hover': { bgcolor: 'rgba(0,0,0,0.05)' } }}>
          <X size={20} />
        </IconButton>
      </Box>

      {/* Content */}
      <Box sx={{ p: 3, overflow: 'auto', height: 'calc(100% - 73px)' }}>
        {/* Title */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="caption" fontWeight="600" sx={{ mb: 1, display: 'block', color: 'text.secondary' }}>
            Label
          </Typography>
          <TextField
            fullWidth
            size="small"
            value={node.title}
            onChange={(e) => handleUpdate('title', e.target.value)}
            placeholder="Node title"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                '&:hover fieldset': {
                  borderColor: 'primary.main',
                },
              }
            }}
          />
        </Box>

        {/* Content */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="caption" fontWeight="600" sx={{ mb: 1, display: 'block', color: 'text.secondary' }}>
            Content
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            size="small"
            value={node.content || ''}
            onChange={(e) => handleUpdate('content', e.target.value)}
            placeholder="Node content..."
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              }
            }}
          />
        </Box>

        {/* Color */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="caption" fontWeight="600" sx={{ mb: 1, display: 'block', color: 'text.secondary' }}>
            Color Theme
          </Typography>
          <Select
            fullWidth
            size="small"
            value={node.color || 'blue'}
            onChange={(e) => handleUpdate('color', e.target.value)}
            sx={{ borderRadius: 2 }}
          >
            <MenuItem value="blue">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 16, height: 16, bgcolor: '#3B82F6', borderRadius: '50%' }} />
                <span>Blue</span>
              </Box>
            </MenuItem>
            <MenuItem value="purple">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 16, height: 16, bgcolor: '#A855F7', borderRadius: '50%' }} />
                <span>Purple</span>
              </Box>
            </MenuItem>
            <MenuItem value="green">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 16, height: 16, bgcolor: '#10B981', borderRadius: '50%' }} />
                <span>Green</span>
              </Box>
            </MenuItem>
            <MenuItem value="orange">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 16, height: 16, bgcolor: '#F59E0B', borderRadius: '50%' }} />
                <span>Orange</span>
              </Box>
            </MenuItem>
            <MenuItem value="red">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 16, height: 16, bgcolor: '#EF4444', borderRadius: '50%' }} />
                <span>Red</span>
              </Box>
            </MenuItem>
          </Select>
        </Box>

        {/* Tags */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="caption" fontWeight="600" sx={{ mb: 1, display: 'block', color: 'text.secondary' }}>
            Tags
          </Typography>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
            {node.tags && node.tags.map(tag => (
              <Chip 
                key={tag} 
                label={tag} 
                size="small" 
                onDelete={() => {
                  const newTags = node.tags?.filter(t => t !== tag);
                  handleUpdate('tags', newTags);
                }}
                sx={{ height: 24, fontSize: 11 }}
              />
            ))}
          </Box>
        </Box>

        <Box sx={{ borderTop: '1px solid', borderColor: 'divider', pt: 3, mb: 3 }} />

        {/* AI Configuration Section */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <Sparkles size={16} style={{ color: '#3B82F6' }} />
            <Typography variant="subtitle2" fontWeight="600">
              AI Configuration
            </Typography>
          </Box>
          
          <Typography variant="caption" fontWeight="600" sx={{ mb: 1, display: 'block', color: 'text.secondary' }}>
            Action Selection Model
          </Typography>
          <Select
            fullWidth
            size="small"
            defaultValue="gpt-3.5-turbo"
            sx={{ borderRadius: 2, mb: 2 }}
          >
            <MenuItem value="gpt-4o">GPT-4o</MenuItem>
            <MenuItem value="gpt-4o-mini">GPT-4o Mini</MenuItem>
            <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
            <MenuItem value="claude-3-5-sonnet">Claude 3.5 Sonnet</MenuItem>
          </Select>

          <Typography variant="caption" fontWeight="600" sx={{ mb: 1, display: 'block', color: 'text.secondary' }}>
            Response Model
          </Typography>
          <Select
            fullWidth
            size="small"
            defaultValue="gpt-3.5-turbo"
            sx={{ borderRadius: 2 }}
          >
            <MenuItem value="gpt-4o">GPT-4o</MenuItem>
            <MenuItem value="gpt-4o-mini">GPT-4o Mini</MenuItem>
            <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
            <MenuItem value="claude-3-5-sonnet">Claude 3.5 Sonnet</MenuItem>
          </Select>
        </Box>

        <Box sx={{ borderTop: '1px solid', borderColor: 'divider', pt: 3, mb: 3 }} />

        {/* Context Flow */}
        <Box>
          <Typography variant="subtitle2" fontWeight="600" sx={{ mb: 2 }}>
            Context Flow
          </Typography>
          
          <Box sx={{ 
            p: 2, 
            bgcolor: '#F9FAFB', 
            borderRadius: 2, 
            mb: 1.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <Box>
              <Typography variant="body2" fontWeight="500">Forward memory</Typography>
              <Typography variant="caption" color="text.secondary">To parent</Typography>
            </Box>
            <Switch defaultChecked size="small" />
          </Box>
          
          <Box sx={{ 
            p: 2, 
            bgcolor: '#F9FAFB', 
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <Box>
              <Typography variant="body2" fontWeight="500">Forward last response</Typography>
              <Typography variant="caption" color="text.secondary">To parent</Typography>
            </Box>
            <Switch size="small" />
          </Box>
        </Box>

        <Box sx={{ borderTop: '1px solid', borderColor: 'divider', pt: 3, mt: 3 }} />

        {/* Instructions */}
        <Box>
          <Typography variant="subtitle2" fontWeight="600" sx={{ mb: 2 }}>
            Instructions
          </Typography>
          
          <Typography variant="caption" fontWeight="600" sx={{ mb: 1, display: 'block', color: 'text.secondary' }}>
            Action Selection Instructions
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            size="small"
            placeholder="Enter instructions for this action..."
            sx={{
              mb: 2,
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              }
            }}
          />

          <Typography variant="caption" fontWeight="600" sx={{ mb: 1, display: 'block', color: 'text.secondary' }}>
            Response Instructions
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            size="small"
            placeholder="Instructions for response generation..."
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              }
            }}
          />
        </Box>
      </Box>
    </Drawer>
  );
}


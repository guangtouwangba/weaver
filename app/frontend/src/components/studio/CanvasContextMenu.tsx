import React, { useEffect, useRef } from 'react';
import { Box, Paper, Typography, MenuItem, ListItemIcon, ListItemText, Divider, MenuList } from '@mui/material';
import { AddIcon, StickyNote2Icon, AccountTreeIcon, LayersIcon, DescriptionIcon, UploadFileIcon, AutoAwesomeIcon, PsychologyIcon, CreditCardIcon } from '@/components/ui/icons';
import { useCanvasActions } from '@/hooks/useCanvasActions';

interface CanvasContextMenuProps {
  open: boolean;
  x: number;
  y: number;
  onClose: () => void;
  onOpenImport: () => void;
}

export default function CanvasContextMenu({ open, x, y, onClose, onOpenImport }: CanvasContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const { handleAddNode, handleGenerateContent, handleImportSource } = useCanvasActions({ onOpenImport });

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [open, onClose]);

  if (!open) return null;

  const handleAction = (action: () => void) => {
    action();
    onClose();
  };

  return (
    <Paper
      ref={menuRef}
      elevation={4}
      sx={{
        position: 'fixed',
        top: y,
        left: x,
        width: 260,
        zIndex: 1300, // Above canvas, below some dialogs
        borderRadius: 3,
        overflow: 'hidden',
        bgcolor: 'background.paper',
        boxShadow: '0px 10px 40px -10px rgba(0,0,0,0.1)',
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <MenuList dense sx={{ py: 1 }}>
        <MenuItem onClick={() => handleAction(() => handleAddNode('default', { x, y }))}>
          <ListItemIcon>
            <AddIcon size={18} />
          </ListItemIcon>
          <ListItemText>Add Node</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={() => handleAction(() => handleAddNode('sticky', { x, y }))}>
          <ListItemIcon>
            <StickyNote2Icon size={18} />
          </ListItemIcon>
          <ListItemText>Add Sticky Note</ListItemText>
        </MenuItem>

        <Divider sx={{ my: 1 }} />
        
        <Box sx={{ px: 2, py: 0.5 }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary">
            GENERATE CONTENT
          </Typography>
        </Box>

        <MenuItem onClick={() => handleAction(() => handleGenerateContent('mindmap'))}>
          <ListItemIcon>
            <AccountTreeIcon size={18} sx={{ color: '#6366f1' }} /> {/* Indigo */}
          </ListItemIcon>
          <ListItemText>Generate Mind Map</ListItemText>
        </MenuItem>

        <MenuItem onClick={() => handleAction(() => handleGenerateContent('flashcards'))}>
          <ListItemIcon>
            <CreditCardIcon size={18} sx={{ color: '#f59e0b' }} /> {/* Amber */}
          </ListItemIcon>
          <ListItemText>Generate Flashcards</ListItemText>
        </MenuItem>

        <MenuItem onClick={() => handleAction(() => handleGenerateContent('summary'))}>
          <ListItemIcon>
            <DescriptionIcon size={18} sx={{ color: '#3b82f6' }} /> {/* Blue */}
          </ListItemIcon>
          <ListItemText>Generate Summary</ListItemText>
        </MenuItem>

        <Divider sx={{ my: 1 }} />

        <MenuItem onClick={() => handleAction(handleImportSource)}>
          <ListItemIcon>
            <UploadFileIcon size={18} />
          </ListItemIcon>
          <ListItemText>Import Source...</ListItemText>
        </MenuItem>
      </MenuList>
    </Paper>
  );
}


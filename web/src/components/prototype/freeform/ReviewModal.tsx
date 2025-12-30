'use client';

import React from 'react';
import { Dialog, Box, IconButton, AppBar, Toolbar, Typography, Slide } from '@mui/material';
import { TransitionProps } from '@mui/material/transitions';
import { X, Maximize2, Minimize2, MoreHorizontal } from 'lucide-react';
import PDFReviewer from './PDFReviewer';

const Transition = React.forwardRef(function Transition(
    props: TransitionProps & { children: React.ReactElement },
    ref: React.Ref<unknown>,
) {
    return <Slide direction="up" ref={ref} {...props} />;
});

interface ReviewModalProps {
    file: {
        id: string;
        name: string;
        type: string;
    } | null;
    onClose: () => void;
    isDragging?: boolean;
    onDragStateChange?: (isDragging: boolean) => void;
    onDrop?: (e: React.DragEvent) => void;
}

export default function ReviewModal({ file, onClose, isDragging, onDragStateChange, onDrop }: ReviewModalProps) {
    if (!file) return null;

    const handleDragOver = (e: React.DragEvent) => {
        if (isDragging) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        }
    };

    return (
        <Dialog
            open={!!file}
            onClose={onClose}
            TransitionComponent={Transition}
            maxWidth="xl"
            fullWidth
            onDragOver={handleDragOver}
            onDrop={onDrop}
            PaperProps={{
                onDragOver: handleDragOver,
                onDrop: onDrop,
                sx: {
                    height: '85vh',
                    borderRadius: '16px',
                    overflow: 'hidden',
                    bgcolor: '#F3F4F6',
                    boxShadow: '0 24px 48px rgba(0,0,0,0.2), 0 0 0 1px rgba(0,0,0,0.05)',
                    transition: 'all 0.3s ease',
                    opacity: isDragging ? 0.4 : 1,
                    // Remove pointerEvents: 'none' to avoid killing the drag start
                    // pointerEvents: isDragging ? 'none' : 'auto',
                    // Allow dragging to reduce opacity so user can see canvas
                    '&:active': {
                        opacity: 0.9
                    }
                }
            }}
            sx={{
                zIndex: 1500,
                // Make the backdrop semi-transparent so we can see where to drag to
                '& .MuiBackdrop-root': {
                    backgroundColor: 'rgba(0, 0, 0, 0.2)',
                    backdropFilter: 'blur(2px)',
                    opacity: isDragging ? 0 : 1,
                    transition: 'opacity 0.3s ease',
                    pointerEvents: isDragging ? 'none' : 'auto'
                }
            }}
        >
            <Box 
                sx={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                }}
            >
                <AppBar 
                    position="static" 
                    elevation={0} 
                    sx={{ 
                        bgcolor: 'white', 
                        borderBottom: '1px solid', 
                        borderColor: 'divider',
                        color: 'text.primary' 
                    }}
                >
                    <Toolbar variant="dense">
                        <IconButton edge="start" color="inherit" onClick={onClose} aria-label="close">
                            <X size={20} />
                        </IconButton>
                        <Typography sx={{ ml: 2, flex: 1, fontWeight: 600 }} variant="subtitle1">
                            Review: {file.name}
                        </Typography>
                        <IconButton size="small" sx={{ mr: 1 }}><Minimize2 size={18} /></IconButton>
                        <IconButton size="small" sx={{ mr: 1 }}><Maximize2 size={18} /></IconButton>
                        <IconButton size="small"><MoreHorizontal size={18} /></IconButton>
                    </Toolbar>
                </AppBar>
                
                <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
                    <PDFReviewer file={file} onDragStateChange={onDragStateChange} />
                </Box>
            </Box>
        </Dialog>
    );
}









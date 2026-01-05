'use client';

import React, { useState } from 'react';
import { Paper, IconButton, Tooltip, Divider, Box, Typography } from '@mui/material';
import { 
    LayoutGrid, 
    List, 
    MousePointer2, 
    Hand, 
    Plus, 
    Minus
} from 'lucide-react';

interface CanvasToolbarProps {
    onZoomIn: () => void;
    onZoomOut: () => void;
    onReset: () => void;
    onClear: () => void;
    zoom: number;
    mode: 'select' | 'hand';
    onModeChange: (mode: 'select' | 'hand') => void;
    viewMode?: 'grid' | 'list';
    onViewModeChange?: (mode: 'grid' | 'list') => void;
}

export default function CanvasToolbar({ 
    onZoomIn, 
    onZoomOut, 
    onReset, 
    onClear, 
    zoom, 
    mode, 
    onModeChange,
    viewMode = 'grid',
    onViewModeChange
}: CanvasToolbarProps) {
    const [localViewMode, setLocalViewMode] = useState<'grid' | 'list'>(viewMode);

    const handleViewModeChange = (newMode: 'grid' | 'list') => {
        setLocalViewMode(newMode);
        onViewModeChange?.(newMode);
    };

    return (
        <Box
            sx={{
                position: 'fixed',
                bottom: 40,
                right: 40,
                display: 'flex',
                flexDirection: 'column',
                gap: 1.5,
                zIndex: 1200
            }}
        >
            {/* View Mode Toggle (Grid/List) */}
            <Paper
                elevation={2}
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: '14px',
                    overflow: 'hidden',
                    bgcolor: 'white',
                    border: '1px solid rgba(0,0,0,0.06)',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.08)'
                }}
            >
                <Tooltip title="Grid View" placement="left">
                    <IconButton 
                        onClick={() => handleViewModeChange('grid')} 
                        size="small" 
                        sx={{ 
                            p: 1.25,
                            borderRadius: 0,
                            color: localViewMode === 'grid' ? '#6366F1' : 'text.secondary',
                            bgcolor: localViewMode === 'grid' ? '#EEF2FF' : 'transparent',
                            '&:hover': {
                                bgcolor: localViewMode === 'grid' ? '#EEF2FF' : 'grey.50'
                            }
                        }}
                    >
                        <LayoutGrid size={18} />
                    </IconButton>
                </Tooltip>
                <Tooltip title="List View" placement="left">
                    <IconButton 
                        onClick={() => handleViewModeChange('list')} 
                        size="small" 
                        sx={{ 
                            p: 1.25,
                            borderRadius: 0,
                            color: localViewMode === 'list' ? '#6366F1' : 'text.secondary',
                            bgcolor: localViewMode === 'list' ? '#EEF2FF' : 'transparent',
                            '&:hover': {
                                bgcolor: localViewMode === 'list' ? '#EEF2FF' : 'grey.50'
                            }
                        }}
                    >
                        <List size={18} />
                    </IconButton>
                </Tooltip>
            </Paper>

            {/* Interaction Mode Toggle (Select/Hand) */}
            <Paper
                elevation={2}
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: '14px',
                    overflow: 'hidden',
                    bgcolor: 'white',
                    border: '1px solid rgba(0,0,0,0.06)',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.08)'
                }}
            >
                <Tooltip title="Select Mode (V)" placement="left">
                    <IconButton 
                        onClick={() => onModeChange('select')} 
                        size="small" 
                        sx={{ 
                            p: 1.25,
                            borderRadius: 0,
                            color: mode === 'select' ? '#6366F1' : 'text.secondary',
                            bgcolor: mode === 'select' ? '#EEF2FF' : 'transparent',
                            '&:hover': {
                                bgcolor: mode === 'select' ? '#EEF2FF' : 'grey.50'
                            }
                        }}
                    >
                        <MousePointer2 size={18} />
                    </IconButton>
                </Tooltip>
                <Tooltip title="Hand Mode (H)" placement="left">
                    <IconButton 
                        onClick={() => onModeChange('hand')} 
                        size="small" 
                        sx={{ 
                            p: 1.25,
                            borderRadius: 0,
                            color: mode === 'hand' ? '#6366F1' : 'text.secondary',
                            bgcolor: mode === 'hand' ? '#EEF2FF' : 'transparent',
                            '&:hover': {
                                bgcolor: mode === 'hand' ? '#EEF2FF' : 'grey.50'
                            }
                        }}
                    >
                        <Hand size={18} />
                    </IconButton>
                </Tooltip>
            </Paper>

            {/* Zoom Controls */}
            <Paper
                elevation={2}
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: '14px',
                    overflow: 'hidden',
                    bgcolor: 'white',
                    border: '1px solid rgba(0,0,0,0.06)',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.08)'
                }}
            >
                <Tooltip title="Add Node" placement="left">
                    <IconButton 
                        onClick={onReset}
                        size="small" 
                        sx={{ 
                            p: 1.25,
                            borderRadius: 0,
                            color: 'text.secondary',
                            '&:hover': {
                                bgcolor: 'grey.50'
                            }
                        }}
                    >
                        <Plus size={18} />
                    </IconButton>
                </Tooltip>
                
                <Divider />

                {/* Zoom Level Display */}
                <Tooltip title="Click to reset zoom" placement="left">
                    <Box 
                        onClick={onReset}
                        sx={{ 
                            py: 1,
                            px: 1.25,
                            textAlign: 'center',
                            cursor: 'pointer',
                            '&:hover': {
                                bgcolor: 'grey.50'
                            }
                        }}
                    >
                        <Typography 
                            variant="caption" 
                            sx={{ 
                                fontWeight: 600,
                                color: 'text.secondary',
                                fontSize: '0.7rem'
                            }}
                        >
                            {Math.round(zoom * 100)}%
                        </Typography>
                    </Box>
                </Tooltip>
                
                <Divider />

                <Tooltip title="Zoom Out" placement="left">
                    <IconButton 
                        onClick={onZoomOut} 
                        size="small" 
                        sx={{ 
                            p: 1.25,
                            borderRadius: 0,
                            color: 'text.secondary',
                            '&:hover': {
                                bgcolor: 'grey.50'
                            }
                        }}
                    >
                        <Minus size={18} />
                    </IconButton>
                </Tooltip>
            </Paper>
        </Box>
    );
}






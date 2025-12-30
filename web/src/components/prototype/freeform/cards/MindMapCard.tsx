'use client';

import React from 'react';
import { Box, Paper, Typography, IconButton } from '@mui/material';
import { Sparkles, Plus } from 'lucide-react';

export interface MindMapCardProps {
    id: string;
    name: string;
    isSelected?: boolean;
    projectColor?: string;
    onMouseDown?: (e: React.MouseEvent) => void;
    onDoubleClick?: (e: React.MouseEvent) => void;
    onExpand?: () => void;
}

export default function MindMapCard({
    id,
    name,
    isSelected = false,
    projectColor = '#6366F1',
    onMouseDown,
    onDoubleClick,
    onExpand
}: MindMapCardProps) {
    return (
        <Paper
            onMouseDown={onMouseDown}
            onDoubleClick={onDoubleClick}
            elevation={isSelected ? 8 : 3}
            sx={{
                width: 220,
                p: 2.5,
                borderRadius: '16px',
                backgroundColor: 'white',
                border: `2px solid ${isSelected ? projectColor : `${projectColor}44`}`,
                boxShadow: isSelected 
                    ? `0 8px 32px ${projectColor}33`
                    : '0 4px 16px rgba(0,0,0,0.06)',
                cursor: 'grab',
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                    borderColor: projectColor,
                    transform: 'translateY(-2px)',
                    boxShadow: `0 12px 32px ${projectColor}22`,
                },
                '&:active': { cursor: 'grabbing' },
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center'
            }}
        >
            {/* Expand Button */}
            <IconButton
                size="small"
                onClick={(e) => {
                    e.stopPropagation();
                    onExpand?.();
                }}
                sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    width: 24,
                    height: 24,
                    backgroundColor: `${projectColor}15`,
                    color: projectColor,
                    '&:hover': {
                        backgroundColor: `${projectColor}25`,
                    }
                }}
            >
                <Plus size={14} />
            </IconButton>

            {/* Icon */}
            <Box sx={{
                p: 1.5,
                borderRadius: '12px',
                backgroundColor: `${projectColor}12`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 1.5
            }}>
                <Sparkles size={24} color={projectColor} />
            </Box>

            {/* Title */}
            <Typography 
                variant="body1" 
                sx={{ 
                    fontWeight: 600,
                    color: 'text.primary',
                    fontSize: '0.95rem',
                    lineHeight: 1.3,
                    mb: 0.75
                }}
            >
                {name}
            </Typography>

            {/* Badge */}
            <Box sx={{
                px: 1.5,
                py: 0.5,
                borderRadius: '6px',
                backgroundColor: `${projectColor}12`,
            }}>
                <Typography 
                    variant="caption" 
                    sx={{ 
                        color: projectColor,
                        fontWeight: 600,
                        fontSize: '0.65rem',
                        letterSpacing: '0.05em'
                    }}
                >
                    MIND MAP
                </Typography>
            </Box>
        </Paper>
    );
}



